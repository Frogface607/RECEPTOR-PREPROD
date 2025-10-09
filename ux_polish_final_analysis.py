#!/usr/bin/env python3
"""
UX POLISH EXPORT SYSTEM FINAL ANALYSIS
Comprehensive analysis of current export system for UX polish requirements
"""

import requests
import json
import zipfile
import tempfile
import os
import re
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def analyze_current_export_system():
    """Comprehensive analysis of current export system"""
    print("🚀 UX POLISH EXPORT SYSTEM COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    print("Анализ текущего состояния системы экспорта для требований UX polish")
    print()
    
    results = {
        'techcard_generation': None,
        'export_workflow': None,
        'file_analysis': None,
        'ux_requirements': {}
    }
    
    # Step 1: Generate test techcard
    print("🔍 STEP 1: TECHCARD GENERATION & ARTICLE ASSIGNMENT")
    print("=" * 60)
    
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
            
            # Analyze article assignment
            articles_assigned = 0
            sku_assigned = 0
            for ing in ingredients:
                if ing.get('product_code') or ing.get('article'):
                    articles_assigned += 1
                if ing.get('skuId'):
                    sku_assigned += 1
            
            results['techcard_generation'] = {
                'success': True,
                'techcard_id': techcard_id,
                'total_ingredients': len(ingredients),
                'articles_assigned': articles_assigned,
                'sku_assigned': sku_assigned,
                'assignment_rate': f"{(articles_assigned/len(ingredients)*100):.1f}%" if ingredients else "0%"
            }
            
            print(f"✅ Techcard generated successfully")
            print(f"   ID: {techcard_id}")
            print(f"   Ingredients: {len(ingredients)}")
            print(f"   Articles assigned: {articles_assigned}/{len(ingredients)} ({results['techcard_generation']['assignment_rate']})")
            print(f"   SKUs assigned: {sku_assigned}/{len(ingredients)}")
            
            # Analyze auto-assignment capability
            if articles_assigned == 0 and sku_assigned == 0:
                results['ux_requirements']['auto_update_articles'] = "❌ No automatic article assignment detected"
            elif articles_assigned > 0 or sku_assigned > 0:
                results['ux_requirements']['auto_update_articles'] = f"⚠️ Partial assignment ({articles_assigned + sku_assigned}/{len(ingredients)} items)"
            
        else:
            print(f"❌ Failed to generate techcard: {response.status_code}")
            results['techcard_generation'] = {'success': False, 'error': response.status_code}
            results['ux_requirements']['auto_update_articles'] = "❌ Cannot test - techcard generation failed"
            return results
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results['techcard_generation'] = {'success': False, 'error': str(e)}
        results['ux_requirements']['auto_update_articles'] = "❌ Cannot test - exception occurred"
        return results
    
    # Step 2: Test export workflow
    print("\n🔍 STEP 2: EXPORT WORKFLOW ANALYSIS")
    print("=" * 60)
    
    techcard_id = results['techcard_generation']['techcard_id']
    
    try:
        # Test preflight
        print("Testing preflight orchestration...")
        preflight_response = requests.post(
            f"{API_BASE}/v1/export/preflight",
            json={"techcardIds": [techcard_id]},
            headers={'Content-Type': 'application/json'}
        )
        
        if preflight_response.status_code == 200:
            preflight_data = preflight_response.json()
            print(f"   ✅ Preflight successful")
            print(f"   TTK Date: {preflight_data.get('ttkDate')}")
            print(f"   Dish skeletons: {preflight_data.get('counts', {}).get('dishSkeletons', 0)}")
            print(f"   Product skeletons: {preflight_data.get('counts', {}).get('productSkeletons', 0)}")
            
            # Test ZIP export
            print("Testing ZIP export...")
            export_response = requests.post(
                f"{API_BASE}/v1/export/zip",
                json={
                    "techcardIds": [techcard_id],
                    "preflight_result": preflight_data
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if export_response.status_code == 200:
                content_type = export_response.headers.get('content-type', '')
                content_disposition = export_response.headers.get('content-disposition', '')
                
                # Extract filename
                filename = None
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                
                results['export_workflow'] = {
                    'success': True,
                    'export_format': 'ZIP',
                    'content_type': content_type,
                    'filename': filename,
                    'file_size': len(export_response.content),
                    'preflight_data': preflight_data
                }
                
                print(f"   ✅ ZIP export successful")
                print(f"   Content-Type: {content_type}")
                print(f"   Filename: {filename}")
                print(f"   Size: {len(export_response.content)} bytes")
                
                # Save ZIP for analysis
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                    tmp_file.write(export_response.content)
                    zip_path = tmp_file.name
                
                # Analyze ZIP contents
                results['file_analysis'] = analyze_zip_contents(zip_path)
                
                # Clean up
                os.unlink(zip_path)
                
            else:
                print(f"   ❌ ZIP export failed: {export_response.status_code}")
                results['export_workflow'] = {'success': False, 'error': export_response.status_code}
                
        else:
            print(f"   ❌ Preflight failed: {preflight_response.status_code}")
            results['export_workflow'] = {'success': False, 'error': preflight_response.status_code}
            
    except Exception as e:
        print(f"❌ Exception in export workflow: {str(e)}")
        results['export_workflow'] = {'success': False, 'error': str(e)}
    
    # Step 3: Analyze UX requirements based on findings
    analyze_ux_requirements(results)
    
    return results

def analyze_zip_contents(zip_path):
    """Analyze ZIP file contents for UX polish requirements"""
    print("\n🔍 STEP 3: FILE CONTENT ANALYSIS")
    print("=" * 60)
    
    analysis = {
        'files_found': [],
        'kilo_conversion_analysis': {},
        'article_format_analysis': {},
        'filename_structure_analysis': {}
    }
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            file_list = zip_file.namelist()
            analysis['files_found'] = file_list
            
            print(f"Files in ZIP: {file_list}")
            
            # Analyze each file
            for filename in file_list:
                print(f"\nAnalyzing {filename}...")
                
                try:
                    # Read file content as text (for pattern analysis)
                    with zip_file.open(filename) as file:
                        content = file.read()
                        content_str = str(content)
                        
                        # Analyze unit patterns for kilo conversion
                        gram_large = re.findall(r'\b([1-9]\d{2,3})\s*г', content_str)
                        gram_decimal = re.findall(r'\b(0\.\d{1,3})\s*г', content_str)
                        kilo_decimal = re.findall(r'\b(0\.\d{1,3})\s*кг', content_str)
                        
                        # Analyze article patterns
                        five_digit = re.findall(r'\b(\d{5})\b', content_str)
                        leading_zero = re.findall(r'\b(0\d{4})\b', content_str)
                        
                        file_analysis = {
                            'large_gram_values': len(gram_large),
                            'decimal_gram_values': len(gram_decimal),
                            'decimal_kilo_values': len(kilo_decimal),
                            'five_digit_articles': len(set(five_digit)),
                            'leading_zero_articles': len(set(leading_zero)),
                            'sample_large_grams': gram_large[:3],
                            'sample_articles': list(set(five_digit))[:3]
                        }
                        
                        analysis['kilo_conversion_analysis'][filename] = file_analysis
                        analysis['article_format_analysis'][filename] = file_analysis
                        
                        print(f"   Large gram values: {file_analysis['large_gram_values']}")
                        print(f"   Decimal values: {file_analysis['decimal_gram_values'] + file_analysis['decimal_kilo_values']}")
                        print(f"   5-digit articles: {file_analysis['five_digit_articles']}")
                        
                except Exception as e:
                    print(f"   ⚠️ Could not analyze {filename}: {str(e)}")
            
            # Analyze filename structure
            analysis['filename_structure_analysis'] = analyze_filename_structure(file_list)
            
    except Exception as e:
        print(f"❌ Error analyzing ZIP: {str(e)}")
        analysis['error'] = str(e)
    
    return analysis

def analyze_filename_structure(file_list):
    """Analyze filename structure for UX polish requirements"""
    print(f"\nFilename Structure Analysis:")
    
    structure_analysis = {
        'total_files': len(file_list),
        'structured_filenames': 0,
        'has_dish_names': 0,
        'has_type_prefixes': 0,
        'filename_quality': 'Poor'
    }
    
    for filename in file_list:
        print(f"   📁 {filename}")
        
        # Check for structured naming
        is_structured = False
        has_dish_name = False
        has_type_prefix = False
        
        # Check for type prefixes
        if any(prefix in filename.lower() for prefix in ['ttk_', 'dish_', 'product_', 'iiko_']):
            has_type_prefix = True
            structure_analysis['has_type_prefixes'] += 1
        
        # Check for dish names (would need to be implemented for specific dishes)
        if any(dish in filename.lower() for dish in ['омлет', 'omlet']):
            has_dish_name = True
            structure_analysis['has_dish_names'] += 1
        
        # Check if filename is structured (has meaningful components)
        if len(filename) > 10 and ('_' in filename or '-' in filename):
            is_structured = True
            structure_analysis['structured_filenames'] += 1
        
        print(f"      Structured: {is_structured}, Type prefix: {has_type_prefix}, Dish name: {has_dish_name}")
    
    # Determine overall quality
    if structure_analysis['structured_filenames'] == structure_analysis['total_files']:
        structure_analysis['filename_quality'] = 'Good'
    elif structure_analysis['structured_filenames'] > 0:
        structure_analysis['filename_quality'] = 'Mixed'
    
    return structure_analysis

def analyze_ux_requirements(results):
    """Analyze UX polish requirements based on all findings"""
    print("\n🔍 STEP 4: UX POLISH REQUIREMENTS ANALYSIS")
    print("=" * 60)
    
    # 1. Auto Update Product Articles (already analyzed)
    
    # 2. Individual XLSX Export vs ZIP
    if results['export_workflow'] and results['export_workflow']['success']:
        export_format = results['export_workflow']['export_format']
        if export_format == 'ZIP':
            results['ux_requirements']['individual_xlsx_export'] = "❌ Currently ZIP only - needs individual XLSX files (TTK_Омлет.xlsx, DishСкелетоны_Омлет.xlsx)"
        else:
            results['ux_requirements']['individual_xlsx_export'] = "✅ Individual XLSX export available"
    else:
        results['ux_requirements']['individual_xlsx_export'] = "❌ Cannot test - export failed"
    
    # 3. Kilo Conversion Analysis
    if results['file_analysis'] and 'kilo_conversion_analysis' in results['file_analysis']:
        total_large_grams = 0
        total_decimal_values = 0
        
        for filename, analysis in results['file_analysis']['kilo_conversion_analysis'].items():
            total_large_grams += analysis['large_gram_values']
            total_decimal_values += analysis['decimal_gram_values'] + analysis['decimal_kilo_values']
        
        if total_large_grams > total_decimal_values:
            results['ux_requirements']['kilo_conversion'] = f"❌ Needs kilo conversion - found {total_large_grams} large gram values vs {total_decimal_values} decimal values"
        elif total_decimal_values > 0:
            results['ux_requirements']['kilo_conversion'] = f"✅ Kilo format detected - {total_decimal_values} decimal values found"
        else:
            results['ux_requirements']['kilo_conversion'] = "⚠️ No clear weight patterns detected"
    else:
        results['ux_requirements']['kilo_conversion'] = "❌ Cannot analyze - no file content available"
    
    # 4. Filename Structure for iikoWeb
    if results['file_analysis'] and 'filename_structure_analysis' in results['file_analysis']:
        structure = results['file_analysis']['filename_structure_analysis']
        quality = structure['filename_quality']
        
        if quality == 'Good':
            results['ux_requirements']['filename_structure'] = f"✅ Good filename structure - {structure['structured_filenames']}/{structure['total_files']} files structured"
        elif quality == 'Mixed':
            results['ux_requirements']['filename_structure'] = f"⚠️ Mixed filename structure - {structure['structured_filenames']}/{structure['total_files']} files structured"
        else:
            results['ux_requirements']['filename_structure'] = f"❌ Poor filename structure - needs dish names and type prefixes"
    else:
        results['ux_requirements']['filename_structure'] = "❌ Cannot analyze - no files available"
    
    # 5. UX Instructions for iikoWeb
    # Test for instruction endpoints
    instruction_endpoints = [
        f"{API_BASE}/v1/export/instructions",
        f"{API_BASE}/v1/help/iiko-import",
        f"{API_BASE}/v1/docs/export-guide"
    ]
    
    instructions_found = 0
    for endpoint in instruction_endpoints:
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                instructions_found += 1
        except:
            pass
    
    if instructions_found > 0:
        results['ux_requirements']['ux_instructions'] = f"✅ Instructions available - {instructions_found} endpoints found"
    else:
        results['ux_requirements']['ux_instructions'] = "❌ No UX instructions found - need comprehensive iikoWeb import guide"

def generate_final_report(results):
    """Generate final comprehensive report"""
    print("\n" + "="*80)
    print("🎯 UX POLISH EXPORT SYSTEM FINAL ANALYSIS REPORT")
    print("="*80)
    
    print(f"\n📊 CURRENT SYSTEM STATUS:")
    
    if results['techcard_generation'] and results['techcard_generation']['success']:
        print(f"   ✅ TechCard Generation: Working")
        print(f"      - Generated techcard with {results['techcard_generation']['total_ingredients']} ingredients")
        print(f"      - Article assignment rate: {results['techcard_generation']['assignment_rate']}")
    else:
        print(f"   ❌ TechCard Generation: Failed")
    
    if results['export_workflow'] and results['export_workflow']['success']:
        print(f"   ✅ Export Workflow: Working")
        print(f"      - Format: {results['export_workflow']['export_format']}")
        print(f"      - File size: {results['export_workflow']['file_size']} bytes")
        print(f"      - Filename: {results['export_workflow']['filename']}")
    else:
        print(f"   ❌ Export Workflow: Failed")
    
    if results['file_analysis'] and 'files_found' in results['file_analysis']:
        files = results['file_analysis']['files_found']
        print(f"   ✅ File Generation: {len(files)} files created")
        print(f"      - Files: {', '.join(files)}")
    else:
        print(f"   ❌ File Generation: No files analyzed")
    
    print(f"\n🎨 UX POLISH REQUIREMENTS STATUS:")
    
    for requirement, status in results['ux_requirements'].items():
        requirement_name = {
            'auto_update_articles': 'Auto Update Product Articles',
            'individual_xlsx_export': 'Individual XLSX Export',
            'kilo_conversion': 'Kilo Conversion (0.200 format)',
            'filename_structure': 'Filename Structure for iikoWeb',
            'ux_instructions': 'UX Instructions for iikoWeb'
        }.get(requirement, requirement)
        
        print(f"   {status} {requirement_name}")
    
    # Count issues
    critical_issues = len([s for s in results['ux_requirements'].values() if s.startswith("❌")])
    warnings = len([s for s in results['ux_requirements'].values() if s.startswith("⚠️")])
    working = len([s for s in results['ux_requirements'].values() if s.startswith("✅")])
    
    print(f"\n📈 SUMMARY:")
    print(f"   ✅ Working: {working}")
    print(f"   ⚠️  Warnings: {warnings}")
    print(f"   ❌ Critical Issues: {critical_issues}")
    print(f"   📊 Success Rate: {(working/(working+warnings+critical_issues)*100):.1f}%")
    
    print(f"\n💡 UX POLISH IMPLEMENTATION PRIORITIES:")
    
    priorities = []
    
    for requirement, status in results['ux_requirements'].items():
        if status.startswith("❌"):
            if 'individual_xlsx_export' in requirement:
                priorities.append("🔥 HIGH: Implement individual XLSX export endpoints (TTK_Омлет.xlsx, DishСкелетоны_Омлет.xlsx)")
            elif 'kilo_conversion' in requirement:
                priorities.append("🔥 HIGH: Convert all weights to kilogram format (0.200 instead of 200г)")
            elif 'filename_structure' in requirement:
                priorities.append("🔥 HIGH: Implement structured filenames with dish names and type prefixes")
            elif 'ux_instructions' in requirement:
                priorities.append("🔥 HIGH: Add comprehensive UX instructions for iikoWeb import workflow")
            elif 'auto_update_articles' in requirement:
                priorities.append("🔥 HIGH: Implement automatic article assignment after manual mapping")
    
    for requirement, status in results['ux_requirements'].items():
        if status.startswith("⚠️"):
            if 'auto_update_articles' in requirement:
                priorities.append("⚠️ MEDIUM: Improve automatic article assignment coverage")
            elif 'filename_structure' in requirement:
                priorities.append("⚠️ MEDIUM: Improve filename structure consistency")
    
    if not priorities:
        priorities.append("🎉 All UX polish requirements are implemented!")
    
    for i, priority in enumerate(priorities, 1):
        print(f"   {i}. {priority}")
    
    print(f"\n🎯 RECOMMENDED WORKFLOW FOR UX POLISH:")
    print(f"   1. Generate техкарта for 'Омлет с зеленью'")
    print(f"   2. Сначала импортируйте скелеты блюд (Dish-Skeletons.xlsx)")
    print(f"   3. Затем импортируйте скелеты продуктов (Product-Skeletons.xlsx)")
    print(f"   4. Наконец импортируйте техкарту (TTK_Омлет.xlsx)")
    print(f"   5. Проверьте все артикулы в формате 0.200 кг")
    print(f"   6. Добавьте UX инструкции для пользователей")
    
    return {
        'critical_issues': critical_issues,
        'warnings': warnings,
        'working': working,
        'success_rate': (working/(working+warnings+critical_issues)*100) if (working+warnings+critical_issues) > 0 else 0,
        'priorities': priorities
    }

def main():
    """Main execution"""
    results = analyze_current_export_system()
    report = generate_final_report(results)
    
    print(f"\n✅ UX POLISH ANALYSIS COMPLETED")
    
    if report['critical_issues'] == 0:
        print(f"🎉 No critical issues found - system ready for UX polish!")
        return True
    else:
        print(f"🚨 {report['critical_issues']} critical issues found requiring implementation")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)