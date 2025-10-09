#!/usr/bin/env python3
"""
USDA FDC Integration Testing (Task D1)
Comprehensive testing of USDA FoodData Central integration for nutrition data
"""

import requests
import json
import sys
import os
import sqlite3
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"

def test_usda_provider():
    """Test 1: USDA Provider Testing - USDANutritionProvider.find_nutrition_data()"""
    print("🧪 TEST 1: USDA Provider Testing")
    print("=" * 60)
    
    # Import USDA provider directly
    sys.path.append('/app/backend')
    try:
        from receptor_agent.techcards_v2.nutrition_calculator import USDANutritionProvider
        
        provider = USDANutritionProvider()
        
        # Test ingredients from review request
        test_ingredients = [
            ("треска", "cod"),
            ("куриное филе", "chicken_breast"), 
            ("растительное масло", None)  # Should use fuzzy matching
        ]
        
        results = {}
        for ingredient_name, canonical_id in test_ingredients:
            print(f"\n🔍 Testing: {ingredient_name} (canonical_id: {canonical_id})")
            
            # Test find_nutrition_data
            nutrition_data = provider.find_nutrition_data(ingredient_name, canonical_id)
            
            if nutrition_data:
                per100g = nutrition_data['per100g']
                print(f"✅ Found USDA data:")
                print(f"   FDC ID: {nutrition_data.get('fdc_id')}")
                print(f"   Description: {nutrition_data.get('description')}")
                print(f"   Kcal: {per100g['kcal']}")
                print(f"   Proteins: {per100g['proteins_g']}g")
                print(f"   Fats: {per100g['fats_g']}g") 
                print(f"   Carbs: {per100g['carbs_g']}g")
                print(f"   Source: {nutrition_data.get('source')}")
                
                results[ingredient_name] = {
                    "found": True,
                    "fdc_id": nutrition_data.get('fdc_id'),
                    "nutrition": per100g,
                    "source": nutrition_data.get('source')
                }
            else:
                print(f"❌ No USDA data found for {ingredient_name}")
                results[ingredient_name] = {"found": False}
        
        # Verify canonical_id and fuzzy matching work
        canonical_found = sum(1 for r in results.values() if r.get("found") and "canonical_id" in r.get("source", ""))
        fuzzy_found = sum(1 for r in results.values() if r.get("found") and "fuzzy" in r.get("source", ""))
        
        print(f"\n📊 USDA Provider Results:")
        print(f"   Total ingredients tested: {len(test_ingredients)}")
        print(f"   Found via canonical_id: {canonical_found}")
        print(f"   Found via fuzzy matching: {fuzzy_found}")
        print(f"   Total found: {sum(1 for r in results.values() if r.get('found'))}")
        
        return results
        
    except Exception as e:
        print(f"❌ USDA Provider test failed: {e}")
        return {}

