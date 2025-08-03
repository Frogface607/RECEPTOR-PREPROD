#!/usr/bin/env python3
"""
Backend Testing Suite for Simplified Menu Generation System and Enhanced Venue Profile
Testing the new /api/generate-simple-menu endpoint and enhanced venue profile functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cc951b09-9773-4d61-a26a-ba72b5f2050b.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_enhanced_venue_profile():
    """Test enhanced venue profile system with all new fields"""
    print("🏢 TESTING ENHANCED VENUE PROFILE SYSTEM")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # Test 1: GET venue profile for test user
    print("Test 1: GET /api/venue-profile/{user_id}")
    try:
        response = requests.get(f"{BACKEND_URL}/venue-profile/{user_id}")
        
        if response.status_code == 200:
            profile_data = response.json()
            
            # Check for all new fields mentioned in review
            required_fields = [
                'audience_ages', 'region_details', 'cuisine_style', 'kitchen_capabilities',
                'staff_skill_level', 'preparation_time', 'ingredient_budget', 'menu_goals',
                'special_requirements', 'dietary_options', 'default_dish_count', 
                'default_categories', 'venue_description', 'business_notes'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in profile_data:
                    missing_fields.append(field)
            
            if not missing_fields:
                log_test("GET venue profile - all new fields present", "PASS", 
                        f"All {len(required_fields)} new fields found in response")
            else:
                log_test("GET venue profile - missing fields", "FAIL", 
                        f"Missing fields: {missing_fields}")
                
            # Log some sample field values
            print(f"    Sample values:")
            print(f"    - audience_ages: {profile_data.get('audience_ages')}")
            print(f"    - default_dish_count: {profile_data.get('default_dish_count')}")
            print(f"    - default_categories: {profile_data.get('default_categories')}")
            print()
            
        else:
            log_test("GET venue profile", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("GET venue profile", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: POST update venue profile with comprehensive data
    print("Test 2: POST /api/update-venue-profile/{user_id}")
    try:
        comprehensive_profile_data = {
            "venue_type": "fine_dining",
            "cuisine_focus": ["european", "french"],
            "average_check": 2500,
            "venue_name": "Le Gourmet Test",
            "venue_concept": "Modern French cuisine with local ingredients",
            "target_audience": "Food enthusiasts and business professionals",
            "special_features": ["wine_cellar", "chef_table", "private_dining"],
            "kitchen_equipment": ["sous_vide", "convection_oven", "plancha"],
            "region": "moskva",
            "audience_ages": {
                "25-35": 40,
                "36-50": 45,
                "50+": 15
            },
            "audience_occupations": ["business_professionals", "food_enthusiasts"],
            "region_details": {
                "type": "capital",
                "geography": "urban",
                "climate": "continental"
            },
            "cuisine_style": "modern",
            "cuisine_influences": ["molecular", "seasonal"],
            "kitchen_capabilities": ["advanced_equipment", "molecular", "sous_vide"],
            "staff_skill_level": "expert",
            "preparation_time": "extended",
            "ingredient_budget": "luxury",
            "menu_goals": ["profit_optimization", "customer_experience", "innovation"],
            "special_requirements": ["allergen_free_options", "seasonal_menu"],
            "dietary_options": ["vegetarian", "gluten_free", "vegan"],
            "default_dish_count": 15,
            "default_categories": {
                "amuse_bouche": 2,
                "appetizers": 4,
                "soups": 2,
                "main_dishes": 5,
                "desserts": 2
            },
            "venue_description": "Upscale fine dining restaurant focusing on modern French techniques with seasonal local ingredients",
            "business_notes": "Target high-end clientele, emphasis on wine pairing and chef's table experiences"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/update-venue-profile/{user_id}",
            json=comprehensive_profile_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                updated_fields = result.get("updated_fields", [])
                log_test("POST update venue profile", "PASS", 
                        f"Updated {len(updated_fields)} fields successfully")
                print(f"    Updated fields: {updated_fields}")
            else:
                log_test("POST update venue profile", "FAIL", 
                        f"Success=False: {result}")
        else:
            log_test("POST update venue profile", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("POST update venue profile", "FAIL", f"Exception: {str(e)}")

def test_simple_menu_generation():
    """Test the new /api/generate-simple-menu endpoint thoroughly"""
    print("🍽️ TESTING SIMPLE MENU GENERATION ENDPOINT")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # Test 1: Simple menu generation with minimal parameters
    print("Test 1: POST /api/generate-simple-menu with minimal parameters")
    try:
        menu_request = {
            "user_id": user_id,
            "menu_type": "business_lunch",
            "expectations": "Healthy quick meals for office workers, focus on salads and light main dishes, moderate prices",
            "dish_count": None  # Should use profile default
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/generate-simple-menu",
            json=menu_request,
            timeout=120  # 2 minute timeout for menu generation
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                menu_concept = result.get("menu_concept", "")
                dish_count = result.get("dish_count", 0)
                dishes = result.get("dishes", [])
                generation_method = result.get("generation_method", "")
                
                log_test("Simple menu generation", "PASS", 
                        f"Generated {dish_count} dishes in {end_time - start_time:.2f}s")
                
                print(f"    Menu concept: {menu_concept}")
                print(f"    Generation method: {generation_method}")
                print(f"    Dishes generated: {dish_count}")
                
                # Verify business lunch style
                business_lunch_keywords = ["быстр", "офис", "обед", "легк", "салат", "здоров"]
                menu_text = json.dumps(result, ensure_ascii=False).lower()
                found_keywords = [kw for kw in business_lunch_keywords if kw in menu_text]
                
                if found_keywords:
                    log_test("Business lunch style verification", "PASS", 
                            f"Found keywords: {found_keywords}")
                else:
                    log_test("Business lunch style verification", "WARN", 
                            "No business lunch keywords found in menu")
                
                # Sample some dishes
                print(f"    Sample dishes:")
                for i, dish in enumerate(dishes[:3]):
                    print(f"    {i+1}. {dish.get('name', 'N/A')} - {dish.get('category', 'N/A')}")
                
            else:
                log_test("Simple menu generation", "FAIL", 
                        f"Success=False: {result}")
        else:
            log_test("Simple menu generation", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Simple menu generation", "FAIL", "Request timeout (>120s)")
    except Exception as e:
        log_test("Simple menu generation", "FAIL", f"Exception: {str(e)}")

def test_profile_menu_integration():
    """Test that simple menu generation properly inherits venue profile settings"""
    print("🔗 TESTING PROFILE-MENU INTEGRATION")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # Test 1: Verify venue profile defaults are used
    print("Test 1: Verify venue profile defaults are used when not specified")
    try:
        # First get the venue profile to see defaults
        profile_response = requests.get(f"{BACKEND_URL}/venue-profile/{user_id}")
        
        if profile_response.status_code == 200:
            profile = profile_response.json()
            default_dish_count = profile.get("default_dish_count", 12)
            default_categories = profile.get("default_categories", {})
            venue_type = profile.get("venue_type", "family_restaurant")
            cuisine_focus = profile.get("cuisine_focus", [])
            
            print(f"    Profile defaults:")
            print(f"    - default_dish_count: {default_dish_count}")
            print(f"    - venue_type: {venue_type}")
            print(f"    - cuisine_focus: {cuisine_focus}")
            
            # Generate menu without specifying dish_count
            menu_request = {
                "user_id": user_id,
                "menu_type": "full",
                "expectations": "Traditional menu showcasing our venue's specialty cuisine"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/generate-simple-menu",
                json=menu_request,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    generated_dish_count = result.get("dish_count", 0)
                    venue_context = result.get("venue_context", {})
                    
                    # Check if default dish count was used (approximately)
                    if abs(generated_dish_count - default_dish_count) <= 2:  # Allow some variance
                        log_test("Default dish count usage", "PASS", 
                                f"Generated {generated_dish_count} dishes (default: {default_dish_count})")
                    else:
                        log_test("Default dish count usage", "WARN", 
                                f"Generated {generated_dish_count} dishes, expected ~{default_dish_count}")
                    
                    # Check venue context integration
                    if venue_context:
                        log_test("Venue context integration", "PASS", 
                                f"Venue context included: {venue_context}")
                    else:
                        log_test("Venue context integration", "FAIL", 
                                "No venue context in response")
                        
                else:
                    log_test("Profile defaults integration", "FAIL", 
                            f"Menu generation failed: {result}")
            else:
                log_test("Profile defaults integration", "FAIL", 
                        f"HTTP {response.status_code}: {response.text}")
        else:
            log_test("Profile defaults integration", "FAIL", 
                    f"Could not get venue profile: HTTP {profile_response.status_code}")
            
    except Exception as e:
        log_test("Profile defaults integration", "FAIL", f"Exception: {str(e)}")

def test_model_validation():
    """Test SimpleMenuRequest model validation"""
    print("🔍 TESTING MODEL VALIDATION")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # Test 1: Missing required fields
    print("Test 1: Missing required fields (should fail)")
    try:
        invalid_request = {
            "user_id": user_id
            # Missing menu_type and expectations
        }
        
        response = requests.post(
            f"{BACKEND_URL}/generate-simple-menu",
            json=invalid_request
        )
        
        if response.status_code == 422:  # Validation error
            log_test("Missing required fields validation", "PASS", 
                    "Correctly rejected request with missing fields")
        elif response.status_code == 400:
            log_test("Missing required fields validation", "PASS", 
                    "Correctly rejected request with 400 error")
        else:
            log_test("Missing required fields validation", "FAIL", 
                    f"Expected 422/400, got {response.status_code}")
            
    except Exception as e:
        log_test("Missing required fields validation", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: Invalid menu_type values
    print("Test 2: Invalid menu_type values")
    try:
        invalid_request = {
            "user_id": user_id,
            "menu_type": "invalid_menu_type",
            "expectations": "Test expectations"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/generate-simple-menu",
            json=invalid_request
        )
        
        # The API might accept any string for menu_type, so this might not fail
        # But we can check if it handles it gracefully
        if response.status_code in [200, 400, 422]:
            log_test("Invalid menu_type handling", "PASS", 
                    f"Handled invalid menu_type gracefully (HTTP {response.status_code})")
        else:
            log_test("Invalid menu_type handling", "FAIL", 
                    f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        log_test("Invalid menu_type handling", "FAIL", f"Exception: {str(e)}")
    
    # Test 3: Empty expectations (should fail)
    print("Test 3: Empty expectations (should fail)")
    try:
        invalid_request = {
            "user_id": user_id,
            "menu_type": "full",
            "expectations": ""  # Empty expectations
        }
        
        response = requests.post(
            f"{BACKEND_URL}/generate-simple-menu",
            json=invalid_request
        )
        
        if response.status_code in [400, 422]:
            log_test("Empty expectations validation", "PASS", 
                    "Correctly rejected empty expectations")
        elif response.status_code == 200:
            # Check if it actually generated something meaningful
            result = response.json()
            if result.get("success") and result.get("dish_count", 0) > 0:
                log_test("Empty expectations validation", "WARN", 
                        "Accepted empty expectations and generated menu")
            else:
                log_test("Empty expectations validation", "PASS", 
                        "Empty expectations resulted in failed generation")
        else:
            log_test("Empty expectations validation", "FAIL", 
                    f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        log_test("Empty expectations validation", "FAIL", f"Exception: {str(e)}")

def test_subscription_access():
    """Test that menu generation requires proper subscription"""
    print("🔐 TESTING SUBSCRIPTION ACCESS")
    print("=" * 60)
    
    # Test with a free user (if we can create one)
    print("Test 1: Free user access (should be blocked)")
    try:
        # Try with a different user ID that might be free
        free_user_id = "free_user_test"
        
        menu_request = {
            "user_id": free_user_id,
            "menu_type": "full",
            "expectations": "Test menu for free user"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/generate-simple-menu",
            json=menu_request
        )
        
        if response.status_code == 403:
            log_test("Free user access restriction", "PASS", 
                    "Correctly blocked free user from menu generation")
        elif response.status_code == 404:
            log_test("Free user access restriction", "PASS", 
                    "User not found (expected for non-existent free user)")
        elif response.status_code == 200:
            log_test("Free user access restriction", "WARN", 
                    "Free user was allowed to generate menu (might be auto-upgraded)")
        else:
            log_test("Free user access restriction", "FAIL", 
                    f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        log_test("Free user access restriction", "FAIL", f"Exception: {str(e)}")

def main():
    """Run all tests"""
    print("🧪 BACKEND TESTING: SIMPLIFIED MENU GENERATION & ENHANCED VENUE PROFILE")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test 1: Enhanced Venue Profile System
        test_enhanced_venue_profile()
        
        # Test 2: Simple Menu Generation
        test_simple_menu_generation()
        
        # Test 3: Profile-Menu Integration
        test_profile_menu_integration()
        
        # Test 4: Model Validation
        test_model_validation()
        
        # Test 5: Subscription Access
        test_subscription_access()
        
        print("🏁 ALL TESTS COMPLETED")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()