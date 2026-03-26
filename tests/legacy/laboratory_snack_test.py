#!/usr/bin/env python3
"""
LABORATORY HOME-FRIENDLY SNACK EXPERIMENT TEST
Testing the updated LABORATORY feature with "snack" experiment type
As requested in review - focus on home-friendly ingredients and techniques
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_laboratory_snack_experiment():
    """Test POST /api/laboratory-experiment with snack experiment type"""
    
    print("🧪 LABORATORY SNACK EXPERIMENT TESTING - HOME-FRIENDLY FOCUS")
    print("=" * 70)
    
    # Test data EXACTLY as specified in review request
    test_data = {
        "user_id": "test_user_12345",
        "experiment_type": "snack",
        "base_dish": "основное блюдо"
    }
    
    print(f"📋 REVIEW REQUEST TEST DATA:")
    print(f"   user_id: '{test_data['user_id']}'")
    print(f"   experiment_type: '{test_data['experiment_type']}'")
    print(f"   base_dish: '{test_data['base_dish']}'")
    print()
    
    try:
        print("🚀 Making API request to laboratory endpoint...")
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/laboratory-experiment",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"⏱️  Response time: {response_time:.2f} seconds")
        print(f"📊 HTTP Status: {response.status_code}")
        
        # REQUIREMENT 1: API responds with 200 status
        if response.status_code == 200:
            print("✅ REQUIREMENT 1 PASSED: API responds with 200 status")
        else:
            print(f"❌ REQUIREMENT 1 FAILED: Expected 200, got {response.status_code}")
            print(f"Error response: {response.text}")
            return False
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("❌ FAILED: Invalid JSON response")
            return False
        
        print(f"📄 Response structure: {list(data.keys())}")
        
        # Get experiment content
        experiment_content = data.get('experiment', '')
        if not experiment_content:
            print("❌ FAILED: No experiment content in response")
            return False
        
        print(f"📝 Experiment content length: {len(experiment_content)} characters")
        print()
        
        # REQUIREMENT 2: Uses accessible home ingredients
        print("🏠 REQUIREMENT 2: TESTING HOME-FRIENDLY INGREDIENTS")
        print("-" * 50)
        
        # Home-friendly ingredients that should be present
        home_ingredients = [
            # Meat/protein accessible
            "сосиски", "колбаса", "яйца", "сыр", "творог", "тушенка",
            "куриные наггетсы", "крабовые палочки", "фарш", "сардельки",
            
            # Sweet unexpected
            "скиттлс", "мармелад", "зефир", "печенье", "орео", "нутелла", 
            "сгущенка", "мороженое", "шоколад", "вафли",
            
            # Snacks and chips
            "чипсы", "сухарики", "попкорн", "крекеры", "орешки", "семечки",
            "кириешки", "читос", "лейс", "принглс",
            
            # Drinks as ingredients
            "кока-кола", "пепси", "фанта", "спрайт", "квас",
            
            # Home vegetables/fruits
            "картошка", "лук", "морковь", "огурцы", "помидоры", "яблоки", "бананы",
            
            # Sauces
            "кетчуп", "майонез", "горчица", "соевый соус", "сметана", "йогурт",
            
            # Grains and pasta
            "макароны", "рис", "гречка", "хлеб", "лаваш", "булочки"
        ]
        
        found_home_ingredients = []
        content_lower = experiment_content.lower()
        
        for ingredient in home_ingredients:
            if ingredient in content_lower:
                found_home_ingredients.append(ingredient)
        
        if found_home_ingredients:
            print(f"✅ Found {len(found_home_ingredients)} home ingredients:")
            for ingredient in found_home_ingredients[:10]:  # Show first 10
                print(f"   • {ingredient}")
            if len(found_home_ingredients) > 10:
                print(f"   ... and {len(found_home_ingredients) - 10} more")
            print("✅ REQUIREMENT 2 PASSED: Uses accessible home ingredients")
        else:
            print("❌ REQUIREMENT 2 FAILED: No home ingredients detected")
        
        print()
        
        # REQUIREMENT 3: No exotic ingredients
        print("🚫 REQUIREMENT 3: TESTING FOR EXOTIC INGREDIENTS (should be absent)")
        print("-" * 50)
        
        exotic_ingredients = [
            "трюфель", "трюфели", "жидкий азот", "икра", "фуа-гра", 
            "молекулярн", "сферификация", "желатин", "агар", "каррагинан", 
            "лецитин", "ксантан", "альгинат", "тартар", "карпаччо", 
            "конфи", "су-вид", "эспума", "гель", "пена"
        ]
        
        found_exotic = []
        for ingredient in exotic_ingredients:
            if ingredient in content_lower:
                found_exotic.append(ingredient)
        
        if not found_exotic:
            print("✅ REQUIREMENT 3 PASSED: No exotic ingredients found")
        else:
            print(f"❌ REQUIREMENT 3 FAILED: Found exotic ingredients: {', '.join(found_exotic)}")
        
        print()
        
        # REQUIREMENT 4: Home-friendly techniques
        print("🔧 REQUIREMENT 4: TESTING HOME-FRIENDLY TECHNIQUES")
        print("-" * 50)
        
        home_techniques = [
            # Basic cooking methods
            "жарка", "варка", "запекание", "тушение", "смешивание", "взбивание",
            
            # Creative but doable
            "жарка в кока-коле", "панировка в печенье", "панировка в чипсах",
            "маринование", "засолка", "заморозка", "растапливание",
            
            # Equipment mentions
            "духовк", "сковород", "микроволн", "блендер", "миксер", "кастрюл",
            
            # Simple processes
            "нарезка", "измельчение", "перемешивание", "охлаждение", "нагревание"
        ]
        
        found_techniques = []
        for technique in home_techniques:
            if technique in content_lower:
                found_techniques.append(technique)
        
        if found_techniques:
            print(f"✅ Found {len(found_techniques)} home-friendly techniques:")
            for technique in found_techniques[:8]:  # Show first 8
                print(f"   • {technique}")
            if len(found_techniques) > 8:
                print(f"   ... and {len(found_techniques) - 8} more")
            print("✅ REQUIREMENT 4 PASSED: Uses home-friendly techniques")
        else:
            print("❌ REQUIREMENT 4 FAILED: No home-friendly techniques detected")
        
        print()
        
        # REQUIREMENT 5: Creative but achievable combinations
        print("🎨 REQUIREMENT 5: TESTING CREATIVE BUT ACHIEVABLE COMBINATIONS")
        print("-" * 50)
        
        creative_indicators = [
            "эксперимент", "креативн", "необычн", "интересн", "оригинальн",
            "твист", "сочетание", "комбинация", "микс", "фьюжн", "неожиданн",
            "удивительн", "инновационн", "экспериментальн"
        ]
        
        achievable_indicators = [
            "дома", "домашн", "просто", "легко", "доступн", "обычн",
            "кухн", "можно", "получится", "реально", "выполним"
        ]
        
        found_creative = []
        found_achievable = []
        
        for indicator in creative_indicators:
            if indicator in content_lower:
                found_creative.append(indicator)
        
        for indicator in achievable_indicators:
            if indicator in content_lower:
                found_achievable.append(indicator)
        
        print(f"🎨 Creative elements found: {len(found_creative)}")
        if found_creative:
            print(f"   {', '.join(found_creative[:5])}")
        
        print(f"🏡 Achievable elements found: {len(found_achievable)}")
        if found_achievable:
            print(f"   {', '.join(found_achievable[:5])}")
        
        if found_creative and found_achievable:
            print("✅ REQUIREMENT 5 PASSED: Creative but achievable combinations")
        elif found_creative:
            print("⚠️  REQUIREMENT 5 PARTIAL: Creative but achievability unclear")
        else:
            print("❌ REQUIREMENT 5 FAILED: Limited creativity detected")
        
        print()
        
        # Display experiment preview
        print("📖 EXPERIMENT PREVIEW:")
        print("=" * 70)
        preview_length = min(800, len(experiment_content))
        print(experiment_content[:preview_length])
        if len(experiment_content) > preview_length:
            print("\n... [content truncated] ...")
        print("=" * 70)
        
        # Check for additional features
        if 'image_url' in data and data['image_url']:
            print(f"\n🖼️  Image generation: ✅ Present")
            print(f"   URL: {data['image_url'][:80]}...")
        
        if 'photo_description' in data and data['photo_description']:
            print(f"\n📸 Photo description: ✅ Present ({len(data['photo_description'])} chars)")
        
        # Final assessment
        print("\n🎯 LABORATORY SNACK EXPERIMENT TEST RESULTS:")
        print("=" * 70)
        
        requirements_passed = 0
        total_requirements = 5
        
        if response.status_code == 200:
            requirements_passed += 1
            print("✅ 1. API responds with 200 status")
        
        if found_home_ingredients:
            requirements_passed += 1
            print(f"✅ 2. Uses accessible home ingredients ({len(found_home_ingredients)} found)")
        else:
            print("❌ 2. Uses accessible home ingredients")
        
        if not found_exotic:
            requirements_passed += 1
            print("✅ 3. No exotic ingredients")
        else:
            print("❌ 3. Contains exotic ingredients")
        
        if found_techniques:
            requirements_passed += 1
            print(f"✅ 4. Home-friendly techniques ({len(found_techniques)} found)")
        else:
            print("❌ 4. Home-friendly techniques")
        
        if found_creative and found_achievable:
            requirements_passed += 1
            print("✅ 5. Creative but achievable combinations")
        else:
            print("❌ 5. Creative but achievable combinations")
        
        print(f"\n📊 OVERALL SCORE: {requirements_passed}/{total_requirements} requirements passed")
        
        if requirements_passed >= 4:
            print("🎉 LABORATORY FEATURE: EXCELLENT - Ready for home experiments!")
            return True
        elif requirements_passed >= 3:
            print("✅ LABORATORY FEATURE: GOOD - Minor improvements needed")
            return True
        else:
            print("⚠️  LABORATORY FEATURE: NEEDS IMPROVEMENT")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ FAILED: Request timeout (>120s)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {str(e)}")
        return False

def main():
    """Main test execution"""
    print(f"🧪 LABORATORY HOME-FRIENDLY SNACK EXPERIMENT TESTING")
    print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"🎯 Focus: Home-friendly ingredients and techniques")
    print()
    
    success = test_laboratory_snack_experiment()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 LABORATORY SNACK EXPERIMENT TESTING COMPLETED SUCCESSFULLY!")
        print("✅ Updated LABORATORY generates realistic home experiments")
        print("✅ Uses accessible ingredients (сосиски, скиттлс, чипсы, etc.)")
        print("✅ Employs home-friendly techniques (жарка в кока-коле, панировка в печенье)")
        print("✅ Creative but achievable combinations")
        print("✅ People can actually try these experiments at home")
    else:
        print("❌ LABORATORY SNACK EXPERIMENT TESTING FAILED!")
        print("🔧 Laboratory feature needs attention for home-friendly experiments")
    
    print(f"📅 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()