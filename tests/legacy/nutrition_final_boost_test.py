#!/usr/bin/env python3
"""
TECH CARD NUTRITION FINAL BOOST - COMPREHENSIVE BACKEND TESTING
================================================================

This test validates the complete TECH CARD NUTRITION FINAL BOOST system
focusing on achieving ≥80% БЖУ coverage with the expanded 216-ingredient catalog.

CRITICAL ACCEPTANCE CRITERIA:
✅ БЖУ покрытие ≥80%: MUST BE ACHIEVED
✅ Каталог 216 ингредиентов: with critical additions
✅ 100% техкарт с покрытием ≥80%: all tests pass
✅ XLSX экспорт работает: stable with БЖУ data
✅ Performance ≤20с: acceptable generation time
"""

import json
import time
import statistics
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TechCardNutritionFinalBoostTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 60
        self.results = {
            'test_start': datetime.now().isoformat(),
            'catalog_validation': {},
            'techcard_generation': {},
            'nutrition_coverage': {},
            'xlsx_export': {},
            'performance': {},
            'final_assessment': {}
        }

    def test_1_expanded_catalog_validation(self):
        """Test 1: Validate expanded catalog (216 ingredients)"""
        print("🔍 TEST 1: EXPANDED CATALOG VALIDATION (216 ingredients)")
        
        try:
            # Check nutrition catalog file
            catalog_path = "/app/backend/data/nutrition_catalog.dev.json"
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
            
            items = catalog.get('items', [])
            catalog_count = len(items)
            
            # Validate critical ingredients
            critical_ingredients = ['вода', 'свекла', 'лук', 'соль']
            found_critical = []
            
            for item in items:
                name = item.get('name', '').lower()
                for critical in critical_ingredients:
                    if critical in name:
                        found_critical.append(critical)
                        break
            
            # Validate БЖУ data completeness
            complete_nutrition = 0
            for item in items:
                per100g = item.get('per100g', {})
                if all(key in per100g for key in ['kcal', 'proteins_g', 'fats_g', 'carbs_g']):
                    complete_nutrition += 1
            
            self.results['catalog_validation'] = {
                'total_ingredients': catalog_count,
                'target_ingredients': 216,
                'meets_target': catalog_count >= 216,
                'critical_ingredients_found': found_critical,
                'critical_ingredients_target': critical_ingredients,
                'complete_nutrition_data': complete_nutrition,
                'nutrition_completeness_rate': complete_nutrition / catalog_count if catalog_count > 0 else 0,
                'source': catalog.get('source', 'unknown')
            }
            
            print(f"   📊 Catalog contains {catalog_count} ingredients (target: 216)")
            print(f"   🎯 Target met: {'✅' if catalog_count >= 216 else '❌'}")
            print(f"   🔑 Critical ingredients found: {len(found_critical)}/{len(critical_ingredients)}")
            print(f"   📈 Complete БЖУ data: {complete_nutrition}/{catalog_count} ({complete_nutrition/catalog_count*100:.1f}%)")
            print(f"   📦 Source: {catalog.get('source', 'unknown')}")
            
            return catalog_count >= 216 and len(found_critical) >= 3
            
        except Exception as e:
            print(f"   ❌ Catalog validation failed: {str(e)}")
            self.results['catalog_validation']['error'] = str(e)
            return False

    def test_2_techcard_generation_with_coverage(self):
        """Test 2: Generate 5 diverse tech cards and measure БЖУ coverage"""
        print("\n🍽️ TEST 2: TECHCARD GENERATION WITH БЖУ COVERAGE")
        
        # Diverse dish names for comprehensive testing
        test_dishes = [
            "Борщ украинский с говядиной",
            "Стейк из говядины с картофельным пюре", 
            "Салат Цезарь с курицей",
            "Паста карбонара с беконом",
            "Рыба запеченная с овощами"
        ]
        
        generated_cards = []
        coverage_scores = []
        generation_times = []
        
        for i, dish_name in enumerate(test_dishes, 1):
            print(f"   🔄 Generating tech card {i}/5: {dish_name}")
            
            try:
                start_time = time.time()
                
                # Generate tech card
                response = self.session.post(
                    f"{API_BASE}/v1/techcards.v2/generate",
                    json={"name": dish_name}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    generation_time = time.time() - start_time
                    generation_times.append(generation_time)
                    
                    # Extract tech card data
                    techcard = data.get('techcard', {})
                    techcard_id = techcard.get('id')
                    
                    # Calculate БЖУ coverage
                    coverage = self.calculate_nutrition_coverage(techcard)
                    coverage_scores.append(coverage)
                    
                    generated_cards.append({
                        'id': techcard_id,
                        'name': dish_name,
                        'coverage': coverage,
                        'generation_time': generation_time,
                        'ingredients_count': len(techcard.get('ingredients', [])),
                        'source': techcard.get('meta', {}).get('source', 'unknown')
                    })
                    
                    print(f"      ✅ Generated in {generation_time:.1f}s, БЖУ coverage: {coverage:.1f}%")
                    
                else:
                    print(f"      ❌ Generation failed: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"      ❌ Generation error: {str(e)}")
        
        # Calculate statistics
        avg_coverage = statistics.mean(coverage_scores) if coverage_scores else 0
        avg_generation_time = statistics.mean(generation_times) if generation_times else 0
        
        self.results['techcard_generation'] = {
            'generated_cards': generated_cards,
            'total_generated': len(generated_cards),
            'target_count': 5,
            'success_rate': len(generated_cards) / len(test_dishes),
            'average_generation_time': avg_generation_time,
            'performance_target_met': avg_generation_time <= 20.0
        }
        
        self.results['nutrition_coverage'] = {
            'individual_scores': coverage_scores,
            'average_coverage': avg_coverage,
            'target_coverage': 80.0,
            'target_met': avg_coverage >= 80.0,
            'cards_above_80': sum(1 for score in coverage_scores if score >= 80.0),
            'coverage_improvement': avg_coverage - 53.0  # vs baseline 53%
        }
        
        print(f"\n   📊 COVERAGE RESULTS:")
        print(f"      Average БЖУ coverage: {avg_coverage:.1f}% (target: ≥80%)")
        print(f"      Target achieved: {'✅' if avg_coverage >= 80.0 else '❌'}")
        print(f"      Cards with ≥80% coverage: {sum(1 for score in coverage_scores if score >= 80.0)}/{len(coverage_scores)}")
        print(f"      Average generation time: {avg_generation_time:.1f}s (target: ≤20s)")
        
        return len(generated_cards) >= 4 and avg_coverage >= 80.0

    def calculate_nutrition_coverage(self, techcard: Dict[str, Any]) -> float:
        """Calculate БЖУ coverage percentage for a tech card"""
        try:
            ingredients = techcard.get('ingredients', [])
            if not ingredients:
                return 0.0
            
            covered_ingredients = 0
            total_ingredients = len(ingredients)
            
            for ingredient in ingredients:
                # Check if ingredient has БЖУ data
                nutrition = ingredient.get('nutrition', {})
                if nutrition and any(nutrition.get(key, 0) > 0 for key in ['kcal', 'proteins_g', 'fats_g', 'carbs_g']):
                    covered_ingredients += 1
            
            coverage = (covered_ingredients / total_ingredients) * 100 if total_ingredients > 0 else 0
            return coverage
            
        except Exception as e:
            print(f"      ⚠️ Coverage calculation error: {str(e)}")
            return 0.0

    def test_3_xlsx_export_validation(self):
        """Test 3: XLSX export with improved БЖУ data"""
        print("\n📋 TEST 3: XLSX EXPORT VALIDATION")
        
        generated_cards = self.results['techcard_generation'].get('generated_cards', [])
        if not generated_cards:
            print("   ❌ No generated cards available for export testing")
            return False
        
        export_results = []
        export_times = []
        
        for i, card in enumerate(generated_cards[:3], 1):  # Test first 3 cards
            print(f"   📤 Exporting card {i}/3: {card['name']}")
            
            try:
                start_time = time.time()
                
                # Test enhanced export
                response = self.session.post(
                    f"{API_BASE}/v1/techcards.v2/export/enhanced/iiko.xlsx",
                    json={
                        "techcard_ids": [card['id']],
                        "operational_rounding": True
                    }
                )
                
                export_time = time.time() - start_time
                export_times.append(export_time)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    
                    export_results.append({
                        'card_id': card['id'],
                        'card_name': card['name'],
                        'success': True,
                        'file_size': content_length,
                        'export_time': export_time,
                        'content_type': content_type
                    })
                    
                    print(f"      ✅ Exported successfully: {content_length} bytes in {export_time:.2f}s")
                    
                else:
                    print(f"      ❌ Export failed: HTTP {response.status_code}")
                    export_results.append({
                        'card_id': card['id'],
                        'card_name': card['name'],
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"      ❌ Export error: {str(e)}")
                export_results.append({
                    'card_id': card['id'],
                    'card_name': card['name'],
                    'success': False,
                    'error': str(e)
                })
        
        successful_exports = sum(1 for result in export_results if result.get('success', False))
        avg_export_time = statistics.mean(export_times) if export_times else 0
        successful_file_sizes = [r.get('file_size', 0) for r in export_results if r.get('success', False)]
        avg_file_size = statistics.mean(successful_file_sizes) if successful_file_sizes else 0
        
        self.results['xlsx_export'] = {
            'export_results': export_results,
            'successful_exports': successful_exports,
            'total_attempts': len(export_results),
            'success_rate': successful_exports / len(export_results) if export_results else 0,
            'average_export_time': avg_export_time,
            'average_file_size': avg_file_size,
            'target_file_size': 6000,  # ~6KB+
            'file_size_target_met': avg_file_size >= 6000
        }
        
        print(f"\n   📊 EXPORT RESULTS:")
        print(f"      Successful exports: {successful_exports}/{len(export_results)}")
        print(f"      Average file size: {avg_file_size:.0f} bytes (target: ≥6KB)")
        print(f"      Average export time: {avg_export_time:.2f}s")
        
        return successful_exports >= 2

    def test_4_alt_export_cleanup(self):
        """Test 4: ALT Export Cleanup functionality"""
        print("\n🧹 TEST 4: ALT EXPORT CLEANUP")
        
        try:
            # Test ALT export cleanup stats
            response = self.session.get(f"{API_BASE}/v1/export/cleanup/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"   ✅ Cleanup stats accessible: {stats}")
                
                # Test cleanup audit
                audit_response = self.session.post(f"{API_BASE}/v1/export/cleanup/audit")
                if audit_response.status_code == 200:
                    audit = audit_response.json()
                    print(f"   ✅ Cleanup audit working: {len(audit.get('issues', []))} issues found")
                    return True
                else:
                    print(f"   ❌ Cleanup audit failed: HTTP {audit_response.status_code}")
                    return False
            else:
                print(f"   ❌ Cleanup stats failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ ALT Export Cleanup error: {str(e)}")
            return False

    def test_5_performance_validation(self):
        """Test 5: Performance validation"""
        print("\n⚡ TEST 5: PERFORMANCE VALIDATION")
        
        generation_times = [card.get('generation_time', 0) for card in self.results['techcard_generation'].get('generated_cards', [])]
        export_times = [result.get('export_time', 0) for result in self.results['xlsx_export'].get('export_results', []) if result.get('success', False)]
        
        avg_generation = statistics.mean(generation_times) if generation_times else 0
        max_generation = max(generation_times) if generation_times else 0
        avg_export = statistics.mean(export_times) if export_times else 0
        
        performance_met = avg_generation <= 20.0 and max_generation <= 30.0
        
        self.results['performance'] = {
            'average_generation_time': avg_generation,
            'max_generation_time': max_generation,
            'average_export_time': avg_export,
            'generation_target': 20.0,
            'performance_target_met': performance_met,
            'total_workflow_time': avg_generation + avg_export
        }
        
        print(f"   📊 PERFORMANCE METRICS:")
        print(f"      Average generation time: {avg_generation:.1f}s (target: ≤20s)")
        print(f"      Maximum generation time: {max_generation:.1f}s")
        print(f"      Average export time: {avg_export:.2f}s")
        print(f"      Performance target met: {'✅' if performance_met else '❌'}")
        
        return performance_met

    def test_6_system_integration(self):
        """Test 6: Full system integration"""
        print("\n🔗 TEST 6: SYSTEM INTEGRATION")
        
        try:
            # Test NutritionCalculator with expanded catalog
            test_ingredients = [
                {"name": "говядина", "quantity": 200},
                {"name": "картофель", "quantity": 300},
                {"name": "морковь", "quantity": 100}
            ]
            
            # Test catalog search with expanded data
            search_results = []
            for ingredient in test_ingredients:
                response = self.session.get(
                    f"{API_BASE}/v1/techcards.v2/catalog-search",
                    params={"q": ingredient["name"], "source": "catalog"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    search_results.append({
                        'ingredient': ingredient["name"],
                        'found': len(results) > 0,
                        'results_count': len(results)
                    })
                    print(f"   🔍 Search '{ingredient['name']}': {len(results)} results")
                else:
                    search_results.append({
                        'ingredient': ingredient["name"],
                        'found': False,
                        'error': f"HTTP {response.status_code}"
                    })
            
            successful_searches = sum(1 for result in search_results if result.get('found', False))
            integration_success = successful_searches >= 2
            
            print(f"   📊 Integration results: {successful_searches}/{len(search_results)} searches successful")
            
            return integration_success
            
        except Exception as e:
            print(f"   ❌ System integration error: {str(e)}")
            return False

    def generate_final_assessment(self):
        """Generate final assessment of TECH CARD NUTRITION FINAL BOOST"""
        print("\n🎯 FINAL ASSESSMENT: TECH CARD NUTRITION FINAL BOOST")
        
        # Collect all test results
        catalog_ok = self.results['catalog_validation'].get('meets_target', False)
        coverage_ok = self.results['nutrition_coverage'].get('target_met', False)
        export_ok = self.results['xlsx_export'].get('success_rate', 0) >= 0.8
        performance_ok = self.results['performance'].get('performance_target_met', False)
        
        # Calculate overall success
        critical_criteria = [catalog_ok, coverage_ok, export_ok, performance_ok]
        success_rate = sum(critical_criteria) / len(critical_criteria)
        
        avg_coverage = self.results['nutrition_coverage'].get('average_coverage', 0)
        catalog_count = self.results['catalog_validation'].get('total_ingredients', 0)
        
        self.results['final_assessment'] = {
            'overall_success': success_rate >= 0.8,
            'success_rate': success_rate,
            'critical_criteria_met': {
                'expanded_catalog_216': catalog_ok,
                'coverage_80_percent': coverage_ok,
                'xlsx_export_working': export_ok,
                'performance_under_20s': performance_ok
            },
            'key_metrics': {
                'catalog_ingredients': catalog_count,
                'average_coverage': avg_coverage,
                'coverage_improvement': avg_coverage - 53.0,
                'target_achievement': avg_coverage >= 80.0
            },
            'project_status': 'SUCCESS' if success_rate >= 0.8 and avg_coverage >= 80.0 else 'NEEDS_IMPROVEMENT'
        }
        
        print(f"\n   🏆 PROJECT GOAL ACHIEVEMENT:")
        print(f"      ✅ Expanded catalog (216 ingredients): {'✅' if catalog_ok else '❌'}")
        print(f"      ✅ БЖУ coverage ≥80%: {'✅' if coverage_ok else '❌'} ({avg_coverage:.1f}%)")
        print(f"      ✅ XLSX export working: {'✅' if export_ok else '❌'}")
        print(f"      ✅ Performance ≤20s: {'✅' if performance_ok else '❌'}")
        print(f"\n   🎯 OVERALL SUCCESS: {'✅ ACHIEVED' if success_rate >= 0.8 and avg_coverage >= 80.0 else '❌ NEEDS WORK'}")
        print(f"      Success rate: {success_rate*100:.1f}%")
        print(f"      Coverage improvement: +{avg_coverage - 53.0:.1f}% vs baseline")
        
        return success_rate >= 0.8 and avg_coverage >= 80.0

    def save_results(self):
        """Save test results to file"""
        self.results['test_end'] = datetime.now().isoformat()
        
        with open('/app/tech_card_nutrition_final_boost_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: /app/tech_card_nutrition_final_boost_results.json")

def main():
    """Main test execution"""
    print("🚀 TECH CARD NUTRITION FINAL BOOST - COMPREHENSIVE TESTING")
    print("=" * 70)
    
    tester = TechCardNutritionFinalBoostTester()
    test_results = []
    
    # Execute all tests
    test_results.append(tester.test_1_expanded_catalog_validation())
    test_results.append(tester.test_2_techcard_generation_with_coverage())
    test_results.append(tester.test_3_xlsx_export_validation())
    test_results.append(tester.test_4_alt_export_cleanup())
    test_results.append(tester.test_5_performance_validation())
    test_results.append(tester.test_6_system_integration())
    
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
    print(f"   Final assessment: {'✅ SUCCESS' if final_success else '❌ NEEDS IMPROVEMENT'}")
    
    if final_success:
        print(f"\n🎉 TECH CARD NUTRITION FINAL BOOST: PROJECT GOAL ACHIEVED!")
        print(f"   ✅ БЖУ coverage ≥80% confirmed")
        print(f"   ✅ Expanded catalog (216 ingredients) operational")
        print(f"   ✅ XLSX export with improved data working")
        print(f"   ✅ Performance targets met")
    else:
        print(f"\n⚠️ TECH CARD NUTRITION FINAL BOOST: NEEDS IMPROVEMENT")
        print(f"   Review results for specific issues to address")

if __name__ == "__main__":
    main()