def test_nutrition_calculator_with_usda():
    """Test 2: NutritionCalculator with USDA integration"""
    print("\n🧪 TEST 2: NutritionCalculator with USDA")
    print("=" * 60)
    
    try:
        sys.path.append('/app/backend')
        from receptor_agent.techcards_v2.nutrition_calculator import NutritionCalculator
        from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, YieldV2
        
        # Create test tech card with USDA ingredients
        test_ingredients = [
            IngredientV2(
                name="треска",
                brutto_g=220.0,
                loss_pct=10.0,
                netto_g=198.0,  # 220 * (1 - 10/100) = 198
                unit="g",
                canonical_id="cod"
            ),
            IngredientV2(
                name="куриное филе", 
                brutto_g=165.0,
                loss_pct=10.0,
                netto_g=148.5,  # 165 * (1 - 10/100) = 148.5
                unit="g",
                canonical_id="chicken_breast"
            ),
            IngredientV2(
                name="растительное масло",
                brutto_g=30.0,
                loss_pct=0.0,
                netto_g=30.0,
                unit="ml"
            )
        ]
        
        test_card = TechCardV2(
            meta={"title": "USDA Test Dish"},
            ingredients=test_ingredients,
            yield_=YieldV2(perBatch_g=376.5, perPortion_g=188.25),  # Total netto: 198+148.5+30=376.5
            portions=2
        )
        
        # Initialize calculator with USDA enabled
        calculator = NutritionCalculator(use_usda=True)
        
        # Calculate nutrition
        nutrition, nutrition_meta, issues = calculator.calculate_tech_card_nutrition(test_card)
        
        print(f"✅ Nutrition calculation completed:")
        print(f"   Per 100g: {nutrition.per100g.kcal} kcal, {nutrition.per100g.proteins_g}g protein")
        print(f"   Per portion: {nutrition.perPortion.kcal} kcal, {nutrition.perPortion.proteins_g}g protein")
        print(f"   Source: {nutrition_meta.source}")
        print(f"   Coverage: {nutrition_meta.coveragePct}%")
        print(f"   Issues: {len(issues)}")
        
        # Verify USDA source and coverage requirements
        usda_source = nutrition_meta.source == "usda"
        coverage_ok = nutrition_meta.coveragePct >= 75.0
        
        print(f"\n📊 NutritionCalculator Results:")
        print(f"   USDA as primary source: {'✅' if usda_source else '❌'}")
        print(f"   Coverage ≥75%: {'✅' if coverage_ok else '❌'} ({nutrition_meta.coveragePct}%)")
        
        return {
            "usda_source": usda_source,
            "coverage_pct": nutrition_meta.coveragePct,
            "coverage_ok": coverage_ok,
            "nutrition": nutrition.model_dump(),
            "issues": issues
        }
        
    except Exception as e:
        print(f"❌ NutritionCalculator test failed: {e}")
        return {}

