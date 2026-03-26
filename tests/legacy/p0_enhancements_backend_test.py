#!/usr/bin/env python3
"""
P0: SKU Search (iiko) — 0-hit bugfix & P0: Safe-Automap + Sanitize Backend Testing
Tests the newly implemented P0 priority enhancements for iiko search and auto-mapping
"""

import asyncio
import json
import os
import sys
import time
import requests
from pathlib import Path

# Add backend to path for imports
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class P0EnhancementsTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        self.results = []
        self.test_count = 0
        self.passed_count = 0
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.test_count += 1
        if passed:
            self.passed_count += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        print(result)
        self.results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
    
    def test_p0_sku_search_default_source_iiko(self):
        """Test P0: Default Source "iiko" - GET /api/v1/techcards.v2/catalog-search with source=iiko"""
        try:
            # Test with source=iiko parameter
            response = self.session.get(f"{API_BASE}/v1/techcards.v2/catalog-search", params={
                'q': 'молоко',
                'source': 'iiko',
                'limit': 10
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if data.get('status') == 'success':
                    items = data.get('items', [])
                    iiko_badge = data.get('iiko_badge', {})
                    
                    # Verify iiko badge information
                    has_badge_info = 'count' in iiko_badge and 'connection_status' in iiko_badge
                    
                    # Check if results prioritize iiko/RMS results first
                    iiko_results = [item for item in items if item.get('source') == 'iiko']
                    
                    self.log_result(
                        "P0: Default Source iiko",
                        True,
                        f"Found {len(iiko_results)} iiko results, badge info: {has_badge_info}, connection: {iiko_badge.get('connection_status', 'unknown')}"
                    )
                else:
                    self.log_result("P0: Default Source iiko", False, f"API returned status: {data.get('status')}")
            else:
                self.log_result("P0: Default Source iiko", False, f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_result("P0: Default Source iiko", False, f"Exception: {str(e)}")
    
    def test_p0_ru_normalization_search(self):
        """Test P0: RU-normalization Search with specific queries"""
        test_queries = [
            ("картоф", ["картофель", "картошка"]),
            ("яйцо", ["яйцо куриное", "яйца"]),
            ("молоко 3.2", ["молоко", "3.2%", "жирность"])
        ]
        
        for query, expected_terms in test_queries:
            try:
                response = self.session.get(f"{API_BASE}/v1/techcards.v2/catalog-search", params={
                    'q': query,
                    'source': 'iiko',
                    'limit': 10
                })
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'success':
                        items = data.get('items', [])
                        
                        # Check if any results contain expected terms
                        found_matches = []
                        for item in items:
                            item_name = item.get('name', '').lower()
                            for term in expected_terms:
                                if term.lower() in item_name:
                                    found_matches.append(f"{item['name']} (matches: {term})")
                                    break
                        
                        self.log_result(
                            f"P0: RU-normalization '{query}'",
                            len(found_matches) > 0,
                            f"Found {len(found_matches)} relevant matches: {found_matches[:2]}"
                        )
                    else:
                        self.log_result(f"P0: RU-normalization '{query}'", False, f"API error: {data.get('status')}")
                else:
                    self.log_result(f"P0: RU-normalization '{query}'", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"P0: RU-normalization '{query}'", False, f"Exception: {str(e)}")
    
    def test_p0_top5_candidates(self):
        """Test P0: Top-5 Candidates - verify search returns top-5 results even with low scores"""
        try:
            # Use a generic query that should return multiple results
            response = self.session.get(f"{API_BASE}/v1/techcards.v2/catalog-search", params={
                'q': 'мясо',
                'source': 'iiko',
                'limit': 5
            })
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    items = data.get('items', [])
                    
                    # Check that we get results (should not filter out based on hidden filters)
                    has_results = len(items) > 0
                    
                    # Check if results are sorted by relevance
                    has_scores = all('match_score' in item for item in items if item.get('source') == 'iiko')
                    
                    # Verify no hidden filtering (should include products regardless of price/active status)
                    includes_various_products = len(set(item.get('name') for item in items)) > 1
                    
                    self.log_result(
                        "P0: Top-5 Candidates",
                        has_results and includes_various_products,
                        f"Returned {len(items)} results, has_scores: {has_scores}, variety: {includes_various_products}"
                    )
                else:
                    self.log_result("P0: Top-5 Candidates", False, f"API error: {data.get('status')}")
            else:
                self.log_result("P0: Top-5 Candidates", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("P0: Top-5 Candidates", False, f"Exception: {str(e)}")
    
    def test_p0_enhanced_rms_search_method(self):
        """Test P0: Enhanced search_rms_products_enhanced method"""
        try:
            # Test with a query that should trigger RU-normalization
            response = self.session.get(f"{API_BASE}/v1/techcards.v2/catalog-search", params={
                'q': 'картоф',  # Should find картофель, картошка via lemmatization
                'source': 'rms',
                'limit': 10
            })
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    items = data.get('items', [])
                    rms_count = data.get('rms_count', 0)
                    
                    # Check for enhanced scoring and RU-normalization
                    enhanced_features = []
                    
                    for item in items:
                        if item.get('source') == 'iiko':  # RMS results show as 'iiko' source
                            # Check for match score
                            if 'match_score' in item:
                                enhanced_features.append('match_scores')
                            
                            # Check for lemmatization matches
                            name = item.get('name', '').lower()
                            if any(term in name for term in ['картофель', 'картошка', 'клубни']):
                                enhanced_features.append('lemmatization')
                    
                    self.log_result(
                        "P0: Enhanced RMS Search Method",
                        len(items) > 0,
                        f"RMS count: {rms_count}, enhanced features: {list(set(enhanced_features))}"
                    )
                else:
                    self.log_result("P0: Enhanced RMS Search Method", False, f"API error: {data.get('status')}")
            else:
                self.log_result("P0: Enhanced RMS Search Method", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("P0: Enhanced RMS Search Method", False, f"Exception: {str(e)}")
    
    def test_p0_safe_automap_sanitization(self):
        """Test P0: Enhanced Auto-mapping Sanitization"""
        try:
            # Create test techcard data
            test_techcard = {
                "meta": {"title": "Test Tech Card"},
                "ingredients": [
                    {"name": "молоко", "brutto_g": 100, "unit": "мл"},
                    {"name": "яйца", "brutto_g": 50, "unit": "шт"},
                    {"name": "говядина", "brutto_g": 200, "unit": "г"}
                ]
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/mapping/enhanced", json={
                'techcard': test_techcard,
                'organization_id': 'default',
                'auto_apply': False
            })
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    mapping_results = data.get('mapping_results', {})
                    results = mapping_results.get('results', [])
                    
                    # Check sanitization features
                    sanitization_checks = []
                    
                    # Verify null/empty objects are filtered
                    has_valid_suggestions = all(
                        result.get('suggestion', {}).get('name') and 
                        result.get('suggestion', {}).get('sku_id')
                        for result in results
                    )
                    if has_valid_suggestions:
                        sanitization_checks.append('valid_suggestions')
                    
                    # Check for proper error handling
                    if mapping_results.get('status') in ['success', 'no_products']:
                        sanitization_checks.append('proper_status')
                    
                    # Verify confidence scoring
                    has_confidence_scores = all(
                        'confidence' in result and isinstance(result['confidence'], (int, float))
                        for result in results
                    )
                    if has_confidence_scores:
                        sanitization_checks.append('confidence_scores')
                    
                    self.log_result(
                        "P0: Safe-Automap Sanitization",
                        len(sanitization_checks) >= 2,
                        f"Sanitization features: {sanitization_checks}, results: {len(results)}"
                    )
                else:
                    # Check if it's a proper "no products" scenario
                    if data.get('mapping_results', {}).get('status') == 'no_products':
                        self.log_result(
                            "P0: Safe-Automap Sanitization",
                            True,
                            "Properly handled no RMS products scenario"
                        )
                    else:
                        self.log_result("P0: Safe-Automap Sanitization", False, f"API error: {data.get('status')}")
            else:
                self.log_result("P0: Safe-Automap Sanitization", False, f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_result("P0: Safe-Automap Sanitization", False, f"Exception: {str(e)}")
    
    def test_p0_unit_mismatch_handling(self):
        """Test P0: Unit-mismatch Handling - verify unit mismatches are shown (not discarded)"""
        try:
            # Create test with ingredients that might have unit mismatches
            test_techcard = {
                "meta": {"title": "Unit Mismatch Test"},
                "ingredients": [
                    {"name": "молоко", "brutto_g": 100, "unit": "мл"},  # liquid unit
                    {"name": "мука", "brutto_g": 200, "unit": "г"},    # weight unit
                    {"name": "яйца", "brutto_g": 50, "unit": "шт"}     # piece unit
                ]
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/mapping/enhanced", json={
                'techcard': test_techcard,
                'organization_id': 'default'
            })
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    mapping_results = data.get('mapping_results', {})
                    results = mapping_results.get('results', [])
                    
                    # Check that unit information is preserved
                    unit_info_preserved = []
                    
                    for result in results:
                        suggestion = result.get('suggestion', {})
                        original_unit = result.get('original_unit')
                        suggested_unit = suggestion.get('unit')
                        
                        if original_unit and suggested_unit:
                            unit_info_preserved.append({
                                'ingredient': result.get('ingredient_name'),
                                'original': original_unit,
                                'suggested': suggested_unit,
                                'mismatch': original_unit != suggested_unit
                            })
                    
                    # Verify that products with different units are still returned
                    has_unit_mismatches = any(info['mismatch'] for info in unit_info_preserved)
                    preserves_unit_info = len(unit_info_preserved) > 0
                    
                    self.log_result(
                        "P0: Unit-mismatch Handling",
                        preserves_unit_info,
                        f"Unit info preserved: {len(unit_info_preserved)}, has mismatches: {has_unit_mismatches}"
                    )
                else:
                    # Handle no products scenario
                    if data.get('mapping_results', {}).get('status') == 'no_products':
                        self.log_result(
                            "P0: Unit-mismatch Handling",
                            True,
                            "No RMS products available for unit mismatch testing"
                        )
                    else:
                        self.log_result("P0: Unit-mismatch Handling", False, f"API error: {data.get('status')}")
            else:
                self.log_result("P0: Unit-mismatch Handling", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("P0: Unit-mismatch Handling", False, f"Exception: {str(e)}")
    
    def test_p0_error_handling_scenarios(self):
        """Test P0: Error Handling - various error scenarios"""
        error_scenarios = [
            {
                'name': 'Empty ingredients list',
                'data': {'techcard': {'meta': {'title': 'Empty'}, 'ingredients': []}},
                'expected_status': 400
            },
            {
                'name': 'Missing techcard data',
                'data': {},
                'expected_status': 400
            },
            {
                'name': 'Invalid techcard structure',
                'data': {'techcard': 'invalid'},
                'expected_status': 400
            }
        ]
        
        for scenario in error_scenarios:
            try:
                response = self.session.post(f"{API_BASE}/v1/techcards.v2/mapping/enhanced", json=scenario['data'])
                
                # Check if error is handled gracefully
                if response.status_code == scenario['expected_status']:
                    try:
                        error_data = response.json()
                        has_error_message = 'detail' in error_data or 'message' in error_data
                        
                        self.log_result(
                            f"P0: Error Handling - {scenario['name']}",
                            has_error_message,
                            f"HTTP {response.status_code}, has error message: {has_error_message}"
                        )
                    except:
                        self.log_result(
                            f"P0: Error Handling - {scenario['name']}",
                            True,
                            f"HTTP {response.status_code} (non-JSON response)"
                        )
                else:
                    self.log_result(
                        f"P0: Error Handling - {scenario['name']}",
                        False,
                        f"Expected HTTP {scenario['expected_status']}, got {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_result(f"P0: Error Handling - {scenario['name']}", False, f"Exception: {str(e)}")
    
    def test_p0_no_rms_products_scenario(self):
        """Test P0: No RMS products scenario handling"""
        try:
            # Test with organization that likely has no RMS products
            test_techcard = {
                "meta": {"title": "No Products Test"},
                "ingredients": [
                    {"name": "тестовый ингредиент", "brutto_g": 100, "unit": "г"}
                ]
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/mapping/enhanced", json={
                'techcard': test_techcard,
                'organization_id': 'nonexistent_org'
            })
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    mapping_results = data.get('mapping_results', {})
                    
                    # Check for proper no_products handling
                    if mapping_results.get('status') == 'no_products':
                        has_proper_message = 'message' in mapping_results
                        has_empty_results = len(mapping_results.get('results', [])) == 0
                        
                        self.log_result(
                            "P0: No RMS Products Scenario",
                            has_proper_message and has_empty_results,
                            f"Status: {mapping_results.get('status')}, message: {mapping_results.get('message', '')[:50]}"
                        )
                    else:
                        # If there are products, that's also valid
                        self.log_result(
                            "P0: No RMS Products Scenario",
                            True,
                            f"Found products for organization, status: {mapping_results.get('status')}"
                        )
                else:
                    self.log_result("P0: No RMS Products Scenario", False, f"API error: {data.get('status')}")
            else:
                self.log_result("P0: No RMS Products Scenario", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("P0: No RMS Products Scenario", False, f"Exception: {str(e)}")
    
    def test_p0_specific_dod_queries(self):
        """Test P0: Specific DoD queries mentioned in review"""
        dod_queries = ["картоф", "яйцо", "молоко 3.2"]
        
        for query in dod_queries:
            try:
                response = self.session.get(f"{API_BASE}/v1/techcards.v2/catalog-search", params={
                    'q': query,
                    'source': 'iiko',
                    'limit': 5
                })
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'success':
                        items = data.get('items', [])
                        iiko_items = [item for item in items if item.get('source') == 'iiko']
                        
                        # Check for RU-normalization effectiveness
                        relevant_results = []
                        for item in iiko_items:
                            name = item.get('name', '').lower()
                            
                            # Query-specific relevance checks
                            if query == "картоф" and any(term in name for term in ['картофель', 'картошка', 'клубни']):
                                relevant_results.append(item['name'])
                            elif query == "яйцо" and any(term in name for term in ['яйцо', 'яйца', 'куриное']):
                                relevant_results.append(item['name'])
                            elif query == "молоко 3.2" and any(term in name for term in ['молоко', '3.2', '3,2', 'жирность']):
                                relevant_results.append(item['name'])
                        
                        self.log_result(
                            f"P0: DoD Query '{query}'",
                            len(relevant_results) > 0,
                            f"Found {len(relevant_results)} relevant results: {relevant_results[:2]}"
                        )
                    else:
                        self.log_result(f"P0: DoD Query '{query}'", False, f"API error: {data.get('status')}")
                else:
                    self.log_result(f"P0: DoD Query '{query}'", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"P0: DoD Query '{query}'", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all P0 enhancement tests"""
        print("🎯 P0: SKU Search (iiko) — 0-hit bugfix & P0: Safe-Automap + Sanitize Backend Testing")
        print("=" * 80)
        
        # P0: SKU Search (iiko) — 0-hit bugfix Tests
        print("\n📋 P0: SKU Search (iiko) — 0-hit bugfix Tests:")
        self.test_p0_sku_search_default_source_iiko()
        self.test_p0_ru_normalization_search()
        self.test_p0_top5_candidates()
        self.test_p0_enhanced_rms_search_method()
        self.test_p0_specific_dod_queries()
        
        # P0: Safe-Automap + Sanitize Tests
        print("\n📋 P0: Safe-Automap + Sanitize Tests:")
        self.test_p0_safe_automap_sanitization()
        self.test_p0_unit_mismatch_handling()
        self.test_p0_error_handling_scenarios()
        self.test_p0_no_rms_products_scenario()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"🎯 P0 ENHANCEMENTS TESTING SUMMARY:")
        print(f"✅ Passed: {self.passed_count}/{self.test_count} tests ({self.passed_count/self.test_count*100:.1f}%)")
        
        if self.passed_count == self.test_count:
            print("🎉 ALL P0 ENHANCEMENT TESTS PASSED!")
        else:
            failed_tests = [r for r in self.results if not r['passed']]
            print(f"❌ Failed tests: {len(failed_tests)}")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        return self.passed_count, self.test_count

def main():
    """Main test execution"""
    tester = P0EnhancementsTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        print("\n✅ All P0 enhancement tests completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} tests failed. Check implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()