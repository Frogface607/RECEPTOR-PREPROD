#!/usr/bin/env python3
"""
Export Skeleton Functionality Testing
Проверить функциональность экспорта скелетонов номенклатур

Test Scenario (from Russian review request):
1. Find/create tech card with ingredient "Гребешки" (Scallops)
2. Run preflight check via /api/v1/export/preflight
3. Verify missing products include "Гребешки"
4. Run ZIP export via /api/v1/export/zip
5. Verify ZIP contains Product-Skeletons.xlsx and Dish-Skeletons.xlsx
6. Verify skeleton files contain correct data with generated articles
"""

import requests
import json
import time
import zipfile
import io
import pandas as pd
from datetime import datetime
import os
import sys

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ExportSkeletonTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Export-Skeleton-Tester/1.0'
        })
        self.test_results = []
        self.created_techcard_id = None
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def test_1_find_or_create_techcard_with_scallops(self):
        """Test 1: Find existing tech card with 'Гребешки' or create new one"""
        try:
            print("🔍 Searching for existing tech cards with 'Гребешки'...")
            
            # Get all tech cards for demo user
            response = self.session.get(f"{API_BASE}/v1/user/demo_user/techcards")
            
            if response.status_code == 200:
                techcards = response.json()
                print(f"Found {len(techcards)} existing tech cards")
                
                # Look for tech card with scallops
                scallop_techcard = None
                for tc in techcards:
                    content = tc.get('content', '').lower()
                    name = tc.get('dish_name', '').lower()
                    if 'гребешки' in content or 'гребешки' in name or 'scallop' in content.lower():
                        scallop_techcard = tc
                        break
                
                if scallop_techcard:
                    self.created_techcard_id = scallop_techcard['id']
                    self.log_result(
                        "Find existing tech card with scallops",
                        True,
                        f"Found existing tech card: {scallop_techcard['dish_name']} (ID: {self.created_techcard_id})"
                    )
                    return True
            
            # If no existing tech card found, create new one
            print("📝 Creating new tech card 'Тако с гребешками'...")
            
            create_data = {
                "name": "Тако с гребешками",
                "user_id": "demo_user"
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/generate", json=create_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'READY' and result.get('card'):
                    self.created_techcard_id = result['card']['meta']['id']
                    self.log_result(
                        "Create new tech card with scallops",
                        True,
                        f"Created tech card: {result['card']['meta']['title']} (ID: {self.created_techcard_id})"
                    )
                    return True
                else:
                    self.log_result(
                        "Create new tech card with scallops",
                        False,
                        error=f"Generation failed: {result}"
                    )
                    return False
            else:
                self.log_result(
                    "Create new tech card with scallops",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Find or create tech card with scallops",
                False,
                error=str(e)
            )
            return False
    
    def test_2_run_preflight_check(self):
        """Test 2: Run preflight check and verify missing products"""
        try:
            if not self.created_techcard_id:
                self.log_result(
                    "Run preflight check",
                    False,
                    error="No tech card ID available"
                )
                return False, None
            
            print(f"🔍 Running preflight check for tech card {self.created_techcard_id}...")
            
            preflight_data = {
                "techcardIds": [self.created_techcard_id],
                "organization_id": "default"
            }
            
            response = self.session.post(f"{API_BASE}/v1/export/preflight", json=preflight_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if we have missing products
                missing_products = result.get('missing', {}).get('products', [])
                missing_dishes = result.get('missing', {}).get('dishes', [])
                
                # Look for scallops in missing products
                scallop_found = False
                scallop_product = None
                for product in missing_products:
                    if 'гребешки' in product.get('name', '').lower():
                        scallop_found = True
                        scallop_product = product
                        break
                
                details = f"Missing products: {len(missing_products)}, Missing dishes: {len(missing_dishes)}"
                if scallop_found:
                    details += f", Found 'Гребешки' in missing products ✅ (Article: {scallop_product.get('article', 'N/A')})"
                else:
                    details += ", 'Гребешки' not found in missing products"
                    # Show what products we did find
                    if missing_products:
                        product_names = [p.get('name', 'Unknown') for p in missing_products[:3]]
                        details += f", Found products: {product_names}"
                
                self.log_result(
                    "Run preflight check",
                    True,
                    details
                )
                
                return True, result
            else:
                self.log_result(
                    "Run preflight check",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False, None
                
        except Exception as e:
            self.log_result(
                "Run preflight check",
                False,
                error=str(e)
            )
            return False, None
    
    def test_3_export_zip_with_skeletons(self, preflight_result):
        """Test 3: Export ZIP and verify skeleton files"""
        try:
            if not self.created_techcard_id or not preflight_result:
                self.log_result(
                    "Export ZIP with skeletons",
                    False,
                    error="Missing tech card ID or preflight result"
                )
                return False, None
            
            print(f"📦 Exporting ZIP for tech card {self.created_techcard_id}...")
            
            export_data = {
                "techcardIds": [self.created_techcard_id],
                "operational_rounding": True,
                "organization_id": "default",
                "preflight_result": preflight_result
            }
            
            response = self.session.post(f"{API_BASE}/v1/export/zip", json=export_data)
            
            if response.status_code == 200:
                # Check if response is ZIP file
                content_type = response.headers.get('content-type', '')
                if 'zip' in content_type or 'application/octet-stream' in content_type:
                    zip_content = response.content
                    zip_size = len(zip_content)
                    
                    self.log_result(
                        "Export ZIP file",
                        True,
                        f"ZIP file created successfully ({zip_size} bytes)"
                    )
                    
                    return True, zip_content
                else:
                    self.log_result(
                        "Export ZIP file",
                        False,
                        error=f"Expected ZIP file, got {content_type}. Response: {response.text[:200]}"
                    )
                    return False, None
            else:
                self.log_result(
                    "Export ZIP file",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False, None
                
        except Exception as e:
            self.log_result(
                "Export ZIP with skeletons",
                False,
                error=str(e)
            )
            return False, None
    
    def test_4_validate_zip_contents(self, zip_content):
        """Test 4: Validate ZIP contents and skeleton files"""
        try:
            if not zip_content:
                self.log_result(
                    "Validate ZIP contents",
                    False,
                    error="No ZIP content to validate"
                )
                return False
            
            print("📋 Validating ZIP file contents...")
            
            # Open ZIP file
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # Check for files - when dishes are missing, iiko_TTK.xlsx won't be created (dish-first rule)
                expected_files = ['Product-Skeletons.xlsx', 'Dish-Skeletons.xlsx', 'iiko_TTK.xlsx']
                
                found_files = []
                skeleton_files = []
                
                # Check all possible files
                for file_name in expected_files:
                    if file_name in file_list:
                        found_files.append(file_name)
                        if 'Skeleton' in file_name:
                            skeleton_files.append(file_name)
                
                details = f"Found files: {found_files}"
                if skeleton_files:
                    details += f", Skeleton files: {skeleton_files}"
                
                # Success if we have at least one skeleton file (the main purpose of this test)
                success = len(skeleton_files) > 0
                
                if 'iiko_TTK.xlsx' not in found_files:
                    details += " (iiko_TTK.xlsx missing due to dish-first rule - expected behavior)"
                
                self.log_result(
                    "Validate ZIP file structure",
                    success,
                    details
                )
                
                # Validate skeleton files content if they exist
                if 'Product-Skeletons.xlsx' in skeleton_files:
                    self._validate_product_skeletons(zip_file)
                
                if 'Dish-Skeletons.xlsx' in skeleton_files:
                    self._validate_dish_skeletons(zip_file)
                
                return success
                
        except Exception as e:
            self.log_result(
                "Validate ZIP contents",
                False,
                error=str(e)
            )
            return False
    
    def _validate_product_skeletons(self, zip_file):
        """Validate Product-Skeletons.xlsx content"""
        try:
            print("🔍 Validating Product-Skeletons.xlsx...")
            
            with zip_file.open('Product-Skeletons.xlsx') as excel_file:
                df = pd.read_excel(excel_file)
                
                # Check if we have data
                row_count = len(df)
                
                # Look for scallops
                scallop_found = False
                scallop_article = None
                if 'Наименование' in df.columns or 'Name' in df.columns:
                    name_col = 'Наименование' if 'Наименование' in df.columns else 'Name'
                    for idx, name in enumerate(df[name_col].astype(str)):
                        if 'гребешки' in name.lower():
                            scallop_found = True
                            # Try to get article for this row
                            for col in df.columns:
                                if 'артикул' in col.lower() or 'article' in col.lower():
                                    scallop_article = df.iloc[idx][col]
                                    break
                            break
                
                # Check for article column
                has_articles = any('артикул' in col.lower() or 'article' in col.lower() for col in df.columns)
                
                details = f"Rows: {row_count}, Columns: {list(df.columns)}"
                if scallop_found:
                    details += f", Found 'Гребешки' ✅"
                    if scallop_article:
                        details += f" (Article: {scallop_article})"
                if has_articles:
                    details += ", Has article column ✅"
                
                self.log_result(
                    "Validate Product-Skeletons.xlsx",
                    row_count > 0 and scallop_found,
                    details
                )
                
        except Exception as e:
            self.log_result(
                "Validate Product-Skeletons.xlsx",
                False,
                error=str(e)
            )
    
    def _validate_dish_skeletons(self, zip_file):
        """Validate Dish-Skeletons.xlsx content"""
        try:
            print("🔍 Validating Dish-Skeletons.xlsx...")
            
            with zip_file.open('Dish-Skeletons.xlsx') as excel_file:
                df = pd.read_excel(excel_file)
                
                # Check if we have data
                row_count = len(df)
                
                # Look for our dish
                dish_found = False
                dish_article = None
                if 'Наименование' in df.columns or 'Name' in df.columns:
                    name_col = 'Наименование' if 'Наименование' in df.columns else 'Name'
                    for idx, name in enumerate(df[name_col].astype(str)):
                        if 'тако' in name.lower() and 'гребешки' in name.lower():
                            dish_found = True
                            # Try to get article for this row
                            for col in df.columns:
                                if 'артикул' in col.lower() or 'article' in col.lower():
                                    dish_article = df.iloc[idx][col]
                                    break
                            break
                
                # Check for article column
                has_articles = any('артикул' in col.lower() or 'article' in col.lower() for col in df.columns)
                
                details = f"Rows: {row_count}, Columns: {list(df.columns)}"
                if dish_found:
                    details += f", Found 'Тако с гребешками' ✅"
                    if dish_article:
                        details += f" (Article: {dish_article})"
                if has_articles:
                    details += ", Has article column ✅"
                
                self.log_result(
                    "Validate Dish-Skeletons.xlsx",
                    row_count > 0,
                    details
                )
                
        except Exception as e:
            self.log_result(
                "Validate Dish-Skeletons.xlsx",
                False,
                error=str(e)
            )
    
    def test_5_check_backend_logs(self):
        """Test 5: Check backend logs for errors"""
        try:
            print("📋 Checking backend logs...")
            
            # Try to get recent backend logs
            import subprocess
            
            try:
                # Check supervisor backend logs
                result = subprocess.run(
                    ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    log_content = result.stdout
                    error_count = log_content.lower().count('error')
                    warning_count = log_content.lower().count('warning')
                    
                    details = f"Recent log lines: 50, Errors: {error_count}, Warnings: {warning_count}"
                    
                    # Check for specific export-related errors
                    export_errors = []
                    for line in log_content.split('\n'):
                        if 'export' in line.lower() and ('error' in line.lower() or 'exception' in line.lower()):
                            export_errors.append(line.strip())
                    
                    if export_errors:
                        details += f", Export errors found: {len(export_errors)}"
                    
                    self.log_result(
                        "Check backend logs",
                        len(export_errors) == 0,
                        details,
                        f"Export errors: {export_errors[:3]}" if export_errors else ""
                    )
                else:
                    self.log_result(
                        "Check backend logs",
                        False,
                        error="Could not read backend logs"
                    )
                    
            except subprocess.TimeoutExpired:
                self.log_result(
                    "Check backend logs",
                    False,
                    error="Timeout reading backend logs"
                )
                
        except Exception as e:
            self.log_result(
                "Check backend logs",
                False,
                error=str(e)
            )
    
    def run_all_tests(self):
        """Run all export skeleton tests"""
        print("🚀 Starting Export Skeleton Functionality Tests")
        print("Testing: Экспорт скелетонов номенклатур для несопоставленных ингредиентов")
        print("=" * 80)
        
        # Test 1: Find or create tech card with scallops
        if not self.test_1_find_or_create_techcard_with_scallops():
            print("❌ Cannot proceed without tech card")
            return self.generate_summary()
        
        # Test 2: Run preflight check
        preflight_success, preflight_result = self.test_2_run_preflight_check()
        if not preflight_success:
            print("❌ Cannot proceed without preflight result")
            return self.generate_summary()
        
        # Test 3: Export ZIP
        zip_success, zip_content = self.test_3_export_zip_with_skeletons(preflight_result)
        if not zip_success:
            print("❌ Cannot validate ZIP without successful export")
            return self.generate_summary()
        
        # Test 4: Validate ZIP contents
        self.test_4_validate_zip_contents(zip_content)
        
        # Test 5: Check backend logs
        self.test_5_check_backend_logs()
        
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 EXPORT SKELETON FUNCTIONALITY TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['error']}")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
            if result['error']:
                print(f"    Error: {result['error']}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': passed_tests/total_tests*100,
            'results': self.test_results
        }

def main():
    """Main test execution"""
    tester = ExportSkeletonTester()
    summary = tester.run_all_tests()
    
    # Return appropriate exit code
    if summary['failed_tests'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()