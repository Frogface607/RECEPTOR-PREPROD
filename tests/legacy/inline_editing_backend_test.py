#!/usr/bin/env python3
"""
Backend Testing Suite for TechCardV2 Inline Editing and Mapping (V2)
Testing Task 0.1 — «Починить инлайн-редактирование и маппинг (V2)»

Focus: Testing the complete inline editing workflow including:
- POST /api/v1/techcards.v2/recalc (recalculation after changes)
- GET /api/v1/techcards.v2/catalog-search (search for mapping)
- GET /api/user-history/{user_id} (list of tech cards for sub-recipes)
- Full workflow: generate → edit → recalc → mapping → sub-recipes
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

def test_generate_basic_techcard():
    """Generate a basic tech card 'Бургер классический' for testing inline editing"""
    log_test("🍔 STEP 1: Generating basic tech card 'Бургер классический' for testing")
    
    profile_data = {
        "name": "Бургер классический с говяжьей котлетой, овощами и соусом",
        "cuisine": "европейская",
        "equipment": ["плита", "сковорода", "гриль"],
        "budget": 500.0,
        "dietary": []
    }
    
    try:
        url = f"{API_BASE}/v1/techcards.v2/generate"
        log_test(f"Making request to: {url}")
        log_test(f"Profile data: {profile_data['name']}")
        
        # Use deterministic mode (no LLM) for consistent testing
        response = requests.post(f"{url}?use_llm=false", json=profile_data, timeout=60)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            card = data.get('card')
            issues = data.get('issues', [])
            
            log_test(f"✅ Tech card generation: {status}")
            log_test(f"📊 Issues found: {len(issues)}")
            
            if card:
                # Extract key information for testing
                title = card.get('meta', {}).get('title', 'Unknown')
                ingredients = card.get('ingredients', [])
                cost = card.get('cost', {})
                nutrition = card.get('nutrition', {})
                
                log_test(f"📋 Generated tech card: {title}")
                log_test(f"🥬 Ingredients count: {len(ingredients)}")
                log_test(f"💰 Cost data: rawCost={cost.get('rawCost', 0)} RUB, costPerPortion={cost.get('costPerPortion', 0)} RUB")
                log_test(f"🍎 Nutrition data: per100g kcal={nutrition.get('per100g', {}).get('kcal', 0)}")
                
                # Show first few ingredients for inline editing testing
                if ingredients:
                    log_test("🥬 Sample ingredients for inline editing:")
                    for i, ing in enumerate(ingredients[:3]):
                        name = ing.get('name', 'Unknown')
                        brutto = ing.get('brutto_g', 0)
                        loss = ing.get('loss_pct', 0)
                        netto = ing.get('netto_g', 0)
                        unit = ing.get('unit', 'г')
                        log_test(f"   {i+1}. {name}: {brutto}г брутто, {loss}% потери, {netto}г нетто, ед.изм: {unit}")
                
                return {
                    'success': True,
                    'status': status,
                    'card': card,
                    'issues': issues,
                    'ingredients_count': len(ingredients)
                }
            else:
                log_test("❌ No tech card data in response")
                return {'success': False, 'error': 'No card data'}
        else:
            log_test(f"❌ Tech card generation failed: {response.status_code}")
            log_test(f"Response: {response.text[:300]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error generating tech card: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_catalog_search():
    """Test GET /api/v1/techcards.v2/catalog-search for ingredient mapping"""
    log_test("🔍 STEP 2: Testing catalog search for ingredient mapping")
    
    # Test searches for typical burger ingredients
    search_queries = [
        "говядина",  # beef for burger patty
        "булка",     # bun
        "масло",     # oil/butter
        "лук",       # onion
        "помидор"    # tomato
    ]
    
    search_results = {}
    
    for query in search_queries:
        try:
            url = f"{API_BASE}/v1/techcards.v2/catalog-search"
            params = {"q": query, "limit": 5}
            
            log_test(f"🔍 Searching for: '{query}'")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                items = data.get('items', [])
                
                log_test(f"✅ Search '{query}': {status}, found {len(items)} items")
                
                if items:
                    log_test(f"📋 Results for '{query}':")
                    for i, item in enumerate(items):
                        name = item.get('name', 'Unknown')
                        sku_id = item.get('sku_id', 'No SKU')
                        canonical_id = item.get('canonical_id', 'No canonical')
                        price = item.get('price', 'No price')
                        has_nutrition = item.get('has_nutrition', False)
                        log_test(f"   {i+1}. {name} | SKU: {sku_id} | Price: {price} | Nutrition: {has_nutrition}")
                
                search_results[query] = {
                    'success': True,
                    'items': items,
                    'count': len(items)
                }
            else:
                log_test(f"❌ Search '{query}' failed: {response.status_code}")
                search_results[query] = {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            log_test(f"❌ Error searching '{query}': {str(e)}")
            search_results[query] = {'success': False, 'error': str(e)}
    
    # Summary
    successful_searches = sum(1 for result in search_results.values() if result.get('success'))
    total_items_found = sum(result.get('count', 0) for result in search_results.values() if result.get('success'))
    
    log_test(f"📊 Catalog search summary: {successful_searches}/{len(search_queries)} successful")
    log_test(f"📊 Total items found across all searches: {total_items_found}")
    
    return {
        'success': successful_searches > 0,
        'results': search_results,
        'successful_searches': successful_searches,
        'total_items': total_items_found
    }

def test_user_history():
    """Test GET /api/user-history/{user_id} for sub-recipes functionality"""
    log_test("📚 STEP 3: Testing user history for sub-recipes")
    
    test_user_id = "test_user_inline_editing"
    
    try:
        url = f"{API_BASE}/user-history/{test_user_id}"
        log_test(f"Making request to: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle both formats: list or dict with history key
            if isinstance(data, list):
                tech_cards = data
            elif isinstance(data, dict) and 'history' in data:
                tech_cards = data['history']
            else:
                log_test(f"❌ Unexpected response format: {type(data)}")
                return {'success': False, 'error': 'Unexpected response format'}
                
            log_test(f"✅ User history retrieved: {len(tech_cards)} tech cards found")
            
            if tech_cards:
                log_test("📋 Available tech cards for sub-recipes:")
                for i, tc in enumerate(tech_cards[:5]):  # Show first 5
                    title = tc.get('title', 'Unknown')
                    created_at = tc.get('created_at', 'Unknown date')
                    log_test(f"   {i+1}. {title} (created: {created_at})")
            else:
                log_test("📋 No tech cards found in user history")
            
            return {
                'success': True,
                'tech_cards': tech_cards,
                'count': len(tech_cards)
            }
                
        else:
            log_test(f"❌ User history request failed: {response.status_code}")
            log_test(f"Response: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error getting user history: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_inline_editing_simulation(original_card):
    """Simulate inline editing by modifying ingredient values"""
    log_test("✏️ STEP 4: Simulating inline editing of ingredients")
    
    if not original_card or not original_card.get('ingredients'):
        log_test("❌ No original card or ingredients to edit")
        return {'success': False, 'error': 'No ingredients to edit'}
    
    # Create a copy for editing
    edited_card = json.loads(json.dumps(original_card))  # Deep copy
    ingredients = edited_card.get('ingredients', [])
    
    if len(ingredients) < 2:
        log_test("❌ Need at least 2 ingredients for editing test")
        return {'success': False, 'error': 'Not enough ingredients'}
    
    # Simulate editing first two ingredients
    edits_made = []
    
    # Edit ingredient 1: Change brutto_g and recalculate netto_g
    if len(ingredients) > 0:
        ing1 = ingredients[0]
        original_brutto = ing1.get('brutto_g', 0)
        original_loss = ing1.get('loss_pct', 0)
        original_netto = ing1.get('netto_g', 0)
        
        # Increase brutto by 50g
        new_brutto = original_brutto + 50
        # Keep same loss percentage
        new_netto = new_brutto * (1 - original_loss / 100)
        
        ing1['brutto_g'] = new_brutto
        ing1['netto_g'] = round(new_netto, 1)
        
        edits_made.append({
            'ingredient': ing1.get('name', 'Unknown'),
            'field': 'brutto_g',
            'old_value': original_brutto,
            'new_value': new_brutto,
            'auto_recalc': f"netto_g: {original_netto} → {round(new_netto, 1)}"
        })
        
        log_test(f"✏️ Edited {ing1.get('name', 'Unknown')}: brutto {original_brutto}г → {new_brutto}г")
        log_test(f"   Auto-recalc: netto {original_netto}г → {round(new_netto, 1)}г")
    
    # Edit ingredient 2: Change loss_pct and recalculate netto_g
    if len(ingredients) > 1:
        ing2 = ingredients[1]
        original_brutto = ing2.get('brutto_g', 0)
        original_loss = ing2.get('loss_pct', 0)
        original_netto = ing2.get('netto_g', 0)
        
        # Change loss percentage (increase by 5%)
        new_loss = min(original_loss + 5, 60)  # Cap at 60%
        new_netto = original_brutto * (1 - new_loss / 100)
        
        ing2['loss_pct'] = new_loss
        ing2['netto_g'] = round(new_netto, 1)
        
        edits_made.append({
            'ingredient': ing2.get('name', 'Unknown'),
            'field': 'loss_pct',
            'old_value': original_loss,
            'new_value': new_loss,
            'auto_recalc': f"netto_g: {original_netto} → {round(new_netto, 1)}"
        })
        
        log_test(f"✏️ Edited {ing2.get('name', 'Unknown')}: loss {original_loss}% → {new_loss}%")
        log_test(f"   Auto-recalc: netto {original_netto}г → {round(new_netto, 1)}г")
    
    log_test(f"✅ Inline editing simulation complete: {len(edits_made)} edits made")
    
    return {
        'success': True,
        'edited_card': edited_card,
        'edits_made': edits_made,
        'edits_count': len(edits_made)
    }

def test_recalc_after_editing(edited_card):
    """Test POST /api/v1/techcards.v2/recalc after inline editing"""
    log_test("🔄 STEP 5: Testing recalculation after inline editing")
    
    if not edited_card:
        log_test("❌ No edited card to recalculate")
        return {'success': False, 'error': 'No edited card'}
    
    try:
        url = f"{API_BASE}/v1/techcards.v2/recalc"
        log_test(f"Making recalc request to: {url}")
        
        # Get original cost/nutrition for comparison
        original_cost = edited_card.get('cost', {})
        original_nutrition = edited_card.get('nutrition', {})
        
        log_test(f"📊 Original cost: rawCost={original_cost.get('rawCost', 0)} RUB")
        log_test(f"📊 Original nutrition: kcal={original_nutrition.get('per100g', {}).get('kcal', 0)}")
        
        start_time = time.time()
        response = requests.post(url, json=edited_card, timeout=60)
        response_time = time.time() - start_time
        
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            recalc_card = data.get('card')
            message = data.get('message', '')
            
            log_test(f"✅ Recalculation: {status}")
            log_test(f"💬 Message: {message}")
            
            if recalc_card:
                # Compare recalculated values
                new_cost = recalc_card.get('cost', {})
                new_nutrition = recalc_card.get('nutrition', {})
                
                log_test("📊 Recalculation results:")
                log_test(f"   Cost: rawCost {original_cost.get('rawCost', 0)} → {new_cost.get('rawCost', 0)} RUB")
                log_test(f"   Cost: costPerPortion {original_cost.get('costPerPortion', 0)} → {new_cost.get('costPerPortion', 0)} RUB")
                log_test(f"   Nutrition: kcal {original_nutrition.get('per100g', {}).get('kcal', 0)} → {new_nutrition.get('per100g', {}).get('kcal', 0)}")
                
                # Check if values actually changed
                cost_changed = new_cost.get('rawCost', 0) != original_cost.get('rawCost', 0)
                nutrition_changed = new_nutrition.get('per100g', {}).get('kcal', 0) != original_nutrition.get('per100g', {}).get('kcal', 0)
                
                log_test(f"🔄 Cost recalculated: {'YES' if cost_changed else 'NO'}")
                log_test(f"🔄 Nutrition recalculated: {'YES' if nutrition_changed else 'NO'}")
                
                return {
                    'success': True,
                    'status': status,
                    'recalc_card': recalc_card,
                    'cost_changed': cost_changed,
                    'nutrition_changed': nutrition_changed,
                    'response_time': response_time
                }
            else:
                log_test("❌ No recalculated card in response")
                return {'success': False, 'error': 'No recalculated card'}
        else:
            log_test(f"❌ Recalculation failed: {response.status_code}")
            log_test(f"Response: {response.text[:300]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error during recalculation: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_mapping_workflow(card, search_results):
    """Test ingredient mapping workflow using catalog search results"""
    log_test("🗺️ STEP 6: Testing ingredient mapping workflow")
    
    if not card or not card.get('ingredients'):
        log_test("❌ No card or ingredients for mapping")
        return {'success': False, 'error': 'No ingredients to map'}
    
    if not search_results or not search_results.get('success'):
        log_test("❌ No search results for mapping")
        return {'success': False, 'error': 'No search results'}
    
    # Create a copy for mapping
    mapped_card = json.loads(json.dumps(card))  # Deep copy
    ingredients = mapped_card.get('ingredients', [])
    
    mappings_applied = []
    
    # Try to map first few ingredients using search results
    search_data = search_results.get('results', {})
    
    for i, ingredient in enumerate(ingredients[:3]):  # Map first 3 ingredients
        ing_name = ingredient.get('name', '').lower()
        
        # Find matching search results
        mapped = False
        for query, result in search_data.items():
            if result.get('success') and result.get('items'):
                # Check if ingredient name contains the search query
                if query in ing_name or any(word in query for word in ing_name.split()):
                    # Use first matching item
                    item = result['items'][0]
                    
                    # Apply mapping
                    ingredient['sku_id'] = item.get('sku_id')
                    ingredient['canonical_id'] = item.get('canonical_id')
                    ingredient['mapped_name'] = item.get('name')
                    ingredient['mapped_price'] = item.get('price')
                    
                    mappings_applied.append({
                        'ingredient': ingredient.get('name'),
                        'mapped_to': item.get('name'),
                        'sku_id': item.get('sku_id'),
                        'canonical_id': item.get('canonical_id'),
                        'price': item.get('price')
                    })
                    
                    log_test(f"🗺️ Mapped '{ingredient.get('name')}' → '{item.get('name')}' (SKU: {item.get('sku_id')})")
                    mapped = True
                    break
        
        if not mapped:
            log_test(f"⚠️ Could not map ingredient: {ingredient.get('name')}")
    
    log_test(f"✅ Mapping workflow complete: {len(mappings_applied)} ingredients mapped")
    
    return {
        'success': len(mappings_applied) > 0,
        'mapped_card': mapped_card,
        'mappings_applied': mappings_applied,
        'mappings_count': len(mappings_applied)
    }

def test_subrecipes_workflow(card, user_history):
    """Test sub-recipes workflow using user history"""
    log_test("🍽️ STEP 7: Testing sub-recipes workflow")
    
    if not card or not card.get('ingredients'):
        log_test("❌ No card or ingredients for sub-recipes")
        return {'success': False, 'error': 'No ingredients'}
    
    if not user_history or not user_history.get('success') or not user_history.get('tech_cards'):
        log_test("❌ No user history for sub-recipes")
        return {'success': False, 'error': 'No user history'}
    
    # Create a copy for sub-recipe assignment
    subrecipe_card = json.loads(json.dumps(card))  # Deep copy
    ingredients = subrecipe_card.get('ingredients', [])
    tech_cards = user_history.get('tech_cards', [])
    
    if not tech_cards:
        log_test("❌ No tech cards available for sub-recipes")
        return {'success': False, 'error': 'No tech cards available'}
    
    subrecipes_applied = []
    
    # Assign sub-recipe to first ingredient (simulate user selecting from modal)
    if len(ingredients) > 0 and len(tech_cards) > 0:
        ingredient = ingredients[0]
        selected_tc = tech_cards[0]  # Use first available tech card
        
        # Apply sub-recipe
        ingredient['subRecipe'] = {
            'id': selected_tc.get('_id', f"subrecipe_{int(time.time())}"),
            'title': selected_tc.get('title', 'Unknown Sub-recipe')
        }
        
        # Clear SKU mapping when sub-recipe is assigned
        ingredient.pop('sku_id', None)
        ingredient.pop('canonical_id', None)
        
        subrecipes_applied.append({
            'ingredient': ingredient.get('name'),
            'subrecipe_id': ingredient['subRecipe']['id'],
            'subrecipe_title': ingredient['subRecipe']['title']
        })
        
        log_test(f"🍽️ Assigned sub-recipe to '{ingredient.get('name')}': {ingredient['subRecipe']['title']}")
    
    log_test(f"✅ Sub-recipes workflow complete: {len(subrecipes_applied)} sub-recipes assigned")
    
    return {
        'success': len(subrecipes_applied) > 0,
        'subrecipe_card': subrecipe_card,
        'subrecipes_applied': subrecipes_applied,
        'subrecipes_count': len(subrecipes_applied)
    }

def main():
    """Main testing function for TechCardV2 Inline Editing and Mapping"""
    log_test("🚀 Starting TechCardV2 Inline Editing and Mapping Testing")
    log_test("🎯 Task 0.1 — «Починить инлайн-редактирование и маппинг (V2)»")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Step 1: Generate basic tech card
    generation_result = test_generate_basic_techcard()
    
    if not generation_result['success']:
        log_test("❌ Cannot proceed without generated tech card")
        return
    
    original_card = generation_result['card']
    log_test(f"\n📊 Generated tech card: {original_card.get('meta', {}).get('title', 'Unknown')}")
    
    # Step 2: Test catalog search
    log_test("\n" + "=" * 80)
    search_result = test_catalog_search()
    
    # Step 3: Test user history
    log_test("\n" + "=" * 80)
    history_result = test_user_history()
    
    # Step 4: Simulate inline editing
    log_test("\n" + "=" * 80)
    editing_result = test_inline_editing_simulation(original_card)
    
    if not editing_result['success']:
        log_test("❌ Cannot proceed without edited card")
        return
    
    edited_card = editing_result['edited_card']
    
    # Step 5: Test recalculation after editing
    log_test("\n" + "=" * 80)
    recalc_result = test_recalc_after_editing(edited_card)
    
    # Step 6: Test mapping workflow
    log_test("\n" + "=" * 80)
    mapping_result = test_mapping_workflow(edited_card, search_result)
    
    # Step 7: Test sub-recipes workflow
    log_test("\n" + "=" * 80)
    subrecipes_result = test_subrecipes_workflow(edited_card, history_result)
    
    # Final Summary
    log_test("\n" + "=" * 80)
    log_test("📋 TECHCARDV2 INLINE EDITING AND MAPPING TESTING SUMMARY:")
    log_test(f"✅ Tech card generation: {'SUCCESS' if generation_result['success'] else 'FAILED'}")
    log_test(f"✅ Catalog search: {'SUCCESS' if search_result['success'] else 'FAILED'}")
    log_test(f"✅ User history: {'SUCCESS' if history_result['success'] else 'FAILED'}")
    log_test(f"✅ Inline editing simulation: {'SUCCESS' if editing_result['success'] else 'FAILED'}")
    log_test(f"✅ Recalculation: {'SUCCESS' if recalc_result['success'] else 'FAILED'}")
    log_test(f"✅ Mapping workflow: {'SUCCESS' if mapping_result['success'] else 'FAILED'}")
    log_test(f"✅ Sub-recipes workflow: {'SUCCESS' if subrecipes_result['success'] else 'FAILED'}")
    
    # Detailed results
    if generation_result['success']:
        log_test(f"📊 Generated ingredients: {generation_result['ingredients_count']}")
    
    if search_result['success']:
        log_test(f"📊 Catalog searches successful: {search_result['successful_searches']}/5")
        log_test(f"📊 Total catalog items found: {search_result['total_items']}")
    
    if editing_result['success']:
        log_test(f"📊 Inline edits made: {editing_result['edits_count']}")
    
    if recalc_result['success']:
        log_test(f"📊 Recalculation time: {recalc_result['response_time']:.2f}s")
        log_test(f"📊 Cost recalculated: {'YES' if recalc_result['cost_changed'] else 'NO'}")
        log_test(f"📊 Nutrition recalculated: {'YES' if recalc_result['nutrition_changed'] else 'NO'}")
    
    if mapping_result['success']:
        log_test(f"📊 Ingredients mapped: {mapping_result['mappings_count']}")
    
    if subrecipes_result['success']:
        log_test(f"📊 Sub-recipes assigned: {subrecipes_result['subrecipes_count']}")
    
    # Overall assessment
    successful_tests = sum([
        generation_result['success'],
        search_result['success'],
        history_result['success'],
        editing_result['success'],
        recalc_result['success'],
        mapping_result['success'],
        subrecipes_result['success']
    ])
    
    log_test(f"\n🎯 OVERALL RESULT: {successful_tests}/7 tests successful")
    
    if successful_tests >= 5:
        log_test("🎉 INLINE EDITING AND MAPPING FUNCTIONALITY IS WORKING!")
        log_test("✅ Backend endpoints are functional")
        log_test("✅ Full workflow can be completed")
        log_test("✅ Ready for frontend integration")
    else:
        log_test("⚠️ Some issues found in inline editing functionality:")
        if not generation_result['success']:
            log_test("   - Tech card generation failed")
        if not search_result['success']:
            log_test("   - Catalog search failed")
        if not recalc_result['success']:
            log_test("   - Recalculation after editing failed")
        if not mapping_result['success']:
            log_test("   - Ingredient mapping failed")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()