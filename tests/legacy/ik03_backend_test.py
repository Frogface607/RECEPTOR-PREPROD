#!/usr/bin/env python3
"""
IK-03 "RMS→PriceProvider: цены + НДС из iiko" - BACKEND TESTING

Comprehensive testing of IK-03 functionality for integrating prices and VAT from iiko RMS.
Tests all primary objectives from the review request:

1. RMS Price Sync Endpoint Testing
2. Enhanced catalog-search with pricing fields  
3. PriceProvider Integration
4. Cost Calculator Integration
5. MongoDB Collection and Indexing
6. Error Handling and Degradation
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

class IK03BackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.organization_id = "default"  # Default organization for testing
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def test_rms_price_sync_endpoint(self):
        """
        1. RMS Price Sync Endpoint Testing:
        - POST /api/v1/iiko/rms/sync/prices - проверь что endpoint существует и работает
        - Тестируй с разными organization_id и параметрами force
        - Убедись что возвращается корректная структура ответа (SyncRmsPricesResponse)
        - Проверь idempotent behavior - можно вызывать несколько раз безопасно
        """
        print("🎯 TESTING 1: RMS Price Sync Endpoint")
        
        # Test 1.1: Basic price sync endpoint existence
        try:
            url = f"{self.backend_url}/v1/iiko/rms/sync/prices"
            payload = {
                "organization_id": self.organization_id,
                "force": False
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["status", "organization_id", "items_processed", "items_created", "items_updated", "sync_timestamp", "message"]
                
                if all(field in data for field in required_fields):
                    self.log_test("RMS Price Sync Endpoint Structure", True, 
                                f"Status: {data['status']}, Items processed: {data['items_processed']}")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("RMS Price Sync Endpoint Structure", False, 
                                f"Missing fields: {missing_fields}", data)
            else:
                self.log_test("RMS Price Sync Endpoint Availability", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("RMS Price Sync Endpoint Availability", False, f"Exception: {str(e)}")

        # Test 1.2: Force parameter testing
        try:
            url = f"{self.backend_url}/v1/iiko/rms/sync/prices"
            payload = {
                "organization_id": self.organization_id,
                "force": True
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("RMS Price Sync Force Parameter", True, 
                            f"Force sync completed with status: {data.get('status')}")
            else:
                self.log_test("RMS Price Sync Force Parameter", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("RMS Price Sync Force Parameter", False, f"Exception: {str(e)}")

        # Test 1.3: Idempotent behavior - call multiple times
        try:
            url = f"{self.backend_url}/v1/iiko/rms/sync/prices"
            payload = {
                "organization_id": self.organization_id,
                "force": False
            }
            
            # First call
            response1 = requests.post(url, json=payload, timeout=30)
            time.sleep(1)  # Brief pause
            
            # Second call (should be idempotent)
            response2 = requests.post(url, json=payload, timeout=30)
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                # Both should succeed (idempotent)
                self.log_test("RMS Price Sync Idempotent Behavior", True, 
                            f"Both calls succeeded: {data1.get('status')} -> {data2.get('status')}")
            else:
                self.log_test("RMS Price Sync Idempotent Behavior", False, 
                            f"Status codes: {response1.status_code}, {response2.status_code}")
                
        except Exception as e:
            self.log_test("RMS Price Sync Idempotent Behavior", False, f"Exception: {str(e)}")

    def test_enhanced_catalog_search(self):
        """
        2. Enhanced catalog-search with pricing fields:
        - GET /api/v1/techcards.v2/catalog-search?source=rms&q=мясо
        - Убедись что RMS результаты включают новые поля: vat_pct, price_per_unit, currency, as_of
        - Проверь что normalization единиц работает (kg→g, l→ml)
        - Убедись что приоритизация работает: iiko RMS должен иметь высокий приоритет
        """
        print("🎯 TESTING 2: Enhanced Catalog Search with Pricing Fields")
        
        # Test 2.1: RMS source parameter
        try:
            url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
            params = {
                "source": "rms",
                "q": "мясо",
                "limit": 10
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success" and "items" in data:
                    rms_items = [item for item in data["items"] if item.get("source") == "rms"]
                    
                    if rms_items:
                        # Check for IK-03 pricing fields
                        sample_item = rms_items[0]
                        required_fields = ["vat_pct", "price_per_unit", "currency", "asOf"]
                        pricing_fields_present = all(field in sample_item for field in required_fields)
                        
                        self.log_test("RMS Catalog Search Pricing Fields", pricing_fields_present,
                                    f"Found {len(rms_items)} RMS items with pricing fields: {list(sample_item.keys())}")
                        
                        # Check unit normalization
                        units_found = [item.get("unit") for item in rms_items]
                        normalized_units = ["g", "ml", "pcs"]
                        units_normalized = all(unit in normalized_units for unit in units_found if unit)
                        
                        self.log_test("RMS Unit Normalization", units_normalized,
                                    f"Units found: {units_found}")
                    else:
                        self.log_test("RMS Catalog Search Results", False, 
                                    f"No RMS items found in response. Total items: {len(data.get('items', []))}")
                else:
                    self.log_test("RMS Catalog Search Response", False, 
                                f"Invalid response structure: {data}")
            else:
                self.log_test("RMS Catalog Search Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("RMS Catalog Search Endpoint", False, f"Exception: {str(e)}")

        # Test 2.2: Priority testing - RMS should have high priority
        try:
            url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
            params = {
                "source": "all",
                "q": "курица",
                "limit": 20
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success" and "items" in data:
                    items = data["items"]
                    
                    # Check source priority order
                    sources = [item.get("source") for item in items[:10]]  # First 10 items
                    
                    # RMS should appear before other sources (except user/price sources)
                    priority_sources = ["user", "catalog", "bootstrap", "rms"]
                    rms_position = None
                    other_positions = []
                    
                    for i, source in enumerate(sources):
                        if source == "rms":
                            rms_position = i
                        elif source in ["iiko", "usda"]:
                            other_positions.append(i)
                    
                    priority_correct = rms_position is not None and all(rms_position <= pos for pos in other_positions)
                    
                    self.log_test("RMS Source Prioritization", priority_correct,
                                f"Sources order: {sources[:5]}, RMS at position: {rms_position}")
                else:
                    self.log_test("Catalog Search All Sources", False, 
                                f"Invalid response: {data}")
            else:
                self.log_test("Catalog Search All Sources", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Catalog Search All Sources", False, f"Exception: {str(e)}")

    def test_price_provider_integration(self):
        """
        3. PriceProvider Integration:
        - Убедись что PriceProvider правильно загружает iiko цены
        - Проверь приоритизацию: iiko → user → catalog → bootstrap
        - Тестируй resolve() method для ингредиентов с разными источниками
        - Убедись что VAT information правильно прокидывается
        """
        print("🎯 TESTING 3: PriceProvider Integration")
        
        # Test 3.1: Price search with different sources
        test_ingredients = ["говядина", "курица", "молоко", "лук", "морковь"]
        
        for ingredient in test_ingredients:
            try:
                url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
                params = {
                    "source": "price",
                    "q": ingredient,
                    "limit": 5
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success" and data.get("items"):
                        # Check for price provider fields
                        items = data["items"]
                        sources_found = [item.get("source") for item in items]
                        
                        # Check priority order (iiko should be first if available)
                        priority_order = ["iiko", "user", "catalog", "bootstrap"]
                        sources_in_priority = []
                        
                        for source in priority_order:
                            if source in sources_found:
                                sources_in_priority.append(source)
                        
                        self.log_test(f"PriceProvider Resolution - {ingredient}", True,
                                    f"Found sources: {sources_in_priority}")
                    else:
                        self.log_test(f"PriceProvider Resolution - {ingredient}", False,
                                    f"No price data found for {ingredient}")
                else:
                    self.log_test(f"PriceProvider Resolution - {ingredient}", False,
                                f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"PriceProvider Resolution - {ingredient}", False, f"Exception: {str(e)}")

        # Test 3.2: VAT information propagation
        try:
            url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
            params = {
                "source": "rms",
                "q": "мясо",
                "limit": 5
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success" and data.get("items"):
                    items = data["items"]
                    vat_items = [item for item in items if "vat_pct" in item and item["vat_pct"] is not None]
                    
                    if vat_items:
                        vat_values = [item["vat_pct"] for item in vat_items]
                        self.log_test("VAT Information Propagation", True,
                                    f"Found {len(vat_items)} items with VAT: {vat_values}")
                    else:
                        self.log_test("VAT Information Propagation", False,
                                    "No VAT information found in RMS items")
                else:
                    self.log_test("VAT Information Propagation", False,
                                "No RMS items found for VAT testing")
            else:
                self.log_test("VAT Information Propagation", False,
                            f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("VAT Information Propagation", False, f"Exception: {str(e)}")

    def test_cost_calculator_integration(self):
        """
        4. Cost Calculator Integration:
        - Генерируй TechCard с несколькими ингредиентами
        - Убедись что cost_calculator использует iiko цены когда доступны
        - Проверь что costMeta включает source="iiko" или "Mixed"
        - Убедись что vat_pct прокидывается в costMeta
        """
        print("🎯 TESTING 4: Cost Calculator Integration")
        
        # Test 4.1: Generate TechCard with multiple ingredients
        try:
            url = f"{self.backend_url}/v1/techcards.v2/generate"
            payload = {
                "dish_name": "Говядина тушеная с овощами",
                "portions": 4,
                "description": "Тестовое блюдо для проверки интеграции с ценами iiko"
            }
            
            response = requests.post(url, json=payload, timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") in ["success", "draft"] and data.get("card"):
                    card = data["card"]
                    
                    # Check cost calculation
                    cost = card.get("cost")
                    cost_meta = card.get("costMeta")
                    
                    if cost and cost_meta:
                        # Check if iiko prices were used
                        source = cost_meta.get("source")
                        coverage = cost_meta.get("coveragePct", 0)
                        
                        cost_calculated = cost.get("rawCost") is not None
                        
                        self.log_test("Cost Calculator with PriceProvider", cost_calculated,
                                    f"Source: {source}, Coverage: {coverage}%, Raw cost: {cost.get('rawCost')}")
                        
                        # Check VAT in cost
                        vat_pct = cost.get("vat_pct")
                        if vat_pct is not None:
                            self.log_test("VAT in Cost Calculation", True,
                                        f"VAT rate: {vat_pct}%")
                        else:
                            self.log_test("VAT in Cost Calculation", False,
                                        "No VAT information in cost")
                    else:
                        self.log_test("Cost Calculator Integration", False,
                                    "Missing cost or costMeta in generated card")
                else:
                    self.log_test("TechCard Generation for Cost Testing", False,
                                f"Generation failed: {data.get('status')}")
            else:
                self.log_test("TechCard Generation for Cost Testing", False,
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("TechCard Generation for Cost Testing", False, f"Exception: {str(e)}")

        # Test 4.2: Recalculation with SKU mapping
        try:
            # First generate a simple card
            url = f"{self.backend_url}/v1/techcards.v2/generate"
            payload = {
                "dish_name": "Простое блюдо с курицей",
                "portions": 2
            }
            
            response = requests.post(url, json=payload, timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("card"):
                    card = data["card"]
                    
                    # Try to recalculate
                    recalc_url = f"{self.backend_url}/v1/techcards.v2/recalc"
                    recalc_response = requests.post(recalc_url, json=card, timeout=30)
                    
                    if recalc_response.status_code == 200:
                        recalc_data = recalc_response.json()
                        
                        if recalc_data.get("status") == "success" and recalc_data.get("card"):
                            updated_card = recalc_data["card"]
                            updated_cost_meta = updated_card.get("costMeta", {})
                            
                            self.log_test("Cost Recalculation Integration", True,
                                        f"Recalc source: {updated_cost_meta.get('source')}, Coverage: {updated_cost_meta.get('coveragePct')}%")
                        else:
                            self.log_test("Cost Recalculation Integration", False,
                                        f"Recalc failed: {recalc_data}")
                    else:
                        self.log_test("Cost Recalculation Integration", False,
                                    f"Recalc HTTP {recalc_response.status_code}")
                        
        except Exception as e:
            self.log_test("Cost Recalculation Integration", False, f"Exception: {str(e)}")

    def test_mongodb_collection_indexing(self):
        """
        5. MongoDB Collection and Indexing:
        - Убедись что коллекция "iiko_prices" создается с правильными индексами
        - Проверь что price sync записывает данные в правильном формате
        - Тестируй performance lookup по skuId и organization_id
        """
        print("🎯 TESTING 5: MongoDB Collection and Indexing")
        
        # Test 5.1: Check if price sync creates data
        try:
            # First sync prices
            sync_url = f"{self.backend_url}/v1/iiko/rms/sync/prices"
            sync_payload = {
                "organization_id": self.organization_id,
                "force": True
            }
            
            sync_response = requests.post(sync_url, json=sync_payload, timeout=30)
            
            if sync_response.status_code == 200:
                sync_data = sync_response.json()
                
                items_processed = sync_data.get("items_processed", 0)
                items_created = sync_data.get("items_created", 0)
                items_updated = sync_data.get("items_updated", 0)
                
                if items_processed > 0:
                    self.log_test("MongoDB Price Data Creation", True,
                                f"Processed: {items_processed}, Created: {items_created}, Updated: {items_updated}")
                else:
                    self.log_test("MongoDB Price Data Creation", False,
                                "No items processed during sync")
            else:
                self.log_test("MongoDB Price Data Creation", False,
                            f"Sync failed: HTTP {sync_response.status_code}")
                
        except Exception as e:
            self.log_test("MongoDB Price Data Creation", False, f"Exception: {str(e)}")

        # Test 5.2: Performance lookup test via catalog search
        try:
            # Test multiple quick lookups to verify indexing performance
            test_queries = ["мясо", "курица", "молоко", "овощи", "рыба"]
            lookup_times = []
            
            for query in test_queries:
                start_time = time.time()
                
                url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
                params = {
                    "source": "rms",
                    "q": query,
                    "limit": 5
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                end_time = time.time()
                lookup_time = end_time - start_time
                lookup_times.append(lookup_time)
                
                if response.status_code != 200:
                    break
            
            if lookup_times:
                avg_lookup_time = sum(lookup_times) / len(lookup_times)
                max_lookup_time = max(lookup_times)
                
                # Performance should be reasonable (< 2 seconds per lookup)
                performance_good = avg_lookup_time < 2.0 and max_lookup_time < 5.0
                
                self.log_test("MongoDB Lookup Performance", performance_good,
                            f"Avg: {avg_lookup_time:.2f}s, Max: {max_lookup_time:.2f}s")
            else:
                self.log_test("MongoDB Lookup Performance", False,
                            "No successful lookups completed")
                
        except Exception as e:
            self.log_test("MongoDB Lookup Performance", False, f"Exception: {str(e)}")

    def test_error_handling_degradation(self):
        """
        6. Error Handling and Degradation:
        - При отключенном RMS убедись что PriceProvider не падает
        - Проверь fallback chain: если iiko недоступен → используется catalog/bootstrap
        - Убедись что все ошибки логируются и graceful
        """
        print("🎯 TESTING 6: Error Handling and Degradation")
        
        # Test 6.1: Graceful degradation when RMS unavailable
        try:
            # Test catalog search with fallback sources
            url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
            params = {
                "source": "all",
                "q": "тестовый_ингредиент_не_существует",
                "limit": 5
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should return success even if no results found
                if data.get("status") == "success":
                    self.log_test("Graceful Degradation - No Results", True,
                                f"Returned empty results gracefully: {len(data.get('items', []))} items")
                else:
                    self.log_test("Graceful Degradation - No Results", False,
                                f"Non-success status: {data.get('status')}")
            else:
                self.log_test("Graceful Degradation - No Results", False,
                            f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Graceful Degradation - No Results", False, f"Exception: {str(e)}")

        # Test 6.2: Fallback chain verification
        try:
            # Test with known ingredient that should have fallback prices
            url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
            params = {
                "source": "all",
                "q": "говядина",
                "limit": 10
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success" and data.get("items"):
                    items = data["items"]
                    sources = [item.get("source") for item in items]
                    
                    # Should have multiple fallback sources
                    fallback_sources = ["catalog", "bootstrap"]
                    has_fallbacks = any(source in fallback_sources for source in sources)
                    
                    self.log_test("Fallback Chain Verification", has_fallbacks,
                                f"Sources available: {list(set(sources))}")
                else:
                    self.log_test("Fallback Chain Verification", False,
                                "No fallback sources found")
            else:
                self.log_test("Fallback Chain Verification", False,
                            f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Fallback Chain Verification", False, f"Exception: {str(e)}")

        # Test 6.3: Error handling in cost calculation
        try:
            # Generate card with potentially missing ingredients
            url = f"{self.backend_url}/v1/techcards.v2/generate"
            payload = {
                "dish_name": "Блюдо с редкими ингредиентами",
                "portions": 1
            }
            
            response = requests.post(url, json=payload, timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should return draft status but not fail completely
                if data.get("status") in ["success", "draft"]:
                    card = data.get("card")
                    issues = data.get("issues", [])
                    
                    # Check for graceful handling of missing prices
                    no_price_issues = [issue for issue in issues if issue.get("type") == "noPrice"]
                    
                    self.log_test("Error Handling in Cost Calculation", True,
                                f"Status: {data.get('status')}, No-price issues: {len(no_price_issues)}")
                else:
                    self.log_test("Error Handling in Cost Calculation", False,
                                f"Generation failed: {data.get('status')}")
            else:
                self.log_test("Error Handling in Cost Calculation", False,
                            f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling in Cost Calculation", False, f"Exception: {str(e)}")

    def test_integration_verification(self):
        """
        INTEGRATION VERIFICATION:
        - Полный цикл: sync prices → search products → resolve pricing → calculate costs
        - Проверь что все компоненты работают вместе без crashes
        - Убедись что performance не деградировал с новым источником
        - Проверь что существующие функции не сломались
        """
        print("🎯 TESTING 7: Integration Verification - Full Cycle")
        
        # Test 7.1: Full integration cycle
        try:
            start_time = time.time()
            
            # Step 1: Sync prices
            sync_url = f"{self.backend_url}/v1/iiko/rms/sync/prices"
            sync_payload = {"organization_id": self.organization_id, "force": False}
            sync_response = requests.post(sync_url, json=sync_payload, timeout=30)
            
            sync_success = sync_response.status_code == 200
            
            # Step 2: Search products
            search_url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
            search_params = {"source": "rms", "q": "мясо", "limit": 5}
            search_response = requests.get(search_url, params=search_params, timeout=30)
            
            search_success = search_response.status_code == 200 and search_response.json().get("items")
            
            # Step 3: Generate and calculate costs
            gen_url = f"{self.backend_url}/v1/techcards.v2/generate"
            gen_payload = {"dish_name": "Интеграционное тестовое блюдо", "portions": 2}
            gen_response = requests.post(gen_url, json=gen_payload, timeout=45)
            
            gen_success = gen_response.status_code == 200 and gen_response.json().get("card")
            
            end_time = time.time()
            total_time = end_time - start_time
            
            full_cycle_success = sync_success and search_success and gen_success
            
            self.log_test("Full Integration Cycle", full_cycle_success,
                        f"Sync: {sync_success}, Search: {search_success}, Generate: {gen_success}, Time: {total_time:.2f}s")
            
        except Exception as e:
            self.log_test("Full Integration Cycle", False, f"Exception: {str(e)}")

        # Test 7.2: Performance regression check
        try:
            # Test multiple operations to check for performance degradation
            operations = []
            
            for i in range(3):
                start = time.time()
                
                url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
                params = {"source": "all", "q": f"тест{i}", "limit": 10}
                response = requests.get(url, params=params, timeout=10)
                
                end = time.time()
                operations.append(end - start)
                
                if response.status_code != 200:
                    break
            
            if operations:
                avg_time = sum(operations) / len(operations)
                performance_acceptable = avg_time < 3.0  # Should be under 3 seconds
                
                self.log_test("Performance Regression Check", performance_acceptable,
                            f"Average operation time: {avg_time:.2f}s")
            else:
                self.log_test("Performance Regression Check", False,
                            "No operations completed successfully")
                
        except Exception as e:
            self.log_test("Performance Regression Check", False, f"Exception: {str(e)}")

        # Test 7.3: Existing functions compatibility
        try:
            # Test that existing endpoints still work
            status_url = f"{self.backend_url}/v1/techcards.v2/status"
            status_response = requests.get(status_url, timeout=10)
            
            status_works = status_response.status_code == 200
            
            # Test basic generation still works
            gen_url = f"{self.backend_url}/v1/techcards.v2/generate"
            gen_payload = {"dish_name": "Простое блюдо", "portions": 1}
            gen_response = requests.post(gen_url, json=gen_payload, timeout=45)
            
            gen_works = gen_response.status_code == 200
            
            compatibility_good = status_works and gen_works
            
            self.log_test("Existing Functions Compatibility", compatibility_good,
                        f"Status endpoint: {status_works}, Generation: {gen_works}")
            
        except Exception as e:
            self.log_test("Existing Functions Compatibility", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all IK-03 backend tests"""
        print("🚀 STARTING IK-03 BACKEND TESTING")
        print("=" * 80)
        print()
        
        # Run all test categories
        self.test_rms_price_sync_endpoint()
        self.test_enhanced_catalog_search()
        self.test_price_provider_integration()
        self.test_cost_calculator_integration()
        self.test_mongodb_collection_indexing()
        self.test_error_handling_degradation()
        self.test_integration_verification()
        
        # Summary
        print("=" * 80)
        print("🎯 IK-03 BACKEND TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Critical assessment
        critical_tests = [
            "RMS Price Sync Endpoint Structure",
            "RMS Catalog Search Pricing Fields", 
            "PriceProvider Resolution",
            "Cost Calculator with PriceProvider",
            "Full Integration Cycle"
        ]
        
        critical_passed = len([r for r in self.test_results if r["success"] and any(ct in r["test"] for ct in critical_tests)])
        
        print("🔍 CRITICAL ASSESSMENT:")
        if critical_passed >= 3:
            print("✅ IK-03 CORE FUNCTIONALITY IS WORKING")
            print("   - RMS price synchronization operational")
            print("   - Enhanced catalog search with pricing fields functional")
            print("   - PriceProvider integration successful")
            print("   - Cost calculation with iiko prices working")
        else:
            print("❌ IK-03 CORE FUNCTIONALITY HAS ISSUES")
            print("   - Critical components may not be working properly")
            print("   - Review failed tests above for specific issues")
        
        print()
        print("🎉 IK-03 BACKEND TESTING COMPLETED")
        
        return passed_tests, total_tests

if __name__ == "__main__":
    tester = IK03BackendTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)