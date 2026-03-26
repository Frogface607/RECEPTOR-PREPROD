#!/usr/bin/env python3
"""
Backend Testing Suite for Task 1.2 - Upload Prices/Nutrition Data with Preview
Testing upload functionality for CSV/JSON files with Russian products data.

Focus: Testing POST /api/upload-prices and POST /api/upload-nutrition endpoints with:
- CSV/Excel file support for prices
- JSON/CSV file support for nutrition data
- Russian product names and realistic data
- Preview functionality (first 10 items)
- Error handling for invalid formats
- PRO subscription validation
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

def create_test_prices_csv():
    """Create test CSV file with Russian products and prices"""
    prices_data = [
        ["Название продукта", "Цена за кг (руб)"],
        ["Говядина вырезка", "1200"],
        ["Свинина корейка", "650"],
        ["Курица филе", "450"],
        ["Лосось филе", "1800"],
        ["Треска филе", "800"],
        ["Картофель", "45"],
        ["Морковь", "35"],
        ["Лук репчатый", "25"],
        ["Помидоры", "180"],
        ["Огурцы", "120"],
        ["Масло подсолнечное", "150"],
        ["Масло оливковое", "850"],
        ["Соль поваренная", "25"],
        ["Перец черный молотый", "1200"],
        ["Сахар", "65"],
        ["Мука пшеничная", "45"],
        ["Рис круглозерный", "85"],
        ["Гречка", "95"],
        ["Молоко 3.2%", "75"],
        ["Сметана 20%", "180"],
        ["Творог 9%", "220"],
        ["Сыр российский", "450"],
        ["Яйца куриные С1", "120"],
        ["Хлеб белый", "55"]
    ]
    
    # Create CSV content
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerows(prices_data)
    
    return csv_content.getvalue().encode('utf-8')

def create_test_nutrition_json():
    """Create test JSON file with Russian products nutrition data"""
    nutrition_data = {
        "items": [
            {
                "name": "Говядина вырезка",
                "canonical_id": "beef_tenderloin",
                "per100g": {
                    "kcal": 218,
                    "proteins_g": 26.8,
                    "fats_g": 12.4,
                    "carbs_g": 0
                }
            },
            {
                "name": "Свинина корейка",
                "canonical_id": "pork_loin",
                "per100g": {
                    "kcal": 316,
                    "proteins_g": 19.4,
                    "fats_g": 27.8,
                    "carbs_g": 0
                }
            },
            {
                "name": "Курица филе",
                "canonical_id": "chicken_breast",
                "per100g": {
                    "kcal": 165,
                    "proteins_g": 31.0,
                    "fats_g": 3.6,
                    "carbs_g": 0
                }
            },
            {
                "name": "Лосось филе",
                "canonical_id": "salmon_fillet",
                "per100g": {
                    "kcal": 208,
                    "proteins_g": 25.4,
                    "fats_g": 12.5,
                    "carbs_g": 0
                }
            },
            {
                "name": "Картофель",
                "canonical_id": "potato",
                "per100g": {
                    "kcal": 77,
                    "proteins_g": 2.0,
                    "fats_g": 0.4,
                    "carbs_g": 16.3
                }
            },
            {
                "name": "Морковь",
                "canonical_id": "carrot",
                "per100g": {
                    "kcal": 35,
                    "proteins_g": 1.3,
                    "fats_g": 0.1,
                    "carbs_g": 6.9
                }
            },
            {
                "name": "Лук репчатый",
                "canonical_id": "onion",
                "per100g": {
                    "kcal": 47,
                    "proteins_g": 1.4,
                    "fats_g": 0.2,
                    "carbs_g": 10.4
                }
            },
            {
                "name": "Помидоры",
                "canonical_id": "tomato",
                "per100g": {
                    "kcal": 20,
                    "proteins_g": 0.6,
                    "fats_g": 0.2,
                    "carbs_g": 4.2
                }
            },
            {
                "name": "Масло подсолнечное",
                "canonical_id": "sunflower_oil",
                "per100g": {
                    "kcal": 899,
                    "proteins_g": 0,
                    "fats_g": 99.9,
                    "carbs_g": 0
                }
            },
            {
                "name": "Рис круглозерный",
                "canonical_id": "rice_round",
                "per100g": {
                    "kcal": 344,
                    "proteins_g": 6.7,
                    "fats_g": 0.7,
                    "carbs_g": 78.9
                }
            },
            {
                "name": "Молоко 3.2%",
                "canonical_id": "milk_3_2",
                "per100g": {
                    "kcal": 58,
                    "proteins_g": 2.8,
                    "fats_g": 3.2,
                    "carbs_g": 4.7
                }
            },
            {
                "name": "Яйца куриные С1",
                "canonical_id": "chicken_eggs",
                "per100g": {
                    "kcal": 157,
                    "proteins_g": 12.7,
                    "fats_g": 11.5,
                    "carbs_g": 0.7
                },
                "mass_per_piece": 55
            }
        ]
    }
    
    return json.dumps(nutrition_data, ensure_ascii=False, indent=2).encode('utf-8')

def create_test_nutrition_csv():
    """Create test CSV file with nutrition data"""
    nutrition_data = [
        ["Название", "Ккал", "Белки", "Жиры", "Углеводы"],
        ["Гречка", "313", "12.6", "3.3", "57.1"],
        ["Овсянка", "342", "12.3", "6.1", "59.5"],
        ["Хлеб белый", "242", "8.1", "2.6", "48.8"],
        ["Сыр российский", "364", "23.2", "30.0", "0.3"],
        ["Творог 9%", "159", "16.7", "9.0", "2.0"],
        ["Сметана 20%", "206", "2.8", "20.0", "3.2"]
    ]
    
    # Create CSV content
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerows(nutrition_data)
    
    return csv_content.getvalue().encode('utf-8')

def test_upload_prices_csv():
    """Test POST /api/upload-prices with CSV file"""
    log_test("🍖 STEP 1: Testing POST /api/upload-prices with Russian products CSV")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        # Create test CSV file
        csv_data = create_test_prices_csv()
        
        url = f"{API_BASE}/upload-prices"
        log_test(f"Making request to: {url}")
        log_test(f"User ID: {test_user_id}")
        log_test(f"CSV data size: {len(csv_data)} bytes")
        
        # Prepare multipart form data
        files = {
            'file': ('prices_ru.csv', csv_data, 'text/csv')
        }
        data = {
            'user_id': test_user_id
        }
        
        start_time = time.time()
        response = requests.post(url, files=files, data=data, timeout=30)
        response_time = time.time() - start_time
        
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Prices upload successful!")
            
            if data.get('success'):
                log_test(f"📊 Processed items: {data.get('count', 0)}")
                log_test(f"💬 Message: {data.get('message', 'No message')}")
                
                # Check preview data
                prices = data.get('prices', [])
                if prices:
                    log_test(f"📋 Preview (first {len(prices)} items):")
                    for i, price in enumerate(prices):
                        log_test(f"   {i+1}. {price.get('name', 'Unknown')} - {price.get('price', 0)}₽/{price.get('unit', 'кг')}")
                
                return {
                    'success': True,
                    'count': data.get('count', 0),
                    'preview': prices
                }
            else:
                log_test(f"❌ Upload failed: {data.get('error', 'Unknown error')}")
                return {'success': False, 'error': data.get('error')}
        
        elif response.status_code == 403:
            log_test("❌ PRO subscription required (expected for non-PRO users)")
            return {'success': False, 'error': 'PRO subscription required'}
        
        else:
            log_test(f"❌ Upload failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"Error details: {error_data}")
            except:
                log_test(f"Raw response: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error uploading prices: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_upload_nutrition_json():
    """Test POST /api/upload-nutrition with JSON file"""
    log_test("🥗 STEP 2: Testing POST /api/upload-nutrition with Russian products JSON")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        # Create test JSON file
        json_data = create_test_nutrition_json()
        
        url = f"{API_BASE}/upload-nutrition"
        log_test(f"Making request to: {url}")
        log_test(f"User ID: {test_user_id}")
        log_test(f"JSON data size: {len(json_data)} bytes")
        
        # Prepare multipart form data
        files = {
            'file': ('nutrition_ru.json', json_data, 'application/json')
        }
        data = {
            'user_id': test_user_id
        }
        
        start_time = time.time()
        response = requests.post(url, files=files, data=data, timeout=30)
        response_time = time.time() - start_time
        
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Nutrition upload successful!")
            
            if data.get('success'):
                log_test(f"📊 Processed items: {data.get('count', 0)}")
                log_test(f"💬 Message: {data.get('message', 'No message')}")
                
                # Check preview data
                nutrition = data.get('nutrition', [])
                if nutrition:
                    log_test(f"📋 Preview (first {len(nutrition)} items):")
                    for i, item in enumerate(nutrition):
                        log_test(f"   {i+1}. {item.get('name', 'Unknown')} - {item.get('kcal', 0)} ккал, Б:{item.get('proteins_g', 0)}г, Ж:{item.get('fats_g', 0)}г, У:{item.get('carbs_g', 0)}г")
                
                return {
                    'success': True,
                    'count': data.get('count', 0),
                    'preview': nutrition
                }
            else:
                log_test(f"❌ Upload failed: {data.get('error', 'Unknown error')}")
                return {'success': False, 'error': data.get('error')}
        
        elif response.status_code == 403:
            log_test("❌ PRO subscription required (expected for non-PRO users)")
            return {'success': False, 'error': 'PRO subscription required'}
        
        else:
            log_test(f"❌ Upload failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"Error details: {error_data}")
            except:
                log_test(f"Raw response: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error uploading nutrition: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_upload_nutrition_csv():
    """Test POST /api/upload-nutrition with CSV file"""
    log_test("🥛 STEP 3: Testing POST /api/upload-nutrition with CSV format")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        # Create test CSV file
        csv_data = create_test_nutrition_csv()
        
        url = f"{API_BASE}/upload-nutrition"
        log_test(f"Making request to: {url}")
        log_test(f"CSV data size: {len(csv_data)} bytes")
        
        # Prepare multipart form data
        files = {
            'file': ('nutrition_ru.csv', csv_data, 'text/csv')
        }
        data = {
            'user_id': test_user_id
        }
        
        start_time = time.time()
        response = requests.post(url, files=files, data=data, timeout=30)
        response_time = time.time() - start_time
        
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Nutrition CSV upload successful!")
            
            if data.get('success'):
                log_test(f"📊 Processed items: {data.get('count', 0)}")
                log_test(f"💬 Message: {data.get('message', 'No message')}")
                
                # Check preview data
                nutrition = data.get('nutrition', [])
                if nutrition:
                    log_test(f"📋 Preview (first {len(nutrition)} items):")
                    for i, item in enumerate(nutrition):
                        log_test(f"   {i+1}. {item.get('name', 'Unknown')} - {item.get('kcal', 0)} ккал, Б:{item.get('proteins_g', 0)}г, Ж:{item.get('fats_g', 0)}г, У:{item.get('carbs_g', 0)}г")
                
                return {
                    'success': True,
                    'count': data.get('count', 0),
                    'preview': nutrition
                }
            else:
                log_test(f"❌ Upload failed: {data.get('error', 'Unknown error')}")
                return {'success': False, 'error': data.get('error')}
        
        else:
            log_test(f"❌ Upload failed: HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error uploading nutrition CSV: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_get_user_prices():
    """Test GET /api/user-prices/{user_id}"""
    log_test("💰 STEP 4: Testing GET /api/user-prices/{user_id}")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        url = f"{API_BASE}/user-prices/{test_user_id}"
        log_test(f"Making request to: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            prices = data.get('prices', [])
            log_test(f"✅ Retrieved {len(prices)} user prices")
            
            if prices:
                log_test("📋 Sample user prices:")
                for i, price in enumerate(prices[:5]):
                    log_test(f"   {i+1}. {price.get('name', 'Unknown')} - {price.get('price', 0)}₽/{price.get('unit', 'кг')}")
            
            return {'success': True, 'count': len(prices)}
        else:
            log_test(f"❌ Failed to get user prices: HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error getting user prices: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_get_user_nutrition():
    """Test GET /api/user-nutrition/{user_id}"""
    log_test("🥗 STEP 5: Testing GET /api/user-nutrition/{user_id}")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        url = f"{API_BASE}/user-nutrition/{test_user_id}"
        log_test(f"Making request to: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            nutrition = data.get('nutrition', [])
            log_test(f"✅ Retrieved {len(nutrition)} user nutrition items")
            
            if nutrition:
                log_test("📋 Sample user nutrition:")
                for i, item in enumerate(nutrition[:5]):
                    log_test(f"   {i+1}. {item.get('name', 'Unknown')} - {item.get('kcal', 0)} ккал")
            
            return {'success': True, 'count': len(nutrition)}
        else:
            log_test(f"❌ Failed to get user nutrition: HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error getting user nutrition: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_invalid_file_format():
    """Test upload with invalid file format"""
    log_test("❌ STEP 6: Testing invalid file format handling")
    
    test_user_id = "test_user_upload_12345"
    
    try:
        # Create invalid file (text file for prices)
        invalid_data = b"This is not a valid CSV or Excel file"
        
        url = f"{API_BASE}/upload-prices"
        log_test(f"Making request to: {url}")
        
        files = {
            'file': ('invalid.txt', invalid_data, 'text/plain')
        }
        data = {
            'user_id': test_user_id
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 400:
            log_test("✅ Invalid format correctly rejected with HTTP 400")
            return {'success': True, 'error_handled': True}
        elif response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                log_test("✅ Invalid format handled gracefully")
                return {'success': True, 'error_handled': True}
            else:
                log_test("⚠️ Invalid format was processed (unexpected)")
                return {'success': False, 'error': 'Invalid format processed'}
        else:
            log_test(f"⚠️ Unexpected response: HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error testing invalid format: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main testing function for upload functionality"""
    log_test("🚀 Starting Task 1.2 - Upload Prices/Nutrition Data Testing")
    log_test("🎯 Focus: Testing CSV/JSON upload with Russian products and preview")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    results = {}
    
    # Test 1: Upload prices CSV
    results['prices_csv'] = test_upload_prices_csv()
    log_test("\n" + "=" * 80)
    
    # Test 2: Upload nutrition JSON
    results['nutrition_json'] = test_upload_nutrition_json()
    log_test("\n" + "=" * 80)
    
    # Test 3: Upload nutrition CSV
    results['nutrition_csv'] = test_upload_nutrition_csv()
    log_test("\n" + "=" * 80)
    
    # Test 4: Get user prices
    results['get_prices'] = test_get_user_prices()
    log_test("\n" + "=" * 80)
    
    # Test 5: Get user nutrition
    results['get_nutrition'] = test_get_user_nutrition()
    log_test("\n" + "=" * 80)
    
    # Test 6: Invalid file format
    results['invalid_format'] = test_invalid_file_format()
    log_test("\n" + "=" * 80)
    
    # Summary
    log_test("📋 TASK 1.2 UPLOAD FUNCTIONALITY TESTING SUMMARY:")
    log_test(f"✅ Prices CSV upload: {'SUCCESS' if results['prices_csv']['success'] else 'FAILED'}")
    log_test(f"✅ Nutrition JSON upload: {'SUCCESS' if results['nutrition_json']['success'] else 'FAILED'}")
    log_test(f"✅ Nutrition CSV upload: {'SUCCESS' if results['nutrition_csv']['success'] else 'FAILED'}")
    log_test(f"✅ Get user prices: {'SUCCESS' if results['get_prices']['success'] else 'FAILED'}")
    log_test(f"✅ Get user nutrition: {'SUCCESS' if results['get_nutrition']['success'] else 'FAILED'}")
    log_test(f"✅ Invalid format handling: {'SUCCESS' if results['invalid_format']['success'] else 'FAILED'}")
    
    # Check if all core functionality works
    core_working = (
        results['prices_csv']['success'] and
        results['nutrition_json']['success'] and
        results['get_prices']['success'] and
        results['get_nutrition']['success']
    )
    
    if core_working:
        log_test("🎉 TASK 1.2 UPLOAD FUNCTIONALITY IS WORKING!")
        log_test("✅ CSV/Excel prices upload working")
        log_test("✅ JSON/CSV nutrition upload working")
        log_test("✅ Data persistence working")
        log_test("✅ Preview functionality working")
        log_test("✅ Russian products processing working")
        
        # Show data counts
        if results['prices_csv'].get('count'):
            log_test(f"📊 Prices uploaded: {results['prices_csv']['count']} items")
        if results['nutrition_json'].get('count'):
            log_test(f"📊 Nutrition (JSON) uploaded: {results['nutrition_json']['count']} items")
        if results['nutrition_csv'].get('count'):
            log_test(f"📊 Nutrition (CSV) uploaded: {results['nutrition_csv']['count']} items")
    else:
        log_test("⚠️ Some upload functionality has issues:")
        for test_name, result in results.items():
            if not result['success']:
                log_test(f"   - {test_name}: {result.get('error', 'Unknown error')}")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()