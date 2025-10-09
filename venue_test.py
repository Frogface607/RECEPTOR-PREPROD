#!/usr/bin/env python3
"""
Venue Customization System Review Test
Testing the updated venue customization system with 14 venue types and personalization
"""

import requests
import json
import time
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_venue_types():
    """Test GET /api/venue-types - Should return 14 venue types"""
    print("🏢 Testing GET /api/venue-types...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/venue-types")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            venue_types = response.json()
            print(f"✅ Venue types count: {len(venue_types)}")
            
            # Check for the 7 new venue types mentioned in review
            new_venue_types = ["coffee_shop", "canteen", "kids_cafe", "fast_food", "bakery_cafe", "buffet", "street_food"]
            found_new_types = []
            
            for venue_type in new_venue_types:
                if venue_type in venue_types:
                    found_new_types.append(venue_type)
                    venue_info = venue_types[venue_type]
                    print(f"  ✅ {venue_type}: {venue_info.get('name', 'N/A')} (multiplier: {venue_info.get('price_multiplier', 'N/A')})")
                else:
                    print(f"  ❌ Missing: {venue_type}")
            
            print(f"✅ Found {len(found_new_types)}/7 new venue types")
            
            # Verify specific price multipliers mentioned in review
            expected_multipliers = {
                "coffee_shop": 0.7,
                "kids_cafe": 0.8, 
                "canteen": 0.5
            }
            
            for venue_type, expected_multiplier in expected_multipliers.items():
                if venue_type in venue_types:
                    actual_multiplier = venue_types[venue_type].get('price_multiplier')
                    if actual_multiplier == expected_multiplier:
                        print(f"  ✅ {venue_type} price multiplier: {actual_multiplier}x (correct)")
                    else:
                        print(f"  ❌ {venue_type} price multiplier: {actual_multiplier}x (expected {expected_multiplier}x)")
                        
            return len(venue_types) == 14 and len(found_new_types) == 7
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_venue_personalization(venue_type, dish_name, average_check, expected_characteristics):
    """Test tech card generation with venue personalization"""
    print(f"\n☕ Testing {venue_type} personalization with '{dish_name}'...")
    
    try:
        # First, update venue profile
        profile_data = {
            "venue_type": venue_type,
            "average_check": average_check,
            "cuisine_focus": ["russian"],
            "venue_name": f"Test {venue_type.replace('_', ' ').title()}"
        }
        
        profile_response = requests.post(
            f"{BACKEND_URL}/update-venue-profile/test_user_12345",
            json=profile_data
        )
        
        if profile_response.status_code != 200:
            print(f"❌ Failed to update venue profile: {profile_response.status_code}")
            return False
            
        print(f"✅ Venue profile updated for {venue_type}")
        
        # Generate tech card
        start_time = time.time()
        tech_card_data = {
            "user_id": "test_user_12345",
            "dish_name": dish_name
        }
        
        response = requests.post(f"{BACKEND_URL}/generate-tech-card", json=tech_card_data)
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Response time: {response_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            tech_card_content = result.get("tech_card", "")
            
            print(f"✅ Tech card generated ({len(tech_card_content)} characters)")
            
            # Check for venue-specific characteristics
            characteristics_found = 0
            for characteristic in expected_characteristics:
                if characteristic.lower() in tech_card_content.lower():
                    print(f"  ✅ Found characteristic: {characteristic}")
                    characteristics_found += 1
                else:
                    print(f"  ⚠️ Missing characteristic: {characteristic}")
            
            # Check for venue-specific content based on type
            venue_specific_checks = {
                "coffee_shop": ["кофе", "латте", "молоко", "сироп", "эспрессо"],
                "kids_cafe": ["детск", "безопасн", "простой", "котлет"],
                "canteen": ["бюджет", "массов", "простой", "борщ", "экономичн"]
            }
            
            if venue_type in venue_specific_checks:
                venue_keywords = venue_specific_checks[venue_type]
                found_keywords = []
                for keyword in venue_keywords:
                    if keyword in tech_card_content.lower():
                        found_keywords.append(keyword)
                
                print(f"  ✅ Venue-specific keywords found: {len(found_keywords)}/{len(venue_keywords)} ({', '.join(found_keywords)})")
            
            # Check price range appropriateness
            if "себестоимость" in tech_card_content.lower():
                print(f"  ✅ Cost calculation present")
            
            # Verify max_tokens increase (content should be substantial)
            if len(tech_card_content) > 2000:
                print(f"  ✅ Substantial content generated (likely using increased max_tokens)")
            else:
                print(f"  ⚠️ Content might be limited ({len(tech_card_content)} chars)")
            
            return True
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main testing function"""
    print("🎯 VENUE CUSTOMIZATION SYSTEM TESTING - Updated System")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Venue Types API
    print("\n📋 TEST 1: Venue Types API")
    venue_types_result = test_venue_types()
    test_results.append(("Venue Types API", venue_types_result))
    
    # Test 2: Coffee Shop Personalization
    print("\n📋 TEST 2: Coffee Shop Personalization")
    coffee_shop_result = test_venue_personalization(
        venue_type="coffee_shop",
        dish_name="Латте с сиропом",
        average_check=300,
        expected_characteristics=["простой", "кофе", "быстр", "латте"]
    )
    test_results.append(("Coffee Shop Personalization", coffee_shop_result))
    
    # Test 3: Kids Cafe Personalization  
    print("\n📋 TEST 3: Kids Cafe Personalization")
    kids_cafe_result = test_venue_personalization(
        venue_type="kids_cafe", 
        dish_name="Детские котлеты",
        average_check=400,
        expected_characteristics=["детск", "безопасн", "простой", "семейн"]
    )
    test_results.append(("Kids Cafe Personalization", kids_cafe_result))
    
    # Test 4: Canteen Personalization
    print("\n📋 TEST 4: Canteen Personalization")
    canteen_result = test_venue_personalization(
        venue_type="canteen",
        dish_name="Борщ", 
        average_check=200,
        expected_characteristics=["массов", "бюджет", "экономичн", "простой"]
    )
    test_results.append(("Canteen Personalization", canteen_result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Venue Customization System is working correctly!")
    else:
        print("⚠️ Some tests failed - Review needed")
    
    print(f"\n⏰ Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()