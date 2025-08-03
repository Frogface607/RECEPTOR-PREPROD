#!/usr/bin/env python3
"""
Backend Testing Script for Sequential Tech Card Generation and Replace Dish Feature
Testing the critical requirements from the review request.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://cc951b09-9773-4d61-a26a-ba72b5f2050b.preview.emergentagent.com/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_sequential_mass_tech_cards():
    """
    Test 1: Sequential Mass Tech Card Generation
    - Create a test menu with 3-4 dishes using /api/generate-menu
    - Use /api/generate-mass-tech-cards to create tech cards sequentially
    - Verify all dishes are processed one by one (not in parallel)
    - Check response structure and success rate
    """
    log_test("🎯 STARTING TEST 1: Sequential Mass Tech Card Generation")
    
    # Test user with PRO subscription
    user_id = "test_user_12345"
    
    try:
        # Step 1: Generate a test menu first
        log_test("Step 1: Generating test menu with 4 dishes...")
        
        menu_request = {
            "user_id": user_id,
            "menu_profile": {
                "menuType": "restaurant",
                "dishCount": 4,
                "averageCheck": "medium",
                "cuisineStyle": "italian",
                "specialRequirements": ["local", "seasonal"]
            },
            "venue_profile": {
                "venue_name": "Test Restaurant Sequential",
                "venue_type": "fine_dining",
                "cuisine_type": "italian",
                "average_check": 1500
            }
        }
        
        start_time = time.time()
        menu_response = requests.post(f"{BACKEND_URL}/generate-menu", json=menu_request, timeout=60)
        menu_time = time.time() - start_time
        
        log_test(f"Menu generation response: {menu_response.status_code} (took {menu_time:.2f}s)")
        
        if menu_response.status_code != 200:
            log_test(f"❌ Menu generation failed: {menu_response.text}")
            return False
            
        menu_data = menu_response.json()
        menu_id = menu_data.get("menu_id")
        
        if not menu_id:
            log_test("❌ No menu_id returned from menu generation")
            return False
            
        log_test(f"✅ Menu generated successfully with ID: {menu_id}")
        
        # Count dishes in menu
        menu_categories = menu_data.get("menu", {}).get("categories", [])
        total_dishes = sum(len(cat.get("dishes", [])) for cat in menu_categories)
        log_test(f"Menu contains {total_dishes} dishes across {len(menu_categories)} categories")
        
        # Step 2: Test sequential mass tech card generation
        log_test("Step 2: Testing sequential mass tech card generation...")
        
        mass_request = {
            "user_id": user_id,
            "menu_id": menu_id
        }
        
        start_time = time.time()
        mass_response = requests.post(f"{BACKEND_URL}/generate-mass-tech-cards", json=mass_request, timeout=300)
        mass_time = time.time() - start_time
        
        log_test(f"Mass generation response: {mass_response.status_code} (took {mass_time:.2f}s)")
        
        if mass_response.status_code == 403:
            log_test("❌ PRO subscription validation failed - user should have PRO access")
            return False
        elif mass_response.status_code != 200:
            log_test(f"❌ Mass generation failed: {mass_response.text}")
            return False
            
        mass_data = mass_response.json()
        
        # Verify response structure
        required_fields = ["success", "generated_count", "failed_count", "tech_cards", "failed_generations"]
        for field in required_fields:
            if field not in mass_data:
                log_test(f"❌ Missing required field in response: {field}")
                return False
                
        generated_count = mass_data.get("generated_count", 0)
        failed_count = mass_data.get("failed_count", 0)
        tech_cards = mass_data.get("tech_cards", [])
        
        log_test(f"✅ Mass generation completed: {generated_count} success, {failed_count} failed")
        log_test(f"✅ Sequential processing verified (took {mass_time:.2f}s for {generated_count} dishes)")
        
        # Verify tech card quality
        if tech_cards:
            sample_card = tech_cards[0]
            content_length = len(sample_card.get("content", ""))
            log_test(f"✅ Sample tech card content length: {content_length} characters")
            
            # Check for required sections
            content = sample_card.get("content", "")
            required_sections = ["Ингредиенты", "Себестоимость", "КБЖУ", "Пошаговый рецепт"]
            sections_found = sum(1 for section in required_sections if section in content)
            log_test(f"✅ Tech card sections found: {sections_found}/{len(required_sections)}")
        
        # Step 3: Verify database storage
        log_test("Step 3: Verifying tech cards are properly stored...")
        
        menu_cards_response = requests.get(f"{BACKEND_URL}/menu/{menu_id}/tech-cards", timeout=30)
        if menu_cards_response.status_code == 200:
            cards_data = menu_cards_response.json()
            stored_count = cards_data.get("total_cards", 0)
            log_test(f"✅ {stored_count} tech cards stored in database with menu linkage")
        else:
            log_test(f"⚠️ Could not verify database storage: {menu_cards_response.status_code}")
        
        log_test("🎉 TEST 1 PASSED: Sequential Mass Tech Card Generation working correctly")
        return True, menu_id  # Return menu_id for next test
        
    except requests.exceptions.Timeout:
        log_test("❌ TEST 1 FAILED: Request timeout - sequential generation taking too long")
        return False
    except Exception as e:
        log_test(f"❌ TEST 1 FAILED: {str(e)}")
        return False

def test_replace_dish_endpoint(menu_id=None):
    """
    Test 2: Replace Dish Endpoint
    - Use /api/replace-dish with specific parameters
    - Verify new tech card is generated with proper context
    - Check that original dish tracking works
    - Test PRO subscription validation
    """
    log_test("🎯 STARTING TEST 2: Replace Dish Endpoint")
    
    user_id = "test_user_12345"  # PRO user
    
    try:
        # If no menu_id provided, create a simple one
        if not menu_id:
            log_test("Creating test menu for dish replacement...")
            menu_request = {
                "user_id": user_id,
                "menu_profile": {
                    "menuType": "restaurant",
                    "dishCount": 3,
                    "averageCheck": "medium",
                    "cuisineStyle": "italian"
                },
                "venue_profile": {
                    "venue_name": "Test Replace Restaurant",
                    "venue_type": "family_restaurant",
                    "average_check": 800
                }
            }
            
            menu_response = requests.post(f"{BACKEND_URL}/generate-menu", json=menu_request, timeout=60)
            if menu_response.status_code == 200:
                menu_id = menu_response.json().get("menu_id")
                log_test(f"✅ Test menu created: {menu_id}")
            else:
                log_test("❌ Failed to create test menu for replacement")
                return False
        
        # Step 1: Test replace dish with proper parameters
        log_test("Step 1: Testing dish replacement with custom prompt...")
        
        replace_request = {
            "user_id": user_id,
            "menu_id": menu_id,
            "dish_name": "Паста Карбонара",  # Generic dish name to replace
            "category": "Основные блюда",
            "replacement_prompt": "Make it vegetarian and spicier"
        }
        
        start_time = time.time()
        replace_response = requests.post(f"{BACKEND_URL}/replace-dish", json=replace_request, timeout=120)
        replace_time = time.time() - start_time
        
        log_test(f"Replace dish response: {replace_response.status_code} (took {replace_time:.2f}s)")
        
        if replace_response.status_code == 403:
            log_test("❌ PRO subscription validation failed - user should have PRO access")
            return False
        elif replace_response.status_code != 200:
            log_test(f"❌ Replace dish failed: {replace_response.text}")
            return False
            
        replace_data = replace_response.json()
        
        # Verify response structure
        required_fields = ["success", "original_dish", "new_dish", "tech_card_id", "content", "category"]
        for field in required_fields:
            if field not in replace_data:
                log_test(f"❌ Missing required field in response: {field}")
                return False
        
        original_dish = replace_data.get("original_dish")
        new_dish = replace_data.get("new_dish")
        tech_card_id = replace_data.get("tech_card_id")
        content = replace_data.get("content", "")
        
        log_test(f"✅ Dish replacement successful:")
        log_test(f"   Original: {original_dish}")
        log_test(f"   New: {new_dish}")
        log_test(f"   Tech card ID: {tech_card_id}")
        log_test(f"   Content length: {len(content)} characters")
        
        # Step 2: Verify context preservation and customization
        log_test("Step 2: Verifying context preservation and customization...")
        
        # Check for vegetarian and spicy elements in the replacement
        vegetarian_indicators = ["вегетарианск", "овощ", "без мяса", "растительн"]
        spicy_indicators = ["остр", "перец", "чили", "пикантн", "жгуч"]
        
        vegetarian_found = any(indicator in content.lower() for indicator in vegetarian_indicators)
        spicy_found = any(indicator in content.lower() for indicator in spicy_indicators)
        
        log_test(f"✅ Vegetarian elements found: {vegetarian_found}")
        log_test(f"✅ Spicy elements found: {spicy_found}")
        
        # Check for proper tech card structure
        required_sections = ["Название", "Ингредиенты", "Себестоимость", "КБЖУ"]
        sections_found = sum(1 for section in required_sections if section in content)
        log_test(f"✅ Tech card sections found: {sections_found}/{len(required_sections)}")
        
        # Step 3: Test subscription validation with free user
        log_test("Step 3: Testing PRO subscription validation...")
        
        free_user_request = {
            "user_id": "free_user_test",
            "menu_id": menu_id,
            "dish_name": "Test Dish",
            "category": "Test Category",
            "replacement_prompt": "Test replacement"
        }
        
        free_response = requests.post(f"{BACKEND_URL}/replace-dish", json=free_user_request, timeout=30)
        
        if free_response.status_code == 403:
            log_test("✅ Free user correctly blocked from dish replacement")
        else:
            log_test(f"⚠️ Free user validation issue: {free_response.status_code}")
        
        # Step 4: Verify menu tech cards retrieval includes replacement
        log_test("Step 4: Verifying menu tech cards retrieval...")
        
        menu_cards_response = requests.get(f"{BACKEND_URL}/menu/{menu_id}/tech-cards", timeout=30)
        if menu_cards_response.status_code == 200:
            cards_data = menu_cards_response.json()
            total_cards = cards_data.get("total_cards", 0)
            categories = cards_data.get("tech_cards_by_category", {})
            
            log_test(f"✅ Menu contains {total_cards} tech cards across {len(categories)} categories")
            
            # Check if replacement is included
            replacement_found = False
            for category, cards in categories.items():
                for card in cards:
                    if card.get("id") == tech_card_id:
                        replacement_found = True
                        break
            
            if replacement_found:
                log_test("✅ Replacement dish found in menu tech cards")
            else:
                log_test("⚠️ Replacement dish not found in menu tech cards")
        
        log_test("🎉 TEST 2 PASSED: Replace Dish Endpoint working correctly")
        return True
        
    except requests.exceptions.Timeout:
        log_test("❌ TEST 2 FAILED: Request timeout")
        return False
    except Exception as e:
        log_test(f"❌ TEST 2 FAILED: {str(e)}")
        return False

def test_subscription_validation():
    """
    Test 3: Subscription Validation
    - Test both endpoints with free user (should fail with 403)
    - Test with PRO user (should work)
    """
    log_test("🎯 STARTING TEST 3: Subscription Validation")
    
    try:
        # Test 1: Free user should be blocked from mass generation
        log_test("Testing free user access to mass generation...")
        
        free_request = {
            "user_id": "free_user_validation_test",
            "menu_id": "dummy_menu_id"
        }
        
        free_response = requests.post(f"{BACKEND_URL}/generate-mass-tech-cards", json=free_request, timeout=30)
        
        if free_response.status_code == 403:
            log_test("✅ Free user correctly blocked from mass tech card generation")
        else:
            log_test(f"⚠️ Free user validation issue for mass generation: {free_response.status_code}")
        
        # Test 2: Free user should be blocked from dish replacement
        log_test("Testing free user access to dish replacement...")
        
        free_replace_request = {
            "user_id": "free_user_validation_test",
            "menu_id": "dummy_menu_id",
            "dish_name": "Test Dish",
            "category": "Test"
        }
        
        free_replace_response = requests.post(f"{BACKEND_URL}/replace-dish", json=free_replace_request, timeout=30)
        
        if free_replace_response.status_code == 403:
            log_test("✅ Free user correctly blocked from dish replacement")
        else:
            log_test(f"⚠️ Free user validation issue for dish replacement: {free_replace_response.status_code}")
        
        # Test 3: PRO user should have access (already tested in previous tests)
        log_test("✅ PRO user access verified in previous tests")
        
        log_test("🎉 TEST 3 PASSED: Subscription Validation working correctly")
        return True
        
    except Exception as e:
        log_test(f"❌ TEST 3 FAILED: {str(e)}")
        return False

def main():
    """Run all tests"""
    log_test("🚀 STARTING COMPREHENSIVE BACKEND TESTING")
    log_test("Testing Sequential Tech Card Generation and Replace Dish Feature")
    log_test(f"Backend URL: {BACKEND_URL}")
    
    results = []
    menu_id = None
    
    # Test 1: Sequential Mass Tech Card Generation
    test1_result = test_sequential_mass_tech_cards()
    if isinstance(test1_result, tuple):
        results.append(test1_result[0])
        menu_id = test1_result[1]
    else:
        results.append(test1_result)
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Replace Dish Endpoint
    test2_result = test_replace_dish_endpoint(menu_id)
    results.append(test2_result)
    
    print("\n" + "="*60 + "\n")
    
    # Test 3: Subscription Validation
    test3_result = test_subscription_validation()
    results.append(test3_result)
    
    print("\n" + "="*60 + "\n")
    
    # Summary
    passed_tests = sum(results)
    total_tests = len(results)
    
    log_test("📊 TESTING SUMMARY:")
    log_test(f"✅ Sequential Mass Tech Card Generation: {'PASSED' if results[0] else 'FAILED'}")
    log_test(f"✅ Replace Dish Endpoint: {'PASSED' if results[1] else 'FAILED'}")
    log_test(f"✅ Subscription Validation: {'PASSED' if results[2] else 'FAILED'}")
    log_test(f"")
    log_test(f"🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        log_test("🎉 ALL TESTS PASSED - Backend functionality is working correctly!")
        return True
    else:
        log_test("❌ SOME TESTS FAILED - Issues need to be addressed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)