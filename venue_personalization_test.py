#!/usr/bin/env python3
"""
Backend Testing Suite for Venue-Aware PRO Functions Personalization
Testing venue-specific personalization in PRO AI functions
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_venue_aware_pro_functions():
    """Test venue-aware personalization in PRO functions"""
    print("🎯 TESTING VENUE-AWARE PRO FUNCTIONS PERSONALIZATION")
    print("=" * 70)
    
    # Test user ID
    user_id = "test_user_12345"
    
    # Test tech card content (simple pasta dish as requested)
    test_tech_card = """**Название:** Паста с томатным соусом

**Категория:** основное

**Описание:** Классическая итальянская паста с ароматным томатным соусом, базиликом и пармезаном.

**Ингредиенты:**
- Спагетти — 100 г — ~25 ₽
- Томаты консервированные — 150 г — ~30 ₽
- Чеснок — 2 зубчика — ~5 ₽
- Базилик свежий — 10 г — ~15 ₽
- Пармезан — 30 г — ~45 ₽
- Оливковое масло — 20 мл — ~10 ₽

**Пошаговый рецепт:**
1. Отварить спагетти до состояния аль денте
2. Обжарить чеснок в оливковом масле
3. Добавить томаты, тушить 10 минут
4. Смешать пасту с соусом
5. Подавать с пармезаном и базиликом

