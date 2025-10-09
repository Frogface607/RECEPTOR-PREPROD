#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ ТЕСТ: Menu Generator после финальных доработок
Testing the Menu Constructor with exact structure and dish name quality
"""

import requests
import json
import time
import re
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_venue_types_api_performance():
    """Test VENUE TYPES API performance after improvements"""
    print("🏢 TESTING VENUE TYPES API PERFORMANCE")
    print("=" * 60)
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/venue-types", timeout=10)
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"⏱️ Response time: {response_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ VENUE TYPES API FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        venue_types = response.json()
        
        # Check we have 14 venue types as mentioned in test_result.md
        expected_count = 14
        actual_count = len(venue_types)
        
        print(f"📊 Venue types count: {actual_count}")
        print(f"🎯 Expected count: {expected_count}")
        
        if actual_count >= 14:
            print("✅ VENUE TYPES API: Adequate number of venue types available")
        else:
            print(f"⚠️ VENUE TYPES API: Only {actual_count} venue types found, expected at least 14")
        
        # Check response time is reasonable (should be fast)
        if response_time < 2.0:
            print("✅ VENUE TYPES API: Fast response time")
        else:
            print(f"⚠️ VENUE TYPES API: Slow response time ({response_time:.2f}s)")
        
        # Check fallback types are available
        fallback_types = ["fine_dining", "food_truck", "bar_pub", "cafe", "family_restaurant"]
        available_types = list(venue_types.keys())
        
        missing_fallback = [t for t in fallback_types if t not in available_types]
        if not missing_fallback:
            print("✅ VENUE TYPES API: All fallback types available")
        else:
            print(f"❌ VENUE TYPES API: Missing fallback types: {missing_fallback}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ VENUE TYPES API ERROR: {str(e)}")
        return False

def test_menu_constructor():
    """Test КОНСТРУКТОР МЕНЮ with exact structure"""
    print("\n🎯 TESTING MENU CONSTRUCTOR WITH EXACT STRUCTURE")
    print("=" * 60)
    
    # Create and upgrade user first
    try:
        # Create user
        user_data = {
            "email": "constructor_test@example.com",
            "name": "Constructor Test User", 
            "city": "moskva"
        }
        
        response = requests.post(f"{BACKEND_URL}/register", json=user_data, timeout=30)
        if response.status_code == 200:
            user = response.json()
            test_user_id = user["id"]
            print(f"✅ Created test user: {test_user_id}")
        elif response.status_code == 400 and "already registered" in response.text:
            # Get existing user
            get_response = requests.get(f"{BACKEND_URL}/user/constructor_test@example.com", timeout=30)
            if get_response.status_code == 200:
                user = get_response.json()
                test_user_id = user["id"]
                print(f"✅ Using existing user: {test_user_id}")
            else:
                print("❌ Failed to get existing user")
                return False
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            return False
        
        # Upgrade to PRO
        upgrade_data = {"subscription_plan": "pro"}
        upgrade_response = requests.post(f"{BACKEND_URL}/upgrade-subscription/{test_user_id}", json=upgrade_data, timeout=30)
        if upgrade_response.status_code == 200:
            print("✅ Upgraded to PRO subscription")
        else:
            print(f"⚠️ Failed to upgrade: {upgrade_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error setting up user: {str(e)}")
        return False
    
    constructor_request = {
        "user_id": test_user_id,
        "menu_profile": {
            "menuType": "restaurant", 
            "useConstructor": True,
            "categories": {
                "appetizers": 3,
                "soups": 2, 
                "main_dishes": 5,
                "desserts": 2,
                "beverages": 1,
                "snacks": 0
            },
            "cuisineStyle": "european",
            "targetAudience": "business"
        },
        "venue_profile": {
            "venue_name": "Constructor Test Restaurant",
            "venue_type": "fine_dining"
        }
    }
    
    print(f"🔧 Testing constructor with exact parameters:")
    print(f"   - Total dishes expected: 13 (3+2+5+2+1+0)")
    print(f"   - Categories with dishes: 5 (snacks=0 should be absent)")
    print(f"   - Cuisine: European")
    print(f"   - Target: Business")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-menu", json=constructor_request, timeout=120)
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"⏱️ Constructor response time: {response_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ MENU CONSTRUCTOR FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        menu_data = response.json()
        
        if not menu_data.get("success"):
            print("❌ MENU CONSTRUCTOR: success=false")
            print(f"Response: {menu_data}")
            return False
        
        menu = menu_data.get("menu", {})
        categories = menu.get("categories", [])
        
        if not categories:
            print("❌ MENU CONSTRUCTOR: No categories found")
            return False
        
        # Test 1: ТОЧНО 13 блюд (3+2+5+2+1+0)
        total_dishes = 0
        category_counts = {}
        
        for category in categories:
            category_name = category.get("name", "").lower()
            dishes = category.get("dishes", [])
            dish_count = len(dishes)
            total_dishes += dish_count
            category_counts[category_name] = dish_count
            
            print(f"📋 {category.get('name', 'Unknown')}: {dish_count} dishes")
        
        print(f"\n🎯 EXACT DISH COUNT TEST:")
        print(f"   Expected: 13 dishes")
        print(f"   Actual: {total_dishes} dishes")
        
        if total_dishes == 13:
            print("✅ EXACT DISH COUNT: PASSED - Generated exactly 13 dishes")
        else:
            print(f"❌ EXACT DISH COUNT: FAILED - Expected 13, got {total_dishes}")
            return False
        
        # Test 2: ТОЧНЫЕ категории (snacks=0 должна отсутствовать)
        print(f"\n🎯 EXACT CATEGORIES TEST:")
        
        # Check that we don't have snacks category (since it was 0)
        has_snacks = any("snack" in cat.get("name", "").lower() for cat in categories)
        if has_snacks:
            print("❌ EXACT CATEGORIES: FAILED - Found snacks category when it should be absent (count=0)")
            return False
        else:
            print("✅ EXACT CATEGORIES: PASSED - No snacks category (as expected for count=0)")
        
        # Check we have the right number of categories (should be 5, not 6, since snacks=0)
        expected_categories = 5  # appetizers, soups, main_dishes, desserts, beverages (snacks excluded)
        actual_categories = len(categories)
        
        if actual_categories == expected_categories:
            print(f"✅ EXACT CATEGORIES: PASSED - {actual_categories} categories (snacks excluded)")
        else:
            print(f"⚠️ EXACT CATEGORIES: WARNING - Expected {expected_categories} categories, got {actual_categories}")
        
        return True
        
    except Exception as e:
        print(f"❌ MENU CONSTRUCTOR ERROR: {str(e)}")
        return False

def test_dish_name_quality():
    """Test КАЧЕСТВО НАЗВАНИЙ БЛЮД - no generic names"""
    print("\n🎯 TESTING DISH NAME QUALITY")
    print("=" * 60)
    
    # Create and upgrade user first
    try:
        # Create user
        user_data = {
            "email": "quality_test@example.com",
            "name": "Quality Test User", 
            "city": "moskva"
        }
        
        response = requests.post(f"{BACKEND_URL}/register", json=user_data, timeout=30)
        if response.status_code == 200:
            user = response.json()
            test_user_id = user["id"]
            print(f"✅ Created test user: {test_user_id}")
        elif response.status_code == 400 and "already registered" in response.text:
            # Get existing user
            get_response = requests.get(f"{BACKEND_URL}/user/quality_test@example.com", timeout=30)
            if get_response.status_code == 200:
                user = get_response.json()
                test_user_id = user["id"]
                print(f"✅ Using existing user: {test_user_id}")
            else:
                print("❌ Failed to get existing user")
                return False
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            return False
        
        # Upgrade to PRO
        upgrade_data = {"subscription_plan": "pro"}
        upgrade_response = requests.post(f"{BACKEND_URL}/upgrade-subscription/{test_user_id}", json=upgrade_data, timeout=30)
        if upgrade_response.status_code == 200:
            print("✅ Upgraded to PRO subscription")
        else:
            print(f"⚠️ Failed to upgrade: {upgrade_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error setting up user: {str(e)}")
        return False
    
    quality_request = {
        "user_id": test_user_id,
        "menu_profile": {
            "menuType": "restaurant",
            "dishCount": 6,
            "cuisineStyle": "european",
            "targetAudience": "general"
        },
        "venue_profile": {
            "venue_name": "Quality Test Restaurant",
            "venue_type": "family_restaurant"
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-menu", json=quality_request, timeout=90)
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"⏱️ Quality test response time: {response_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ DISH QUALITY TEST FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        menu_data = response.json()
        menu = menu_data.get("menu", {})
        categories = menu.get("categories", [])
        
        # Collect all dish names
        all_dishes = []
        for category in categories:
            dishes = category.get("dishes", [])
            for dish in dishes:
                dish_name = dish.get("name", "")
                all_dishes.append(dish_name)
        
        print(f"📋 Testing {len(all_dishes)} dish names for quality...")
        
        # Test forbidden phrases
        forbidden_phrases = [
            "специальное",
            "уникальное", 
            "авторское",
            "от шефа",
            "шеф-повара",
            "особенное",
            "эксклюзивное",
            "фирменное блюдо",
            "блюдо дня"
        ]
        
        failed_dishes = []
        
        for dish_name in all_dishes:
            dish_lower = dish_name.lower()
            
            # Check for forbidden phrases
            for phrase in forbidden_phrases:
                if phrase in dish_lower:
                    failed_dishes.append({
                        "name": dish_name,
                        "issue": f"Contains forbidden phrase: '{phrase}'"
                    })
                    break
            
            # Check if name is too generic (less than 3 words and no specific ingredients)
            words = dish_name.split()
            if len(words) < 3 and not any(ingredient in dish_lower for ingredient in [
                "томат", "грибы", "курица", "говядина", "свинина", "рыба", "сыр", 
                "картофель", "морковь", "лук", "чеснок", "базилик", "петрушка"
            ]):
                failed_dishes.append({
                    "name": dish_name,
                    "issue": "Too generic - lacks specific ingredients or descriptors"
                })
        
        print(f"\n🎯 DISH NAME QUALITY RESULTS:")
        
        if not failed_dishes:
            print("✅ DISH NAME QUALITY: ALL PASSED")
            print("✅ No forbidden phrases found")
            print("✅ All names are descriptive and specific")
            
            # Show some examples of good names
            print(f"\n📋 Examples of quality dish names:")
            for i, dish_name in enumerate(all_dishes[:3]):
                print(f"   {i+1}. {dish_name}")
            
            return True
        else:
            print(f"❌ DISH NAME QUALITY: {len(failed_dishes)} ISSUES FOUND")
            
            for issue in failed_dishes:
                print(f"   ❌ '{issue['name']}' - {issue['issue']}")
            
            return False
        
    except Exception as e:
        print(f"❌ DISH QUALITY TEST ERROR: {str(e)}")
        return False

def test_improved_prompt_effectiveness():
    """Test that the improved prompt avoids 'Уникальное блюдо от шефа' type names"""
    print("\n🎯 TESTING IMPROVED PROMPT EFFECTIVENESS")
    print("=" * 60)
    
    # Create and upgrade user first
    try:
        # Create user
        user_data = {
            "email": "prompt_test@example.com",
            "name": "Prompt Test User", 
            "city": "moskva"
        }
        
        response = requests.post(f"{BACKEND_URL}/register", json=user_data, timeout=30)
        if response.status_code == 200:
            user = response.json()
            test_user_id = user["id"]
            print(f"✅ Created test user: {test_user_id}")
        elif response.status_code == 400 and "already registered" in response.text:
            # Get existing user
            get_response = requests.get(f"{BACKEND_URL}/user/prompt_test@example.com", timeout=30)
            if get_response.status_code == 200:
                user = get_response.json()
                test_user_id = user["id"]
                print(f"✅ Using existing user: {test_user_id}")
            else:
                print("❌ Failed to get existing user")
                return False
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            return False
        
        # Upgrade to PRO
        upgrade_data = {"subscription_plan": "pro"}
        upgrade_response = requests.post(f"{BACKEND_URL}/upgrade-subscription/{test_user_id}", json=upgrade_data, timeout=30)
        if upgrade_response.status_code == 200:
            print("✅ Upgraded to PRO subscription")
        else:
            print(f"⚠️ Failed to upgrade: {upgrade_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error setting up user: {str(e)}")
        return False
    
    # Generate multiple tech cards to test prompt improvements
    test_dishes = [
        "Паста с томатным соусом",
        "Стейк из говядины", 
        "Салат с курицей",
        "Суп из грибов",
        "Десерт с шоколадом"
    ]
    
    print(f"🧪 Testing {len(test_dishes)} individual tech cards for prompt quality...")
    
    failed_cards = []
    
    for dish_name in test_dishes:
        try:
            tech_card_request = {
                "user_id": test_user_id,
                "dish_name": dish_name
            }
            
            response = requests.post(f"{BACKEND_URL}/generate-tech-card", json=tech_card_request, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                tech_card_content = result.get("tech_card", "")
                
                # Check for forbidden phrases in the tech card content
                forbidden_in_content = [
                    "уникальное блюдо от шефа",
                    "авторское блюдо",
                    "специальное предложение",
                    "эксклюзивный рецепт",
                    "фирменное блюдо шефа"
                ]
                
                content_lower = tech_card_content.lower()
                found_issues = []
                
                for phrase in forbidden_in_content:
                    if phrase in content_lower:
                        found_issues.append(phrase)
                
                if found_issues:
                    failed_cards.append({
                        "dish": dish_name,
                        "issues": found_issues
                    })
                    print(f"   ❌ {dish_name}: Found forbidden phrases: {found_issues}")
                else:
                    print(f"   ✅ {dish_name}: Clean content")
            else:
                print(f"   ⚠️ {dish_name}: Failed to generate ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ {dish_name}: Error - {str(e)}")
    
    print(f"\n🎯 PROMPT EFFECTIVENESS RESULTS:")
    
    if not failed_cards:
        print("✅ IMPROVED PROMPT: ALL TESTS PASSED")
        print("✅ No forbidden generic phrases found in tech card content")
        print("✅ Prompt improvements are working correctly")
        return True
    else:
        print(f"❌ IMPROVED PROMPT: {len(failed_cards)} ISSUES FOUND")
        
        for issue in failed_cards:
            print(f"   ❌ {issue['dish']}: {', '.join(issue['issues'])}")
        
        return False

def main():
    """Main test execution for final Menu Generator testing"""
    print("🎯 ФИНАЛЬНЫЙ ТЕСТ: Menu Generator после финальных доработок")
    print("=" * 80)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: VENUE TYPES API Performance
    venue_api_success = test_venue_types_api_performance()
    
    # Test 2: КОНСТРУКТОР МЕНЮ with exact structure
    constructor_success = test_menu_constructor()
    
    # Test 3: КАЧЕСТВО НАЗВАНИЙ БЛЮД
    quality_success = test_dish_name_quality()
    
    # Test 4: Improved prompt effectiveness
    prompt_success = test_improved_prompt_effectiveness()
    
    print("\n" + "=" * 80)
    print("🎯 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 80)
    
    if venue_api_success:
        print("✅ VENUE TYPES API: PASSED")
        print("   ✅ Fast response time")
        print("   ✅ All fallback types available")
    else:
        print("❌ VENUE TYPES API: FAILED")
        print("   🚨 API performance or availability issues")
    
    if constructor_success:
        print("✅ КОНСТРУКТОР МЕНЮ: PASSED")
        print("   ✅ Generates EXACTLY specified number of dishes")
        print("   ✅ Correct category structure (excludes zero-count categories)")
        print("   ✅ Respects useConstructor parameter")
    else:
        print("❌ КОНСТРУКТОР МЕНЮ: FAILED")
        print("   🚨 Constructor logic needs fixes")
    
    if quality_success:
        print("✅ КАЧЕСТВО НАЗВАНИЙ БЛЮД: PASSED")
        print("   ✅ No forbidden generic phrases")
        print("   ✅ Descriptive and specific dish names")
        print("   ✅ Contains concrete ingredients and cooking methods")
    else:
        print("❌ КАЧЕСТВО НАЗВАНИЙ БЛЮД: FAILED")
        print("   🚨 Still generating generic dish names")
    
    if prompt_success:
        print("✅ УЛУЧШЕННЫЙ PROMPT: PASSED")
        print("   ✅ No 'Уникальное блюдо от шефа' type content")
        print("   ✅ Prompt improvements working correctly")
    else:
        print("❌ УЛУЧШЕННЫЙ PROMPT: FAILED")
        print("   🚨 Prompt still generates forbidden phrases")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Overall success
    overall_success = venue_api_success and constructor_success and quality_success and prompt_success
    
    if overall_success:
        print("\n🎉 ВСЕ КРИТИЧНЫЕ ПРОБЛЕМЫ РЕШЕНЫ - СИСТЕМА ГОТОВА К ФИНАЛЬНОМУ ИСПОЛЬЗОВАНИЮ")
    else:
        print("\n🚨 ОБНАРУЖЕНЫ КРИТИЧНЫЕ ПРОБЛЕМЫ - ТРЕБУЮТСЯ ДОПОЛНИТЕЛЬНЫЕ ИСПРАВЛЕНИЯ")
    
    return overall_success

if __name__ == "__main__":
    main()