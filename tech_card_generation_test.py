#!/usr/bin/env python3
"""
Backend Testing: Tech Card Generation & Process Steps Validation
Testing the process steps validation fix to resolve critical error preventing tech card generation.

FOCUS AREAS:
1. Tech Card Generation: Test POST /api/v1/techcards.v2/generate endpoint with sample tech card request
2. Process Steps Validation: Verify that the improved quality_validator handles process steps correctly 
3. Enhanced Export: Test POST /api/v1/techcards.v2/export/enhanced/iiko.xlsx to ensure export works
4. Error Handling: Test that the safety checks work for malformed process data
5. Complete Workflow: Validate end-to-end tech card generation and validation

TEST SCENARIOS:
- Generate tech card with proper process steps (list of dictionaries)
- Test with malformed process steps (strings instead of objects) to verify error handling
- Validate that enhanced export works without the 'str' object has no attribute 'get' error
- Test complete tech card generation workflow from start to finish
- Verify that quality validator provides proper error messages for malformed data
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechCardGenerationTester:
    """Test suite for tech card generation and process steps validation"""
    
    def __init__(self):
        # Get backend URL from environment
        self.backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        if not self.backend_url.endswith('/api'):
            self.backend_url = f"{self.backend_url}/api"
        
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        logger.info(f"🔧 Backend URL: {self.backend_url}")
    
    def log_test_result(self, test_name: str, passed: bool, details: str = "", data: Any = None):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            logger.info(f"✅ {test_name}: PASSED - {details}")
        else:
            logger.error(f"❌ {test_name}: FAILED - {details}")
        
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    async def test_tech_card_generation_with_proper_process_steps(self):
        """Test 1: Tech card generation with proper process steps (list of dictionaries)"""
        logger.info("🔍 Testing tech card generation with proper process steps...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Sample tech card request with proper process steps
                sample_request = {
                    "name": "Салат Цезарь с курицей",
                    "description": "Классический салат Цезарь с куриным филе",
                    "category": "Салаты",
                    "portions": 1,
                    "ingredients": [
                        {
                            "name": "Куриное филе",
                            "quantity": 150,
                            "unit": "г"
                        },
                        {
                            "name": "Салат Романо",
                            "quantity": 100,
                            "unit": "г"
                        },
                        {
                            "name": "Пармезан",
                            "quantity": 30,
                            "unit": "г"
                        },
                        {
                            "name": "Гренки",
                            "quantity": 20,
                            "unit": "г"
                        },
                        {
                            "name": "Соус Цезарь",
                            "quantity": 50,
                            "unit": "мл"
                        }
                    ],
                    "process_steps": [
                        {
                            "n": 1,
                            "action": "Куриное филе отварить в подсоленной воде до готовности",
                            "time_min": 15,
                            "temp_c": 100
                        },
                        {
                            "n": 2,
                            "action": "Остудить курицу и нарезать кубиками",
                            "time_min": 5,
                            "temp_c": 20
                        },
                        {
                            "n": 3,
                            "action": "Салат Романо промыть и нарезать",
                            "time_min": 3,
                            "temp_c": 20
                        },
                        {
                            "n": 4,
                            "action": "Смешать все ингредиенты с соусом",
                            "time_min": 2,
                            "temp_c": 20
                        },
                        {
                            "n": 5,
                            "action": "Посыпать тертым пармезаном и гренками",
                            "time_min": 1,
                            "temp_c": 20
                        }
                    ]
                }
                
                response = await client.post(
                    f"{self.backend_url}/v1/techcards.v2/generate",
                    json=sample_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    card = data.get('card')
                    issues = data.get('issues', [])
                    
                    self.log_test_result(
                        "Tech Card Generation - Proper Process Steps",
                        status in ['success', 'draft'],
                        f"Status: {status}, Issues: {len(issues)}",
                        {
                            "status": status,
                            "has_card": card is not None,
                            "issues_count": len(issues),
                            "process_steps_count": len(card.get('process', {}).get('steps', [])) if card else 0
                        }
                    )
                    
                    # Validate that process steps are properly handled
                    if card and 'process' in card:
                        process_steps = card['process'].get('steps', [])
                        
                        # Check if process steps are list of dictionaries
                        all_steps_valid = all(isinstance(step, dict) for step in process_steps)
                        
                        self.log_test_result(
                            "Process Steps Format Validation",
                            all_steps_valid,
                            f"All {len(process_steps)} steps are dictionaries: {all_steps_valid}",
                            {"steps_count": len(process_steps), "all_valid": all_steps_valid}
                        )
                        
                        # Check for required fields in process steps
                        required_fields = ['n', 'action']
                        steps_with_required_fields = 0
                        
                        for step in process_steps:
                            if isinstance(step, dict) and all(field in step for field in required_fields):
                                steps_with_required_fields += 1
                        
                        self.log_test_result(
                            "Process Steps Required Fields",
                            steps_with_required_fields == len(process_steps),
                            f"{steps_with_required_fields}/{len(process_steps)} steps have required fields",
                            {"valid_steps": steps_with_required_fields, "total_steps": len(process_steps)}
                        )
                    
                    return card  # Return for use in other tests
                
                else:
                    self.log_test_result(
                        "Tech Card Generation - Proper Process Steps",
                        False,
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    return None
                
        except Exception as e:
            self.log_test_result(
                "Tech Card Generation - Proper Process Steps",
                False,
                f"Exception: {str(e)}"
            )
            return None
    
    async def test_tech_card_generation_with_malformed_process_steps(self):
        """Test 2: Tech card generation with malformed process steps to verify error handling"""
        logger.info("🔍 Testing tech card generation with malformed process steps...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Sample tech card request with malformed process steps (strings instead of objects)
                malformed_request = {
                    "name": "Тест с неправильными этапами",
                    "description": "Тест обработки ошибок",
                    "category": "Тест",
                    "portions": 1,
                    "ingredients": [
                        {
                            "name": "Тестовый ингредиент",
                            "quantity": 100,
                            "unit": "г"
                        }
                    ],
                    "process_steps": [
                        "Это строка вместо объекта",  # This should cause an error
                        "Еще одна строка",
                        {"n": 3, "action": "Правильный этап"}  # Mixed format
                    ]
                }
                
                response = await client.post(
                    f"{self.backend_url}/v1/techcards.v2/generate",
                    json=malformed_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    issues = data.get('issues', [])
                    
                    # Should handle malformed data gracefully
                    self.log_test_result(
                        "Tech Card Generation - Malformed Process Steps",
                        status in ['draft', 'error'],  # Should not be 'success' with malformed data
                        f"Status: {status}, Issues: {len(issues)}",
                        {
                            "status": status,
                            "issues_count": len(issues),
                            "issues": issues[:3]  # First 3 issues for debugging
                        }
                    )
                    
                    # Check if validation caught the malformed process steps
                    process_errors = [issue for issue in issues if 'process' in issue.get('field', '').lower()]
                    
                    self.log_test_result(
                        "Process Steps Error Detection",
                        len(process_errors) > 0,
                        f"Found {len(process_errors)} process-related validation errors",
                        {"process_errors": process_errors}
                    )
                
                else:
                    self.log_test_result(
                        "Tech Card Generation - Malformed Process Steps",
                        response.status_code in [400, 422],  # Should return validation error
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                
        except Exception as e:
            self.log_test_result(
                "Tech Card Generation - Malformed Process Steps",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_quality_validator_process_steps_handling(self):
        """Test 3: Quality validator process steps handling directly"""
        logger.info("🔍 Testing quality validator process steps handling...")
        
        try:
            # Test with proper process steps
            proper_techcard = {
                "meta": {"title": "Test Card"},
                "ingredients": [{"name": "Test", "brutto_g": 100, "netto_g": 90, "unit": "g"}],
                "yield": {"perPortion_g": 200, "perBatch_g": 200},
                "portions": 1,
                "process": {
                    "steps": [
                        {"n": 1, "action": "Step 1", "time_min": 5},
                        {"n": 2, "action": "Step 2", "time_min": 10},
                        {"n": 3, "action": "Step 3", "time_min": 15}
                    ]
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.backend_url}/v1/techcards.v2/validate/quality",
                    json={"techcard": proper_techcard}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    quality_score = data.get('quality_score', {})
                    issues = data.get('validation_issues', [])
                    
                    self.log_test_result(
                        "Quality Validator - Proper Process Steps",
                        data.get('status') == 'success',
                        f"Score: {quality_score.get('score', 0)}, Issues: {len(issues)}",
                        {
                            "quality_score": quality_score,
                            "issues_count": len(issues),
                            "process_issues": [i for i in issues if 'process' in i.get('field', '')]
                        }
                    )
                
                else:
                    self.log_test_result(
                        "Quality Validator - Proper Process Steps",
                        False,
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            
            # Test with malformed process steps
            malformed_techcard = {
                "meta": {"title": "Test Card"},
                "ingredients": [{"name": "Test", "brutto_g": 100, "netto_g": 90, "unit": "g"}],
                "yield": {"perPortion_g": 200, "perBatch_g": 200},
                "portions": 1,
                "process": [  # This should be an object with 'steps' key, not a list
                    "String step 1",
                    "String step 2"
                ]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.backend_url}/v1/techcards.v2/validate/quality",
                    json={"techcard": malformed_techcard}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('validation_issues', [])
                    process_issues = [i for i in issues if 'process' in i.get('field', '').lower()]
                    
                    self.log_test_result(
                        "Quality Validator - Malformed Process Steps",
                        len(process_issues) > 0,
                        f"Detected {len(process_issues)} process validation issues",
                        {"process_issues": process_issues}
                    )
                
                else:
                    self.log_test_result(
                        "Quality Validator - Malformed Process Steps",
                        response.status_code in [400, 422],
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                
        except Exception as e:
            self.log_test_result(
                "Quality Validator Process Steps Handling",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_enhanced_export_without_str_error(self):
        """Test 4: Enhanced export to ensure it works without 'str' object has no attribute 'get' error"""
        logger.info("🔍 Testing enhanced export without str error...")
        
        try:
            # Create a sample tech card for export
            sample_techcard = {
                "meta": {
                    "id": "test-export-001",
                    "title": "Тест экспорта",
                    "description": "Тест исправления ошибки экспорта"
                },
                "ingredients": [
                    {
                        "name": "Тестовый ингредиент 1",
                        "brutto_g": 110,
                        "netto_g": 100,
                        "loss_pct": 9.1,
                        "unit": "g",
                        "skuId": "test-guid-1",
                        "product_code": "12345"
                    },
                    {
                        "name": "Тестовый ингредиент 2",
                        "brutto_g": 55,
                        "netto_g": 50,
                        "loss_pct": 9.1,
                        "unit": "ml",
                        "skuId": "test-guid-2",
                        "product_code": "67890"
                    }
                ],
                "yield": {
                    "perPortion_g": 150,
                    "perBatch_g": 150
                },
                "portions": 1,
                "nutrition": {"per100g": {}, "perPortion": {}},
                "cost": {"per100g": {}, "perPortion": {}},
                "process": {
                    "steps": [
                        {"n": 1, "action": "Подготовить ингредиенты", "time_min": 5},
                        {"n": 2, "action": "Смешать компоненты", "time_min": 10},
                        {"n": 3, "action": "Подать к столу", "time_min": 2}
                    ]
                }
            }
            
            # Test different meta object scenarios that could cause the 'str' error
            test_scenarios = [
                {
                    "name": "Normal Meta Object",
                    "techcard": sample_techcard
                },
                {
                    "name": "String Meta (Edge Case)",
                    "techcard": {
                        **sample_techcard,
                        "meta": "string_meta_value"  # This could cause the 'str' error
                    }
                },
                {
                    "name": "Empty Meta Object",
                    "techcard": {
                        **sample_techcard,
                        "meta": {}
                    }
                },
                {
                    "name": "None Meta Object",
                    "techcard": {
                        **sample_techcard,
                        "meta": None
                    }
                }
            ]
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                for scenario in test_scenarios:
                    try:
                        response = await client.post(
                            f"{self.backend_url}/v1/techcards.v2/export/enhanced/iiko.xlsx",
                            json={
                                "techcard": scenario["techcard"],
                                "options": {
                                    "use_product_codes": True,
                                    "operational_rounding": True
                                },
                                "organization_id": "default",
                                "user_email": "test@example.com"
                            }
                        )
                        
                        if response.status_code == 200:
                            # Check if we got an Excel file
                            content_type = response.headers.get('content-type', '')
                            is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                            
                            self.log_test_result(
                                f"Enhanced Export - {scenario['name']}",
                                is_excel,
                                f"Export successful, Content-Type: {content_type}, Size: {len(response.content)} bytes",
                                {
                                    "content_type": content_type,
                                    "size": len(response.content),
                                    "scenario": scenario['name']
                                }
                            )
                        
                        elif response.status_code == 400:
                            # Validation errors are acceptable for malformed data
                            error_text = response.text
                            has_str_error = "'str' object has no attribute 'get'" in error_text
                            
                            self.log_test_result(
                                f"Enhanced Export - {scenario['name']}",
                                not has_str_error,  # Pass if no 'str' error
                                f"HTTP 400 (validation error): No 'str' error detected" if not has_str_error else "CRITICAL: 'str' error still present",
                                {
                                    "status_code": response.status_code,
                                    "has_str_error": has_str_error,
                                    "error_text": error_text[:200]
                                }
                            )
                        
                        else:
                            # Other errors
                            error_text = response.text
                            has_str_error = "'str' object has no attribute 'get'" in error_text
                            
                            self.log_test_result(
                                f"Enhanced Export - {scenario['name']}",
                                not has_str_error,  # Pass if no 'str' error
                                f"HTTP {response.status_code}: {'No str error' if not has_str_error else 'CRITICAL: str error present'}",
                                {
                                    "status_code": response.status_code,
                                    "has_str_error": has_str_error,
                                    "error_text": error_text[:200]
                                }
                            )
                    
                    except Exception as e:
                        # Check if the exception is the 'str' error
                        has_str_error = "'str' object has no attribute 'get'" in str(e)
                        
                        self.log_test_result(
                            f"Enhanced Export - {scenario['name']}",
                            not has_str_error,
                            f"Exception: {'No str error' if not has_str_error else 'CRITICAL: str error in exception'}",
                            {
                                "exception": str(e),
                                "has_str_error": has_str_error
                            }
                        )
                
        except Exception as e:
            self.log_test_result(
                "Enhanced Export Without Str Error",
                False,
                f"Test setup exception: {str(e)}"
            )
    
    async def test_complete_workflow_validation(self):
        """Test 5: Complete workflow from generation to export"""
        logger.info("🔍 Testing complete tech card workflow...")
        
        try:
            # Step 1: Generate a tech card
            generation_request = {
                "name": "Борщ украинский",
                "description": "Традиционный украинский борщ",
                "category": "Супы",
                "portions": 1,
                "ingredients": [
                    {"name": "Свекла", "quantity": 100, "unit": "г"},
                    {"name": "Капуста", "quantity": 80, "unit": "г"},
                    {"name": "Морковь", "quantity": 50, "unit": "г"},
                    {"name": "Лук репчатый", "quantity": 40, "unit": "г"},
                    {"name": "Говядина", "quantity": 120, "unit": "г"}
                ],
                "process_steps": [
                    {"n": 1, "action": "Подготовить овощи", "time_min": 10},
                    {"n": 2, "action": "Отварить мясо", "time_min": 60},
                    {"n": 3, "action": "Добавить овощи", "time_min": 20},
                    {"n": 4, "action": "Варить до готовности", "time_min": 30}
                ]
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Generate tech card
                gen_response = await client.post(
                    f"{self.backend_url}/v1/techcards.v2/generate",
                    json=generation_request
                )
                
                if gen_response.status_code == 200:
                    gen_data = gen_response.json()
                    generated_card = gen_data.get('card')
                    
                    self.log_test_result(
                        "Complete Workflow - Generation Step",
                        generated_card is not None,
                        f"Status: {gen_data.get('status')}, Card generated: {generated_card is not None}",
                        {"generation_status": gen_data.get('status')}
                    )
                    
                    if generated_card:
                        # Step 2: Validate quality
                        quality_response = await client.post(
                            f"{self.backend_url}/v1/techcards.v2/validate/quality",
                            json={"techcard": generated_card}
                        )
                        
                        if quality_response.status_code == 200:
                            quality_data = quality_response.json()
                            quality_score = quality_data.get('quality_score', {})
                            
                            self.log_test_result(
                                "Complete Workflow - Quality Validation",
                                quality_data.get('status') == 'success',
                                f"Quality score: {quality_score.get('score', 0)}, Production ready: {quality_score.get('is_production_ready', False)}",
                                {"quality_score": quality_score}
                            )
                            
                            # Step 3: Try export
                            export_response = await client.post(
                                f"{self.backend_url}/v1/techcards.v2/export/enhanced/iiko.xlsx",
                                json={
                                    "techcard": generated_card,
                                    "options": {
                                        "use_product_codes": False,  # Use GUIDs for this test
                                        "operational_rounding": False
                                    },
                                    "organization_id": "default",
                                    "user_email": "test@example.com"
                                }
                            )
                            
                            export_success = export_response.status_code == 200
                            if export_success:
                                content_type = export_response.headers.get('content-type', '')
                                is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                                export_success = is_excel
                            
                            self.log_test_result(
                                "Complete Workflow - Export Step",
                                export_success,
                                f"Export status: {export_response.status_code}, Is Excel: {is_excel if export_success else 'N/A'}",
                                {
                                    "export_status": export_response.status_code,
                                    "content_type": export_response.headers.get('content-type', ''),
                                    "size": len(export_response.content) if export_success else 0
                                }
                            )
                            
                            # Overall workflow success
                            workflow_success = (
                                generated_card is not None and
                                quality_data.get('status') == 'success' and
                                export_success
                            )
                            
                            self.log_test_result(
                                "Complete Workflow - End-to-End",
                                workflow_success,
                                f"Generation ✓, Quality ✓, Export ✓" if workflow_success else "Some steps failed",
                                {
                                    "generation_ok": generated_card is not None,
                                    "quality_ok": quality_data.get('status') == 'success',
                                    "export_ok": export_success
                                }
                            )
                        
                        else:
                            self.log_test_result(
                                "Complete Workflow - Quality Validation",
                                False,
                                f"Quality validation failed: HTTP {quality_response.status_code}"
                            )
                
                else:
                    self.log_test_result(
                        "Complete Workflow - Generation Step",
                        False,
                        f"Generation failed: HTTP {gen_response.status_code}"
                    )
                
        except Exception as e:
            self.log_test_result(
                "Complete Workflow Validation",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_error_handling_safety_checks(self):
        """Test 6: Error handling and safety checks for various edge cases"""
        logger.info("🔍 Testing error handling and safety checks...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test cases with various malformed data
                test_cases = [
                    {
                        "name": "Empty Request",
                        "data": {},
                        "expected_status": [400, 422]
                    },
                    {
                        "name": "Missing Ingredients",
                        "data": {
                            "name": "Test",
                            "description": "Test",
                            "process_steps": []
                        },
                        "expected_status": [200, 400, 422]  # May generate with warnings
                    },
                    {
                        "name": "Invalid Process Steps Type",
                        "data": {
                            "name": "Test",
                            "ingredients": [{"name": "Test", "quantity": 100, "unit": "g"}],
                            "process_steps": "not a list"
                        },
                        "expected_status": [200, 400, 422]  # Should handle gracefully
                    },
                    {
                        "name": "Mixed Process Steps Types",
                        "data": {
                            "name": "Test",
                            "ingredients": [{"name": "Test", "quantity": 100, "unit": "g"}],
                            "process_steps": [
                                {"n": 1, "action": "Valid step"},
                                "Invalid string step",
                                {"n": 3, "action": "Another valid step"}
                            ]
                        },
                        "expected_status": [200, 400, 422]  # Should handle gracefully
                    }
                ]
                
                for test_case in test_cases:
                    try:
                        response = await client.post(
                            f"{self.backend_url}/v1/techcards.v2/generate",
                            json=test_case["data"]
                        )
                        
                        status_ok = response.status_code in test_case["expected_status"]
                        
                        # Check for critical errors in response
                        response_text = response.text
                        has_critical_error = (
                            "AttributeError" in response_text or
                            "TypeError" in response_text or
                            "'str' object has no attribute" in response_text
                        )
                        
                        self.log_test_result(
                            f"Error Handling - {test_case['name']}",
                            status_ok and not has_critical_error,
                            f"HTTP {response.status_code} (expected {test_case['expected_status']}), No critical errors: {not has_critical_error}",
                            {
                                "status_code": response.status_code,
                                "expected_status": test_case["expected_status"],
                                "has_critical_error": has_critical_error,
                                "response_preview": response_text[:200]
                            }
                        )
                    
                    except Exception as e:
                        # Check if exception contains critical errors
                        has_critical_error = (
                            "AttributeError" in str(e) or
                            "TypeError" in str(e) or
                            "'str' object has no attribute" in str(e)
                        )
                        
                        self.log_test_result(
                            f"Error Handling - {test_case['name']}",
                            not has_critical_error,
                            f"Exception handled gracefully: {not has_critical_error}",
                            {
                                "exception": str(e),
                                "has_critical_error": has_critical_error
                            }
                        )
                
        except Exception as e:
            self.log_test_result(
                "Error Handling Safety Checks",
                False,
                f"Test setup exception: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Run all tech card generation tests"""
        logger.info("🚀 Starting Tech Card Generation Testing Suite...")
        start_time = time.time()
        
        # Run all test methods
        test_methods = [
            self.test_tech_card_generation_with_proper_process_steps,
            self.test_tech_card_generation_with_malformed_process_steps,
            self.test_quality_validator_process_steps_handling,
            self.test_enhanced_export_without_str_error,
            self.test_complete_workflow_validation,
            self.test_error_handling_safety_checks
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} failed: {e}")
                self.log_test_result(
                    test_method.__name__,
                    False,
                    f"Test method exception: {str(e)}"
                )
        
        # Calculate results
        end_time = time.time()
        duration = end_time - start_time
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        # Summary
        logger.info("=" * 80)
        logger.info("🎯 TECH CARD GENERATION TESTING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"📊 Total Tests: {self.total_tests}")
        logger.info(f"✅ Passed: {self.passed_tests}")
        logger.info(f"❌ Failed: {self.total_tests - self.passed_tests}")
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        logger.info(f"⏱️ Duration: {duration:.2f}s")
        
        # Detailed results
        logger.info("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            logger.info(f"{status} {result['test']}: {result['details']}")
        
        # Critical issues summary
        critical_failures = [r for r in self.test_results if not r['passed'] and 
                           ('str' in r['details'] or 'AttributeError' in r['details'] or 'TypeError' in r['details'])]
        
        if critical_failures:
            logger.error("\n🚨 CRITICAL ISSUES DETECTED:")
            for failure in critical_failures:
                logger.error(f"❌ {failure['test']}: {failure['details']}")
        
        return {
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'success_rate': success_rate,
            'duration': duration,
            'results': self.test_results,
            'critical_failures': len(critical_failures)
        }


async def main():
    """Main test execution"""
    tester = TechCardGenerationTester()
    results = await tester.run_all_tests()
    
    # Return appropriate exit code
    if results['success_rate'] >= 70 and results['critical_failures'] == 0:
        logger.info("🎉 Testing completed successfully!")
        return 0
    else:
        logger.error("💥 Testing failed - critical issues detected or too many failures")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)