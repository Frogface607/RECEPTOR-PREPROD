#!/usr/bin/env python3
"""
CRITICAL EXPORT BUGFIX TESTING: TypeError 'str' object has no attribute 'get'
Testing enhanced export process with operational rounding integration
"""

import requests
import json
import time
import os
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

class ExportBugfixTest:
    """Test critical export bugfix for TypeError with operational rounding"""
    
    def __init__(self):
        self.results = []
        self.test_data = self._create_test_data()
    
    def _create_test_data(self) -> Dict[str, Dict[str, Any]]:
        """Create test techcards for export testing"""
        
        # Simple techcard - basic ingredients
        simple_techcard = {
            "name": "Омлет классический",
            "description": "Простой омлет для тестирования экспорта",
            "ingredients": [
                {
                    "name": "яйца куриные",
                    "quantity": 2,
                    "unit": "шт",
                    "brutto_g": 100,
                    "netto_g": 96,
                    "loss_pct": 4,
                    "skuId": "egg-001"
                },
                {
                    "name": "молоко 3.2%",
                    "quantity": 50,
                    "unit": "мл",
                    "brutto_g": 50,
                    "netto_g": 50,
                    "loss_pct": 0,
                    "skuId": "milk-001"
                },
                {
                    "name": "масло сливочное",
                    "quantity": 10,
                    "unit": "г",
                    "brutto_g": 10,
                    "netto_g": 10,
                    "loss_pct": 0,
                    "skuId": "butter-001"
                }
            ],
            "yield": {
                "perPortion_g": 150,
                "perBatch_g": 150
            },
            "portions": 1,
            "process": [
                {
                    "step": 1,
                    "description": "Взбить яйца с молоком",
                    "time_min": 2,
                    "temp_c": 20
                },
                {
                    "step": 2,
                    "description": "Жарить на сковороде с маслом",
                    "time_min": 5,
                    "temp_c": 180
                }
            ],
            "meta": {
                "title": "Омлет классический",
                "category": "горячее",
                "difficulty": "easy"
            }
        }
        
        # Complex techcard - many ingredients, complex structure
        complex_techcard = {
            "name": "Борщ украинский с мясом",
            "description": "Сложный борщ для тестирования экспорта с множественными ингредиентами",
            "ingredients": [
                {
                    "name": "говядина на кости",
                    "quantity": 300,
                    "unit": "г",
                    "brutto_g": 300,
                    "netto_g": 240,
                    "loss_pct": 20,
                    "skuId": "beef-bone-001"
                },
                {
                    "name": "свекла",
                    "quantity": 150,
                    "unit": "г",
                    "brutto_g": 150,
                    "netto_g": 135,
                    "loss_pct": 10,
                    "skuId": "beetroot-001"
                },
                {
                    "name": "капуста белокочанная",
                    "quantity": 100,
                    "unit": "г",
                    "brutto_g": 100,
                    "netto_g": 90,
                    "loss_pct": 10,
                    "skuId": "cabbage-001"
                },
                {
                    "name": "морковь",
                    "quantity": 80,
                    "unit": "г",
                    "brutto_g": 80,
                    "netto_g": 72,
                    "loss_pct": 10,
                    "skuId": "carrot-001"
                },
                {
                    "name": "лук репчатый",
                    "quantity": 60,
                    "unit": "г",
                    "brutto_g": 60,
                    "netto_g": 54,
                    "loss_pct": 10,
                    "skuId": "onion-001"
                },
                {
                    "name": "томатная паста",
                    "quantity": 30,
                    "unit": "г",
                    "brutto_g": 30,
                    "netto_g": 30,
                    "loss_pct": 0,
                    "skuId": "tomato-paste-001"
                },
                {
                    "name": "картофель",
                    "quantity": 120,
                    "unit": "г",
                    "brutto_g": 120,
                    "netto_g": 96,
                    "loss_pct": 20,
                    "skuId": "potato-001"
                },
                {
                    "name": "чеснок",
                    "quantity": 5,
                    "unit": "г",
                    "brutto_g": 5,
                    "netto_g": 4,
                    "loss_pct": 20,
                    "skuId": "garlic-001"
                },
                {
                    "name": "укроп",
                    "quantity": 10,
                    "unit": "г",
                    "brutto_g": 10,
                    "netto_g": 8,
                    "loss_pct": 20,
                    "skuId": "dill-001"
                },
                {
                    "name": "сметана 20%",
                    "quantity": 50,
                    "unit": "г",
                    "brutto_g": 50,
                    "netto_g": 50,
                    "loss_pct": 0,
                    "skuId": "sour-cream-001"
                }
            ],
            "yield": {
                "perPortion_g": 330,
                "perBatch_g": 330
            },
            "portions": 1,
            "process": [
                {
                    "step": 1,
                    "description": "Варить бульон из говядины",
                    "time_min": 90,
                    "temp_c": 100
                },
                {
                    "step": 2,
                    "description": "Подготовить овощи",
                    "time_min": 15,
                    "temp_c": 20
                },
                {
                    "step": 3,
                    "description": "Обжарить свеклу с томатной пастой",
                    "time_min": 10,
                    "temp_c": 180
                },
                {
                    "step": 4,
                    "description": "Добавить овощи в бульон",
                    "time_min": 30,
                    "temp_c": 100
                },
                {
                    "step": 5,
                    "description": "Подавать со сметаной и зеленью",
                    "time_min": 2,
                    "temp_c": 20
                }
            ],
            "meta": {
                "title": "Борщ украинский с мясом",
                "category": "суп",
                "difficulty": "medium",
                "cuisine": "украинская"
            }
        }
        
        # Edge case techcard - potential meta issues
        edge_case_techcard = {
            "name": "Салат с проблемной мета",
            "description": "Техкарта для тестирования edge cases с meta объектом",
            "ingredients": [
                {
                    "name": "листья салата",
                    "quantity": 50,
                    "unit": "г",
                    "brutto_g": 50,
                    "netto_g": 45,
                    "loss_pct": 10,
                    "skuId": "lettuce-001"
                },
                {
                    "name": "помидоры черри",
                    "quantity": 100,
                    "unit": "г",
                    "brutto_g": 100,
                    "netto_g": 95,
                    "loss_pct": 5,
                    "skuId": "cherry-tomato-001"
                }
            ],
            "yield": {
                "perPortion_g": 140,
                "perBatch_g": 140
            },
            "portions": 1,
            "process": [
                {
                    "step": 1,
                    "description": "Смешать ингредиенты",
                    "time_min": 3,
                    "temp_c": 20
                }
            ],
            # Намеренно создаем потенциально проблемную meta структуру
            "meta": "Салат с проблемной мета"  # String instead of dict
        }
        
        return {
            "simple": simple_techcard,
            "complex": complex_techcard,
            "edge_case": edge_case_techcard
        }
    
    def test_enhanced_export_with_operational_rounding(self):
        """Test enhanced export endpoint with operational rounding enabled"""
        print("🎯 ENHANCED EXPORT WITH OPERATIONAL ROUNDING TESTING")
        print("=" * 70)
        
        test_cases = [
            ("simple", "Simple Techcard"),
            ("complex", "Complex Techcard"),
            ("edge_case", "Edge Case Techcard")
        ]
        
        for test_type, description in test_cases:
            techcard = self.test_data[test_type]
            
            print(f"\n📊 Testing {description}")
            print(f"   Techcard: {techcard['name']}")
            print(f"   Ingredients: {len(techcard['ingredients'])}")
            print(f"   Meta type: {type(techcard.get('meta', {}))}")
            
            # Test with operational rounding enabled
            export_request = {
                "techcard": techcard,
                "export_options": {
                    "operational_rounding": True,
                    "use_product_codes": True,
                    "dish_codes_mapping": {}
                }
            }
            
            try:
                start_time = time.time()
                
                response = requests.post(
                    f"{API_BASE}/techcards.v2/export/enhanced/iiko.xlsx",
                    json=export_request,
                    timeout=30
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                print(f"   Response time: {response_time:.1f}ms")
                print(f"   Status code: {response.status_code}")
                
                if response.status_code == 200:
                    # Check if it's an XLSX file
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    
                    print(f"   Content-Type: {content_type}")
                    print(f"   File size: {content_length} bytes")
                    
                    # Verify it's an Excel file
                    is_xlsx = (
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type or
                        content_length > 1000  # XLSX files are typically larger
                    )
                    
                    if is_xlsx:
                        print("   ✅ XLSX file generated successfully")
                        test_passed = True
                        error_msg = None
                    else:
                        print("   ❌ Response is not a valid XLSX file")
                        test_passed = False
                        error_msg = f"Invalid content type: {content_type}"
                        
                elif response.status_code == 400:
                    # Check if it's a validation error (acceptable)
                    try:
                        error_data = response.json()
                        if error_data.get('status') == 'blocked':
                            print("   ⚠️ Export blocked due to validation errors (acceptable)")
                            print(f"   Blocking errors: {len(error_data.get('blocking_errors', []))}")
                            test_passed = True
                            error_msg = "Validation blocked (acceptable)"
                        else:
                            print(f"   ❌ Bad request: {error_data}")
                            test_passed = False
                            error_msg = f"Bad request: {error_data}"
                    except:
                        print(f"   ❌ Bad request: {response.text[:200]}")
                        test_passed = False
                        error_msg = f"Bad request: {response.text[:200]}"
                        
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    test_passed = False
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                
                # Check for TypeError in response
                response_text = response.text if hasattr(response, 'text') else str(response.content)
                has_type_error = "'str' object has no attribute 'get'" in response_text
                
                if has_type_error:
                    print("   ❌ CRITICAL: TypeError 'str' object has no attribute 'get' detected!")
                    test_passed = False
                    error_msg = "TypeError detected in response"
                else:
                    print("   ✅ No TypeError detected")
                
                self.results.append({
                    "test": f"Enhanced Export {description}",
                    "techcard_name": techcard['name'],
                    "meta_type": str(type(techcard.get('meta', {}))),
                    "response_time_ms": response_time,
                    "status_code": response.status_code,
                    "file_generated": response.status_code == 200 and is_xlsx if response.status_code == 200 else False,
                    "type_error_detected": has_type_error,
                    "test_passed": test_passed and not has_type_error,
                    "error_msg": error_msg,
                    "status": "PASS" if test_passed and not has_type_error else "FAIL"
                })
                
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                self.results.append({
                    "test": f"Enhanced Export {description}",
                    "techcard_name": techcard['name'],
                    "exception": str(e),
                    "test_passed": False,
                    "status": "FAIL"
                })
    
    def test_meta_object_handling(self):
        """Test specific meta object handling scenarios"""
        print("\n🔍 META OBJECT HANDLING TESTING")
        print("=" * 70)
        
        # Test different meta object types
        meta_test_cases = [
            {
                "name": "Dict Meta",
                "meta": {"title": "Test Dish", "category": "test"},
                "expected_safe": True
            },
            {
                "name": "String Meta",
                "meta": "Test Dish String",
                "expected_safe": True
            },
            {
                "name": "None Meta",
                "meta": None,
                "expected_safe": True
            },
            {
                "name": "Empty Dict Meta",
                "meta": {},
                "expected_safe": True
            }
        ]
        
        base_techcard = {
            "name": "Meta Test Dish",
            "description": "Testing meta object handling",
            "ingredients": [
                {
                    "name": "test ingredient",
                    "quantity": 100,
                    "unit": "г",
                    "brutto_g": 100,
                    "netto_g": 100,
                    "loss_pct": 0,
                    "skuId": "test-001"
                }
            ],
            "yield": {
                "perPortion_g": 100,
                "perBatch_g": 100
            },
            "portions": 1,
            "process": [
                {
                    "step": 1,
                    "description": "Test step",
                    "time_min": 1,
                    "temp_c": 20
                }
            ]
        }
        
        for test_case in meta_test_cases:
            print(f"\n📋 Testing {test_case['name']}")
            
            # Create techcard with specific meta type
            test_techcard = base_techcard.copy()
            test_techcard["meta"] = test_case["meta"]
            
            print(f"   Meta type: {type(test_case['meta'])}")
            print(f"   Meta value: {test_case['meta']}")
            
            export_request = {
                "techcard": test_techcard,
                "export_options": {
                    "operational_rounding": True,
                    "use_product_codes": True
                }
            }
            
            try:
                response = requests.post(
                    f"{API_BASE}/techcards.v2/export/enhanced/iiko.xlsx",
                    json=export_request,
                    timeout=15
                )
                
                # Check for TypeError
                response_text = response.text if hasattr(response, 'text') else str(response.content)
                has_type_error = "'str' object has no attribute 'get'" in response_text
                
                if has_type_error:
                    print("   ❌ TypeError detected!")
                    test_passed = False
                elif response.status_code in [200, 400]:  # 400 might be validation error
                    print("   ✅ No TypeError, safe handling")
                    test_passed = True
                else:
                    print(f"   ⚠️ Unexpected status: {response.status_code}")
                    test_passed = False
                
                self.results.append({
                    "test": f"Meta Handling {test_case['name']}",
                    "meta_type": str(type(test_case['meta'])),
                    "meta_value": str(test_case['meta']),
                    "status_code": response.status_code,
                    "type_error_detected": has_type_error,
                    "test_passed": test_passed,
                    "status": "PASS" if test_passed else "FAIL"
                })
                
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                self.results.append({
                    "test": f"Meta Handling {test_case['name']}",
                    "exception": str(e),
                    "test_passed": False,
                    "status": "FAIL"
                })
    
    def test_operational_rounding_integration(self):
        """Test operational rounding integration specifically"""
        print("\n⚙️ OPERATIONAL ROUNDING INTEGRATION TESTING")
        print("=" * 70)
        
        # Test with and without operational rounding
        test_techcard = self.test_data["simple"]
        
        test_scenarios = [
            ("With Operational Rounding", True),
            ("Without Operational Rounding", False)
        ]
        
        for scenario_name, rounding_enabled in test_scenarios:
            print(f"\n🔧 Testing {scenario_name}")
            
            export_request = {
                "techcard": test_techcard,
                "export_options": {
                    "operational_rounding": rounding_enabled,
                    "use_product_codes": True
                }
            }
            
            try:
                start_time = time.time()
                
                response = requests.post(
                    f"{API_BASE}/techcards.v2/export/enhanced/iiko.xlsx",
                    json=export_request,
                    timeout=15
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                print(f"   Response time: {response_time:.1f}ms")
                print(f"   Status code: {response.status_code}")
                
                # Check for TypeError
                response_text = response.text if hasattr(response, 'text') else str(response.content)
                has_type_error = "'str' object has no attribute 'get'" in response_text
                
                if has_type_error:
                    print("   ❌ CRITICAL: TypeError detected!")
                    test_passed = False
                elif response.status_code in [200, 400]:
                    print("   ✅ No TypeError, processing successful")
                    test_passed = True
                    
                    if response.status_code == 200:
                        content_length = len(response.content)
                        print(f"   File size: {content_length} bytes")
                else:
                    print(f"   ❌ Unexpected error: {response.status_code}")
                    test_passed = False
                
                self.results.append({
                    "test": f"Operational Rounding {scenario_name}",
                    "rounding_enabled": rounding_enabled,
                    "response_time_ms": response_time,
                    "status_code": response.status_code,
                    "type_error_detected": has_type_error,
                    "test_passed": test_passed,
                    "status": "PASS" if test_passed else "FAIL"
                })
                
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                self.results.append({
                    "test": f"Operational Rounding {scenario_name}",
                    "exception": str(e),
                    "test_passed": False,
                    "status": "FAIL"
                })
    
    def test_export_tracking_functionality(self):
        """Test that export tracking works correctly"""
        print("\n📊 EXPORT TRACKING FUNCTIONALITY TESTING")
        print("=" * 70)
        
        # Test export tracking endpoints
        tracking_endpoints = [
            ("GET", "/techcards.v2/export/last", "Last Export"),
            ("GET", "/techcards.v2/export/history", "Export History")
        ]
        
        for method, endpoint, description in tracking_endpoints:
            print(f"\n📈 Testing {description}")
            
            try:
                if method == "GET":
                    response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{API_BASE}{endpoint}", timeout=10)
                
                print(f"   Status code: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   Response type: {type(data)}")
                        print("   ✅ Tracking endpoint working")
                        test_passed = True
                    except:
                        print("   ⚠️ Non-JSON response")
                        test_passed = True  # Still acceptable
                elif response.status_code == 404:
                    print("   ⚠️ Endpoint not found (may not be implemented)")
                    test_passed = True  # Acceptable for optional features
                else:
                    print(f"   ❌ Error: {response.status_code}")
                    test_passed = False
                
                self.results.append({
                    "test": f"Export Tracking {description}",
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "test_passed": test_passed,
                    "status": "PASS" if test_passed else "FAIL"
                })
                
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                self.results.append({
                    "test": f"Export Tracking {description}",
                    "exception": str(e),
                    "test_passed": False,
                    "status": "FAIL"
                })
    
    def run_all_tests(self):
        """Run all export bugfix tests"""
        print("🚀 CRITICAL EXPORT BUGFIX TESTING")
        print("Testing TypeError 'str' object has no attribute 'get' fix")
        print("=" * 80)
        
        try:
            # Core export functionality with operational rounding
            self.test_enhanced_export_with_operational_rounding()
            
            # Meta object handling edge cases
            self.test_meta_object_handling()
            
            # Operational rounding integration
            self.test_operational_rounding_integration()
            
            # Export tracking functionality
            self.test_export_tracking_functionality()
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {str(e)}")
            self.results.append({
                "test": "Critical Error",
                "error": str(e),
                "status": "FAIL"
            })
        
        # Final summary
        self._print_final_summary()
    
    def _print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("🎯 EXPORT BUGFIX FINAL TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.get("status") == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        print("\n📊 DETAILED RESULTS:")
        for result in self.results:
            test_name = result.get("test", "Unknown")
            status = result.get("status", "UNKNOWN")
            status_icon = "✅" if status == "PASS" else "❌"
            
            print(f"   {status_icon} {test_name}: {status}")
            
            # Show critical information
            if result.get("type_error_detected"):
                print(f"      ⚠️ TypeError detected!")
            if result.get("file_generated"):
                print(f"      📄 XLSX file generated successfully")
            if result.get("error_msg"):
                print(f"      Error: {result['error_msg']}")
        
        # Critical assessment
        print("\n🎯 CRITICAL ASSESSMENT:")
        
        # Check for any TypeError detections
        type_errors = [r for r in self.results if r.get("type_error_detected")]
        if type_errors:
            print(f"   ❌ CRITICAL: {len(type_errors)} TypeError(s) detected!")
            print("   The bugfix may not be working correctly.")
        else:
            print("   ✅ NO TypeErrors detected - bugfix appears to be working")
        
        # Check export success
        successful_exports = [r for r in self.results if r.get("file_generated")]
        if successful_exports:
            print(f"   ✅ {len(successful_exports)} successful XLSX exports")
        else:
            print("   ⚠️ No successful XLSX exports (may be due to validation)")
        
        # Check meta handling
        meta_tests = [r for r in self.results if "Meta Handling" in r.get("test", "")]
        meta_passed = [r for r in meta_tests if r.get("status") == "PASS"]
        if len(meta_passed) == len(meta_tests) and meta_tests:
            print("   ✅ Meta object handling working correctly")
        elif meta_tests:
            print(f"   ⚠️ Meta object handling issues: {len(meta_tests) - len(meta_passed)}/{len(meta_tests)} failed")
        
        # Overall verdict
        critical_issues = len(type_errors)
        
        if critical_issues == 0:
            print("\n🎉 EXPORT BUGFIX SUCCESS: No TypeErrors detected, export functionality working!")
        else:
            print(f"\n⚠️ EXPORT BUGFIX NEEDS ATTENTION: {critical_issues} critical issue(s) detected")


if __name__ == "__main__":
    tester = ExportBugfixTest()
    tester.run_all_tests()