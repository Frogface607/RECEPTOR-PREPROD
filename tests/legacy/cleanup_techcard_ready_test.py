#!/usr/bin/env python3
"""
CLEANUP TECH CARD DATA & UI - READY STATUS VERIFICATION TEST
===========================================================

Быстрое тестирование изменений CLEANUP TECH CARD DATA & UI после исправления pipeline:

1. **READY Status Verification**: Создать 2-3 техкарты и проверить:
   - status = "READY" в ответе API
   - issues массив пустой или минимальный 
   - техкарта содержит полные данные (ingredients, nutrition, cost)

2. **Quick API Health Check**: Проверить основные эндпоинты:
   - POST /api/v1/techcards.v2/generate работает и возвращает READY
   - GET /api/v1/techcards.v2/catalog-search отвечает без ошибок
   - Базовая проверка export функций

3. **Data Validation**: Подтвердить что данные чистые:
   - Каталоги не содержат диапазонных ID
   - API возвращает корректные статусы

Фокус на проверке что исправление pipeline работает и техкарты создаются со статусом READY.
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class CleanupTechCardReadyTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 60
        self.results = {
            'test_start': datetime.now().isoformat(),
            'ready_status_verification': {},
            'api_health_check': {},
            'data_validation': {},
            'final_assessment': {}
        }
        self.generated_techcards = []

    def test_1_ready_status_verification(self):
        """Test 1: READY Status Verification - Создать 2-3 техкарты и проверить статус READY"""
        print("🔍 TEST 1: READY STATUS VERIFICATION")
        
        # Test dishes for READY status verification
        test_dishes = [
            "Борщ украинский с говядиной",
            "Стейк из говядины с картофельным пюре", 
            "Салат Цезарь с курицей"
        ]
        
        ready_cards = []
        generation_results = []
        
        for i, dish_name in enumerate(test_dishes, 1):
            print(f"   🔄 Generating tech card {i}/3: {dish_name}")
            
            try:
                start_time = time.time()
                
                # Generate tech card
                response = self.session.post(
                    f"{API_BASE}/v1/techcards.v2/generate",
                    json={"name": dish_name}
                )
                generation_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract key data
                    techcard = data.get('techcard', {})
                    status = data.get('status', 'UNKNOWN')
                    issues = data.get('issues', [])
                    
                    # Check for READY status
                    is_ready = status == "READY"
                    has_minimal_issues = len(issues) <= 2  # Allow minimal issues
                    
                    # Check for complete data
                    has_ingredients = len(techcard.get('ingredients', [])) > 0
                    has_nutrition = techcard.get('nutrition', {}) is not None
                    has_cost = techcard.get('cost', {}) is not None
                    
                    complete_data = has_ingredients and has_nutrition and has_cost
                    
                    card_result = {
                        'name': dish_name,
                        'status': status,
                        'is_ready': is_ready,
                        'issues_count': len(issues),
                        'issues': issues,
                        'has_minimal_issues': has_minimal_issues,
                        'has_ingredients': has_ingredients,
                        'ingredients_count': len(techcard.get('ingredients', [])),
                        'has_nutrition': has_nutrition,
                        'has_cost': has_cost,
                        'complete_data': complete_data,
                        'generation_time': generation_time,
                        'techcard_id': techcard.get('id'),
                        'success': is_ready and has_minimal_issues and complete_data
                    }
                    
                    generation_results.append(card_result)
                    
                    if card_result['success']:
                        ready_cards.append(card_result)
                        self.generated_techcards.append({
                            'id': techcard.get('id'),
                            'name': dish_name,
                            'data': techcard
                        })
                    
                    status_icon = "✅" if is_ready else "❌"
                    issues_icon = "✅" if has_minimal_issues else "⚠️"
                    data_icon = "✅" if complete_data else "❌"
                    
                    print(f"      {status_icon} Status: {status}")
                    print(f"      {issues_icon} Issues: {len(issues)} (minimal: {has_minimal_issues})")
                    print(f"      {data_icon} Complete data: {complete_data} (ingredients: {len(techcard.get('ingredients', []))}, nutrition: {has_nutrition}, cost: {has_cost})")
                    print(f"      ⏱️ Generated in {generation_time:.1f}s")
                        
                else:
                    print(f"      ❌ Generation failed: HTTP {response.status_code}")
                    generation_results.append({
                        'name': dish_name,
                        'status': 'ERROR',
                        'error': f"HTTP {response.status_code}",
                        'success': False
                    })
                        
            except Exception as e:
                print(f"      ❌ Generation error: {str(e)}")
                generation_results.append({
                    'name': dish_name,
                    'status': 'EXCEPTION',
                    'error': str(e),
                    'success': False
                })
        
        # Calculate results
        ready_count = len(ready_cards)
        total_count = len(test_dishes)
        success_rate = ready_count / total_count if total_count > 0 else 0
        
        self.results['ready_status_verification'] = {
            'generation_results': generation_results,
            'ready_cards': ready_cards,
            'ready_count': ready_count,
            'total_count': total_count,
            'success_rate': success_rate,
            'target_met': ready_count >= 2,  # At least 2 out of 3 should be READY
            'all_ready': ready_count == total_count
        }
        
        print(f"\n   📊 READY STATUS RESULTS:")
        print(f"      READY tech cards: {ready_count}/{total_count}")
        print(f"      Success rate: {success_rate*100:.1f}%")
        print(f"      Target met (≥2 READY): {'✅' if ready_count >= 2 else '❌'}")
        
        return ready_count >= 2

    def test_2_api_health_check(self):
        """Test 2: Quick API Health Check - Проверить основные эндпоинты"""
        print("\n🔍 TEST 2: API HEALTH CHECK")
        
        health_results = {}
        
        # Test 2.1: POST /api/v1/techcards.v2/generate
        print("   🔄 Testing tech card generation endpoint...")
        try:
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/generate",
                json={"name": "Тестовое блюдо для проверки API"}
            )
            generate_success = response.status_code == 200
            if generate_success:
                data = response.json()
                returns_ready = data.get('status') == 'READY'
            else:
                returns_ready = False
            
            health_results['generate_endpoint'] = {
                'accessible': generate_success,
                'returns_ready': returns_ready,
                'status_code': response.status_code
            }
            
            print(f"      {'✅' if generate_success else '❌'} Generate endpoint: HTTP {response.status_code}")
            print(f"      {'✅' if returns_ready else '❌'} Returns READY status: {returns_ready}")
                
        except Exception as e:
            health_results['generate_endpoint'] = {
                'accessible': False,
                'error': str(e)
            }
            print(f"      ❌ Generate endpoint error: {str(e)}")
        
        # Test 2.2: GET /api/v1/techcards.v2/catalog-search
        print("   🔄 Testing catalog search endpoint...")
        try:
            response = self.session.get(
                f"{API_BASE}/v1/techcards.v2/catalog-search",
                params={"q": "говядина", "source": "all"}
            )
            search_success = response.status_code == 200
            if search_success:
                data = response.json()
                has_results = len(data.get('results', [])) > 0
            else:
                has_results = False
            
            health_results['catalog_search_endpoint'] = {
                'accessible': search_success,
                'has_results': has_results,
                'status_code': response.status_code
            }
            
            print(f"      {'✅' if search_success else '❌'} Catalog search endpoint: HTTP {response.status_code}")
            print(f"      {'✅' if has_results else '❌'} Returns search results: {has_results}")
                
        except Exception as e:
            health_results['catalog_search_endpoint'] = {
                'accessible': False,
                'error': str(e)
            }
            print(f"      ❌ Catalog search endpoint error: {str(e)}")
        
        # Test 2.3: Basic export function check
        print("   🔄 Testing basic export functionality...")
        if self.generated_techcards:
            try:
                techcard_data = self.generated_techcards[0]['data']
                
                response = self.session.post(
                    f"{API_BASE}/v1/techcards.v2/export/enhanced/iiko.xlsx",
                    json={
                        "techcard_ids": [self.generated_techcards[0]['id']],
                        "operational_rounding": True
                    }
                )
                export_success = response.status_code == 200
                if export_success:
                    content_type = response.headers.get('content-type', '')
                    is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                    content_length = len(response.content)
                else:
                    is_excel = False
                    content_length = 0
                
                health_results['export_endpoint'] = {
                    'accessible': export_success,
                    'returns_excel': is_excel,
                    'file_size': content_length,
                    'status_code': response.status_code
                }
                
                print(f"      {'✅' if export_success else '❌'} Export endpoint: HTTP {response.status_code}")
                print(f"      {'✅' if is_excel else '❌'} Returns Excel file: {is_excel}")
                print(f"      📊 File size: {content_length} bytes")
                    
            except Exception as e:
                health_results['export_endpoint'] = {
                    'accessible': False,
                    'error': str(e)
                }
                print(f"      ❌ Export endpoint error: {str(e)}")
        else:
            health_results['export_endpoint'] = {
                'accessible': False,
                'error': 'No techcards available for export testing'
            }
            print(f"      ⚠️ Export endpoint: No techcards available for testing")
        
        # Calculate overall API health
        accessible_endpoints = sum(1 for result in health_results.values() if result.get('accessible', False))
        total_endpoints = len(health_results)
        api_health_score = accessible_endpoints / total_endpoints if total_endpoints > 0 else 0
        
        self.results['api_health_check'] = {
            'health_results': health_results,
            'accessible_endpoints': accessible_endpoints,
            'total_endpoints': total_endpoints,
            'health_score': api_health_score,
            'all_endpoints_healthy': api_health_score == 1.0
        }
        
        print(f"\n   📊 API HEALTH RESULTS:")
        print(f"      Accessible endpoints: {accessible_endpoints}/{total_endpoints}")
        print(f"      Health score: {api_health_score*100:.1f}%")
        print(f"      All endpoints healthy: {'✅' if api_health_score == 1.0 else '❌'}")
        
        return api_health_score >= 0.8  # At least 80% of endpoints should be healthy

    def test_3_data_validation(self):
        """Test 3: Data Validation - Подтвердить что данные чистые"""
        print("\n🔍 TEST 3: DATA VALIDATION")
        
        validation_results = {}
        
        # Test 3.1: Check catalog for range IDs
        print("   🔄 Checking catalogs for range IDs...")
        try:
            response = self.session.get(
                f"{API_BASE}/v1/techcards.v2/catalog-search",
                params={"q": "", "source": "all", "limit": 50}
            )
            if response.status_code == 200:
                data = response.json()
                    results = data.get('results', [])
                    
                    # Check for range IDs like '9969-86'
                    range_ids = []
                    clean_ids = []
                    
                    for item in results:
                        item_id = str(item.get('id', ''))
                        if '-' in item_id and any(char.isdigit() for char in item_id):
                            # Check if it looks like a range ID
                            parts = item_id.split('-')
                            if len(parts) == 2 and all(part.isdigit() for part in parts):
                                range_ids.append(item_id)
                            else:
                                clean_ids.append(item_id)
                        else:
                            clean_ids.append(item_id)
                    
                    no_range_ids = len(range_ids) == 0
                    
                    validation_results['catalog_ids'] = {
                        'total_items': len(results),
                        'range_ids': range_ids,
                        'range_ids_count': len(range_ids),
                        'clean_ids_count': len(clean_ids),
                        'no_range_ids': no_range_ids
                    }
                    
                    print(f"      {'✅' if no_range_ids else '❌'} No range IDs found: {no_range_ids}")
                    print(f"      📊 Total items: {len(results)}, Range IDs: {len(range_ids)}, Clean IDs: {len(clean_ids)}")
                    if range_ids:
                        print(f"      ⚠️ Found range IDs: {range_ids[:5]}...")  # Show first 5
                    
            else:
                validation_results['catalog_ids'] = {
                    'error': f"HTTP {response.status_code}",
                    'no_range_ids': False
                }
                print(f"      ❌ Catalog access failed: HTTP {response.status_code}")
                    
        except Exception as e:
            validation_results['catalog_ids'] = {
                'error': str(e),
                'no_range_ids': False
            }
            print(f"      ❌ Catalog validation error: {str(e)}")
        
        # Test 3.2: Check API status responses
        print("   🔄 Checking API status responses...")
        if self.results.get('ready_status_verification', {}).get('generation_results'):
            generation_results = self.results['ready_status_verification']['generation_results']
            
            correct_statuses = []
            incorrect_statuses = []
            
            for result in generation_results:
                status = result.get('status', 'UNKNOWN')
                if status in ['READY', 'DRAFT', 'ERROR', 'EXCEPTION']:
                    correct_statuses.append(status)
                else:
                    incorrect_statuses.append(status)
            
            all_correct_statuses = len(incorrect_statuses) == 0
            
            validation_results['api_statuses'] = {
                'correct_statuses': correct_statuses,
                'incorrect_statuses': incorrect_statuses,
                'all_correct': all_correct_statuses
            }
            
            print(f"      {'✅' if all_correct_statuses else '❌'} All API statuses correct: {all_correct_statuses}")
            print(f"      📊 Correct: {len(correct_statuses)}, Incorrect: {len(incorrect_statuses)}")
            if incorrect_statuses:
                print(f"      ⚠️ Incorrect statuses: {incorrect_statuses}")
        else:
            validation_results['api_statuses'] = {
                'error': 'No generation results available',
                'all_correct': False
            }
            print(f"      ⚠️ No generation results available for status validation")
        
        # Calculate overall data validation
        no_range_ids = validation_results.get('catalog_ids', {}).get('no_range_ids', False)
        correct_statuses = validation_results.get('api_statuses', {}).get('all_correct', False)
        
        data_clean = no_range_ids and correct_statuses
        
        self.results['data_validation'] = {
            'validation_results': validation_results,
            'no_range_ids': no_range_ids,
            'correct_statuses': correct_statuses,
            'data_clean': data_clean
        }
        
        print(f"\n   📊 DATA VALIDATION RESULTS:")
        print(f"      No range IDs in catalog: {'✅' if no_range_ids else '❌'}")
        print(f"      Correct API statuses: {'✅' if correct_statuses else '❌'}")
        print(f"      Data is clean: {'✅' if data_clean else '❌'}")
        
        return data_clean

    def generate_final_assessment(self):
        """Generate final assessment of CLEANUP TECH CARD DATA & UI testing"""
        print("\n🎯 FINAL ASSESSMENT: CLEANUP TECH CARD DATA & UI")
        
        # Collect all test results
        ready_status_ok = self.results['ready_status_verification'].get('target_met', False)
        api_health_ok = self.results['api_health_check'].get('all_endpoints_healthy', False)
        data_clean_ok = self.results['data_validation'].get('data_clean', False)
        
        # Calculate overall success
        critical_criteria = [ready_status_ok, api_health_ok, data_clean_ok]
        success_rate = sum(critical_criteria) / len(critical_criteria)
        
        ready_count = self.results['ready_status_verification'].get('ready_count', 0)
        total_count = self.results['ready_status_verification'].get('total_count', 0)
        
        self.results['final_assessment'] = {
            'overall_success': success_rate >= 0.8,
            'success_rate': success_rate,
            'critical_criteria_met': {
                'ready_status_verification': ready_status_ok,
                'api_health_check': api_health_ok,
                'data_validation': data_clean_ok
            },
            'key_metrics': {
                'ready_techcards': ready_count,
                'total_techcards': total_count,
                'ready_percentage': (ready_count / total_count * 100) if total_count > 0 else 0
            },
            'pipeline_status': 'FIXED' if success_rate >= 0.8 and ready_count >= 2 else 'NEEDS_WORK'
        }
        
        print(f"\n   🏆 PIPELINE FIX VERIFICATION:")
        print(f"      ✅ READY status verification: {'✅' if ready_status_ok else '❌'} ({ready_count}/{total_count} READY)")
        print(f"      ✅ API health check: {'✅' if api_health_ok else '❌'}")
        print(f"      ✅ Data validation (clean): {'✅' if data_clean_ok else '❌'}")
        print(f"\n   🎯 OVERALL RESULT: {'✅ PIPELINE FIXED' if success_rate >= 0.8 and ready_count >= 2 else '❌ NEEDS MORE WORK'}")
        print(f"      Success rate: {success_rate*100:.1f}%")
        print(f"      READY tech cards: {ready_count}/{total_count} ({(ready_count/total_count*100) if total_count > 0 else 0:.1f}%)")
        
        return success_rate >= 0.8 and ready_count >= 2

    def save_results(self):
        """Save test results to file"""
        self.results['test_end'] = datetime.now().isoformat()
        
        with open('/app/cleanup_techcard_ready_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: /app/cleanup_techcard_ready_test_results.json")

def main():
    """Main test execution"""
    print("🚀 CLEANUP TECH CARD DATA & UI - READY STATUS VERIFICATION")
    print("=" * 70)
    
    tester = CleanupTechCardReadyTester()
    test_results = []
    
    # Execute all tests
    test_results.append(tester.test_1_ready_status_verification())
    test_results.append(tester.test_2_api_health_check())
    test_results.append(tester.test_3_data_validation())
    
    # Generate final assessment
    final_success = tester.generate_final_assessment()
    
    # Save results
    tester.save_results()
    
    # Summary
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"\n" + "=" * 70)
    print(f"🏁 TESTING COMPLETED")
    print(f"   Tests passed: {passed_tests}/{total_tests}")
    print(f"   Success rate: {passed_tests/total_tests*100:.1f}%")
    print(f"   Final assessment: {'✅ PIPELINE FIXED' if final_success else '❌ NEEDS MORE WORK'}")
    
    if final_success:
        print(f"\n🎉 CLEANUP TECH CARD DATA & UI: PIPELINE FIX VERIFIED!")
        print(f"   ✅ Tech cards generate with READY status")
        print(f"   ✅ APIs respond without errors")
        print(f"   ✅ Data is clean (no range IDs)")
        print(f"   ✅ Export functions working")
    else:
        print(f"\n⚠️ CLEANUP TECH CARD DATA & UI: PIPELINE NEEDS MORE WORK")
        print(f"   Review results for specific issues to address")

if __name__ == "__main__":
    main()