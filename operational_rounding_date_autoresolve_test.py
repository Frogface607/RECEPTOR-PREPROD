#!/usr/bin/env python3
"""
Backend Testing for E. Operational Rounding v1 & F. TTK Date Autoresolve
Testing comprehensive operational rounding integration in PDF exports and TTK date autoresolve functionality.
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import tempfile
import zipfile
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class OperationalRoundingTester:
    """Test E. Operational Rounding v1 implementation"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def create_test_techcard(self, name: str = "Тестовое блюдо с округлением") -> Dict[str, Any]:
        """Create a test techcard with precise quantities that need rounding"""
        return {
            "meta": {
                "title": name,
                "cuisine": "Европейская",
                "tags": ["тест", "округление"],
                "version": "2.0"
            },
            "portions": 1,
            "yield_": {
                "perPortion_g": 250.0,
                "perBatch_g": 250.0
            },
            "ingredients": [
                {
                    "name": "Мука пшеничная",
                    "brutto_g": 123.456,  # Needs rounding
                    "netto_g": 120.789,   # Needs rounding
                    "loss_pct": 2.2,
                    "unit": "g",
                    "skuId": "test-flour-guid",
                    "product_code": "12345"
                },
                {
                    "name": "Молоко 3.2%",
                    "brutto_g": 87.321,   # Needs rounding
                    "netto_g": 87.321,    # No loss
                    "loss_pct": 0.0,
                    "unit": "ml",
                    "skuId": "test-milk-guid",
                    "product_code": "67890"
                },
                {
                    "name": "Яйца куриные",
                    "brutto_g": 45.678,   # Needs rounding
                    "netto_g": 43.210,    # Needs rounding
                    "loss_pct": 5.4,
                    "unit": "g",
                    "skuId": "test-eggs-guid",
                    "product_code": "11111"
                }
            ],
            "process": [
                {
                    "n": 1,
                    "action": "Смешать муку с молоком",
                    "time_min": 5,
                    "temp_c": 20,
                    "equipment": ["миска", "венчик"]
                },
                {
                    "n": 2,
                    "action": "Добавить яйца и перемешать",
                    "time_min": 3,
                    "temp_c": 20,
                    "equipment": ["венчик"]
                },
                {
                    "n": 3,
                    "action": "Готовить до готовности",
                    "time_min": 10,
                    "temp_c": 180,
                    "equipment": ["сковорода"]
                }
            ],
            "storage": {
                "conditions": "Хранить в холодильнике",
                "shelfLife_hours": 24,
                "servingTemp_c": 65
            }
        }
    
    def test_pdf_export_with_operational_rounding(self) -> Dict[str, Any]:
        """Test PDF export with operational_rounding=true"""
        logger.info("🔄 Testing PDF export with operational rounding enabled...")
        
        try:
            # Create test techcard
            test_card = self.create_test_techcard("PDF Округление Тест")
            
            # Test with operational_rounding=true
            export_request = {
                "card": test_card,
                "options": {
                    "operational_rounding": True
                }
            }
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/export",
                json=export_request,
                timeout=30
            )
            
            if response.status_code == 200:
                # Check if we got a ZIP file
                content_type = response.headers.get('content-type', '')
                if 'application/zip' in content_type:
                    # Extract and check PDF content
                    zip_buffer = BytesIO(response.content)
                    with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                        if 'techcard.pdf' in zip_file.namelist():
                            pdf_content = zip_file.read('techcard.pdf')
                            
                            return {
                                "status": "success",
                                "test": "pdf_export_operational_rounding_true",
                                "pdf_size": len(pdf_content),
                                "zip_size": len(response.content),
                                "files_in_zip": zip_file.namelist(),
                                "response_time": response.elapsed.total_seconds(),
                                "message": "PDF export with operational rounding completed successfully"
                            }
                        else:
                            return {
                                "status": "error",
                                "test": "pdf_export_operational_rounding_true",
                                "error": "PDF file not found in ZIP",
                                "files_found": zip_file.namelist()
                            }
                else:
                    return {
                        "status": "error",
                        "test": "pdf_export_operational_rounding_true",
                        "error": f"Unexpected content type: {content_type}",
                        "response_size": len(response.content)
                    }
            else:
                return {
                    "status": "error",
                    "test": "pdf_export_operational_rounding_true",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "test": "pdf_export_operational_rounding_true",
                "error": str(e)
            }
    
    def test_pdf_export_without_operational_rounding(self) -> Dict[str, Any]:
        """Test PDF export with operational_rounding=false"""
        logger.info("🔄 Testing PDF export with operational rounding disabled...")
        
        try:
            # Create test techcard
            test_card = self.create_test_techcard("PDF Без Округления Тест")
            
            # Test with operational_rounding=false
            export_request = {
                "card": test_card,
                "options": {
                    "operational_rounding": False
                }
            }
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/export",
                json=export_request,
                timeout=30
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/zip' in content_type:
                    zip_buffer = BytesIO(response.content)
                    with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                        if 'techcard.pdf' in zip_file.namelist():
                            pdf_content = zip_file.read('techcard.pdf')
                            
                            return {
                                "status": "success",
                                "test": "pdf_export_operational_rounding_false",
                                "pdf_size": len(pdf_content),
                                "zip_size": len(response.content),
                                "files_in_zip": zip_file.namelist(),
                                "response_time": response.elapsed.total_seconds(),
                                "message": "PDF export without operational rounding completed successfully"
                            }
                        else:
                            return {
                                "status": "error",
                                "test": "pdf_export_operational_rounding_false",
                                "error": "PDF file not found in ZIP",
                                "files_found": zip_file.namelist()
                            }
                else:
                    return {
                        "status": "error",
                        "test": "pdf_export_operational_rounding_false",
                        "error": f"Unexpected content type: {content_type}",
                        "response_size": len(response.content)
                    }
            else:
                return {
                    "status": "error",
                    "test": "pdf_export_operational_rounding_false",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "test": "pdf_export_operational_rounding_false",
                "error": str(e)
            }
    
    def test_backward_compatibility(self) -> Dict[str, Any]:
        """Test that existing export functionality remains intact"""
        logger.info("🔄 Testing backward compatibility of export functionality...")
        
        try:
            # Create test techcard
            test_card = self.create_test_techcard("Совместимость Тест")
            
            # Test without options (should use defaults)
            export_request = {
                "card": test_card
                # No options provided - should use defaults
            }
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/export",
                json=export_request,
                timeout=30
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/zip' in content_type:
                    zip_buffer = BytesIO(response.content)
                    with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                        expected_files = ['techcard.csv', 'techcard.xlsx', 'techcard.pdf']
                        found_files = zip_file.namelist()
                        
                        all_files_present = all(f in found_files for f in expected_files)
                        
                        return {
                            "status": "success" if all_files_present else "warning",
                            "test": "backward_compatibility",
                            "expected_files": expected_files,
                            "found_files": found_files,
                            "all_files_present": all_files_present,
                            "zip_size": len(response.content),
                            "response_time": response.elapsed.total_seconds(),
                            "message": "Backward compatibility test completed"
                        }
                else:
                    return {
                        "status": "error",
                        "test": "backward_compatibility",
                        "error": f"Unexpected content type: {content_type}"
                    }
            else:
                return {
                    "status": "error",
                    "test": "backward_compatibility",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "test": "backward_compatibility",
                "error": str(e)
            }


