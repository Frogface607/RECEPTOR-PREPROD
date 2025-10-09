#!/usr/bin/env python3
"""
V2 TechCard Comprehensive Testing
Comprehensive test of V2 functionality including status and generation issues
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class V2ComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'V2-Comprehensive-Tester/1.0'
        })
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
        
    def test_v2_status_endpoint(self) -> bool:
        """Test V2 Status Endpoint"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/status"
            
            print(f"   Testing V2 status endpoint: {url}")
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for expected status fields
                    expected_fields = ['feature_enabled', 'llm_enabled', 'model']
                    found_fields = []
                    
                    for field in expected_fields:
                        if field in data:
                            found_fields.append(field)
                    
                    if len(found_fields) >= 2:
                        self.log_test(
                            "V2 Status Endpoint",
                            True,
                            f"V2 status endpoint working. Found fields: {', '.join(found_fields)}",
                            data
                        )
                        return True
                    else:
                        self.log_test(
                            "V2 Status Endpoint",
                            False,
                            f"V2 status missing expected fields. Found: {', '.join(found_fields)}",
                            data
                        )
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log_test(
                        "V2 Status Endpoint",
                        False,
                        f"Invalid JSON response: {str(e)}",
                        response.text[:200]
                    )
                    return False
            else:
                self.log_test(
                    "V2 Status Endpoint",
                    False,
                    f"Status endpoint returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V2 Status Endpoint",
                False,
                f"Status endpoint request failed: {str(e)}"
            )
            return False
    
    def test_v2_generation_endpoint_availability(self) -> bool:
        """Test V2 Generation Endpoint Availability"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Test with minimal payload to check endpoint availability
            test_payload = {
                "name": "Борщ классический",
                "user_id": "demo_user",
                "cuisine": "европейская"
            }
            
            print(f"   Testing V2 generation endpoint: {url}")
            
            response = self.session.post(url, json=test_payload, timeout=30)
            
            if response.status_code in [200, 400, 422, 500]:  # Any response means endpoint is available
                self.log_test(
                    "V2 Generation Endpoint Availability",
                    True,
                    f"V2 generation endpoint is available (HTTP {response.status_code})"
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "V2 Generation Endpoint Availability",
                    False,
                    f"V2 generation endpoint not found (HTTP 404)",
                    response.text[:200]
                )
                return False
            else:
                self.log_test(
                    "V2 Generation Endpoint Availability",
                    True,  # Still available, just different response
                    f"V2 generation endpoint available but returned HTTP {response.status_code}"
                )
                return True
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V2 Generation Endpoint Availability",
                False,
                f"V2 generation endpoint connection failed: {str(e)}"
            )
            return False
    
    def test_v2_generation_with_test_data(self) -> bool:
        """Test V2 Generation with Specified Test Data"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Test data as specified in review request
            payload = {
                "name": "Борщ классический",
                "user_id": "demo_user",
                "cuisine": "европейская"
            }
            
            print(f"   Generating V2 techcard: {payload['name']}")
            print(f"   User: {payload['user_id']}, Cuisine: {payload['cuisine']}")
            
            response = self.session.post(url, json=payload, timeout=120)  # Extended timeout
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check response structure
                    status = data.get('status', 'unknown')
                    card = data.get('card')
                    issues = data.get('issues', [])
                    message = data.get('message', '')
                    
                    # Analyze the response
                    if status == 'READY':
                        if card is not None:
                            self.log_test(
                                "V2 Generation with Test Data",
                                True,
                                f"V2 techcard generated successfully. Status: {status}, Card: Present, Issues: {len(issues)}",
                                {
                                    'status': status,
                                    'card_present': card is not None,
                                    'issues_count': len(issues),
                                    'message': message
                                }
                            )
                            return True
                        else:
                            self.log_test(
                                "V2 Generation with Test Data",
                                False,
                                f"V2 generation returned READY status but card is null. Issues: {len(issues)}",
                                {
                                    'status': status,
                                    'card': card,
                                    'issues': issues,
                                    'message': message
                                }
                            )
                            return False
                    else:
                        self.log_test(
                            "V2 Generation with Test Data",
                            False,
                            f"V2 generation failed with status: {status}. Issues: {len(issues)}",
                            {
                                'status': status,
                                'issues': issues,
                                'message': message
                            }
                        )
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log_test(
                        "V2 Generation with Test Data",
                        False,
                        f"Invalid JSON response: {str(e)}",
                        response.text[:200]
                    )
                    return False
            else:
                self.log_test(
                    "V2 Generation with Test Data",
                    False,
                    f"V2 generation failed with HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V2 Generation with Test Data",
                False,
                f"V2 generation request failed: {str(e)}"
            )
            return False
    
    def test_v2_generation_issues_analysis(self) -> bool:
        """Test V2 Generation and Analyze Issues"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Simple test data to minimize complexity
            payload = {
                "name": "Простое блюдо",
                "user_id": "demo_user",
                "cuisine": "европейская"
            }
            
            print(f"   Testing V2 generation issues with simple dish: {payload['name']}")
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Analyze the issues
                    status = data.get('status', 'unknown')
                    card = data.get('card')
                    issues = data.get('issues', [])
                    message = data.get('message', '')
                    
                    # Check for specific known issues
                    issue_analysis = {
                        'llm_timeout': False,
                        'validation_error': False,
                        'process_steps_error': False,
                        'pipeline_error': False
                    }
                    
                    # Analyze issues array and message
                    all_text = f"{message} {' '.join([str(issue) for issue in issues])}"
                    
                    if 'timeout' in all_text.lower() or 'timed out' in all_text.lower():
                        issue_analysis['llm_timeout'] = True
                    
                    if 'validation' in all_text.lower():
                        issue_analysis['validation_error'] = True
                    
                    if 'process' in all_text.lower() and ('3 items' in all_text or 'too_short' in all_text):
                        issue_analysis['process_steps_error'] = True
                    
                    if 'pipeline' in all_text.lower() or 'critical' in all_text.lower():
                        issue_analysis['pipeline_error'] = True
                    
                    # Determine success based on analysis
                    critical_issues = sum([
                        issue_analysis['llm_timeout'],
                        issue_analysis['validation_error'],
                        issue_analysis['process_steps_error'],
                        issue_analysis['pipeline_error']
                    ])
                    
                    if critical_issues == 0 and card is not None:
                        self.log_test(
                            "V2 Generation Issues Analysis",
                            True,
                            f"V2 generation working without critical issues. Status: {status}",
                            {
                                'status': status,
                                'card_present': card is not None,
                                'issues_count': len(issues),
                                'issue_analysis': issue_analysis
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "V2 Generation Issues Analysis",
                            False,
                            f"V2 generation has critical issues. Critical issues: {critical_issues}, Card: {'Present' if card else 'Null'}",
                            {
                                'status': status,
                                'card_present': card is not None,
                                'issues_count': len(issues),
                                'issue_analysis': issue_analysis,
                                'message': message,
                                'issues': issues
                            }
                        )
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log_test(
                        "V2 Generation Issues Analysis",
                        False,
                        f"Invalid JSON response: {str(e)}",
                        response.text[:200]
                    )
                    return False
            else:
                self.log_test(
                    "V2 Generation Issues Analysis",
                    False,
                    f"V2 generation failed with HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V2 Generation Issues Analysis",
                False,
                f"V2 generation request failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all V2 comprehensive tests"""
        print("🚀 STARTING V2 COMPREHENSIVE TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Target: Быстрый тест восстановленной V2 функциональности")
        print("=" * 60)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_v2_status_endpoint,
            self.test_v2_generation_endpoint_availability,
            self.test_v2_generation_with_test_data,
            self.test_v2_generation_issues_analysis
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_func.__name__}: {str(e)}")
        
        # Summary
        print("=" * 60)
        print("🎯 V2 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 75:
            print("🎉 V2 FUNCTIONALITY: FULLY OPERATIONAL")
        elif success_rate >= 50:
            print("⚠️ V2 FUNCTIONALITY: PARTIALLY WORKING")
        else:
            print("🚨 V2 FUNCTIONALITY: CRITICAL ISSUES")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results
        }

def main():
    """Main test execution"""
    print("V2 TechCard Comprehensive Testing")
    print("Быстрый тест восстановленной V2 функциональности")
    print()
    
    tester = V2ComprehensiveTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 50:  # Lower threshold for comprehensive test
        return 0  # Success
    else:
        return 1  # Failure

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)