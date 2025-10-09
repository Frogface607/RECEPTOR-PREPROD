#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
import time
from datetime import datetime
import uuid

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class RevolutionaryAITester:
    def __init__(self):
        self.test_user_id = f"revolutionary_test_{str(uuid.uuid4())[:8]}"
        self.results = []
        self.generated_tech_cards = []
        self.test_dish_name = "Борщ украинский с говядиной"
        
    async def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.results.append(result)
        print(result)
        
    async def test_real_ai_generation(self):
        """Test 1: REAL AI GENERATION with OpenAI API"""
        print(f"\n🔥 ТЕСТ 1: РЕВОЛЮЦИОННАЯ AI ГЕНЕРАЦИЯ - {self.test_dish_name}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                start_time = time.time()
                
                # Generate tech card with real LLM
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/generate?use_llm=true",
                    json={
                        "name": self.test_dish_name,
                        "user_id": self.test_user_id
                    }
                )
                
                generation_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    tech_card = data.get('card', {})
                    status = data.get('status', '')
                    
                    # Check if it's a real AI generation (not skeleton)
                    if tech_card and len(tech_card.get('ingredients', [])) > 5:
                        # Check generation time (should be 10-60 seconds for real AI)
                        if 10 <= generation_time <= 60:
                            await self.log_result(
                                "Real AI Generation", 
                                True, 
                                f"Generated in {generation_time:.1f}s with {len(tech_card.get('ingredients', []))} ingredients, status: {status}"
                            )
                            self.generated_tech_cards.append({'card': tech_card, 'response': data})
                            return tech_card, data
                        else:
                            await self.log_result(
                                "Real AI Generation", 
                                False, 
                                f"Generation time {generation_time:.1f}s suspicious (expected 10-60s), status: {status}"
                            )
                            self.generated_tech_cards.append({'card': tech_card, 'response': data})
                            return tech_card, data  # Still return for further testing
                    else:
                        await self.log_result(
                            "Real AI Generation", 
                            False, 
                            f"Generated skeleton with only {len(tech_card.get('ingredients', []))} ingredients, status: {status}"
                        )
                else:
                    await self.log_result(
                        "Real AI Generation", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
        except Exception as e:
            await self.log_result(
                "Real AI Generation", 
                False, 
                f"Exception: {str(e)}"
            )
        
        return None, None
    
    async def test_article_regression_fix(self, tech_card):
        """Test 2: ARTICLE REGRESSION FIX"""
        print(f"\n🔥 ТЕСТ 2: ИСПРАВЛЕНИЕ РЕГРЕССИИ АРТИКУЛОВ")
        
        if not tech_card:
            await self.log_result(
                "Article Regression Fix", 
                False, 
                "No tech card available for testing"
            )
            return
        
        # Check dish article
        dish_article = tech_card.get('article')
        if dish_article and dish_article != "null" and dish_article is not None:
            await self.log_result(
                "Dish Article Population", 
                True, 
                f"Dish article: {dish_article}"
            )
        else:
            await self.log_result(
                "Dish Article Population", 
                False, 
                f"CRITICAL REGRESSION: Dish article is null/empty: {dish_article} (logs show article 10000 was generated but not saved to tech card)"
            )
        
        # Check ingredient product codes
        ingredients = tech_card.get('ingredients', [])
        populated_codes = 0
        total_ingredients = len(ingredients)
        
        for ingredient in ingredients:
            product_code = ingredient.get('product_code')
            if product_code and product_code != "null" and product_code is not None:
                populated_codes += 1
        
        if populated_codes > 0:
            await self.log_result(
                "Ingredient Product Codes", 
                True, 
                f"{populated_codes}/{total_ingredients} ingredients have product_code"
            )
        else:
            await self.log_result(
                "Ingredient Product Codes", 
                False, 
                f"All {total_ingredients} ingredients have null product_code"
            )
    
    async def test_status_ready(self, tech_card, response_data=None):
        """Test 3: STATUS READY (not DRAFT)"""
        print(f"\n🔥 ТЕСТ 3: СТАТУС READY")
        
        if not tech_card:
            await self.log_result(
                "Status Ready", 
                False, 
                "No tech card available for testing"
            )
            return
        
        # Status is in the response root, not in the card
        status = response_data.get('status', '') if response_data else tech_card.get('status', '')
        if status == 'READY':
            await self.log_result(
                "Status Ready", 
                True, 
                f"Tech card status: {status}"
            )
        else:
            await self.log_result(
                "Status Ready", 
                False, 
                f"Tech card status: {status} (expected READY)"
            )
        
        # Check for validation errors
        issues = response_data.get('issues', []) if response_data else tech_card.get('issues', [])
        critical_issues = [issue for issue in issues if isinstance(issue, dict) and issue.get('level') == 'error']
        
        if len(critical_issues) == 0:
            await self.log_result(
                "No Critical Validation Errors", 
                True, 
                f"Found {len(issues)} total issues, 0 critical errors"
            )
        else:
            await self.log_result(
                "No Critical Validation Errors", 
                False, 
                f"Found {len(critical_issues)} critical validation errors"
            )
    
    async def test_database_persistence(self, tech_card):
        """Test 4: DATABASE PERSISTENCE"""
        print(f"\n🔥 ТЕСТ 4: СОХРАНЕНИЕ В БД")
        
        if not tech_card:
            await self.log_result(
                "Database Persistence", 
                False, 
                "No tech card available for testing"
            )
            return
        
        tech_card_id = tech_card.get('id') or tech_card.get('meta', {}).get('id')
        if not tech_card_id:
            await self.log_result(
                "Database Persistence", 
                False, 
                f"Tech card has no ID in card or meta: {list(tech_card.keys())}"
            )
            return
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check if tech card is saved in user history
                response = await client.get(f"{API_BASE}/user-history/{self.test_user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    history = data.get('history', [])
                    
                    # Look for our tech card in history
                    found_tech_card = None
                    for item in history:
                        if item.get('id') == tech_card_id:
                            found_tech_card = item
                            break
                    
                    if found_tech_card:
                        await self.log_result(
                            "Database Persistence", 
                            True, 
                            f"Tech card found in user history with ID: {tech_card_id}"
                        )
                        
                        # Check user_id association
                        found_user_id = found_tech_card.get('user_id') or found_tech_card.get('meta', {}).get('user_id')
                        if found_user_id == self.test_user_id:
                            await self.log_result(
                                "User ID Association", 
                                True, 
                                f"Tech card correctly associated with user: {self.test_user_id}"
                            )
                        else:
                            await self.log_result(
                                "User ID Association", 
                                False, 
                                f"Tech card user_id mismatch: {found_user_id} vs {self.test_user_id}"
                            )
                    else:
                        await self.log_result(
                            "Database Persistence", 
                            False, 
                            f"Tech card not found in user history (searched {len(history)} items)"
                        )
                else:
                    await self.log_result(
                        "Database Persistence", 
                        False, 
                        f"Failed to fetch user history: HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            await self.log_result(
                "Database Persistence", 
                False, 
                f"Exception: {str(e)}"
            )
    
    async def test_data_quality(self, tech_card):
        """Test 5: DATA QUALITY (no warning labels)"""
        print(f"\n🔥 ТЕСТ 5: КАЧЕСТВО ДАННЫХ")
        
        if not tech_card:
            await self.log_result(
                "Data Quality", 
                False, 
                "No tech card available for testing"
            )
            return
        
        # Check for warning labels in ingredients
        ingredients = tech_card.get('ingredients', [])
        warning_count = 0
        warning_types = []
        
        for ingredient in ingredients:
            name = ingredient.get('name', '')
            
            # Check for problematic warning patterns
            if 'Без SKU' in name:
                warning_count += 1
                warning_types.append('Без SKU')
            if 'no БЖУ' in name:
                warning_count += 1
                warning_types.append('no БЖУ')
            if 'no price' in name:
                warning_count += 1
                warning_types.append('no price')
        
        if warning_count == 0:
            await self.log_result(
                "No Warning Labels", 
                True, 
                f"All {len(ingredients)} ingredients clean (no warning labels)"
            )
        else:
            await self.log_result(
                "No Warning Labels", 
                False, 
                f"Found {warning_count} warning labels: {', '.join(set(warning_types))}"
            )
        
        # Check for clean IDs (UUID format, no ranges)
        tech_card_id = tech_card.get('id') or tech_card.get('meta', {}).get('id')
        if tech_card_id and '-' in tech_card_id and len(tech_card_id) > 30:
            # Looks like UUID
            await self.log_result(
                "Clean UUID Format", 
                True, 
                f"Tech card ID is clean UUID: {tech_card_id[:8]}..."
            )
        else:
            await self.log_result(
                "Clean UUID Format", 
                False, 
                f"Tech card ID is not UUID format: {tech_card_id}"
            )
    
    async def test_dashboard_display(self):
        """Test 6: DASHBOARD DISPLAY"""
        print(f"\n🔥 ТЕСТ 6: ОТОБРАЖЕНИЕ В DASHBOARD")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get user dashboard/stats
                response = await client.get(f"{API_BASE}/user-history/{self.test_user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    history = data.get('history', [])
                    
                    tech_card_count = len(history)
                    if tech_card_count > 0:
                        await self.log_result(
                            "Dashboard Display", 
                            True, 
                            f"Dashboard shows {tech_card_count} tech cards for user"
                        )
                        
                        # Check if our generated tech card is visible
                        if self.generated_tech_cards:
                            our_card_data = self.generated_tech_cards[0]
                            our_card_id = our_card_data.get('card', {}).get('id') or our_card_data.get('card', {}).get('meta', {}).get('id')
                            found = any(item.get('id') == our_card_id for item in history)
                            
                            if found:
                                await self.log_result(
                                    "Generated Card Visible", 
                                    True, 
                                    f"Our generated tech card is visible in dashboard"
                                )
                            else:
                                await self.log_result(
                                    "Generated Card Visible", 
                                    False, 
                                    f"Our generated tech card not found in dashboard (looking for ID: {our_card_id})"
                                )
                    else:
                        await self.log_result(
                            "Dashboard Display", 
                            False, 
                            "Dashboard shows 0 tech cards despite successful generation"
                        )
                else:
                    await self.log_result(
                        "Dashboard Display", 
                        False, 
                        f"Failed to fetch dashboard: HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            await self.log_result(
                "Dashboard Display", 
                False, 
                f"Exception: {str(e)}"
            )
    
    async def run_revolutionary_tests(self):
        """Run all revolutionary tests"""
        print("🔥 РЕВОЛЮЦИОННЫЙ ТЕСТ С НАСТОЯЩИМ OPENAI КЛЮЧОМ!")
        print("=" * 80)
        
        # Test 1: Real AI Generation
        tech_card, response_data = await self.test_real_ai_generation()
        
        # Test 2: Article Regression Fix
        await self.test_article_regression_fix(tech_card)
        
        # Test 3: Status Ready
        await self.test_status_ready(tech_card, response_data)
        
        # Test 4: Database Persistence
        await self.test_database_persistence(tech_card)
        
        # Test 5: Data Quality
        await self.test_data_quality(tech_card)
        
        # Test 6: Dashboard Display
        await self.test_dashboard_display()
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 РЕВОЛЮЦИОННЫЕ РЕЗУЛЬТАТЫ:")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.results if "✅ PASS" in result)
        total_tests = len(self.results)
        
        for result in self.results:
            print(result)
        
        print(f"\n🎯 ИТОГО: {passed_tests}/{total_tests} тестов пройдено")
        
        if passed_tests == total_tests:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! РЕВОЛЮЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        elif passed_tests >= total_tests * 0.8:
            print("✅ БОЛЬШИНСТВО ТЕСТОВ ПРОЙДЕНО! СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ! ТРЕБУЕТСЯ ДОРАБОТКА!")
        
        return {
            'passed': passed_tests,
            'total': total_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'results': self.results,
            'generated_tech_cards': self.generated_tech_cards
        }

async def main():
    """Main test execution"""
    tester = RevolutionaryAITester()
    results = await tester.run_revolutionary_tests()
    
    # Return exit code based on results
    if results['success_rate'] >= 0.8:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())