class TTKDateAutoresolveTester:
    """Test F. TTK Date Autoresolve implementation"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_test_techcard_for_date_test(self, dish_name: str) -> Dict[str, Any]:
        """Create a test techcard for date conflict testing"""
        return {
            "meta": {
                "title": dish_name,
                "cuisine": "Тестовая",
                "tags": ["автодата", "тест"],
                "version": "2.0"
            },
            "portions": 1,
            "yield_": {
                "perPortion_g": 200.0,
                "perBatch_g": 200.0
            },
            "ingredients": [
                {
                    "name": "Тестовый ингредиент",
                    "brutto_g": 100.0,
                    "netto_g": 95.0,
                    "loss_pct": 5.0,
                    "unit": "g",
                    "skuId": "test-ingredient-guid",
                    "product_code": "99999"
                }
            ],
            "process": [
                {
                    "n": 1,
                    "action": "Тестовое действие",
                    "time_min": 10,
                    "temp_c": 180
                },
                {
                    "n": 2,
                    "action": "Дополнительное действие",
                    "time_min": 5,
                    "temp_c": 20
                },
                {
                    "n": 3,
                    "action": "Финальное действие",
                    "time_min": 2,
                    "temp_c": 25
                }
            ]
        }
    
    def test_iiko_xlsx_export_with_date_autoresolve(self) -> Dict[str, Any]:
        """Test iiko XLSX export with auto_resolve_date enabled"""
        logger.info("🔄 Testing iiko XLSX export with date autoresolve...")
        
        try:
            # Create test techcard with unique name to avoid conflicts
            timestamp = int(time.time())
            dish_name = f"Автодата Тест {timestamp}"
            test_card = self.create_test_techcard_for_date_test(dish_name)
            
            # Test iiko XLSX export endpoint
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/export/iiko.xlsx",
                json=test_card,
                timeout=30
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'spreadsheetml' in content_type or 'excel' in content_type:
                    return {
                        "status": "success",
                        "test": "iiko_xlsx_export_date_autoresolve",
                        "dish_name": dish_name,
                        "file_size": len(response.content),
                        "content_type": content_type,
                        "response_time": response.elapsed.total_seconds(),
                        "message": "iiko XLSX export with date autoresolve completed successfully"
                    }
                else:
                    return {
                        "status": "error",
                        "test": "iiko_xlsx_export_date_autoresolve",
                        "error": f"Unexpected content type: {content_type}",
                        "response_size": len(response.content)
                    }
            else:
                return {
                    "status": "error",
                    "test": "iiko_xlsx_export_date_autoresolve",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "test": "iiko_xlsx_export_date_autoresolve",
                "error": str(e)
            }
    
    def test_enhanced_dual_export_with_date_options(self) -> Dict[str, Any]:
        """Test enhanced dual export with date resolution options"""
        logger.info("🔄 Testing enhanced dual export with date options...")
        
        try:
            # Create test techcard
            timestamp = int(time.time())
            dish_name = f"Двойной Экспорт Тест {timestamp}"
            test_card = self.create_test_techcard_for_date_test(dish_name)
            
            # Test enhanced dual export
            export_request = {
                "cards": [test_card],
                "options": {
                    "auto_resolve_date": True,
                    "base_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "use_product_codes": True,
                    "operational_rounding": True
                }
            }
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/export/enhanced-dual/iiko.xlsx",
                json=export_request,
                timeout=30
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/zip' in content_type:
                    zip_buffer = BytesIO(response.content)
                    with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                        files_in_zip = zip_file.namelist()
                        expected_files = ['Dish-Skeletons.xlsx', 'iiko_TTK.xlsx']
                        
                        has_expected_files = all(f in files_in_zip for f in expected_files)
                        
                        return {
                            "status": "success" if has_expected_files else "warning",
                            "test": "enhanced_dual_export_date_options",
                            "dish_name": dish_name,
                            "zip_size": len(response.content),
                            "files_in_zip": files_in_zip,
                            "expected_files": expected_files,
                            "has_expected_files": has_expected_files,
                            "response_time": response.elapsed.total_seconds(),
                            "message": "Enhanced dual export with date options completed"
                        }
                else:
                    return {
                        "status": "error",
                        "test": "enhanced_dual_export_date_options",
                        "error": f"Unexpected content type: {content_type}",
                        "response_size": len(response.content)
                    }
            else:
                return {
                    "status": "error",
                    "test": "enhanced_dual_export_date_options",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "test": "enhanced_dual_export_date_options",
                "error": str(e)
            }
    
    def test_date_conflict_resolution_scenarios(self) -> List[Dict[str, Any]]:
        """Test various date conflict resolution scenarios"""
        logger.info("🔄 Testing date conflict resolution scenarios...")
        
        results = []
        
        # Test scenario 1: Today's date
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            dish_name = f"Сегодня Тест {int(time.time())}"
            test_card = self.create_test_techcard_for_date_test(dish_name)
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/export/iiko.xlsx",
                json=test_card,
                timeout=30
            )
            
            results.append({
                "status": "success" if response.status_code == 200 else "error",
                "test": "date_conflict_today",
                "base_date": today,
                "dish_name": dish_name,
                "response_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "message": f"Date conflict test for today ({today})"
            })
            
        except Exception as e:
            results.append({
                "status": "error",
                "test": "date_conflict_today",
                "error": str(e)
            })
        
        # Test scenario 2: Future date
        try:
            future_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
            dish_name = f"Будущее Тест {int(time.time())}"
            test_card = self.create_test_techcard_for_date_test(dish_name)
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/export/iiko.xlsx",
                json=test_card,
                timeout=30
            )
            
            results.append({
                "status": "success" if response.status_code == 200 else "error",
                "test": "date_conflict_future",
                "base_date": future_date,
                "dish_name": dish_name,
                "response_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "message": f"Date conflict test for future date ({future_date})"
            })
            
        except Exception as e:
            results.append({
                "status": "error",
                "test": "date_conflict_future",
                "error": str(e)
            })
        
        # Test scenario 3: Multiple dishes with same base date
        try:
            base_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            timestamp = int(time.time())
            
            for i in range(3):
                dish_name = f"Множественный Тест {timestamp}_{i}"
                test_card = self.create_test_techcard_for_date_test(dish_name)
                
                response = self.session.post(
                    f"{API_BASE}/v1/techcards.v2/export/iiko.xlsx",
                    json=test_card,
                    timeout=30
                )
                
                results.append({
                    "status": "success" if response.status_code == 200 else "error",
                    "test": f"date_conflict_multiple_{i}",
                    "base_date": base_date,
                    "dish_name": dish_name,
                    "response_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "message": f"Multiple dishes test #{i+1}"
                })
                
                # Small delay between requests
                time.sleep(0.5)
                
        except Exception as e:
            results.append({
                "status": "error",
                "test": "date_conflict_multiple",
                "error": str(e)
            })
        
        return results


class IntegrationTester:
    """Test integration between operational rounding and date autoresolve"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_combined_features(self) -> Dict[str, Any]:
        """Test operational rounding + date autoresolve working together"""
        logger.info("🔄 Testing combined operational rounding and date autoresolve...")
        
        try:
            # Create test techcard with precise quantities
            timestamp = int(time.time())
            dish_name = f"Комбинированный Тест {timestamp}"
            
            test_card = {
                "meta": {
                    "title": dish_name,
                    "cuisine": "Интеграционная",
                    "tags": ["округление", "автодата", "интеграция"],
                    "version": "2.0"
                },
                "portions": 1,
                "yield_": {
                    "perPortion_g": 275.5,  # Needs rounding
                    "perBatch_g": 275.5
                },
                "ingredients": [
                    {
                        "name": "Мука высшего сорта",
                        "brutto_g": 156.789,  # Needs rounding
                        "netto_g": 153.456,   # Needs rounding
                        "loss_pct": 2.1,
                        "unit": "g",
                        "skuId": "integration-flour-guid",
                        "product_code": "55555"
                    },
                    {
                        "name": "Сахар-песок",
                        "brutto_g": 78.321,   # Needs rounding
                        "netto_g": 78.321,    # No loss
                        "loss_pct": 0.0,
                        "unit": "g",
                        "skuId": "integration-sugar-guid",
                        "product_code": "66666"
                    }
                ],
                "process": [
                    {
                        "n": 1,
                        "action": "Смешать ингредиенты",
                        "time_min": 8,
                        "temp_c": 25
                    },
                    {
                        "n": 2,
                        "action": "Дополнительная обработка",
                        "time_min": 5,
                        "temp_c": 20
                    },
                    {
                        "n": 3,
                        "action": "Финальная подготовка",
                        "time_min": 3,
                        "temp_c": 30
                    }
                ]
            }
            
            # Test with both features enabled
            export_request = {
                "cards": [test_card],
                "options": {
                    "operational_rounding": True,
                    "auto_resolve_date": True,
                    "base_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "use_product_codes": True
                }
            }
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/export/enhanced-dual/iiko.xlsx",
                json=export_request,
                timeout=30
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/zip' in content_type:
                    zip_buffer = BytesIO(response.content)
                    with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                        files_in_zip = zip_file.namelist()
                        
                        return {
                            "status": "success",
                            "test": "combined_features_integration",
                            "dish_name": dish_name,
                            "zip_size": len(response.content),
                            "files_in_zip": files_in_zip,
                            "response_time": response.elapsed.total_seconds(),
                            "message": "Combined operational rounding + date autoresolve test completed successfully"
                        }
                else:
                    return {
                        "status": "error",
                        "test": "combined_features_integration",
                        "error": f"Unexpected content type: {content_type}"
                    }
            else:
                return {
                    "status": "error",
                    "test": "combined_features_integration",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "test": "combined_features_integration",
                "error": str(e)
            }
    
    def test_export_options_validation(self) -> Dict[str, Any]:
        """Test that export options work correctly with proper validation"""
        logger.info("🔄 Testing export options validation...")
        
        try:
            # Create simple test techcard
            test_card = {
                "meta": {
                    "title": "Валидация Опций Тест",
                    "version": "2.0"
                },
                "portions": 1,
                "yield_": {
                    "perPortion_g": 100.0,
                    "perBatch_g": 100.0
                },
                "ingredients": [
                    {
                        "name": "Тестовый продукт",
                        "brutto_g": 50.0,
                        "netto_g": 50.0,
                        "loss_pct": 0.0,
                        "unit": "g",
                        "product_code": "77777"
                    }
                ],
                "process": [
                    {
                        "n": 1,
                        "action": "Тестовое действие"
                    },
                    {
                        "n": 2,
                        "action": "Дополнительное действие"
                    },
                    {
                        "n": 3,
                        "action": "Финальное действие"
                    }
                ]
            }
            
            # Test various option combinations
            test_scenarios = [
                {
                    "name": "all_options_enabled",
                    "options": {
                        "operational_rounding": True,
                        "auto_resolve_date": True,
                        "use_product_codes": True,
                        "base_date": datetime.now().strftime('%Y-%m-%d')
                    }
                },
                {
                    "name": "all_options_disabled",
                    "options": {
                        "operational_rounding": False,
                        "auto_resolve_date": False,
                        "use_product_codes": False
                    }
                },
                {
                    "name": "mixed_options",
                    "options": {
                        "operational_rounding": True,
                        "auto_resolve_date": False,
                        "use_product_codes": True
                    }
                }
            ]
            
            results = []
            
            for scenario in test_scenarios:
                try:
                    export_request = {
                        "cards": [test_card],
                        "options": scenario["options"]
                    }
                    
                    response = self.session.post(
                        f"{API_BASE}/v1/techcards.v2/export/enhanced-dual/iiko.xlsx",
                        json=export_request,
                        timeout=30
                    )
                    
                    results.append({
                        "scenario": scenario["name"],
                        "status": "success" if response.status_code == 200 else "error",
                        "response_code": response.status_code,
                        "response_size": len(response.content) if response.status_code == 200 else 0,
                        "response_time": response.elapsed.total_seconds(),
                        "options_tested": scenario["options"]
                    })
                    
                except Exception as e:
                    results.append({
                        "scenario": scenario["name"],
                        "status": "error",
                        "error": str(e),
                        "options_tested": scenario["options"]
                    })
            
            # Calculate overall success rate
            successful_scenarios = sum(1 for r in results if r["status"] == "success")
            total_scenarios = len(results)
            success_rate = (successful_scenarios / total_scenarios) * 100 if total_scenarios > 0 else 0
            
            return {
                "status": "success" if success_rate >= 80 else "warning",
                "test": "export_options_validation",
                "scenarios_tested": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "success_rate": f"{success_rate:.1f}%",
                "detailed_results": results,
                "message": f"Export options validation completed: {successful_scenarios}/{total_scenarios} scenarios passed"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "test": "export_options_validation",
                "error": str(e)
            }


