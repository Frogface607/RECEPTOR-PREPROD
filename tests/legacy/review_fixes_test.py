#!/usr/bin/env python3
"""
Review Fixes Testing Suite
Testing the main functions after fixes as requested:

1. GET /api/iiko/health - check IIKo integration works after token fix
2. GET /api/iiko/organizations - should work with new token  
3. POST /api/generate-tech-card - main function with 'city' field fix
4. POST /api/simple-menu - simple menu generation

Focus: Verify fixes for 'city' field error, IIKo token updates, and PRO restrictions
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_iiko_health():
    """Test GET /api/iiko/health - check IIKo integration after token fix"""
    log_test("🏥 STEP 1: Testing GET /api/iiko/health - IIKo integration health check")
    
    try:
        url = f"{API_BASE}/iiko/health"
        log_test(f"Making request to: {url}")
        
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response_time = time.time() - start_time
        
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ IIKo health check successful!")
            
            # Check health status
            status = data.get('status', 'unknown')
            connection = data.get('connection', 'unknown')
            
            log_test(f"📊 IIKo Status: {status}")
            log_test(f"🔗 Connection: {connection}")
            
            if 'auth_working' in data:
                log_test(f"🔐 Authentication: {'✅ Working' if data['auth_working'] else '❌ Failed'}")
            
            if 'organizations_count' in data:
                log_test(f"🏢 Organizations found: {data['organizations_count']}")
            
            if 'menu_access' in data:
                log_test(f"📋 Menu access: {'✅ Available' if data['menu_access'] else '❌ Not available'}")
            
            # Check if token was refreshed successfully
            if status == 'healthy':
                log_test("🎉 IIKo token refresh and integration working correctly!")
                return {'success': True, 'status': status, 'connection': connection}
            else:
                log_test(f"⚠️ IIKo integration has issues: status={status}, connection={connection}")
                return {'success': False, 'status': status, 'connection': connection}
        else:
            log_test(f"❌ IIKo health check failed: HTTP {response.status_code}")
            log_test(f"Response: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error checking IIKo health: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_iiko_organizations():
    """Test GET /api/iiko/organizations - should work with new token"""
    log_test("🏢 STEP 2: Testing GET /api/iiko/organizations - verify token works")
    
    try:
        url = f"{API_BASE}/iiko/organizations"
        log_test(f"Making request to: {url}")
        
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response_time = time.time() - start_time
        
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Organizations retrieved successfully!")
            
            organizations = data.get('organizations', [])
            log_test(f"📊 Found {len(organizations)} organizations")
            
            if organizations:
                log_test("🏢 Organizations list:")
                for i, org in enumerate(organizations):
                    name = org.get('name', 'Unknown')
                    org_id = org.get('id', 'No ID')
                    address = org.get('address', 'No address')
                    active = org.get('active', False)
                    log_test(f"   {i+1}. {name} (ID: {org_id})")
                    log_test(f"      Address: {address}")
                    log_test(f"      Active: {'✅' if active else '❌'}")
                
                log_test("🎉 IIKo organizations endpoint working with updated token!")
                return {'success': True, 'organizations': organizations, 'count': len(organizations)}
            else:
                log_test("⚠️ No organizations found")
                return {'success': True, 'organizations': [], 'count': 0}
        else:
            log_test(f"❌ Organizations request failed: HTTP {response.status_code}")
            log_test(f"Response: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error getting organizations: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_generate_tech_card():
    """Test POST /api/generate-tech-card - main function with 'city' field fix"""
    log_test("🍽️ STEP 3: Testing POST /api/generate-tech-card - verify 'city' field fix")
    
    # Test data as specified in review request (using test_user_ prefix for backend compatibility)
    test_data = {
        "user_id": "test_user_12345",
        "dish_name": "Тестовое блюдо", 
        "customization": "простое блюдо для теста"
    }
    
    log_test(f"📝 Test data:")
    log_test(f"   User ID: {test_data['user_id']}")
    log_test(f"   Dish name: {test_data['dish_name']}")
    log_test(f"   Customization: {test_data['customization']}")
    
    try:
        url = f"{API_BASE}/generate-tech-card"
        log_test(f"Making request to: {url}")
        
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=120)  # Longer timeout for AI generation
        response_time = time.time() - start_time
        
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Tech card generation successful!")
            
            # Check if tech card content is present
            if 'tech_card' in data:
                tech_card = data['tech_card']
                log_test(f"📋 Tech card generated for: {test_data['dish_name']}")
                
                # Check for key sections in tech card
                content = tech_card if isinstance(tech_card, str) else str(tech_card)
                
                sections_found = []
                if 'ИНГРЕДИЕНТЫ' in content or '🥬' in content:
                    sections_found.append('Ingredients')
                if 'ВРЕМЯ' in content or '⏰' in content:
                    sections_found.append('Time')
                if 'СЕБЕСТОИМОСТЬ' in content or '💰' in content:
                    sections_found.append('Cost')
                if 'РЕЦЕПТ' in content or '👨‍🍳' in content:
                    sections_found.append('Recipe')
                
                log_test(f"📊 Tech card sections found: {', '.join(sections_found)}")
                
                # Check content length
                content_length = len(content)
                log_test(f"📏 Content length: {content_length} characters")
                
                if content_length > 500:
                    log_test("🎉 Tech card generation working correctly!")
                    log_test("✅ 'city' field error appears to be fixed")
                    log_test("✅ No 'только для про пользователей' restriction detected")
                    return {'success': True, 'tech_card': tech_card, 'sections': sections_found}
                else:
                    log_test("⚠️ Tech card seems incomplete or too short")
                    return {'success': False, 'error': 'Incomplete tech card', 'content_length': content_length}
            else:
                log_test("❌ No tech card content in response")
                log_test(f"Response keys: {list(data.keys())}")
                # Check if there's any content in other keys
                for key, value in data.items():
                    if isinstance(value, str) and len(value) > 100:
                        log_test(f"📋 Found content in '{key}': {len(value)} characters")
                        # Treat this as success if we have substantial content
                        if len(value) > 500:
                            log_test("🎉 Tech card generation working correctly!")
                            log_test("✅ 'city' field error appears to be fixed")
                            log_test("✅ No 'только для про пользователей' restriction detected")
                            return {'success': True, 'tech_card': value, 'sections': []}
                return {'success': False, 'error': 'No tech card content'}
                
        elif response.status_code == 403:
            log_test("❌ Access forbidden - PRO subscription required")
            log_test("🚨 'только для про пользователей' restriction still active!")
            return {'success': False, 'error': 'PRO subscription required', 'pro_restriction': True}
        elif response.status_code == 400:
            try:
                error_data = response.json()
                log_test(f"❌ Bad request: {error_data}")
                
                # Check for 'city' field error specifically
                error_msg = str(error_data)
                if 'city' in error_msg.lower():
                    log_test("🚨 'city' field error still present!")
                    return {'success': False, 'error': 'city field error', 'city_error': True}
                else:
                    log_test("❌ Other validation error")
                    return {'success': False, 'error': error_data}
            except:
                log_test(f"❌ Bad request: {response.text[:200]}")
                return {'success': False, 'error': f"HTTP 400: {response.text[:200]}"}
        else:
            log_test(f"❌ Tech card generation failed: HTTP {response.status_code}")
            log_test(f"Response: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error generating tech card: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_simple_menu_generation():
    """Test POST /api/simple-menu - simple menu generation"""
    log_test("📋 STEP 4: Testing POST /api/simple-menu - simple menu generation")
    
    # Test data for simple menu (using test_user_ prefix for backend compatibility)
    test_data = {
        "user_id": "test_user_12345",
        "menu_type": "business_lunch",
        "expectations": "Здоровые быстрые блюда для офисных работников, фокус на салаты и легкие основные блюда, умеренные цены"
    }
    
    log_test(f"📝 Test data:")
    log_test(f"   User ID: {test_data['user_id']}")
    log_test(f"   Menu type: {test_data['menu_type']}")
    log_test(f"   Expectations: {test_data['expectations']}")
    
    try:
        url = f"{API_BASE}/generate-simple-menu"
        log_test(f"Making request to: {url}")
        
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=120)  # Longer timeout for AI generation
        response_time = time.time() - start_time
        
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Simple menu generation successful!")
            
            # Check menu content
            if 'menu' in data:
                menu = data['menu']
                
                if isinstance(menu, list):
                    dish_count = len(menu)
                    log_test(f"📊 Generated {dish_count} dishes")
                    
                    if dish_count > 0:
                        log_test("🍽️ Sample dishes generated:")
                        for i, dish in enumerate(menu[:5]):  # Show first 5 dishes
                            dish_name = dish.get('name', 'Unknown') if isinstance(dish, dict) else str(dish)
                            log_test(f"   {i+1}. {dish_name}")
                        
                        # Check for business lunch characteristics
                        menu_text = str(menu).lower()
                        business_keywords = ['салат', 'легк', 'здоров', 'быстр', 'офис']
                        found_keywords = [kw for kw in business_keywords if kw in menu_text]
                        
                        if found_keywords:
                            log_test(f"✅ Business lunch keywords found: {found_keywords}")
                        
                        log_test("🎉 Simple menu generation working correctly!")
                        return {'success': True, 'menu': menu, 'dish_count': dish_count, 'keywords': found_keywords}
                    else:
                        log_test("⚠️ Empty menu generated")
                        return {'success': False, 'error': 'Empty menu'}
                else:
                    log_test(f"⚠️ Unexpected menu format: {type(menu)}")
                    return {'success': False, 'error': 'Unexpected menu format'}
            elif 'dishes' in data:
                # Check if dishes are in 'dishes' key instead
                dishes = data['dishes']
                dish_count = data.get('dish_count', len(dishes) if isinstance(dishes, list) else 0)
                
                log_test(f"📊 Generated {dish_count} dishes (found in 'dishes' key)")
                
                if isinstance(dishes, list) and len(dishes) > 0:
                    log_test("🍽️ Sample dishes generated:")
                    for i, dish in enumerate(dishes[:5]):  # Show first 5 dishes
                        dish_name = dish.get('name', 'Unknown') if isinstance(dish, dict) else str(dish)
                        log_test(f"   {i+1}. {dish_name}")
                    
                    # Check for business lunch characteristics
                    dishes_text = str(dishes).lower()
                    business_keywords = ['салат', 'легк', 'здоров', 'быстр', 'офис']
                    found_keywords = [kw for kw in business_keywords if kw in dishes_text]
                    
                    if found_keywords:
                        log_test(f"✅ Business lunch keywords found: {found_keywords}")
                    
                    log_test("🎉 Simple menu generation working correctly!")
                    return {'success': True, 'menu': dishes, 'dish_count': dish_count, 'keywords': found_keywords}
                else:
                    log_test("⚠️ Empty dishes list")
                    return {'success': False, 'error': 'Empty dishes list'}
            else:
                log_test("❌ No menu content in response")
                log_test(f"Response keys: {list(data.keys())}")
                return {'success': False, 'error': 'No menu content'}
                
        elif response.status_code == 403:
            log_test("❌ Access forbidden - PRO subscription required")
            log_test("🚨 'только для про пользователей' restriction detected!")
            return {'success': False, 'error': 'PRO subscription required', 'pro_restriction': True}
        else:
            log_test(f"❌ Simple menu generation failed: HTTP {response.status_code}")
            log_test(f"Response: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error generating simple menu: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main testing function for review fixes"""
    log_test("🚀 Starting Review Fixes Testing")
    log_test("🎯 Focus: Verify fixes for 'city' field, IIKo token, and PRO restrictions")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Test results storage
    results = {}
    
    # Step 1: Test IIKo health
    results['iiko_health'] = test_iiko_health()
    log_test("\n" + "=" * 80)
    
    # Step 2: Test IIKo organizations
    results['iiko_organizations'] = test_iiko_organizations()
    log_test("\n" + "=" * 80)
    
    # Step 3: Test tech card generation
    results['tech_card'] = test_generate_tech_card()
    log_test("\n" + "=" * 80)
    
    # Step 4: Test simple menu generation
    results['simple_menu'] = test_simple_menu_generation()
    log_test("\n" + "=" * 80)
    
    # Summary
    log_test("📋 REVIEW FIXES TESTING SUMMARY:")
    log_test("=" * 80)
    
    # IIKo Integration
    iiko_health_ok = results['iiko_health']['success']
    iiko_orgs_ok = results['iiko_organizations']['success']
    log_test(f"🏥 IIKo Health Check: {'✅ PASSED' if iiko_health_ok else '❌ FAILED'}")
    log_test(f"🏢 IIKo Organizations: {'✅ PASSED' if iiko_orgs_ok else '❌ FAILED'}")
    
    if iiko_health_ok and iiko_orgs_ok:
        log_test("🎉 IIKo integration working after token fix!")
    else:
        log_test("⚠️ IIKo integration still has issues")
    
    # Tech Card Generation
    tech_card_ok = results['tech_card']['success']
    city_error = results['tech_card'].get('city_error', False)
    pro_restriction_tech = results['tech_card'].get('pro_restriction', False)
    
    log_test(f"🍽️ Tech Card Generation: {'✅ PASSED' if tech_card_ok else '❌ FAILED'}")
    
    if city_error:
        log_test("🚨 'city' field error still present!")
    elif tech_card_ok:
        log_test("✅ 'city' field error appears to be fixed")
    
    if pro_restriction_tech:
        log_test("🚨 PRO restriction still active for tech cards!")
    elif tech_card_ok:
        log_test("✅ No PRO restriction detected for tech cards")
    
    # Simple Menu Generation
    simple_menu_ok = results['simple_menu']['success']
    pro_restriction_menu = results['simple_menu'].get('pro_restriction', False)
    
    log_test(f"📋 Simple Menu Generation: {'✅ PASSED' if simple_menu_ok else '❌ FAILED'}")
    
    if pro_restriction_menu:
        log_test("🚨 PRO restriction still active for simple menu!")
    elif simple_menu_ok:
        log_test("✅ No PRO restriction detected for simple menu")
    
    # Overall Assessment
    log_test("\n" + "=" * 80)
    log_test("🎯 OVERALL ASSESSMENT:")
    
    all_passed = iiko_health_ok and iiko_orgs_ok and tech_card_ok and simple_menu_ok
    critical_issues = city_error or pro_restriction_tech or pro_restriction_menu
    
    if all_passed and not critical_issues:
        log_test("🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        log_test("✅ IIKo integration working with updated token")
        log_test("✅ 'city' field error resolved")
        log_test("✅ Main functionality working without PRO restrictions")
        log_test("✅ Application ready for use")
    else:
        log_test("⚠️ Some issues still present:")
        if not iiko_health_ok or not iiko_orgs_ok:
            log_test("   - IIKo integration needs attention")
        if city_error:
            log_test("   - 'city' field error not fully resolved")
        if pro_restriction_tech or pro_restriction_menu:
            log_test("   - PRO restrictions still blocking functionality")
        if not tech_card_ok:
            log_test("   - Tech card generation has issues")
        if not simple_menu_ok:
            log_test("   - Simple menu generation has issues")
    
    log_test("=" * 80)
    
    return results

if __name__ == "__main__":
    main()