#!/usr/bin/env python3
"""
IIKo API Structure Analysis Test
Analyzing the exact ProductDto structure requirements from IIKo API error messages
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

def test_iiko_product_structure_analysis():
    """Analyze IIKo ProductDto structure from error messages"""
    log_test("🔍 ANALYZING IIKO PRODUCT DTO STRUCTURE FROM ERROR MESSAGES")
    
    # From the logs, we can see the ProductDto has 34 known properties:
    known_properties = [
        "defaultSalePrice", "num", "taxCategory", "storeBalanceLevels", "name", 
        "canSetOpenPrice", "containers", "modifierSchemaId", "fontColor", 
        "hotLossPercent", "productScaleId", "excludedSections"
        # ... and 22 more properties (truncated in error message)
    ]
    
    log_test("📋 KNOWN IIKO PRODUCT DTO PROPERTIES (from error message):")
    for i, prop in enumerate(known_properties, 1):
        log_test(f"   {i:2d}. {prop}")
    
    log_test(f"\n📊 Total known properties: {len(known_properties)} (error message shows 34 total)")
    log_test("❌ REJECTED FIELDS: active, deleted, description, weight, cookingPlace, assembly, parent, measurementUnit, tags, additionalInfo, code, type, assemblyId, hasAssembly")
    
    return known_properties

def test_minimal_dish_creation():
    """Test creating a DISH with only the minimal required fields"""
    log_test("🧪 TESTING MINIMAL DISH CREATION WITH ONLY REQUIRED FIELDS")
    
    # Based on the error analysis, try with only the most basic fields
    minimal_test_data = {
        "name": "Минимальное тестовое блюдо",
        "organization_id": "default-org-001",
        "description": "Тест с минимальными полями",
        "ingredients": [
            {"name": "Тестовый ингредиент", "quantity": 100, "unit": "г"}
        ],
        "preparation_steps": ["Тестовый шаг"],
        "weight": 100.0,
        "price": 200.0
    }
    
    log_test(f"📝 Testing with minimal data: {minimal_test_data['name']}")
    
    try:
        url = f"{API_BASE}/iiko/products/create-complete-dish"
        log_test(f"🌐 Making request to: {url}")
        
        response = requests.post(url, json=minimal_test_data, timeout=30)
        log_test(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if DISH creation succeeded with minimal fields
            dish_created = data.get('details', {}).get('dish_product', {}).get('created', False)
            
            if dish_created:
                log_test("✅ SUCCESS: Minimal DISH creation worked!")
            else:
                log_test("❌ FAILED: Even minimal DISH creation failed")
                
                # Look for specific error messages
                errors = data.get('errors', [])
                for error in errors:
                    if 'DISH' in error:
                        log_test(f"🔍 DISH Error: {error}")
            
            log_test(f"📋 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            return {'success': dish_created, 'data': data}
        else:
            log_test(f"❌ HTTP Error: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Exception: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_iiko_menu_analysis():
    """Analyze existing IIKo menu to understand product structure"""
    log_test("📊 ANALYZING EXISTING IIKO MENU STRUCTURE")
    
    try:
        url = f"{API_BASE}/iiko/menu/default-org-001"
        log_test(f"🌐 Getting menu from: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            menu = data.get('menu', {})
            items = menu.get('items', [])
            categories = menu.get('categories', [])
            
            log_test(f"📋 Menu analysis:")
            log_test(f"   - Total items: {len(items)}")
            log_test(f"   - Total categories: {len(categories)}")
            
            # Analyze product structure
            if items:
                sample_item = items[0]
                log_test(f"\n🔍 SAMPLE PRODUCT STRUCTURE:")
                log_test(f"📝 Sample item: {sample_item.get('name', 'Unknown')}")
                log_test(f"🏷️ Fields in existing products:")
                
                for key, value in sample_item.items():
                    value_type = type(value).__name__
                    value_preview = str(value)[:50] if len(str(value)) > 50 else str(value)
                    log_test(f"   - {key}: {value_type} = {value_preview}")
                
                # Look for DISH type products
                dish_products = [item for item in items if item.get('type') == 'DISH']
                log_test(f"\n🍽️ DISH type products found: {len(dish_products)}")
                
                if dish_products:
                    dish_sample = dish_products[0]
                    log_test(f"📝 Sample DISH: {dish_sample.get('name', 'Unknown')}")
                    log_test(f"🏷️ DISH-specific fields:")
                    for key, value in dish_sample.items():
                        log_test(f"   - {key}: {value}")
                else:
                    log_test("❌ No DISH type products found in menu")
            
            # Analyze categories
            if categories:
                ai_category = next((cat for cat in categories if 'AI' in cat.get('name', '')), None)
                if ai_category:
                    log_test(f"\n📂 AI Menu Designer category found:")
                    log_test(f"   - ID: {ai_category.get('id')}")
                    log_test(f"   - Name: {ai_category.get('name')}")
                else:
                    log_test("\n📂 AI Menu Designer category not found")
            
            return {'success': True, 'items': items, 'categories': categories}
        else:
            log_test(f"❌ Failed to get menu: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error analyzing menu: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main analysis function"""
    log_test("🔬 Starting IIKo API Structure Analysis")
    log_test("🎯 Goal: Understand why DISH product creation is failing")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Step 1: Analyze ProductDto structure from error messages
    known_properties = test_iiko_product_structure_analysis()
    
    log_test("\n" + "=" * 80)
    
    # Step 2: Analyze existing menu structure
    menu_analysis = test_iiko_menu_analysis()
    
    log_test("\n" + "=" * 80)
    
    # Step 3: Test minimal DISH creation
    minimal_test = test_minimal_dish_creation()
    
    # Summary
    log_test("\n" + "=" * 80)
    log_test("📋 IIKO API STRUCTURE ANALYSIS SUMMARY:")
    
    log_test("\n🔍 KEY FINDINGS:")
    log_test("1. IIKo ProductDto has 34 known properties (from error message)")
    log_test("2. Fields like 'active', 'deleted', 'type' are NOT accepted")
    log_test("3. Most DISH creation endpoints return 404 (not available)")
    log_test("4. Only /resto/api/v2/entities/products/save is accessible but rejects our structure")
    
    log_test("\n💡 RECOMMENDATIONS:")
    log_test("1. Backend needs to use ONLY the 34 valid ProductDto fields")
    log_test("2. Remove all invalid fields from dish_product structure")
    log_test("3. Research the complete list of 34 valid fields")
    log_test("4. Consider if this IIKo installation supports DISH creation at all")
    
    if menu_analysis.get('success'):
        items = menu_analysis.get('items', [])
        dish_count = len([item for item in items if item.get('type') == 'DISH'])
        log_test(f"\n📊 MENU ANALYSIS: {len(items)} total products, {dish_count} DISH products")
        
        if dish_count == 0:
            log_test("⚠️ WARNING: No DISH products found in existing menu!")
            log_test("💡 This IIKo installation may not support DISH product creation")
        else:
            log_test("✅ DISH products exist in menu - creation should be possible")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()