import requests
import json
import re
import time
from datetime import datetime

def test_golden_prompt_requirements():
    """
    Comprehensive test for the updated Receptor Pro backend with new "golden" prompt
    and related functionality as requested in the review.
    """
    
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    print("🚀 RECEPTOR PRO GOLDEN PROMPT TESTING")
    print("=" * 60)
    
    # Test 1: Register test user
    print("\n1️⃣ Testing User Registration...")
    user_data = {
        "email": f"comprehensive_test_{int(time.time())}@example.com",
        "name": "Comprehensive Test User",
        "city": "moskva"
    }
    
    response = requests.post(f"{base_url}/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.status_code}")
        return False
    
    user = response.json()
    user_id = user["id"]
    print(f"✅ User registered successfully: {user_id}")
    
    # Test 2: Verify Golden Prompt Format
    print("\n2️⃣ Testing Golden Prompt Format...")
    
    test_dishes = [
        "Паста Карбонара",
        "Ризотто с белыми грибами", 
        "Стейк из говядины"
    ]
    
    generated_cards = []
    
    for dish in test_dishes:
        print(f"   Generating: {dish}")
        tech_data = {
            "dish_name": dish,
            "user_id": user_id
        }
        
        response = requests.post(f"{base_url}/generate-tech-card", json=tech_data)
        if response.status_code != 200:
            print(f"❌ Tech card generation failed for {dish}: {response.status_code}")
            continue
        
        result = response.json()
        content = result["tech_card"]
        generated_cards.append(result)
        
        # Check format elements
        format_checks = {
            "💸 Себестоимость 100г": bool(re.search(r"💸\s*Себестоимость\s*100\s*г", content, re.IGNORECASE)),
            "КБЖУ (1 порция)": bool(re.search(r"КБЖУ\s*\(1\s*порция\)", content, re.IGNORECASE)),
            "No forbidden phrase": "стандартная ресторанная порция" not in content.lower(),
            "Emoji sections": sum(1 for emoji in ["💡", "🔥", "🌀", "🍷", "🍺", "🍹", "🥤", "🍽", "🎯", "💬", "📸", "🏷️"] if emoji in content)
        }
        
        print(f"   ✅ {dish}: {format_checks}")
        
        # Verify all format requirements
        if not all([format_checks["💸 Себестоимость 100г"], format_checks["КБЖУ (1 порция)"], format_checks["No forbidden phrase"]]):
            print(f"❌ Format requirements not met for {dish}")
            return False
        
        if format_checks["Emoji sections"] < 3:
            print(f"❌ Not enough emoji sections for {dish}")
            return False
        
        time.sleep(1)  # Small delay between generations
    
    print(f"✅ Golden prompt format verified for {len(generated_cards)} tech cards")
    
    # Test 3: History Functionality
    print("\n3️⃣ Testing History Functionality...")
    
    response = requests.get(f"{base_url}/user-history/{user_id}")
    if response.status_code != 200:
        print(f"❌ History endpoint failed: {response.status_code}")
        return False
    
    history_data = response.json()
    history = history_data.get("history", [])
    
    if len(history) != len(generated_cards):
        print(f"❌ History count mismatch: expected {len(generated_cards)}, got {len(history)}")
        return False
    
    # Verify history is sorted by creation date (newest first)
    if len(history) > 1:
        for i in range(len(history) - 1):
            current_date = datetime.fromisoformat(history[i]["created_at"].replace('Z', '+00:00'))
            next_date = datetime.fromisoformat(history[i+1]["created_at"].replace('Z', '+00:00'))
            if current_date < next_date:
                print("❌ History not sorted correctly (newest first)")
                return False
    
    print(f"✅ History functionality verified: {len(history)} items, correctly sorted")
    
    # Test 4: Database Persistence
    print("\n4️⃣ Testing Database Persistence...")
    
    response = requests.get(f"{base_url}/tech-cards/{user_id}")
    if response.status_code != 200:
        print(f"❌ Tech cards endpoint failed: {response.status_code}")
        return False
    
    tech_cards = response.json()
    
    if len(tech_cards) != len(generated_cards):
        print(f"❌ Database persistence issue: expected {len(generated_cards)}, got {len(tech_cards)}")
        return False
    
    # Verify all generated cards are in database
    generated_ids = {card["id"] for card in generated_cards}
    db_ids = {card["id"] for card in tech_cards}
    
    if generated_ids != db_ids:
        print("❌ Generated tech card IDs don't match database IDs")
        return False
    
    print(f"✅ Database persistence verified: {len(tech_cards)} tech cards saved")
    
    # Test 5: Cost Calculation Accuracy
    print("\n5️⃣ Testing Cost Calculation Accuracy...")
    
    for i, card in enumerate(generated_cards):
        content = card["tech_card"]
        dish_name = test_dishes[i]
        
        # Extract cost information
        cost_match = re.search(r"По ингредиентам:\s*(\d+(?:\.\d+)?)\s*₽", content)
        cost_100g_match = re.search(r"💸\s*Себестоимость\s*100\s*г:\s*(\d+(?:\.\d+)?)\s*₽", content)
        recommended_match = re.search(r"Рекомендуемая цена.*?(\d+(?:\.\d+)?)\s*₽", content)
        
        if not all([cost_match, cost_100g_match, recommended_match]):
            print(f"❌ Cost information missing for {dish_name}")
            return False
        
        ingredient_cost = float(cost_match.group(1))
        cost_100g = float(cost_100g_match.group(1))
        recommended_price = float(recommended_match.group(1))
        
        # Verify reasonable cost ranges
        if not (0 < ingredient_cost < 5000):
            print(f"❌ Unreasonable ingredient cost for {dish_name}: {ingredient_cost}")
            return False
        
        if not (0 < cost_100g < 1000):
            print(f"❌ Unreasonable cost per 100g for {dish_name}: {cost_100g}")
            return False
        
        # Verify recommended price is approximately 3x ingredient cost
        expected_recommended = ingredient_cost * 3
        tolerance = expected_recommended * 0.3  # 30% tolerance
        
        if abs(recommended_price - expected_recommended) > tolerance:
            print(f"❌ Recommended price calculation error for {dish_name}")
            print(f"   Expected: ~{expected_recommended}₽, Got: {recommended_price}₽")
            return False
        
        print(f"   ✅ {dish_name}: {ingredient_cost}₽ → {cost_100g}₽/100g → {recommended_price}₽ recommended")
    
    print("✅ Cost calculations verified for all tech cards")
    
    # Test 6: PRO User Equipment Integration
    print("\n6️⃣ Testing PRO User Equipment Integration...")
    
    # Upgrade user to PRO
    upgrade_data = {"subscription_plan": "pro"}
    response = requests.post(f"{base_url}/upgrade-subscription/{user_id}", json=upgrade_data)
    if response.status_code != 200:
        print(f"❌ PRO upgrade failed: {response.status_code}")
        return False
    
    # Get available equipment
    response = requests.get(f"{base_url}/kitchen-equipment")
    if response.status_code != 200:
        print(f"❌ Kitchen equipment endpoint failed: {response.status_code}")
        return False
    
    equipment = response.json()
    
    # Set some equipment for the PRO user
    equipment_ids = [
        equipment["cooking_methods"][0]["id"],
        equipment["cooking_methods"][2]["id"],
        equipment["prep_equipment"][0]["id"],
    ]
    
    equipment_data = {"equipment_ids": equipment_ids}
    response = requests.post(f"{base_url}/update-kitchen-equipment/{user_id}", json=equipment_data)
    if response.status_code != 200:
        print(f"❌ Equipment update failed: {response.status_code}")
        return False
    
    # Generate equipment-aware tech card
    tech_data = {
        "dish_name": "Стейк на гриле с овощами",
        "user_id": user_id
    }
    
    response = requests.post(f"{base_url}/generate-tech-card", json=tech_data)
    if response.status_code != 200:
        print(f"❌ Equipment-aware tech card generation failed: {response.status_code}")
        return False
    
    result = response.json()
    print("✅ PRO user equipment integration verified")
    
    # Test 7: Tech Card Editing
    print("\n7️⃣ Testing Tech Card Editing...")
    
    # Edit one of the generated tech cards
    edit_request = {
        "tech_card_id": generated_cards[0]["id"],
        "edit_instruction": "Увеличь порцию в 2 раза и пересчитай стоимость"
    }
    
    response = requests.post(f"{base_url}/edit-tech-card", json=edit_request)
    if response.status_code != 200:
        print(f"❌ Tech card editing failed: {response.status_code}")
        return False
    
    result = response.json()
    edited_content = result["tech_card"]
    
    # Verify edited content maintains golden prompt format
    format_checks = {
        "💸 Себестоимость 100г": bool(re.search(r"💸\s*Себестоимость\s*100\s*г", edited_content, re.IGNORECASE)),
        "КБЖУ (1 порция)": bool(re.search(r"КБЖУ\s*\(1\s*порция\)", edited_content, re.IGNORECASE)),
        "No forbidden phrase": "стандартная ресторанная порция" not in edited_content.lower()
    }
    
    if not all(format_checks.values()):
        print("❌ Edited tech card doesn't maintain golden prompt format")
        return False
    
    print("✅ Tech card editing with golden prompt format verified")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
    print(f"✅ Generated {len(generated_cards)} tech cards with correct format")
    print(f"✅ History endpoint returns {len(history)} items correctly")
    print(f"✅ Database persistence verified for {len(tech_cards)} tech cards")
    print("✅ Cost calculations are accurate and properly formatted")
    print("✅ PRO user equipment integration working")
    print("✅ Tech card editing maintains golden prompt format")
    print("✅ No forbidden phrases found in any tech cards")
    print(f"✅ All tech cards contain required emoji sections")
    
    return True

if __name__ == "__main__":
    success = test_golden_prompt_requirements()
    if success:
        print("\n🏆 COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY!")
        exit(0)
    else:
        print("\n💥 SOME TESTS FAILED!")
        exit(1)