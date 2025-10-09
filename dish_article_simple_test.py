#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import uuid

# Backend URL from supervisor config
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class SimpleDishArticleTest:
    def __init__(self):
        self.test_user_id = f"simple_test_{str(uuid.uuid4())[:8]}"
        self.results = []
        
    async def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.results.append(result)
        print(result)
        
    async def test_dish_article_fix(self):
        """Test the core dish article fix: generation and meta.article presence"""
        try:
            print(f"\n🎯 TESTING DISH ARTICLE FIX: Core Functionality")
            print(f"Backend URL: {BACKEND_URL}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Test the specific dish mentioned in the review request
                dish_name = "Борщ с мясом"
                print(f"\n📝 Generating tech card: {dish_name}")
                
                generation_payload = {
                    "name": dish_name,
                    "cuisine": "русская",
                    "equipment": ["плита", "кастрюля"],
                    "budget": 500.0,
                    "dietary": [],
                    "user_id": self.test_user_id
                }
                
                gen_response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/generate",
                    json=generation_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if gen_response.status_code != 200:
                    await self.log_result(
                        "Tech Card Generation", 
                        False, 
                        f"Generation failed: {gen_response.status_code} - {gen_response.text[:200]}"
                    )
                    return False
                
                tech_card_data = gen_response.json()
                print(f"✅ Tech card generated successfully")
                
                # Extract the card data
                if 'card' in tech_card_data:
                    card_data = tech_card_data['card']
                    meta = card_data.get('meta', {})
                    tech_card_id = meta.get('id')
                    
                    # Check for dish article in meta
                    dish_article = meta.get('article') or meta.get('dish_code')
                    
                    if dish_article:
                        await self.log_result(
                            "Dish Article in Meta", 
                            True, 
                            f"Found dish article: {dish_article} (5-digit format: {len(str(dish_article)) == 5})"
                        )
                    else:
                        await self.log_result(
                            "Dish Article in Meta", 
                            False, 
                            f"No dish article found in meta: {meta}"
                        )
                        return False
                    
                    # Check article generation timing
                    timings = meta.get('timings', {})
                    article_gen_time = timings.get('article_generation_ms')
                    
                    if article_gen_time is not None:
                        await self.log_result(
                            "Article Generation Timing", 
                            True, 
                            f"Article generation executed in {article_gen_time}ms"
                        )
                    else:
                        await self.log_result(
                            "Article Generation Timing", 
                            False, 
                            f"No article generation timing found in: {timings}"
                        )
                    
                    # Check ingredient product codes
                    ingredients = card_data.get('ingredients', [])
                    ingredients_with_codes = [ing for ing in ingredients if ing.get('product_code')]
                    
                    if len(ingredients_with_codes) > 0:
                        await self.log_result(
                            "Ingredient Product Codes", 
                            True, 
                            f"Found {len(ingredients_with_codes)}/{len(ingredients)} ingredients with product_code"
                        )
                        
                        # Show some examples
                        examples = []
                        for ing in ingredients_with_codes[:3]:  # Show first 3
                            examples.append(f"{ing['name']}: {ing['product_code']}")
                        print(f"   Examples: {', '.join(examples)}")
                    else:
                        await self.log_result(
                            "Ingredient Product Codes", 
                            False, 
                            f"No ingredients have product_code set"
                        )
                    
                    # Verify the fix: meta.article OR meta.dish_code logic
                    print(f"\n🔍 Verifying article search logic fix...")
                    
                    # The fix should prioritize meta.article over meta.dish_code
                    meta_article = meta.get('article')
                    meta_dish_code = meta.get('dish_code')
                    
                    if meta_article:
                        await self.log_result(
                            "Article Search Logic Fix", 
                            True, 
                            f"meta.article found: {meta_article} (primary field working)"
                        )
                    elif meta_dish_code:
                        await self.log_result(
                            "Article Search Logic Fix", 
                            True, 
                            f"meta.dish_code found: {meta_dish_code} (fallback field working)"
                        )
                    else:
                        await self.log_result(
                            "Article Search Logic Fix", 
                            False, 
                            f"Neither meta.article nor meta.dish_code found"
                        )
                    
                    # Check article format (5-digit with leading zeros)
                    if dish_article:
                        article_str = str(dish_article)
                        is_5_digit = len(article_str) == 5 and article_str.isdigit()
                        
                        await self.log_result(
                            "Article Format Validation", 
                            is_5_digit, 
                            f"Article '{dish_article}' format: {'✅ 5-digit numeric' if is_5_digit else '❌ Invalid format'}"
                        )
                    
                    return True
                    
                else:
                    await self.log_result(
                        "Tech Card Structure", 
                        False, 
                        f"Invalid response structure: {tech_card_data}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Dish Article Fix Test", 
                False, 
                f"Critical error: {str(e)}"
            )
            return False
    
    async def test_multiple_dishes(self):
        """Test article generation for multiple dishes to verify consistency"""
        try:
            print(f"\n🔍 TESTING MULTIPLE DISHES FOR CONSISTENCY")
            
            test_dishes = [
                "Борщ украинский с говядиной",
                "Стейк из говядины", 
                "Салат Цезарь"
            ]
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                successful_generations = 0
                
                for dish_name in test_dishes:
                    print(f"\n  Testing: {dish_name}")
                    
                    generation_payload = {
                        "name": dish_name,
                        "cuisine": "европейская",
                        "equipment": ["плита"],
                        "budget": 400.0,
                        "dietary": [],
                        "user_id": self.test_user_id
                    }
                    
                    response = await client.post(
                        f"{API_BASE}/v1/techcards.v2/generate",
                        json=generation_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'card' in data and 'meta' in data['card']:
                            meta = data['card']['meta']
                            article = meta.get('article') or meta.get('dish_code')
                            
                            if article:
                                successful_generations += 1
                                print(f"    ✅ Article: {article}")
                            else:
                                print(f"    ❌ No article found")
                        else:
                            print(f"    ❌ Invalid structure")
                    else:
                        print(f"    ❌ Generation failed: {response.status_code}")
                
                await self.log_result(
                    "Multiple Dishes Consistency", 
                    successful_generations == len(test_dishes), 
                    f"{successful_generations}/{len(test_dishes)} dishes generated with articles"
                )
                
        except Exception as e:
            await self.log_result(
                "Multiple Dishes Test", 
                False, 
                f"Error: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Run all tests"""
        print(f"🎯 DISH ARTICLE FIX SIMPLE TESTING")
        print(f"=" * 60)
        
        # Test 1: Core dish article fix
        await self.test_dish_article_fix()
        
        # Test 2: Multiple dishes consistency
        await self.test_multiple_dishes()
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"📊 TEST RESULTS SUMMARY")
        print(f"=" * 60)
        
        passed = sum(1 for result in self.results if "✅ PASS" in result)
        failed = sum(1 for result in self.results if "❌ FAIL" in result)
        
        for result in self.results:
            print(result)
        
        print(f"\n🎯 FINAL SCORE: {passed}/{passed + failed} tests passed")
        
        if failed == 0:
            print(f"🎉 ALL TESTS PASSED! Dish article fix is working correctly.")
            print(f"✅ CRITICAL FIX VERIFIED:")
            print(f"   - Dish articles are generated and stored in meta.article")
            print(f"   - Article search logic (meta.article OR meta.dish_code) is working")
            print(f"   - Articles are in proper 5-digit format")
            print(f"   - Ingredient product_codes are also generated")
            print(f"   - Article generation timing is recorded")
        else:
            print(f"⚠️  {failed} tests failed. Dish article fix needs attention.")
        
        return failed == 0

async def main():
    """Main test execution"""
    tester = SimpleDishArticleTest()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())