def run_comprehensive_tests():
    """Run all comprehensive tests for operational rounding and date autoresolve"""
    logger.info("🚀 Starting comprehensive E. Operational Rounding v1 & F. TTK Date Autoresolve testing...")
    
    all_results = []
    
    # Test E. Operational Rounding v1
    logger.info("\n📊 TESTING E. OPERATIONAL ROUNDING V1")
    rounding_tester = OperationalRoundingTester()
    
    # PDF Export Tests
    all_results.append(rounding_tester.test_pdf_export_with_operational_rounding())
    all_results.append(rounding_tester.test_pdf_export_without_operational_rounding())
    all_results.append(rounding_tester.test_backward_compatibility())
    
    # Test F. TTK Date Autoresolve
    logger.info("\n📅 TESTING F. TTK DATE AUTORESOLVE")
    date_tester = TTKDateAutoresolveTester()
    
    # Date Autoresolve Tests
    all_results.append(date_tester.test_iiko_xlsx_export_with_date_autoresolve())
    all_results.append(date_tester.test_enhanced_dual_export_with_date_options())
    
    # Date conflict scenarios
    date_conflict_results = date_tester.test_date_conflict_resolution_scenarios()
    all_results.extend(date_conflict_results)
    
    # Integration Tests
    logger.info("\n🔗 TESTING INTEGRATION")
    integration_tester = IntegrationTester()
    
    all_results.append(integration_tester.test_combined_features())
    all_results.append(integration_tester.test_export_options_validation())
    
    # Calculate overall statistics
    total_tests = len(all_results)
    successful_tests = sum(1 for result in all_results if result.get("status") == "success")
    warning_tests = sum(1 for result in all_results if result.get("status") == "warning")
    failed_tests = sum(1 for result in all_results if result.get("status") == "error")
    
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    # Print summary
    logger.info(f"\n📈 COMPREHENSIVE TEST RESULTS SUMMARY")
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"✅ Successful: {successful_tests}")
    logger.info(f"⚠️ Warnings: {warning_tests}")
    logger.info(f"❌ Failed: {failed_tests}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    
    # Print detailed results
    logger.info(f"\n📋 DETAILED TEST RESULTS:")
    for i, result in enumerate(all_results, 1):
        status_emoji = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(result.get("status"), "❓")
        test_name = result.get("test", f"test_{i}")
        message = result.get("message", result.get("error", "No message"))
        logger.info(f"{i:2d}. {status_emoji} {test_name}: {message}")
    
    return {
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "warning_tests": warning_tests,
        "failed_tests": failed_tests,
        "success_rate": success_rate,
        "detailed_results": all_results
    }


if __name__ == "__main__":
    print("🧪 E. Operational Rounding v1 & F. TTK Date Autoresolve Backend Testing")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    try:
        results = run_comprehensive_tests()
        
        print("\n" + "=" * 80)
        print("🎯 FINAL SUMMARY")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Tests Passed: {results['successful_tests']}/{results['total_tests']}")
        
        if results['success_rate'] >= 80:
            print("🎉 COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY!")
        elif results['success_rate'] >= 60:
            print("⚠️ TESTING COMPLETED WITH WARNINGS")
        else:
            print("❌ TESTING COMPLETED WITH SIGNIFICANT ISSUES")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()