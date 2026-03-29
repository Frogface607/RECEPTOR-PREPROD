#!/usr/bin/env python3
"""
Excel/CSV Price Upload Testing Suite
Testing POST /api/upload-prices endpoint as requested in review
"""

import requests
import json
import pandas as pd
import tempfile
import os
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"
TEST_USER_ID = "test_user_12345"

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")

def print_test_result(success, message, details=None):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"   Details: {details}")

def create_test_excel_file():
    """Create test Excel file with sample price data"""
    print_test_header("CREATING TEST EXCEL FILE")
    
    # Sample price data as requested in review
    price_data = [
        {"Название": "Картофель", "Цена": 20, "Единица": "кг"},
        {"Название": "Морковь", "Цена": 25, "Единица": "кг"},
        {"Название": "Лук", "Цена": 15, "Единица": "кг"},
        {"Название": "Мясо говядина", "Цена": 500, "Единица": "кг"},
        {"Название": "Молоко", "Цена": 80, "Единица": "л"},
        {"Название": "Хлеб", "Цена": 35, "Единица": "шт"},
        {"Название": "Яйца", "Цена": 120, "Единица": "десяток"}
    ]
    
    df = pd.DataFrame(price_data)
    
    # Create temporary Excel file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
        df.to_excel(temp_file.name, index=False, engine='openpyxl')
        excel_path = temp_file.name
    
    print_test_result(True, f"Created Excel file with {len(price_data)} items", excel_path)
    return excel_path, price_data

def create_test_csv_file():
    """Create test CSV file with sample price data"""
    print_test_header("CREATING TEST CSV FILE")
    
    # Same sample price data for CSV
    price_data = [
        {"Название": "Картофель", "Цена": 20, "Единица": "кг"},
        {"Название": "Морковь", "Цена": 25, "Единица": "кг"},
        {"Название": "Лук", "Цена": 15, "Единица": "кг"},
        {"Название": "Мясо говядина", "Цена": 500, "Единица": "кг"},
        {"Название": "Молоко", "Цена": 80, "Единица": "л"}
    ]
    
    df = pd.DataFrame(price_data)
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8') as temp_file:
        df.to_csv(temp_file.name, index=False, encoding='utf-8')
        csv_path = temp_file.name
    
    print_test_result(True, f"Created CSV file with {len(price_data)} items", csv_path)
    return csv_path, price_data