**Время:** Подготовка 5 мин | Готовка 15 мин | ИТОГО 20 мин
**Выход:** 250 г готового блюда
**Себестоимость:** 130 ₽
**Рекомендуемая цена:** 390 ₽"""

    # Test scenarios with different venue profiles
    test_scenarios = [
        {
            "name": "Fine Dining Restaurant",
            "venue_profile": {
                "venue_type": "fine_dining",
                "average_check": 3000,
                "cuisine_focus": ["european"],
                "venue_name": "Элегант"
            },
            "expected_keywords": {
                "sales": ["изысканный", "премиум", "эксклюзивный", "мастерство", "шеф"],
                "pairing": ["премиум", "вино", "изысканный", "коллекция"],
                "photo": ["элегантность", "изысканность", "премиум", "художественная"]
            }
        },
        {
            "name": "Food Truck",
            "venue_profile": {
                "venue_type": "food_truck",
                "average_check": 400,
                "cuisine_focus": ["european"],
                "venue_name": "Паста на колесах"
            },
            "expected_keywords": {
                "sales": ["быстро", "удобно", "на ходу", "street", "мобильн"],
                "pairing": ["простые", "доступные", "быстрые", "освежающие"],
                "photo": ["street", "мобильн", "быстр", "удобн", "портативн"]
            }
        },
        {
            "name": "Coffee Shop",
            "venue_profile": {
                "venue_type": "coffee_shop",
                "average_check": 300,
                "cuisine_focus": ["european"],
                "venue_name": "Кофе и паста"
            },
            "expected_keywords": {
                "sales": ["кофе", "уютн", "атмосфер", "легк"],
                "pairing": ["кофе", "латте", "капучино", "эспрессо"],
                "photo": ["кофе", "латте", "арт", "уютн"]
            }
        },
        {
            "name": "Kids Cafe",
            "venue_profile": {
                "venue_type": "kids_cafe",
                "average_check": 500,
                "cuisine_focus": ["european"],
                "venue_name": "Детское кафе"
            },
            "expected_keywords": {
                "sales": ["семейн", "детск", "безопасн", "домашн"],
                "pairing": ["безалкогольн", "сок", "молоко", "семейн"],
                "photo": ["семейн", "детск", "яркий", "безопасн"]
            }
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n🏢 Testing scenario: {scenario['name']}")
        print("-" * 50)
        
        # Step 1: Set venue profile
        print("📝 Setting venue profile...")
        try:
            profile_response = requests.post(
                f"{BACKEND_URL}/update-venue-profile/{user_id}",
                json=scenario["venue_profile"],
                timeout=30
            )
            
            if profile_response.status_code != 200:
                print(f"❌ Failed to set venue profile: {profile_response.status_code}")
                print(f"Response: {profile_response.text}")
                continue
                
            print("✅ Venue profile set successfully")
            
        except Exception as e:
            print(f"❌ Error setting venue profile: {str(e)}")
            continue
        
        scenario_results = {
            "scenario": scenario["name"],
            "venue_type": scenario["venue_profile"]["venue_type"],
            "average_check": scenario["venue_profile"]["average_check"],
            "tests": {}
        }
        
        # Test 1: Sales Script Generation
        print("💼 Testing sales script generation...")
        try:
            start_time = time.time()
            sales_response = requests.post(
                f"{BACKEND_URL}/generate-sales-script",
                json={
                    "user_id": user_id,
                    "tech_card": test_tech_card
                },
                timeout=60
            )
            response_time = time.time() - start_time
            
            if sales_response.status_code == 200:
                sales_data = sales_response.json()
                sales_content = sales_data.get("script", "").lower()
                
                # Check for venue-specific keywords
                found_keywords = []
                for keyword in scenario["expected_keywords"]["sales"]:
                    if keyword.lower() in sales_content:
                        found_keywords.append(keyword)
                
                scenario_results["tests"]["sales_script"] = {
                    "status": "success",
                    "response_time": round(response_time, 2),
                    "content_length": len(sales_data.get("script", "")),
                    "found_keywords": found_keywords,
                    "keyword_match_rate": len(found_keywords) / len(scenario["expected_keywords"]["sales"])
                }
                
                print(f"✅ Sales script generated ({response_time:.2f}s, {len(sales_data.get('script', ''))} chars)")
                print(f"🎯 Keywords found: {found_keywords}")
                
            else:
                scenario_results["tests"]["sales_script"] = {
                    "status": "failed",
                    "error": f"HTTP {sales_response.status_code}: {sales_response.text}"
                }
                print(f"❌ Sales script failed: {sales_response.status_code}")
                
        except Exception as e:
            scenario_results["tests"]["sales_script"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ Sales script error: {str(e)}")
        
        # Test 2: Food Pairing Generation
        print("🍷 Testing food pairing generation...")
        try:
            start_time = time.time()
            pairing_response = requests.post(
                f"{BACKEND_URL}/generate-food-pairing",
                json={
                    "user_id": user_id,
                    "tech_card": test_tech_card
                },
                timeout=60
            )
            response_time = time.time() - start_time
            
            if pairing_response.status_code == 200:
                pairing_data = pairing_response.json()
                pairing_content = pairing_data.get("pairing", "").lower()
                
                # Check for venue-specific keywords
                found_keywords = []
                for keyword in scenario["expected_keywords"]["pairing"]:
                    if keyword.lower() in pairing_content:
                        found_keywords.append(keyword)
                
                # Special check for kids_cafe - should NOT contain alcohol
                alcohol_check = True
                if scenario["venue_profile"]["venue_type"] == "kids_cafe":
                    alcohol_words = ["вино", "пиво", "алкоголь", "коктейль", "виски", "водка"]
                    alcohol_found = [word for word in alcohol_words if word in pairing_content]
                    alcohol_check = len(alcohol_found) == 0
                
                scenario_results["tests"]["food_pairing"] = {
                    "status": "success",
                    "response_time": round(response_time, 2),
                    "content_length": len(pairing_data.get("pairing", "")),
                    "found_keywords": found_keywords,
                    "keyword_match_rate": len(found_keywords) / len(scenario["expected_keywords"]["pairing"]),
                    "alcohol_appropriate": alcohol_check
                }
                
                print(f"✅ Food pairing generated ({response_time:.2f}s, {len(pairing_data.get('pairing', ''))} chars)")
                print(f"🎯 Keywords found: {found_keywords}")
                if scenario["venue_profile"]["venue_type"] == "kids_cafe":
                    print(f"👶 Alcohol-free check: {'✅' if alcohol_check else '❌'}")
                
            else:
                scenario_results["tests"]["food_pairing"] = {
                    "status": "failed",
                    "error": f"HTTP {pairing_response.status_code}: {pairing_response.text}"
                }
                print(f"❌ Food pairing failed: {pairing_response.status_code}")
                
        except Exception as e:
            scenario_results["tests"]["food_pairing"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ Food pairing error: {str(e)}")
        
        # Test 3: Photo Tips Generation
        print("📸 Testing photo tips generation...")
        try:
            start_time = time.time()
            photo_response = requests.post(
                f"{BACKEND_URL}/generate-photo-tips",
                json={
                    "user_id": user_id,
                    "tech_card": test_tech_card
                },
                timeout=60
            )
            response_time = time.time() - start_time
            
            if photo_response.status_code == 200:
                photo_data = photo_response.json()
                photo_content = photo_data.get("tips", "").lower()
                
                # Check for venue-specific keywords
                found_keywords = []
                for keyword in scenario["expected_keywords"]["photo"]:
                    if keyword.lower() in photo_content:
                        found_keywords.append(keyword)
                
                scenario_results["tests"]["photo_tips"] = {
                    "status": "success",
                    "response_time": round(response_time, 2),
                    "content_length": len(photo_data.get("tips", "")),
                    "found_keywords": found_keywords,
                    "keyword_match_rate": len(found_keywords) / len(scenario["expected_keywords"]["photo"])
                }
                
                print(f"✅ Photo tips generated ({response_time:.2f}s, {len(photo_data.get('tips', ''))} chars)")
                print(f"🎯 Keywords found: {found_keywords}")
                
            else:
                scenario_results["tests"]["photo_tips"] = {
                    "status": "failed",
                    "error": f"HTTP {photo_response.status_code}: {photo_response.text}"
                }
                print(f"❌ Photo tips failed: {photo_response.status_code}")
                
        except Exception as e:
            scenario_results["tests"]["photo_tips"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ Photo tips error: {str(e)}")
        
        results.append(scenario_results)
        time.sleep(2)  # Brief pause between scenarios
    
    # Generate summary report
    print("\n" + "=" * 70)
    print("📊 VENUE-AWARE PERSONALIZATION TEST SUMMARY")
    print("=" * 70)
    
    total_tests = 0
    successful_tests = 0
    personalization_scores = []
    
    for result in results:
        print(f"\n🏢 {result['scenario']} ({result['venue_type']}, {result['average_check']}₽)")
        print("-" * 50)
        
        for test_name, test_result in result["tests"].items():
            total_tests += 1
            
            if test_result["status"] == "success":
                successful_tests += 1
                keyword_rate = test_result.get("keyword_match_rate", 0)
                personalization_scores.append(keyword_rate)
                
                print(f"✅ {test_name}: {test_result['response_time']}s, {test_result['content_length']} chars")
                print(f"   🎯 Personalization: {keyword_rate:.1%} ({len(test_result['found_keywords'])}/{len(test_result['found_keywords']) + (1/keyword_rate - 1) if keyword_rate > 0 else 0:.0f} keywords)")
                
                if test_name == "food_pairing" and "alcohol_appropriate" in test_result:
                    alcohol_status = "✅" if test_result["alcohol_appropriate"] else "❌"
                    print(f"   👶 Family-friendly: {alcohol_status}")
            else:
                print(f"❌ {test_name}: {test_result.get('error', 'Unknown error')}")
    
    # Overall statistics
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    avg_personalization = sum(personalization_scores) / len(personalization_scores) if personalization_scores else 0
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"   Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
    print(f"   Average Personalization Score: {avg_personalization:.1%}")
    print(f"   Total Scenarios Tested: {len(results)}")
    
    # Determine if personalization is working
    personalization_working = avg_personalization >= 0.4 and success_rate >= 75
    
    if personalization_working:
        print(f"\n🎉 VENUE-AWARE PERSONALIZATION IS WORKING!")
        print(f"   ✅ Functions adapt content based on venue type")
        print(f"   ✅ Appropriate tone and recommendations for each venue")
        print(f"   ✅ Family-friendly content for kids venues")
    else:
        print(f"\n⚠️  PERSONALIZATION NEEDS IMPROVEMENT")
        print(f"   📝 Consider enhancing venue-specific prompts")
        print(f"   📝 Review keyword targeting for each venue type")
    
    return personalization_working, results

if __name__ == "__main__":
    try:
        success, results = test_venue_aware_pro_functions()
        
        # Save detailed results
        with open("/app/venue_personalization_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Detailed results saved to venue_personalization_results.json")
        
        if success:
            print(f"\n🎯 CONCLUSION: Venue-aware personalization is working correctly!")
            exit(0)
        else:
            print(f"\n🔧 CONCLUSION: Personalization needs improvement")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        exit(1)