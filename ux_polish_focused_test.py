#!/usr/bin/env python3
"""
UX POLISH EXPORT SYSTEM FOCUSED ANALYSIS
Focused analysis of current export system for UX polish requirements
"""

import requests
import json
import time
import os
import re
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_techcard_generation():
    """Test techcard generation and extract ID"""
    print("🔍 TESTING TECHCARD GENERATION")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{API_BASE}/v1/techcards.v2/generate",
            json={"name": "Омлет с зеленью"},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            techcard_id = data.get('card', {}).get('meta', {}).get('id')
            ingredients = data.get('card', {}).get('ingredients', [])
            
            print(f"✅ Techcard generated successfully")
            print(f"   ID: {techcard_id}")
            print(f"   Ingredients: {len(ingredients)}")
            
            # Analyze article assignment
            articles_assigned = 0
            for ing in ingredients:
                if ing.get('product_code') or ing.get('article') or ing.get('skuId'):
                    articles_assigned += 1
            
            print(f"   Articles assigned: {articles_assigned}/{len(ingredients)}")
            
            return techcard_id, data
        else:
            print(f"❌ Failed to generate techcard: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None, None

def test_export_formats(techcard_id):
    """Test different export formats"""
    print("\n🔍 TESTING EXPORT FORMATS")
    print("=" * 50)
    
    if not techcard_id:
        print("❌ No techcard ID available")
        return
    
    # Test different export endpoints
    endpoints = [
        {
            'name': 'Enhanced Export',
            'url': f"{API_BASE}/v1/techcards.v2/export/enhanced/iiko.xlsx",
            'data': {'techcard_ids': [techcard_id], 'operational_rounding': True}
        },
        {
            'name': 'ZIP Export',
            'url': f"{API_BASE}/v1/export/zip", 
            'data': {'techcard_ids': [techcard_id]}
        },
        {
            'name': 'Individual Export',
            'url': f"{API_BASE}/v1/techcards.v2/export/iiko",
            'data': {'techcard_ids': [techcard_id]}
        }
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint['name']}...")
            
            response = requests.post(
                endpoint['url'],
                json=endpoint['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            # Extract filename
            content_disposition = response.headers.get('content-disposition', '')
            filename = None
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            is_zip = 'zip' in content_type.lower()
            is_xlsx = 'spreadsheet' in content_type.lower() or 'excel' in content_type.lower()
            
            results[endpoint['name']] = {
                'status': response.status_code,
                'content_type': content_type,
                'size': content_length,
                'filename': filename,
                'is_zip': is_zip,
                'is_xlsx': is_xlsx,
                'success': response.status_code == 200
            }
            
            if response.status_code == 200:
                print(f"   ✅ Success: {content_type}, {content_length} bytes")
                if filename:
                    print(f"   📁 Filename: {filename}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results[endpoint['name']] = {'error': str(e), 'success': False}
    
    return results

def analyze_export_content(techcard_id):
    """Analyze export content for UX polish requirements"""
    print("\n🔍 ANALYZING EXPORT CONTENT")
    print("=" * 50)
    
    if not techcard_id:
        print("❌ No techcard ID available")
        return
    
    try:
        # Try to get export content
        response = requests.post(
            f"{API_BASE}/v1/techcards.v2/export/enhanced/iiko.xlsx",
            json={'techcard_ids': [techcard_id], 'operational_rounding': True},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            content_str = str(response.content)
            
            # Analyze unit patterns
            print("📊 Unit Analysis:")
            
            # Look for weight patterns
            gram_large = re.findall(r'\b([1-9]\d{2,3})\s*г', content_str)
            gram_decimal = re.findall(r'\b(0\.\d{1,3})\s*г', content_str)
            kilo_decimal = re.findall(r'\b(0\.\d{1,3})\s*кг', content_str)
            
            print(f"   Large gram values (200г): {len(gram_large)} found")
            print(f"   Decimal gram values (0.200г): {len(gram_decimal)} found")
            print(f"   Decimal kilo values (0.200кг): {len(kilo_decimal)} found")
            
            if len(gram_large) > 0:
                print(f"   🚨 NEEDS KILO CONVERSION: Found large gram values")
                print(f"   Sample values: {gram_large[:3]}")
            else:
                print(f"   ✅ Kilo format appears to be used")
            
            # Analyze article patterns
            print("\n📊 Article Analysis:")
            
            five_digit = re.findall(r'\b(\d{5})\b', content_str)
            leading_zero = re.findall(r'\b(0\d{4})\b', content_str)
            
            print(f"   5-digit articles: {len(set(five_digit))} found")
            print(f"   Leading zero articles: {len(set(leading_zero))} found")
            
            if len(set(five_digit)) > 0:
                print(f"   ✅ 5-digit article format detected")
                print(f"   Sample articles: {list(set(five_digit))[:3]}")
            else:
                print(f"   ⚠️  No clear 5-digit article pattern found")
            
            return {
                'kilo_conversion_needed': len(gram_large) > 0,
                'article_format_good': len(set(five_digit)) > 0,
                'sample_large_grams': gram_large[:3],
                'sample_articles': list(set(five_digit))[:3]
            }
            
        else:
            print(f"❌ Failed to get export content: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Exception analyzing content: {str(e)}")
        return None

def check_instruction_endpoints():
    """Check for existing instruction endpoints"""
    print("\n🔍 CHECKING INSTRUCTION ENDPOINTS")
    print("=" * 50)
    
    endpoints = [
        f"{API_BASE}/v1/export/instructions",
        f"{API_BASE}/v1/help/iiko-import", 
        f"{API_BASE}/v1/docs/export-guide",
        f"{API_BASE}/v1/help",
        f"{API_BASE}/docs"
    ]
    
    found_instructions = []
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                found_instructions.append({
                    'url': endpoint,
                    'status': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'size': len(response.content)
                })
                print(f"   ✅ Found: {endpoint}")
            else:
                print(f"   ❌ Not found: {endpoint} ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Error: {endpoint} - {str(e)}")
    
    if found_instructions:
        print(f"\n✅ Found {len(found_instructions)} instruction endpoints")
    else:
        print(f"\n🚨 NO INSTRUCTION ENDPOINTS FOUND - UX instructions needed")
    
    return found_instructions

def generate_ux_polish_report(techcard_data, export_results, content_analysis, instructions):
    """Generate comprehensive UX polish report"""
    print("\n" + "="*80)
    print("🎯 UX POLISH REQUIREMENTS ANALYSIS REPORT")
    print("="*80)
    
    # Analyze each UX polish requirement
    requirements = {}
    
    # 1. Auto Update Product Articles
    if techcard_data:
        ingredients = techcard_data.get('card', {}).get('ingredients', [])
        articles_assigned = sum(1 for ing in ingredients if ing.get('product_code') or ing.get('article') or ing.get('skuId'))
        
        if articles_assigned > 0:
            requirements["Auto Update Product Articles"] = "✅ Working (some articles assigned)"
        else:
            requirements["Auto Update Product Articles"] = "⚠️ Limited (no articles in test case)"
    else:
        requirements["Auto Update Product Articles"] = "❌ Cannot test (no techcard)"
    
    # 2. Individual XLSX Export
    if export_results:
        xlsx_exports = [r for r in export_results.values() if r.get('is_xlsx') and r.get('success')]
        zip_exports = [r for r in export_results.values() if r.get('is_zip') and r.get('success')]
        
        if xlsx_exports and not zip_exports:
            requirements["Individual XLSX Export"] = "✅ Available (XLSX only)"
        elif xlsx_exports and zip_exports:
            requirements["Individual XLSX Export"] = "⚠️ Mixed (both XLSX and ZIP)"
        elif zip_exports and not xlsx_exports:
            requirements["Individual XLSX Export"] = "❌ Missing (ZIP only)"
        else:
            requirements["Individual XLSX Export"] = "❌ No working exports"
    else:
        requirements["Individual XLSX Export"] = "❌ Cannot test"
    
    # 3. Kilo Conversion
    if content_analysis:
        if content_analysis.get('kilo_conversion_needed'):
            requirements["Kilo Conversion (0.200 format)"] = "❌ Needs Implementation (found large gram values)"
        else:
            requirements["Kilo Conversion (0.200 format)"] = "✅ Appears Implemented"
    else:
        requirements["Kilo Conversion (0.200 format)"] = "❌ Cannot analyze"
    
    # 4. Filename Structure
    if export_results:
        good_filenames = []
        for name, result in export_results.items():
            filename = result.get('filename', '')
            if filename and len(filename) > 10 and ('ttk' in filename.lower() or 'dish' in filename.lower()):
                good_filenames.append(filename)
        
        if good_filenames:
            requirements["Filename Structure for iikoWeb"] = f"✅ Good ({len(good_filenames)} structured filenames)"
        else:
            requirements["Filename Structure for iikoWeb"] = "❌ Needs Improvement (no structured filenames)"
    else:
        requirements["Filename Structure for iikoWeb"] = "❌ Cannot test"
    
    # 5. UX Instructions
    if instructions:
        requirements["UX Instructions for iikoWeb"] = f"✅ Available ({len(instructions)} endpoints found)"
    else:
        requirements["UX Instructions for iikoWeb"] = "❌ Missing (no instruction endpoints)"
    
    # Print requirements analysis
    print("\n🎨 UX POLISH REQUIREMENTS STATUS:")
    for requirement, status in requirements.items():
        print(f"   {status} {requirement}")
    
    # Count issues
    critical_issues = len([r for r in requirements.values() if r.startswith("❌")])
    warnings = len([r for r in requirements.values() if r.startswith("⚠️")])
    working = len([r for r in requirements.values() if r.startswith("✅")])
    
    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Working: {working}")
    print(f"   ⚠️  Warnings: {warnings}")
    print(f"   ❌ Critical Issues: {critical_issues}")
    
    # Recommendations
    print(f"\n💡 IMPLEMENTATION RECOMMENDATIONS:")
    
    recommendations = []
    
    for requirement, status in requirements.items():
        if status.startswith("❌"):
            if "Auto Update" in requirement:
                recommendations.append("Implement automatic article assignment after manual mapping")
            elif "Individual XLSX" in requirement:
                recommendations.append("Add individual XLSX export endpoints (TTK_Омлет.xlsx, DishСкелетоны_Омлет.xlsx)")
            elif "Kilo Conversion" in requirement:
                recommendations.append("Convert all weights to kilogram format (0.200 instead of 200г)")
            elif "Filename Structure" in requirement:
                recommendations.append("Implement structured filenames with dish names and type prefixes")
            elif "UX Instructions" in requirement:
                recommendations.append("Add comprehensive UX instructions for iikoWeb import workflow")
    
    if not recommendations:
        recommendations.append("All UX polish requirements appear to be implemented!")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    return {
        'requirements': requirements,
        'critical_issues': critical_issues,
        'warnings': warnings,
        'working': working,
        'recommendations': recommendations
    }

def main():
    """Main execution"""
    print("🚀 UX POLISH EXPORT SYSTEM FOCUSED ANALYSIS")
    print("=" * 80)
    print("Анализ текущего состояния системы экспорта для требований UX polish")
    print()
    
    # Step 1: Generate techcard
    techcard_id, techcard_data = test_techcard_generation()
    
    # Step 2: Test export formats
    export_results = test_export_formats(techcard_id)
    
    # Step 3: Analyze export content
    content_analysis = analyze_export_content(techcard_id)
    
    # Step 4: Check instructions
    instructions = check_instruction_endpoints()
    
    # Step 5: Generate report
    report = generate_ux_polish_report(techcard_data, export_results, content_analysis, instructions)
    
    print(f"\n🎯 ANALYSIS COMPLETED")
    
    if report['critical_issues'] == 0:
        print(f"🎉 No critical issues found - system ready for UX polish!")
        return True
    else:
        print(f"🚨 {report['critical_issues']} critical issues found requiring attention")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)