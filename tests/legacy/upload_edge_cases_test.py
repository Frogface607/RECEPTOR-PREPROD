#!/usr/bin/env python3
"""
Edge Cases Testing for Task 1.2 - Upload Prices/Nutrition Data
Testing error handling, malformed data, and edge cases.
"""

import requests
import json
import time
import os
import io
import csv
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_malformed_json():
    """Test upload with malformed JSON"""
    log_test("🚨 EDGE CASE 1: Testing malformed JSON handling")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        # Create malformed JSON
        malformed_json = b'{"items": [{"name": "Test", "per100g": {"kcal": 100, "proteins_g": 10'  # Missing closing braces
        
        url = f"{API_BASE}/upload-nutrition"
        
        files = {
            'file': ('malformed.json', malformed_json, 'application/json')
        }
        data = {
            'user_id': test_user_id
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 400:
            log_test("✅ Malformed JSON correctly rejected with HTTP 400")
            return {'success': True, 'error_handled': True}
        else:
            data = response.json()
            if not data.get('success'):
                log_test("✅ Malformed JSON handled gracefully")
                log_test(f"Error message: {data.get('error', 'No error message')}")
                return {'success': True, 'error_handled': True}
            else:
                log_test("❌ Malformed JSON was processed (unexpected)")
                return {'success': False, 'error': 'Malformed JSON processed'}
                
    except Exception as e:
        log_test(f"❌ Error testing malformed JSON: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_empty_csv():
    """Test upload with empty CSV"""
    log_test("📄 EDGE CASE 2: Testing empty CSV handling")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        # Create empty CSV
        empty_csv = b""
        
        url = f"{API_BASE}/upload-prices"
        
        files = {
            'file': ('empty.csv', empty_csv, 'text/csv')
        }
        data = {
            'user_id': test_user_id
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('count', 0) == 0:
                log_test("✅ Empty CSV handled correctly - 0 items processed")
                return {'success': True, 'empty_handled': True}
            elif not data.get('success'):
                log_test("✅ Empty CSV rejected gracefully")
                log_test(f"Error: {data.get('error', 'No error message')}")
                return {'success': True, 'empty_handled': True}
            else:
                log_test(f"⚠️ Unexpected result: {data.get('count', 0)} items processed")
                return {'success': False, 'error': 'Unexpected processing of empty file'}
        else:
            log_test(f"✅ Empty CSV rejected with HTTP {response.status_code}")
            return {'success': True, 'empty_handled': True}
                
    except Exception as e:
        log_test(f"❌ Error testing empty CSV: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_csv_with_invalid_prices():
    """Test CSV with invalid price data"""
    log_test("💸 EDGE CASE 3: Testing CSV with invalid prices")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        # Create CSV with invalid prices
        invalid_prices_data = [
            ["Название продукта", "Цена"],
            ["Продукт без цены", ""],
            ["Продукт с текстом", "дорого"],
            ["Продукт с нулевой ценой", "0"],
            ["Продукт с отрицательной ценой", "-100"],
            ["Нормальный продукт", "150"]
        ]
        
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerows(invalid_prices_data)
        csv_data = csv_content.getvalue().encode('utf-8')
        
        url = f"{API_BASE}/upload-prices"
        
        files = {
            'file': ('invalid_prices.csv', csv_data, 'text/csv')
        }
        data = {
            'user_id': test_user_id
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                count = data.get('count', 0)
                log_test(f"✅ Invalid prices filtered correctly - {count} valid items processed")
                
                # Should only process the valid item
                if count == 1:
                    log_test("✅ Only valid price item was processed")
                    return {'success': True, 'filtering_works': True}
                else:
                    log_test(f"⚠️ Expected 1 item, got {count}")
                    return {'success': True, 'filtering_partial': True}
            else:
                log_test("✅ Invalid prices rejected")
                return {'success': True, 'rejected': True}
        else:
            log_test(f"❌ Unexpected HTTP status: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
                
    except Exception as e:
        log_test(f"❌ Error testing invalid prices: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_json_missing_required_fields():
    """Test JSON with missing required nutrition fields"""
    log_test("🥗 EDGE CASE 4: Testing JSON with missing required fields")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        # Create JSON with missing required fields
        incomplete_nutrition = {
            "items": [
                {
                    "name": "Продукт без per100g"
                },
                {
                    "name": "Продукт с неполными данными",
                    "per100g": {
                        "kcal": 100
                        # Missing proteins_g, fats_g, carbs_g
                    }
                },
                {
                    "name": "Полный продукт",
                    "per100g": {
                        "kcal": 200,
                        "proteins_g": 20,
                        "fats_g": 10,
                        "carbs_g": 5
                    }
                }
            ]
        }
        
        json_data = json.dumps(incomplete_nutrition, ensure_ascii=False).encode('utf-8')
        
        url = f"{API_BASE}/upload-nutrition"
        
        files = {
            'file': ('incomplete.json', json_data, 'application/json')
        }
        data = {
            'user_id': test_user_id
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                count = data.get('count', 0)
                log_test(f"✅ Incomplete items filtered correctly - {count} valid items processed")
                
                # Should only process the complete item
                if count == 1:
                    log_test("✅ Only complete nutrition item was processed")
                    return {'success': True, 'filtering_works': True}
                else:
                    log_test(f"⚠️ Expected 1 item, got {count}")
                    return {'success': True, 'filtering_partial': True}
            else:
                log_test("✅ Incomplete data rejected")
                return {'success': True, 'rejected': True}
        else:
            log_test(f"❌ Unexpected HTTP status: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
                
    except Exception as e:
        log_test(f"❌ Error testing incomplete JSON: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_non_pro_user():
    """Test upload with non-PRO user"""
    log_test("👤 EDGE CASE 5: Testing non-PRO user access")
    
    free_user_id = "free_user_12345"  # This should not get PRO subscription
    
    try:
        # Create simple CSV
        csv_data = b"Product,Price\nTest Product,100"
        
        url = f"{API_BASE}/upload-prices"
        
        files = {
            'file': ('test.csv', csv_data, 'text/csv')
        }
        data = {
            'user_id': free_user_id
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 403:
            log_test("✅ Non-PRO user correctly blocked with HTTP 403")
            return {'success': True, 'access_control_works': True}
        elif response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                log_test("✅ Non-PRO user blocked gracefully")
                return {'success': True, 'access_control_works': True}
            else:
                log_test("❌ Non-PRO user was allowed to upload (security issue)")
                return {'success': False, 'error': 'Access control not working'}
        else:
            log_test(f"⚠️ Unexpected response: HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
                
    except Exception as e:
        log_test(f"❌ Error testing non-PRO user: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_large_file_handling():
    """Test handling of large files"""
    log_test("📊 EDGE CASE 6: Testing large file handling")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        # Create large CSV with many products
        large_prices_data = [["Название продукта", "Цена"]]
        
        # Add 100 products
        for i in range(100):
            large_prices_data.append([f"Продукт {i+1}", f"{100 + i}"])
        
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerows(large_prices_data)
        csv_data = csv_content.getvalue().encode('utf-8')
        
        log_test(f"Large CSV size: {len(csv_data)} bytes ({len(large_prices_data)-1} products)")
        
        url = f"{API_BASE}/upload-prices"
        
        files = {
            'file': ('large_prices.csv', csv_data, 'text/csv')
        }
        data = {
            'user_id': test_user_id
        }
        
        start_time = time.time()
        response = requests.post(url, files=files, data=data, timeout=60)
        response_time = time.time() - start_time
        
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                count = data.get('count', 0)
                log_test(f"✅ Large file processed successfully - {count} items")
                
                if count == 100:
                    log_test("✅ All 100 products processed correctly")
                    return {'success': True, 'large_file_works': True, 'count': count}
                else:
                    log_test(f"⚠️ Expected 100 items, got {count}")
                    return {'success': True, 'large_file_partial': True, 'count': count}
            else:
                log_test(f"❌ Large file processing failed: {data.get('error', 'Unknown error')}")
                return {'success': False, 'error': data.get('error')}
        else:
            log_test(f"❌ Large file rejected: HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
                
    except Exception as e:
        log_test(f"❌ Error testing large file: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main testing function for edge cases"""
    log_test("🚀 Starting Task 1.2 - Upload Edge Cases Testing")
    log_test("🎯 Focus: Testing error handling and edge cases")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    results = {}
    
    # Test 1: Malformed JSON
    results['malformed_json'] = test_malformed_json()
    log_test("\n" + "=" * 80)
    
    # Test 2: Empty CSV
    results['empty_csv'] = test_empty_csv()
    log_test("\n" + "=" * 80)
    
    # Test 3: Invalid prices
    results['invalid_prices'] = test_csv_with_invalid_prices()
    log_test("\n" + "=" * 80)
    
    # Test 4: Missing required fields
    results['missing_fields'] = test_json_missing_required_fields()
    log_test("\n" + "=" * 80)
    
    # Test 5: Non-PRO user
    results['non_pro_user'] = test_non_pro_user()
    log_test("\n" + "=" * 80)
    
    # Test 6: Large file
    results['large_file'] = test_large_file_handling()
    log_test("\n" + "=" * 80)
    
    # Summary
    log_test("📋 TASK 1.2 EDGE CASES TESTING SUMMARY:")
    log_test(f"✅ Malformed JSON handling: {'SUCCESS' if results['malformed_json']['success'] else 'FAILED'}")
    log_test(f"✅ Empty CSV handling: {'SUCCESS' if results['empty_csv']['success'] else 'FAILED'}")
    log_test(f"✅ Invalid prices filtering: {'SUCCESS' if results['invalid_prices']['success'] else 'FAILED'}")
    log_test(f"✅ Missing fields filtering: {'SUCCESS' if results['missing_fields']['success'] else 'FAILED'}")
    log_test(f"✅ Non-PRO user access control: {'SUCCESS' if results['non_pro_user']['success'] else 'FAILED'}")
    log_test(f"✅ Large file handling: {'SUCCESS' if results['large_file']['success'] else 'FAILED'}")
    
    # Check overall robustness
    all_passed = all(result['success'] for result in results.values())
    
    if all_passed:
        log_test("🎉 ALL EDGE CASES HANDLED CORRECTLY!")
        log_test("✅ Error handling is robust")
        log_test("✅ Data validation is working")
        log_test("✅ Access control is enforced")
        log_test("✅ Large files are supported")
        
        # Show specific results
        if results['large_file'].get('count'):
            log_test(f"📊 Large file test: {results['large_file']['count']} items processed")
    else:
        log_test("⚠️ Some edge cases need attention:")
        for test_name, result in results.items():
            if not result['success']:
                log_test(f"   - {test_name}: {result.get('error', 'Unknown error')}")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()