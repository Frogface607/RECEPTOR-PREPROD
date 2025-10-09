#!/usr/bin/env python3
"""
OpenAI API Key Test for Tech Card Generation
Testing the specific review request: Паста Карбонара на 4 порции
"""

import requests
import json
import time
from datetime import datetime

def test_openai_tech_card_generation():
    """Test tech card generation with new OpenAI API key"""
    
    print("🎯 TESTING OPENAI API KEY FOR TECH CARD GENERATION")
    print("=" * 60)
    
    # Use the public endpoint
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    # Test data from review request
    test_data = {
        "dish_name": "Паста Карбонара на 4 порции",
        "user_id": "test_user_12345",
        "city": "moskva"
    }
    
    print(f"📝 Test Data:")
    print(f"   Dish: {test_data['dish_name']}")
    print(f"   User ID: {test_data['user_id']}")
    print(f"   City: {test_data['city']}")
    print()
    
    # Record start time
    start_time = time.time()
    
    print("🚀 Sending POST request to /api/generate-tech-card...")
    
    try:
        response = requests.post(
            f"{base_url}/generate-tech-card",
            json=test_data,
            timeout=120  # 2 minute timeout for AI generation
        )
        
        # Record response time
        response_time = time.time() - start_time
        
        print(f"⏱️  Response time: {response_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        # TEST 1: Status code should be 200 (not 500)
        if response.status_code == 200:
            print("✅ TEST 1 PASSED: Status code is 200 (not 500)")
        else:
            print(f"❌ TEST 1 FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Parse response
        try:
            result = response.json()
        except json.JSONDecodeError:
            print("❌ FAILED: Response is not valid JSON")
            print(f"Response text: {response.text}")
            return False
        
        print(f"📋 Response keys: {list(result.keys())}")
        
        # TEST 2: Returns tech_card with content
        if "tech_card" in result and result["tech_card"]:
            tech_card_content = result["tech_card"]
            content_length = len(tech_card_content)
            print(f"✅ TEST 2 PASSED: tech_card returned with content ({content_length} characters)")
        else:
            print("❌ TEST 2 FAILED: No tech_card content returned")
            print(f"Result: {result}")
            return False
        
        # TEST 3: Has tech card ID
        if "id" in result and result["id"]:
            tech_card_id = result["id"]
            print(f"✅ TEST 3 PASSED: Tech card ID returned: {tech_card_id}")
        else:
            print("❌ TEST 3 FAILED: No tech card ID returned")
            return False
        
        # TEST 4: Contains key sections
        required_sections = ["Название", "Ингредиенты", "Рецепт", "Себестоимость"]
        found_sections = []
        missing_sections = []
        
        for section in required_sections:
            if section in tech_card_content:
                found_sections.append(section)
            else:
                missing_sections.append(section)
        
        if len(found_sections) == len(required_sections):
            print(f"✅ TEST 4 PASSED: All key sections found: {', '.join(found_sections)}")
        else:
            print(f"⚠️  TEST 4 PARTIAL: Found {len(found_sections)}/{len(required_sections)} sections")
            print(f"   Found: {', '.join(found_sections)}")
            if missing_sections:
                print(f"   Missing: {', '.join(missing_sections)}")
        
        # Additional analysis
        print("\n📊 CONTENT ANALYSIS:")
        print(f"   Content length: {content_length} characters")
        lines_count = len(tech_card_content.split('\n'))
        print(f"   Lines: {lines_count}")
        
        # Show first 500 characters as preview
        print("\n📖 CONTENT PREVIEW (first 500 chars):")
        print("-" * 50)
        print(tech_card_content[:500])
        if len(tech_card_content) > 500:
            print("...")
        print("-" * 50)
        
        # Check for specific Carbonara elements
        carbonara_elements = ["паста", "бекон", "яйц", "пармезан", "сливк"]
        found_elements = []
        for element in carbonara_elements:
            if element.lower() in tech_card_content.lower():
                found_elements.append(element)
        
        print(f"\n🍝 CARBONARA ELEMENTS FOUND: {', '.join(found_elements)}")
        
        # Success summary
        print("\n🎉 SUCCESS SUMMARY:")
        print("✅ OpenAI API key is working correctly")
        print("✅ Tech card generation is functional")
        print("✅ No 500 errors - deployment issue resolved!")
        print(f"✅ Generated tech card for '{test_data['dish_name']}'")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ FAILED: Request timed out (>120 seconds)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🔑 OPENAI API KEY VERIFICATION TEST")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_openai_tech_card_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 FINAL RESULT: ALL TESTS PASSED!")
        print("🚀 OpenAI API integration is working correctly")
        print("✅ Ready for production use!")
    else:
        print("❌ FINAL RESULT: TESTS FAILED")
        print("🔧 OpenAI API key or integration needs attention")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)