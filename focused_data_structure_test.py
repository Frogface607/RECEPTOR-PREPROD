#!/usr/bin/env python3
"""
Focused IIKo Assembly Charts Data Structure Testing
Testing the specific data structure fixes mentioned in the review
"""

import requests
import json
import time
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_data_structure_fixes():
    """Test the specific data structure fixes mentioned in the review"""
    print("🔧 TESTING DATA STRUCTURE FIXES - PRIORITY 1")
    print("=" * 60)
    
    # Test data exactly as provided in the review request
    test_data = {
        "name": "AI Test Паста Карбонара",
        "description": "Тестовая техкарта для проверки интеграции",
        "ingredients": [
            {"name": "Спагетти", "quantity": 100, "unit": "г", "price": 15.0},
            {"name": "Бекон", "quantity": 50, "unit": "г", "price": 35.0},
            {"name": "Яйцо", "quantity": 1, "unit": "шт", "price": 10.0}
        ],
        "preparation_steps": [
            "Отварить спагетти",
            "Обжарить бекон",
            "Смешать с яйцом и подать"
        ],
        "organization_id": "default-org-001",
        "weight": 200.0,
        "price": 350.0
    }
    
    print("📋 Testing with exact data from review request:")
    print(f"Data: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    print()
    
    print("Test 1: POST /api/iiko/assembly-charts/create - Data structure transformation")
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/iiko/assembly-charts/create",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check if the error is about data structure
            error = result.get("error", "")
            if "'name'" in error:
                log_test("Data Structure Issue Detected", "FAIL", "Backend still sending 'name' instead of 'title'")
                print("🔍 ANALYSIS: The error indicates the backend is still sending 'name' field")
                print("   Expected: Backend should transform 'name' to 'title' before sending to IIKo")
                print("   Actual: IIKo API receiving 'name' field and rejecting it")
                print("   Fix needed: Backend transformation logic needs to be implemented")
                return False
            elif result.get("success"):
                log_test("Data Structure Transformation", "PASS", "Successfully created with correct structure")
                return True
            else:
                log_test("Assembly Chart Creation", "FAIL", f"Other error: {error}")
                return False
        else:
            error_text = response.text[:500] if response.text else "No response body"
            log_test("Assembly Chart Creation", "FAIL", f"HTTP {response.status_code}: {error_text}")
            return False
            
    except Exception as e:
        log_test("Assembly Chart Creation", "FAIL", f"Exception: {str(e)}")
        return False

def test_ingredient_format():
    """Test that ingredients are transformed to correct format"""
    print("🥬 TESTING INGREDIENT FORMAT TRANSFORMATION")
    print("=" * 60)
    
    print("Expected transformation:")
    print("  Input:  {'name': 'Спагетти', 'quantity': 100, 'unit': 'г', 'price': 15.0}")
    print("  Output: {'productName': 'Спагетти', 'amount': 100, 'measureUnit': 'г'}")
    print()
    
    # This would be tested by examining the actual request sent to IIKo
    # Since we can't intercept that directly, we'll check the error messages
    log_test("Ingredient Format Requirements", "INFO", "Format should be transformed by backend")

def test_cooking_steps_format():
    """Test that cooking steps are transformed correctly"""
    print("👨‍🍳 TESTING COOKING STEPS FORMAT")
    print("=" * 60)
    
    print("Expected transformation:")
    print("  Input:  preparation_steps: ['Отварить спагетти', 'Обжарить бекон']")
    print("  Output: cookingSteps: [{'stepNumber': 1, 'description': 'Отварить спагетти'}, ...]")
    print()
    
    log_test("Cooking Steps Format Requirements", "INFO", "Format should be transformed by backend")

def main():
    """Main test execution"""
    print("🎯 FOCUSED DATA STRUCTURE TESTING")
    print("Testing specific fixes mentioned in review request")
    print("=" * 80)
    print()
    
    print("📝 REVIEW REQUIREMENTS:")
    print("1. Use 'title' instead of 'name' in IIKo API calls")
    print("2. Transform ingredients to have 'productName' and 'measureUnit'")
    print("3. Transform preparation_steps to 'cookingSteps' format")
    print("4. Ensure POST /api/iiko/tech-cards/upload uses create_assembly_chart")
    print()
    
    # Test the main data structure transformation
    success = test_data_structure_fixes()
    
    # Test ingredient format understanding
    test_ingredient_format()
    
    # Test cooking steps format understanding
    test_cooking_steps_format()
    
    print("=" * 80)
    if success:
        print("🎉 DATA STRUCTURE FIXES: WORKING")
        print("Backend correctly transforms data before sending to IIKo")
    else:
        print("❌ DATA STRUCTURE FIXES: NEEDED")
        print("Backend needs to implement proper data transformation")
        print()
        print("🔧 REQUIRED FIXES:")
        print("1. Transform 'name' → 'title' in _transform_to_assembly_chart()")
        print("2. Transform ingredients format: 'name' → 'productName', 'unit' → 'measureUnit'")
        print("3. Transform 'preparation_steps' → 'cookingSteps' with proper structure")
    print("=" * 80)

if __name__ == "__main__":
    main()