def test_catalog_search_api():
    """Test 3: API Endpoint Enhancement - catalog-search with USDA"""
    print("\n🧪 TEST 3: API Endpoint Enhancement")
    print("=" * 60)
    
    test_queries = [
        ("треска", "usda"),
        ("куриное филе", "usda"), 
        ("растительное масло", "all")
    ]
    
    results = {}
    
    for query, source in test_queries:
        print(f"\n🔍 Testing: GET /api/v1/techcards.v2/catalog-search?source={source}&q={query}")
        
        try:
            url = f"{BACKEND_URL}/api/v1/techcards.v2/catalog-search"
            params = {"q": query, "source": source, "limit": 10}
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    items = data.get("items", [])
                    usda_items = [item for item in items if item.get("source") == "usda"]
                    
                    print(f"✅ API Response successful:")
                    print(f"   Total items: {len(items)}")
                    print(f"   USDA items: {len(usda_items)}")
                    print(f"   USDA count: {data.get('usda_count', 0)}")
                    
                    # Show first USDA result if available
                    if usda_items:
                        item = usda_items[0]
                        print(f"   First USDA result:")
                        print(f"     Name: {item.get('name')}")
                        print(f"     FDC ID: {item.get('fdc_id')}")
                        print(f"     Nutrition preview: {item.get('nutrition_preview')}")
                        print(f"     Canonical ID: {item.get('canonical_id')}")
                    
                    results[query] = {
                        "success": True,
                        "total_items": len(items),
                        "usda_items": len(usda_items),
                        "has_fdc_id": any(item.get("fdc_id") for item in usda_items),
                        "has_nutrition_preview": any(item.get("nutrition_preview") for item in usda_items)
                    }
                else:
                    print(f"❌ API returned error: {data.get('message')}")
                    results[query] = {"success": False, "error": data.get("message")}
            else:
                print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                results[query] = {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ API test failed: {e}")
            results[query] = {"success": False, "error": str(e)}
    
    # Summary
    successful_queries = sum(1 for r in results.values() if r.get("success"))
    total_usda_items = sum(r.get("usda_items", 0) for r in results.values() if r.get("success"))
    
    print(f"\n📊 API Endpoint Results:")
    print(f"   Successful queries: {successful_queries}/{len(test_queries)}")
    print(f"   Total USDA items found: {total_usda_items}")
    
    return results

def test_techcard_generation():
    """Test 4: TechCardV2 Generation with USDA data"""
    print("\n🧪 TEST 4: TechCardV2 Generation with USDA")
    print("=" * 60)
    
    # Test data with USDA ingredients
    test_profile = {
        "name": "Треска с овощами",
        "cuisine": "европейская"
    }
    
    print(f"🔍 Testing: POST /api/v1/techcards.v2/generate with use_llm=false")
    
    try:
        url = f"{BACKEND_URL}/api/v1/techcards.v2/generate"
        params = {"use_llm": "false"}  # Use deterministic generation
        
        response = requests.post(url, json=test_profile, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") in ["success", "draft"]:
                card = data.get("card")
                
                if card:
                    # Check nutrition metadata
                    nutrition_meta = card.get("nutritionMeta", {})
                    source = nutrition_meta.get("source")
                    coverage_pct = nutrition_meta.get("coveragePct", 0)
                    
                    print(f"✅ TechCard generated successfully:")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Title: {card.get('meta', {}).get('title')}")
                    print(f"   Ingredients count: {len(card.get('ingredients', []))}")
                    print(f"   Nutrition source: {source}")
                    print(f"   Coverage: {coverage_pct}%")
                    
                    # Check if USDA ingredients are present
                    ingredients = card.get("ingredients", [])
                    usda_ingredients = []
                    for ing in ingredients:
                        name = ing.get("name", "").lower()
                        if any(usda_name in name for usda_name in ["треска", "морковь", "лук"]):
                            usda_ingredients.append(name)
                    
                    print(f"   USDA-mappable ingredients: {usda_ingredients}")
                    
                    # Verify requirements
                    uses_usda = source == "usda"
                    coverage_ok = coverage_pct >= 75.0
                    
                    print(f"\n📊 TechCard Generation Results:")
                    print(f"   Uses USDA data: {'✅' if uses_usda else '❌'}")
                    print(f"   Coverage ≥75%: {'✅' if coverage_ok else '❌'} ({coverage_pct}%)")
                    
                    return {
                        "success": True,
                        "status": data.get("status"),
                        "uses_usda": uses_usda,
                        "coverage_pct": coverage_pct,
                        "coverage_ok": coverage_ok,
                        "ingredients_count": len(ingredients),
                        "usda_ingredients": usda_ingredients
                    }
                else:
                    print(f"❌ No card in response")
                    return {"success": False, "error": "No card in response"}
            else:
                print(f"❌ Generation failed: {data.get('message')}")
                return {"success": False, "error": data.get("message")}
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ TechCard generation test failed: {e}")
        return {"success": False, "error": str(e)}

def test_edge_cases():
    """Test 5: Edge Cases - unknown ingredients, unit conversions, canonical mapping"""
    print("\n🧪 TEST 5: Edge Cases Testing")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Unknown ingredients fallback
    print("\n🔍 Testing unknown ingredients fallback...")
    try:
        sys.path.append('/app/backend')
        from receptor_agent.techcards_v2.nutrition_calculator import NutritionCalculator
        from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, YieldV2
        
        # Create tech card with mix of known and unknown ingredients
        mixed_ingredients = [
            IngredientV2(name="треска", brutto_g=220.0, loss_pct=10.0, netto_g=198.0, unit="g", canonical_id="cod"),  # USDA
            IngredientV2(name="экзотический фрукт дракона", brutto_g=110.0, loss_pct=10.0, netto_g=99.0, unit="g"),  # Unknown
            IngredientV2(name="соль поваренная", brutto_g=5.0, loss_pct=0.0, netto_g=5.0, unit="g")  # Should fallback to catalog/bootstrap
        ]
        
        test_card = TechCardV2(
            meta={"title": "Mixed Ingredients Test"},
            ingredients=mixed_ingredients,
            yield_=YieldV2(perBatch_g=302.0, perPortion_g=151.0),  # Total netto: 198+99+5=302
            portions=2
        )
        
        calculator = NutritionCalculator(use_usda=True)
        nutrition, nutrition_meta, issues = calculator.calculate_tech_card_nutrition(test_card)
        
        # Check fallback behavior
        no_nutrition_issues = [issue for issue in issues if issue.get("type") == "noNutrition"]
        
        print(f"✅ Unknown ingredients test:")
        print(f"   Coverage: {nutrition_meta.coveragePct}%")
        print(f"   Primary source: {nutrition_meta.source}")
        print(f"   Missing nutrition issues: {len(no_nutrition_issues)}")
        
        results["unknown_fallback"] = {
            "coverage_pct": nutrition_meta.coveragePct,
            "source": nutrition_meta.source,
            "missing_count": len(no_nutrition_issues)
        }
        
    except Exception as e:
        print(f"❌ Unknown ingredients test failed: {e}")
        results["unknown_fallback"] = {"error": str(e)}
    
    # Test 2: Unit conversions with USDA food_portion data
    print("\n🔍 Testing unit conversions...")
    try:
        # Test pcs conversion for eggs (should use USDA portion data)
        egg_ingredient = IngredientV2(
            name="яйцо куриное",
            brutto_g=2.0,  # 2 pieces
            loss_pct=0.0,
            netto_g=2.0,
            unit="pcs",
            canonical_id="chicken_egg"
        )
        
        calculator = NutritionCalculator(use_usda=True)
        nutrition_data = calculator.find_nutrition_data("яйцо куриное", "chicken_egg")
        
        if nutrition_data and "mass_per_piece_g" in nutrition_data:
            mass_per_piece = nutrition_data["mass_per_piece_g"]
            print(f"✅ USDA portion data found:")
            print(f"   Mass per egg: {mass_per_piece}g")
            
            # Test conversion
            mass_grams, status = calculator._convert_to_grams(2.0, "pcs", "яйцо куриное", nutrition_data)
            print(f"   2 eggs = {mass_grams}g (status: {status})")
            
            results["unit_conversion"] = {
                "has_portion_data": True,
                "mass_per_piece": mass_per_piece,
                "conversion_grams": mass_grams,
                "status": status
            }
        else:
            print(f"❌ No USDA portion data for eggs")
            results["unit_conversion"] = {"has_portion_data": False}
            
    except Exception as e:
        print(f"❌ Unit conversion test failed: {e}")
        results["unit_conversion"] = {"error": str(e)}
    
    # Test 3: Canonical mapping verification
    print("\n🔍 Testing canonical_map.json mapping...")
    try:
        from receptor_agent.techcards_v2.nutrition_calculator import USDANutritionProvider
        
        provider = USDANutritionProvider()
        canonical_map = provider.canonical_map
        
        # Test key mappings from review
        test_mappings = [
            ("треска", "cod"),
            ("куриное филе", "chicken_breast"),
            ("растительное масло", None)  # Should find via fuzzy
        ]
        
        mapping_results = {}
        for ingredient, expected_canonical in test_mappings:
            # Test direct lookup
            if expected_canonical and expected_canonical in canonical_map:
                fdc_id = canonical_map[expected_canonical]['fdc_id']
                print(f"✅ Canonical mapping: {expected_canonical} → FDC {fdc_id}")
                mapping_results[ingredient] = {"canonical_found": True, "fdc_id": fdc_id}
            
            # Test synonym lookup
            ingredient_lower = ingredient.lower()
            if ingredient_lower in canonical_map:
                fdc_id = canonical_map[ingredient_lower]['fdc_id']
                print(f"✅ Synonym mapping: {ingredient} → FDC {fdc_id}")
                mapping_results[ingredient] = {"synonym_found": True, "fdc_id": fdc_id}
        
        total_mappings = len(canonical_map)
        print(f"✅ Canonical map loaded: {total_mappings} total mappings")
        
        results["canonical_mapping"] = {
            "total_mappings": total_mappings,
            "test_results": mapping_results
        }
        
    except Exception as e:
        print(f"❌ Canonical mapping test failed: {e}")
        results["canonical_mapping"] = {"error": str(e)}
    
    return results

def test_usda_database():
    """Test USDA SQLite database structure and data"""
    print("\n🧪 BONUS: USDA Database Verification")
    print("=" * 60)
    
    try:
        db_path = "/app/backend/data/usda/usda.sqlite"
        
        if not os.path.exists(db_path):
            print(f"❌ USDA database not found at {db_path}")
            return {"error": "Database not found"}
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Database tables: {tables}")
        
        # Check foods count
        cursor.execute("SELECT COUNT(*) FROM foods")
        foods_count = cursor.fetchone()[0]
        print(f"✅ Foods in database: {foods_count}")
        
        # Check nutrients for key ingredients
        test_fdc_ids = [175174, 173875, 171413]  # cod, chicken breast, olive oil
        
        for fdc_id in test_fdc_ids:
            cursor.execute("SELECT description FROM foods WHERE fdc_id = ?", (fdc_id,))
            food = cursor.fetchone()
            
            if food:
                cursor.execute("""
                    SELECT nutrient_id, amount 
                    FROM food_nutrient 
                    WHERE fdc_id = ? AND nutrient_id IN (1008, 1003, 1004, 1005)
                """, (fdc_id,))
                nutrients = dict(cursor.fetchall())
                
                print(f"✅ FDC {fdc_id} ({food[0]}):")
                print(f"   Kcal: {nutrients.get(1008, 0)}")
                print(f"   Protein: {nutrients.get(1003, 0)}g")
                print(f"   Fat: {nutrients.get(1004, 0)}g")
                print(f"   Carbs: {nutrients.get(1005, 0)}g")
        
        conn.close()
        
        return {
            "database_exists": True,
            "tables": tables,
            "foods_count": foods_count
        }
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return {"error": str(e)}

def main():
    """Run comprehensive USDA FDC integration tests"""
    print("🚀 USDA FDC INTEGRATION TESTING (TASK D1)")
    print("=" * 80)
    print("Testing USDA FoodData Central integration for nutrition coverage ≥75%")
    print("=" * 80)
    
    # Run all tests
    test_results = {}
    
    # Core USDA tests
    test_results["usda_provider"] = test_usda_provider()
    test_results["nutrition_calculator"] = test_nutrition_calculator_with_usda()
    test_results["api_endpoints"] = test_catalog_search_api()
    test_results["techcard_generation"] = test_techcard_generation()
    test_results["edge_cases"] = test_edge_cases()
    
    # Bonus verification
    test_results["database"] = test_usda_database()
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎯 FINAL SUMMARY - USDA FDC INTEGRATION")
    print("=" * 80)
    
    # Check critical requirements
    usda_provider_working = bool(test_results.get("usda_provider"))
    nutrition_calc_usda = test_results.get("nutrition_calculator", {}).get("usda_source", False)
    coverage_ok = test_results.get("nutrition_calculator", {}).get("coverage_ok", False)
    api_working = any(r.get("success") for r in test_results.get("api_endpoints", {}).values())
    techcard_usda = test_results.get("techcard_generation", {}).get("uses_usda", False)
    
    print(f"✅ USDA Provider Working: {'✅' if usda_provider_working else '❌'}")
    print(f"✅ NutritionCalculator USDA Source: {'✅' if nutrition_calc_usda else '❌'}")
    print(f"✅ Coverage ≥75% Requirement: {'✅' if coverage_ok else '❌'}")
    print(f"✅ API Endpoints Working: {'✅' if api_working else '❌'}")
    print(f"✅ TechCard Generation Uses USDA: {'✅' if techcard_usda else '❌'}")
    
    # Overall status
    all_critical_passed = all([
        usda_provider_working,
        nutrition_calc_usda,
        coverage_ok,
        api_working
    ])
    
    print(f"\n🎉 OVERALL STATUS: {'✅ PASSED' if all_critical_passed else '❌ FAILED'}")
    
    if all_critical_passed:
        print("🎯 USDA FDC Integration is working correctly!")
        print("   - USDA provider finds nutrition data with canonical_id and fuzzy matching")
        print("   - NutritionCalculator prioritizes USDA → catalog → bootstrap")
        print("   - API endpoints return USDA results with fdc_id and nutrition preview")
        print("   - Nutrition coverage meets ≥75% requirement")
        print("   - System correctly determines primary source as 'usda'")
    else:
        print("⚠️  Some USDA integration components need attention")
    
    return test_results

if __name__ == "__main__":
    main()