def test_excel_upload():
    """Test Excel file upload functionality"""
    print_test_header("TESTING EXCEL FILE UPLOAD")
    
    excel_path, expected_data = create_test_excel_file()
    
    try:
        # Prepare file upload
        with open(excel_path, 'rb') as file:
            files = {'file': ('test_prices.xlsx', file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {'user_id': TEST_USER_ID}
            
            start_time = time.time()
            response = requests.post(f"{BACKEND_URL}/upload-prices", files=files, data=data, timeout=60)
            response_time = time.time() - start_time
            
            print(f"⏱️  Response time: {response_time:.2f} seconds")
            print(f"📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📄 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # Verify response structure
                success = result.get('success', False)
                count = result.get('count', 0)
                prices = result.get('prices', [])
                
                print_test_result(success, f"Excel upload successful with {count} items processed")
                
                # Verify expected items are present
                if prices:
                    print("\n🔍 PROCESSED PRICES PREVIEW:")
                    for i, price in enumerate(prices[:5], 1):
                        print(f"   {i}. {price.get('name', 'N/A')} - {price.get('price', 0)}₽/{price.get('unit', 'N/A')}")
                
                # Verify specific items from test data
                expected_names = [item["Название"] for item in expected_data]
                found_names = [price.get('name', '') for price in prices]
                
                matches = 0
                for expected_name in expected_names:
                    if any(expected_name in found_name for found_name in found_names):
                        matches += 1
                
                print_test_result(matches >= 3, f"Found {matches}/{len(expected_names)} expected items in response")
                
                return True, result
            else:
                print_test_result(False, f"Excel upload failed with status {response.status_code}", response.text)
                return False, None
                
    except Exception as e:
        print_test_result(False, f"Excel upload test failed with exception: {str(e)}")
        return False, None
    finally:
        # Cleanup
        if os.path.exists(excel_path):
            os.unlink(excel_path)

def test_csv_upload():
    """Test CSV file upload functionality"""
    print_test_header("TESTING CSV FILE UPLOAD")
    
    csv_path, expected_data = create_test_csv_file()
    
    try:
        # Prepare file upload
        with open(csv_path, 'rb') as file:
            files = {'file': ('test_prices.csv', file, 'text/csv')}
            data = {'user_id': TEST_USER_ID}
            
            start_time = time.time()
            response = requests.post(f"{BACKEND_URL}/upload-prices", files=files, data=data, timeout=60)
            response_time = time.time() - start_time
            
            print(f"⏱️  Response time: {response_time:.2f} seconds")
            print(f"📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📄 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # Verify response structure
                success = result.get('success', False)
                count = result.get('count', 0)
                prices = result.get('prices', [])
                
                print_test_result(success, f"CSV upload successful with {count} items processed")
                
                # Verify expected items are present
                if prices:
                    print("\n🔍 PROCESSED PRICES PREVIEW:")
                    for i, price in enumerate(prices[:5], 1):
                        print(f"   {i}. {price.get('name', 'N/A')} - {price.get('price', 0)}₽/{price.get('unit', 'N/A')}")
                
                return True, result
            else:
                print_test_result(False, f"CSV upload failed with status {response.status_code}", response.text)
                return False, None
                
    except Exception as e:
        print_test_result(False, f"CSV upload test failed with exception: {str(e)}")
        return False, None
    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.unlink(csv_path)

def test_invalid_file_format():
    """Test error handling for invalid file format"""
    print_test_header("TESTING INVALID FILE FORMAT ERROR HANDLING")
    
    # Create a text file with invalid content
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w') as temp_file:
        temp_file.write("This is not a valid Excel or CSV file")
        invalid_path = temp_file.name
    
    try:
        with open(invalid_path, 'rb') as file:
            files = {'file': ('invalid.txt', file, 'text/plain')}
            data = {'user_id': TEST_USER_ID}
            
            response = requests.post(f"{BACKEND_URL}/upload-prices", files=files, data=data, timeout=30)
            
            print(f"📊 Status code: {response.status_code}")
            
            if response.status_code == 400:
                result = response.json()
                print_test_result(True, "Invalid file format correctly rejected", result.get('detail', ''))
                return True
            else:
                print_test_result(False, f"Expected 400 error but got {response.status_code}", response.text)
                return False
                
    except Exception as e:
        print_test_result(False, f"Invalid file test failed with exception: {str(e)}")
        return False
    finally:
        if os.path.exists(invalid_path):
            os.unlink(invalid_path)

def test_missing_required_fields():
    """Test error handling for missing required fields"""
    print_test_header("TESTING MISSING REQUIRED FIELDS ERROR HANDLING")
    
    # Create Excel file with missing data
    incomplete_data = [
        {"Название": "", "Цена": 20, "Единица": "кг"},  # Missing name
        {"Название": "Морковь", "Цена": "", "Единица": "кг"},  # Missing price
        {"Название": "Лук", "Цена": 0, "Единица": "кг"},  # Zero price
    ]
    
    df = pd.DataFrame(incomplete_data)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
        df.to_excel(temp_file.name, index=False, engine='openpyxl')
        incomplete_path = temp_file.name
    
    try:
        with open(incomplete_path, 'rb') as file:
            files = {'file': ('incomplete.xlsx', file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {'user_id': TEST_USER_ID}
            
            response = requests.post(f"{BACKEND_URL}/upload-prices", files=files, data=data, timeout=30)
            
            print(f"📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                count = result.get('count', 0)
                
                # Should process 0 items due to missing required fields
                if count == 0:
                    print_test_result(True, "Missing required fields correctly handled - 0 items processed", result)
                    return True
                else:
                    print_test_result(False, f"Expected 0 items but processed {count}", result)
                    return False
            else:
                print_test_result(False, f"Unexpected status code {response.status_code}", response.text)
                return False
                
    except Exception as e:
        print_test_result(False, f"Missing fields test failed with exception: {str(e)}")
        return False
    finally:
        if os.path.exists(incomplete_path):
            os.unlink(incomplete_path)

def test_non_pro_user_access():
    """Test error handling for non-PRO user access"""
    print_test_header("TESTING NON-PRO USER ACCESS RESTRICTION")
    
    # Use a different user ID that won't auto-create PRO user
    non_pro_user_id = "regular_user_123"
    
    excel_path, _ = create_test_excel_file()
    
    try:
        with open(excel_path, 'rb') as file:
            files = {'file': ('test.xlsx', file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {'user_id': non_pro_user_id}
            
            response = requests.post(f"{BACKEND_URL}/upload-prices", files=files, data=data, timeout=30)
            
            print(f"📊 Status code: {response.status_code}")
            
            if response.status_code == 403:
                result = response.json()
                print_test_result(True, "Non-PRO user correctly blocked", result.get('detail', ''))
                return True
            else:
                print_test_result(False, f"Expected 403 error but got {response.status_code}", response.text)
                return False
                
    except Exception as e:
        print_test_result(False, f"Non-PRO user test failed with exception: {str(e)}")
        return False
    finally:
        if os.path.exists(excel_path):
            os.unlink(excel_path)

def run_price_upload_tests():
    """Run all tests for Excel/CSV price upload functionality"""
    print(f"\n🚀 STARTING EXCEL/CSV PRICE UPLOAD TESTING")
    print(f"🎯 Target endpoint: {BACKEND_URL}/upload-prices")
    print(f"👤 Test user: {TEST_USER_ID}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # Test 1: Excel file upload with valid data
    excel_success, excel_result = test_excel_upload()
    test_results.append(("Excel Upload", excel_success))
    
    # Test 2: CSV file upload with valid data
    csv_success, csv_result = test_csv_upload()
    test_results.append(("CSV Upload", csv_success))
    
    # Test 3: Invalid file format
    invalid_success = test_invalid_file_format()
    test_results.append(("Invalid File Format", invalid_success))
    
    # Test 4: Missing required fields
    missing_success = test_missing_required_fields()
    test_results.append(("Missing Required Fields", missing_success))
    
    # Test 5: Non-PRO user access
    non_pro_success = test_non_pro_user_access()
    test_results.append(("Non-PRO User Access", non_pro_success))
    
    # Summary
    print_test_header("TEST SUMMARY")
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    print(f"📊 OVERALL RESULTS: {passed}/{total} tests passed")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! Excel/CSV price upload functionality is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the issues above.")
        return False

if __name__ == "__main__":
    success = run_price_upload_tests()
    exit(0 if success else 1)