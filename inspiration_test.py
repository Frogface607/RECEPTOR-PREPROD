#!/usr/bin/env python3
"""
Test script for /api/generate-inspiration endpoint
Testing the "ВДОХНОВЕНИЕ" function as requested in review
"""

import requests
import json
import time
from datetime import datetime

def test_generate_inspiration():
    """Test the /api/generate-inspiration endpoint with specified test data"""
    
    # Use the public endpoint for testing
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    print("🎯 TESTING /api/generate-inspiration ENDPOINT")
    print("=" * 60)
    
    # Test data as specified in the review request
    test_data = {
        "user_id": "test_user_12345",
        "tech_card": "**Название:** Борщ украинский\n\n**Категория:** суп\n\n**Описание:** Классический борщ со свеклой и капустой\n\n**Ингредиенты:**\n- Свекла — 100 г — ~25 ₽\n- Капуста — 80 г — ~15 ₽\n- Морковь — 50 г — ~8 ₽\n\n**Пошаговый рецепт:**\n1. Нарезать свеклу\n2. Варить в бульоне\n\n**Время:** 60 минут\n\n**Выход:** 300 мл\n\n**Себестоимость:** 48 ₽",
        "inspiration_prompt": "Создай азиатский твист на это блюдо"
    }
    
    print(f"📝 Test Data:")
    print(f"   User ID: {test_data['user_id']}")
    print(f"   Inspiration Prompt: {test_data['inspiration_prompt']}")
    print(f"   Tech Card: {test_data['tech_card'][:100]}...")
    print()
    
    # Test 1: Check if endpoint works
    print("🔍 TEST 1: Endpoint Functionality")
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/generate-inspiration", json=test_data, timeout=120)
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response_time:.2f} seconds")
        
        if response.status_code == 200:
            print("   ✅ Endpoint is working")
        else:
            print(f"   ❌ Endpoint failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")
        return False
    
    # Test 2: Check response format
    print("\n🔍 TEST 2: Response Format")
    try:
        response_data = response.json()
        print(f"   Response keys: {list(response_data.keys())}")
        
        if "inspiration" in response_data:
            print("   ✅ Response contains 'inspiration' field")
        else:
            print("   ❌ Response missing 'inspiration' field")
            return False
            
    except json.JSONDecodeError:
        print("   ❌ Response is not valid JSON")
        print(f"   Raw response: {response.text[:200]}...")
        return False
    
    # Test 3: Check dish name parsing
    print("\n🔍 TEST 3: Dish Name Parsing")
    inspiration_content = response_data.get("inspiration", "")
    
    # Check if the original dish name "Борщ украинский" is referenced
    if "борщ" in inspiration_content.lower() or "украинский" in inspiration_content.lower():
        print("   ✅ Original dish name correctly parsed and referenced")
    else:
        print("   ⚠️  Original dish name may not be properly referenced")
        print(f"   Content preview: {inspiration_content[:200]}...")
    
    # Test 4: Check creative twist generation
    print("\n🔍 TEST 4: Creative Twist Generation")
    
    # Check for Asian twist elements as requested
    asian_keywords = ["азиат", "китай", "япон", "корей", "тай", "вьетнам", "соевый", "имбирь", "кунжут", "мисо", "рамен", "фо", "том", "кимчи"]
    found_asian_elements = []
    
    for keyword in asian_keywords:
        if keyword in inspiration_content.lower():
            found_asian_elements.append(keyword)
    
    if found_asian_elements:
        print(f"   ✅ Asian twist elements found: {', '.join(found_asian_elements)}")
    else:
        print("   ⚠️  No clear Asian twist elements detected")
    
    # Check content length and structure
    if len(inspiration_content) > 500:
        print("   ✅ Generated substantial content (>500 chars)")
    else:
        print(f"   ⚠️  Content seems short ({len(inspiration_content)} chars)")
    
    # Test 5: Check for required sections
    print("\n🔍 TEST 5: Content Structure")
    required_sections = ["название", "категория", "описание", "ингредиенты", "рецепт", "время", "себестоимость"]
    found_sections = []
    
    for section in required_sections:
        if section in inspiration_content.lower():
            found_sections.append(section)
    
    print(f"   Found sections: {', '.join(found_sections)}")
    if len(found_sections) >= 5:
        print("   ✅ Good content structure with multiple sections")
    else:
        print("   ⚠️  Content structure may be incomplete")
    
    # Test 6: Display sample content
    print("\n🔍 TEST 6: Generated Content Sample")
    print("   " + "="*50)
    print(f"   {inspiration_content[:500]}...")
    if len(inspiration_content) > 500:
        print("   [Content truncated for display]")
    print("   " + "="*50)
    
    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Endpoint working: YES")
    print(f"   ✅ Correct JSON format: YES") 
    print(f"   ✅ Dish name parsing: {'YES' if 'борщ' in inspiration_content.lower() else 'PARTIAL'}")
    print(f"   ✅ Creative twist: {'YES' if found_asian_elements else 'PARTIAL'}")
    print(f"   ✅ Content length: {len(inspiration_content)} characters")
    print(f"   ✅ Response time: {response_time:.2f} seconds")
    
    return True

def test_error_scenarios():
    """Test error scenarios for the inspiration endpoint"""
    
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    print("\n🔍 TESTING ERROR SCENARIOS")
    print("=" * 40)
    
    # Test 1: Missing parameters
    print("🔍 TEST: Missing parameters")
    response = requests.post(f"{base_url}/generate-inspiration", json={})
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print("   ✅ Correctly handles missing parameters")
    else:
        print(f"   ⚠️  Unexpected response: {response.text[:100]}")
    
    # Test 2: Non-PRO user (if we can test this)
    print("\n🔍 TEST: Non-PRO user access")
    non_pro_data = {
        "user_id": "free_user_test",
        "tech_card": "**Название:** Test dish",
        "inspiration_prompt": "Test prompt"
    }
    response = requests.post(f"{base_url}/generate-inspiration", json=non_pro_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 403:
        print("   ✅ Correctly blocks non-PRO users")
    elif response.status_code == 404:
        print("   ✅ User not found (expected for test user)")
    else:
        print(f"   ⚠️  Unexpected response: {response.text[:100]}")

if __name__ == "__main__":
    print("🚀 STARTING INSPIRATION ENDPOINT TESTING")
    print("Testing as requested in review requirements")
    print("=" * 60)
    
    success = test_generate_inspiration()
    
    if success:
        test_error_scenarios()
        print("\n🎉 TESTING COMPLETED SUCCESSFULLY")
    else:
        print("\n❌ TESTING FAILED - CHECK LOGS FOR DETAILS")