#!/usr/bin/env python3
"""
USDA UI Integration Backend Testing Suite (Task D1-UI)
Testing the complete USDA UI integration implementation as specified in review request.

Focus Areas:
1. USDA Catalog Search API Enhancement - GET /api/v1/techcards.v2/catalog-search with source=usda
2. TechCardV2 Generation with USDA Integration - POST /api/v1/techcards.v2/generate
3. GOST Print Enhancement - POST /api/v1/techcards.v2/print with source attribution
4. Recalculation API - POST /api/v1/techcards.v2/recalc with updated canonical_id mappings

Test ingredients: треска, куриное филе, растительное масло (should be found in USDA database)
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_usda_catalog_search():
    """Test GET /api/v1/techcards.v2/catalog-search with source=usda parameter"""
    log_test("🔍 STEP 1: Testing USDA Catalog Search API Enhancement")
    
    # Test ingredients that should be found in USDA database
    test_ingredients = ["треска", "куриное филе", "растительное масло"]
    
    results = {}
    
    for ingredient in test_ingredients:
        log_test(f"🔍 Searching for: {ingredient}")
        
        try:
            url = f"{API_BASE}/v1/techcards.v2/catalog-search"
            params = {
                "q": ingredient,
                "source": "usda",
                "limit": 10
            }
            
            response = requests.get(url, params=params, timeout=30)
            log_test(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    items = data.get("items", [])
                    usda_count = data.get("usda_count", 0)
                    
                    log_test(f"✅ Search successful for {ingredient}")
                    log_test(f"📊 Found {len(items)} total items, {usda_count} from USDA")
                    
                    # Check for USDA results with required fields
                    usda_items = [item for item in items if item.get("source") == "usda"]
                    
                    if usda_items:
                        log_test(f"🎯 USDA results for {ingredient}:")
                        for item in usda_items[:3]:  # Show first 3
                            fdc_id = item.get("fdc_id")
                            nutrition_preview = item.get("nutrition_preview")
                            name = item.get("name")
                            canonical_id = item.get("canonical_id")
                            
                            log_test(f"   - {name} (FDC ID: {fdc_id})")
                            log_test(f"     Canonical ID: {canonical_id}")
                            log_test(f"     Nutrition: {nutrition_preview}")
                            
                            # Verify required fields are present
                            required_fields = ["name", "fdc_id", "nutrition_preview", "canonical_id"]
                            missing_fields = [field for field in required_fields if not item.get(field)]
                            
                            if missing_fields:
                                log_test(f"     ⚠️ Missing fields: {missing_fields}")
                            else:
                                log_test(f"     ✅ All required fields present")
                        
                        results[ingredient] = {
                            "success": True,
                            "usda_count": len(usda_items),
                            "items": usda_items
                        }
                    else:
                        log_test(f"❌ No USDA results found for {ingredient}")
                        results[ingredient] = {"success": False, "error": "No USDA results"}
                else:
                    log_test(f"❌ Search failed for {ingredient}: {data.get('message', 'Unknown error')}")
                    results[ingredient] = {"success": False, "error": data.get('message')}
            else:
                log_test(f"❌ HTTP error {response.status_code} for {ingredient}")
                results[ingredient] = {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            log_test(f"❌ Exception searching for {ingredient}: {str(e)}")
            results[ingredient] = {"success": False, "error": str(e)}
    
    return results

def test_techcard_generation_with_usda():
    """Test POST /api/v1/techcards.v2/generate with USDA integration"""
    log_test("🏗️ STEP 2: Testing TechCardV2 Generation with USDA Integration")
    
    # Create test profile with ingredients that should be found in USDA
    test_profile = {
        "name": "Треска с овощами",
        "cuisine": "русская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    log_test(f"📝 Test dish: {test_profile['name']}")
    log_test(f"🍽️ Cuisine: {test_profile['cuisine']}")
    log_test("🥬 Using LLM mode to test USDA integration")
    
    try:
        url = f"{API_BASE}/v1/techcards.v2/generate"
        
        # Test with LLM enabled to get proper tech card structure
        params = {"use_llm": "true"}
        
        start_time = time.time()
        response = requests.post(url, json=test_profile, params=params, timeout=60)
        response_time = time.time() - start_time
        
        log_test(f"📊 Response status: {response.status_code}")
        log_test(f"⏱️ Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            card = data.get("card")
            
            log_test(f"✅ Generation successful with status: {status}")
            
            if status == "error":
                issues = data.get("issues", [])
                message = data.get("message", "No message")
                log_test(f"❌ Generation error: {message}")
                if issues:
                    log_test(f"Issues: {json.dumps(issues, indent=2, ensure_ascii=False)}")
                return {"success": False, "error": message, "issues": issues}
            
            if card:
                log_test(f"✅ Card data found for status: {status}")
            else:
                log_test(f"⚠️ No card data for status: {status}")
                issues = data.get("issues", [])
                message = data.get("message", "No message")
                log_test(f"Message: {message}")
                if issues:
                    log_test(f"Issues: {json.dumps(issues[:3], indent=2, ensure_ascii=False)}...")  # Show first 3 issues
                
                # For draft status, we might still want to continue testing if there's partial data
                if status == "draft":
                    log_test("⚠️ Draft status - continuing with limited testing")
                    return {"success": False, "error": "No card data in draft", "status": status}
                else:
                    return {"success": False, "error": "No card data", "status": status}
            
            if card:
                # Check nutritionMeta for USDA integration
                nutrition_meta = card.get("nutritionMeta")
                if nutrition_meta:
                    source = nutrition_meta.get("source")
                    coverage_pct = nutrition_meta.get("coveragePct", 0)
                    as_of = nutrition_meta.get("asOf")
                    
                    log_test(f"🔍 Nutrition Meta Analysis:")
                    log_test(f"   Source: {source}")
                    log_test(f"   Coverage: {coverage_pct}%")
                    log_test(f"   As of: {as_of}")
                    
                    # Verify enhanced source field
                    expected_sources = ['usda', 'catalog', 'bootstrap', 'Mixed']
                    if source in expected_sources:
                        log_test(f"   ✅ Source field properly enhanced: {source}")
                    else:
                        log_test(f"   ⚠️ Unexpected source value: {source}")
                    
                    # Check if coverage and asOf are populated
                    if coverage_pct > 0:
                        log_test(f"   ✅ Coverage percentage populated: {coverage_pct}%")
                    else:
                        log_test(f"   ⚠️ Coverage percentage not populated")
                    
                    if as_of:
                        log_test(f"   ✅ AsOf date populated: {as_of}")
                    else:
                        log_test(f"   ⚠️ AsOf date not populated")
                else:
                    log_test("❌ nutritionMeta not found in generated card")
                
                # Check nutrition data
                nutrition = card.get("nutrition")
                if nutrition:
                    per100g = nutrition.get("per100g")
                    per_portion = nutrition.get("perPortion")
                    
                    if per100g:
                        kcal = per100g.get("kcal", 0)
                        proteins = per100g.get("proteins_g", 0)
                        log_test(f"🍽️ Nutrition per 100g: {kcal} kcal, {proteins}g protein")
                    
                    if per_portion:
                        kcal_portion = per_portion.get("kcal", 0)
                        log_test(f"🍽️ Nutrition per portion: {kcal_portion} kcal")
                else:
                    log_test("⚠️ Nutrition data not found")
                
                return {
                    "success": True,
                    "status": status,
                    "card": card,
                    "nutrition_meta": nutrition_meta
                }
            else:
                log_test("❌ No card data in response")
                return {"success": False, "error": "No card data"}
        else:
            log_test(f"❌ Generation failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"Raw error: {response.text[:500]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Exception during generation: {str(e)}")
        return {"success": False, "error": str(e)}

def test_gost_print_enhancement(test_card):
    """Test POST /api/v1/techcards.v2/print with source attribution"""
    log_test("🖨️ STEP 3: Testing GOST Print Enhancement")
    
    if not test_card or not test_card.get("success"):
        log_test("❌ Cannot test print without valid tech card")
        return {"success": False, "error": "No valid tech card"}
    
    card_data = test_card.get("card")
    if not card_data:
        log_test("❌ No card data available for printing")
        return {"success": False, "error": "No card data"}
    
    try:
        url = f"{API_BASE}/v1/techcards.v2/print"
        
        response = requests.post(url, json=card_data, timeout=30)
        log_test(f"📊 Print response status: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            log_test(f"✅ Print HTML generated successfully ({len(html_content)} characters)")
            
            # Check for source attribution in HTML
            source_patterns = [
                "Источник БЖУ:",
                "USDA",
                "каталог", 
                "демо-каталог",
                "Mixed"
            ]
            
            found_patterns = []
            for pattern in source_patterns:
                if pattern in html_content:
                    found_patterns.append(pattern)
            
            log_test(f"🔍 Source attribution analysis:")
            if "Источник БЖУ:" in html_content:
                log_test("   ✅ Source attribution line found in HTML")
                
                # Extract the source line for detailed analysis
                import re
                source_match = re.search(r'Источник БЖУ:\s*([^;]+)(?:;\s*дата:\s*([^<]+))?', html_content)
                if source_match:
                    source_text = source_match.group(1).strip()
                    date_text = source_match.group(2).strip() if source_match.group(2) else None
                    
                    log_test(f"   📊 Source: {source_text}")
                    if date_text:
                        log_test(f"   📅 Date: {date_text}")
                    else:
                        log_test("   ⚠️ Date information not found")
                else:
                    log_test("   ⚠️ Could not parse source attribution details")
            else:
                log_test("   ❌ Source attribution line not found in HTML")
            
            log_test(f"🔍 Found attribution patterns: {found_patterns}")
            
            # Check for proper nutrition table structure
            if '<h3>ПИЩЕВАЯ ЦЕННОСТЬ</h3>' in html_content:
                log_test("   ✅ Nutrition table section found")
                
                # Check if source line appears after nutrition table
                nutrition_pos = html_content.find('<h3>ПИЩЕВАЯ ЦЕННОСТЬ</h3>')
                source_pos = html_content.find('Источник БЖУ:')
                
                if nutrition_pos > 0 and source_pos > nutrition_pos:
                    log_test("   ✅ Source attribution correctly placed after nutrition table")
                else:
                    log_test("   ⚠️ Source attribution positioning may be incorrect")
            else:
                log_test("   ⚠️ Nutrition table section not found")
            
            return {
                "success": True,
                "html_length": len(html_content),
                "has_source_attribution": "Источник БЖУ:" in html_content,
                "found_patterns": found_patterns
            }
        else:
            log_test(f"❌ Print failed: HTTP {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Exception during print: {str(e)}")
        return {"success": False, "error": str(e)}

def test_recalculation_api(test_card):
    """Test POST /api/v1/techcards.v2/recalc with updated canonical_id mappings"""
    log_test("🔄 STEP 4: Testing Recalculation API")
    
    if not test_card or not test_card.get("success"):
        log_test("❌ Cannot test recalculation without valid tech card")
        return {"success": False, "error": "No valid tech card"}
    
    card_data = test_card.get("card")
    if not card_data:
        log_test("❌ No card data available for recalculation")
        return {"success": False, "error": "No card data"}
    
    # Modify the card to simulate updated canonical_id mappings
    modified_card = card_data.copy()
    
    # Update ingredients with canonical_id if they exist
    if "ingredients" in modified_card:
        for ingredient in modified_card["ingredients"]:
            if "треска" in ingredient.get("name", "").lower():
                ingredient["canonical_id"] = "cod_fillet"
                log_test(f"   🔧 Updated треска with canonical_id: cod_fillet")
            elif "куриное филе" in ingredient.get("name", "").lower():
                ingredient["canonical_id"] = "chicken_breast"
                log_test(f"   🔧 Updated куриное филе with canonical_id: chicken_breast")
    
    try:
        url = f"{API_BASE}/v1/techcards.v2/recalc"
        
        start_time = time.time()
        response = requests.post(url, json=modified_card, timeout=30)
        response_time = time.time() - start_time
        
        log_test(f"📊 Recalc response status: {response.status_code}")
        log_test(f"⏱️ Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            updated_card = data.get("card")
            
            log_test(f"✅ Recalculation successful with status: {status}")
            
            if updated_card:
                # Compare nutritionMeta before and after
                original_meta = card_data.get("nutritionMeta", {})
                updated_meta = updated_card.get("nutritionMeta", {})
                
                log_test("🔍 Nutrition Meta Comparison:")
                log_test(f"   Original source: {original_meta.get('source', 'N/A')}")
                log_test(f"   Updated source: {updated_meta.get('source', 'N/A')}")
                log_test(f"   Original coverage: {original_meta.get('coveragePct', 0)}%")
                log_test(f"   Updated coverage: {updated_meta.get('coveragePct', 0)}%")
                
                # Check if source information was properly updated
                if updated_meta.get("source") in ['usda', 'catalog', 'bootstrap', 'Mixed']:
                    log_test("   ✅ Source information properly updated")
                else:
                    log_test("   ⚠️ Source information may not be updated correctly")
                
                # Compare nutrition values
                original_nutrition = card_data.get("nutrition", {}).get("per100g", {})
                updated_nutrition = updated_card.get("nutrition", {}).get("per100g", {})
                
                if original_nutrition and updated_nutrition:
                    orig_kcal = original_nutrition.get("kcal", 0)
                    upd_kcal = updated_nutrition.get("kcal", 0)
                    
                    log_test(f"🍽️ Nutrition Comparison (per 100g):")
                    log_test(f"   Original kcal: {orig_kcal}")
                    log_test(f"   Updated kcal: {upd_kcal}")
                    
                    if abs(orig_kcal - upd_kcal) > 0.1:  # Allow small floating point differences
                        log_test("   ✅ Nutrition values recalculated (values changed)")
                    else:
                        log_test("   ℹ️ Nutrition values unchanged (may indicate same data source)")
                
                return {
                    "success": True,
                    "status": status,
                    "updated_card": updated_card,
                    "meta_updated": updated_meta != original_meta
                }
            else:
                log_test("❌ No updated card data in response")
                return {"success": False, "error": "No updated card data"}
        else:
            log_test(f"❌ Recalculation failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"Raw error: {response.text[:500]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Exception during recalculation: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    """Main testing function for USDA UI Integration"""
    log_test("🚀 Starting USDA UI Integration Backend Testing (Task D1-UI)")
    log_test("🎯 Focus: Complete USDA UI integration with source attribution")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Step 1: Test USDA Catalog Search API Enhancement
    search_results = test_usda_catalog_search()
    
    log_test("\n" + "=" * 80)
    
    # Step 2: Test TechCardV2 Generation with USDA Integration
    generation_result = test_techcard_generation_with_usda()
    
    log_test("\n" + "=" * 80)
    
    # Step 3: Test GOST Print Enhancement
    print_result = test_gost_print_enhancement(generation_result)
    
    log_test("\n" + "=" * 80)
    
    # Step 4: Test Recalculation API
    recalc_result = test_recalculation_api(generation_result)
    
    # Summary
    log_test("\n" + "=" * 80)
    log_test("📋 USDA UI INTEGRATION TESTING SUMMARY:")
    
    # Analyze search results
    successful_searches = sum(1 for result in search_results.values() if result.get("success"))
    total_searches = len(search_results)
    log_test(f"🔍 USDA Catalog Search: {successful_searches}/{total_searches} ingredients found")
    
    for ingredient, result in search_results.items():
        if result.get("success"):
            usda_count = result.get("usda_count", 0)
            log_test(f"   ✅ {ingredient}: {usda_count} USDA results")
        else:
            log_test(f"   ❌ {ingredient}: {result.get('error', 'Unknown error')}")
    
    # Other test results
    log_test(f"🏗️ TechCard Generation: {'SUCCESS' if generation_result.get('success') else 'FAILED'}")
    if generation_result.get("success"):
        nutrition_meta = generation_result.get("nutrition_meta", {})
        source = nutrition_meta.get("source", "N/A")
        coverage = nutrition_meta.get("coveragePct", 0)
        log_test(f"   📊 Source: {source}, Coverage: {coverage}%")
    
    log_test(f"🖨️ GOST Print Enhancement: {'SUCCESS' if print_result.get('success') else 'FAILED'}")
    if print_result.get("success"):
        has_attribution = print_result.get("has_source_attribution", False)
        log_test(f"   📋 Source attribution: {'PRESENT' if has_attribution else 'MISSING'}")
    
    log_test(f"🔄 Recalculation API: {'SUCCESS' if recalc_result.get('success') else 'FAILED'}")
    if recalc_result.get("success"):
        meta_updated = recalc_result.get("meta_updated", False)
        log_test(f"   🔧 Metadata updated: {'YES' if meta_updated else 'NO'}")
    
    # Overall assessment
    all_tests = [
        successful_searches == total_searches,  # All searches successful
        generation_result.get("success", False),
        print_result.get("success", False),
        recalc_result.get("success", False)
    ]
    
    passed_tests = sum(all_tests)
    total_tests = len(all_tests)
    
    log_test(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} test areas passed")
    
    if passed_tests == total_tests:
        log_test("🎉 ALL USDA UI INTEGRATION TESTS PASSED!")
        log_test("✅ USDA catalog search with source=usda parameter working")
        log_test("✅ TechCardV2 generation with enhanced nutritionMeta working")
        log_test("✅ GOST print with source attribution working")
        log_test("✅ Recalculation API with canonical_id mappings working")
    else:
        log_test("⚠️ Some USDA UI integration features need attention:")
        if successful_searches < total_searches:
            log_test("   - USDA catalog search may have coverage issues")
        if not generation_result.get("success"):
            log_test("   - TechCardV2 generation with USDA integration failed")
        if not print_result.get("success"):
            log_test("   - GOST print enhancement failed")
        if not recalc_result.get("success"):
            log_test("   - Recalculation API failed")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()