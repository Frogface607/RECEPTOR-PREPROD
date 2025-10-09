#!/usr/bin/env python3
"""
Enhanced FINANCES Feature Backend Testing
Testing POST /api/analyze-finances with detailed analysis structure
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_enhanced_finances_feature():
    """Test the enhanced FINANCES feature with detailed analysis"""
    print("🎯 TESTING ENHANCED FINANCES FEATURE")
    print("=" * 60)
    
    # Test data as specified in review request
    user_id = "test_user_12345"
    
    # Enhanced tech card content for "Паста Карбонара на 4 порции"
    tech_card_content = """**Название:** Паста Карбонара на 4 порции

**Категория:** основное

**Описание:** Классическая итальянская паста с беконом, яйцами и пармезаном. Кремовая текстура без сливок, только яичные желтки создают шелковистый соус.

**Ингредиенты:** (на 4 порции)

- Спагетти — 400 г — ~120 ₽
- Бекон гуанчале — 200 г — ~400 ₽
- Яйца куриные (желтки) — 4 шт — ~40 ₽
- Пармезан тертый — 100 г — ~300 ₽
- Черный перец — 2 г — ~5 ₽
- Соль — 3 г — ~1 ₽
- Оливковое масло — 30 мл — ~25 ₽

**Пошаговый рецепт:**

1. Отварить спагетти до состояния аль денте (8-10 минут)
2. Обжарить бекон до золотистой корочки (5 минут)
3. Смешать желтки с тертым пармезаном
4. Соединить горячую пасту с беконом и яичной смесью
5. Добавить перец и подавать немедленно

**Время:** Подготовка 10 мин | Готовка 15 мин | ИТОГО 25 мин

**Выход:** 800 г готового блюда

**Порция:** 200 г (одна порция)

**💸 Себестоимость:**

- По ингредиентам: 891 ₽
- Себестоимость 1 порции: 223 ₽
- Рекомендуемая цена (×3): 669 ₽

**КБЖУ на 1 порцию:** Калории 520 ккал | Б 22 г | Ж 28 г | У 45 г

**КБЖУ на 100 г:** Калории 260 ккал | Б 11 г | Ж 14 г | У 22.5 г

**Аллергены:** глютен, яйца, молочные продукты

**Заготовки и хранение:**

- Пармезан можно натереть заранее (хранить в холодильнике 3 дня)
- Бекон нарезать и хранить в контейнере (+2°C, 2 дня)
- Яичную смесь готовить непосредственно перед подачей

**Особенности и советы от шефа:**

- Не добавлять сливки - это не аутентично
- Смешивать пасту с соусом вне огня
- Использовать только желтки для кремовости
*Совет от RECEPTOR:* Добавить немного воды от варки пасты для идеальной консистенции
*Фишка для продвинутых:* Использовать гуанчале вместо обычного бекона
*Вариации:* Карбонара с грибами, с морепродуктами

**Рекомендация подачи:** Глубокие тарелки, подавать горячим, посыпать дополнительным пармезаном

**Теги для меню:** #паста #итальянская_кухня #классика #бекон #яйца

Сгенерировано RECEPTOR AI — экономьте 2 часа на каждой техкарте"""

    print(f"📋 Test Data:")
    print(f"   User ID: {user_id}")
    print(f"   Tech Card: Паста Карбонара на 4 порции")
    print(f"   Expected: Enhanced JSON structure with detailed analysis")
    print()

    # Test POST /api/analyze-finances
    print("🔍 TESTING POST /api/analyze-finances")
    print("-" * 40)
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/analyze-finances",
            json={
                "user_id": user_id,
                "tech_card": tech_card_content
            },
            timeout=60
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"⏱️  Response Time: {response_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API Response: 200 OK")
            
            try:
                data = response.json()
                print(f"📄 Response Structure: {list(data.keys())}")
                
                if data.get("success"):
                    print("✅ Success Flag: True")
                    
                    analysis = data.get("analysis", {})
                    if analysis:
                        print("✅ Analysis Object: Present")
                        print(f"📋 Analysis Keys: {list(analysis.keys())}")
                        
                        # Test required enhanced fields
                        required_fields = [
                            "detailed_cost_breakdown",
                            "cost_breakdown", 
                            "optimization_tips",
                            "supplier_recommendations",
                            "financial_metrics",
                            "business_intelligence",
                            "risk_analysis",
                            "strategic_recommendations"
                        ]
                        
                        print("\n🔍 ENHANCED FIELDS VERIFICATION:")
                        print("-" * 40)
                        
                        all_fields_present = True
                        for field in required_fields:
                            if field in analysis:
                                field_data = analysis[field]
                                if isinstance(field_data, list):
                                    print(f"✅ {field}: Present ({len(field_data)} items)")
                                elif isinstance(field_data, dict):
                                    print(f"✅ {field}: Present ({len(field_data)} keys)")
                                else:
                                    print(f"✅ {field}: Present (value: {field_data})")
                            else:
                                print(f"❌ {field}: MISSING")
                                all_fields_present = False
                        
                        # Test basic financial data
                        print("\n💰 BASIC FINANCIAL DATA:")
                        print("-" * 40)
                        basic_fields = ["dish_name", "total_cost", "recommended_price", "margin_percent", "profitability_rating"]
                        for field in basic_fields:
                            if field in analysis:
                                print(f"✅ {field}: {analysis[field]}")
                            else:
                                print(f"❌ {field}: MISSING")
                        
                        # Test detailed_cost_breakdown structure
                        if "detailed_cost_breakdown" in analysis:
                            print("\n🔍 DETAILED COST BREAKDOWN ANALYSIS:")
                            print("-" * 40)
                            breakdown = analysis["detailed_cost_breakdown"]
                            if isinstance(breakdown, list) and len(breakdown) > 0:
                                print(f"✅ Ingredient-level analysis: {len(breakdown)} ingredients")
                                sample_ingredient = breakdown[0]
                                expected_keys = ["ingredient", "quantity", "unit_price", "total_cost", "percent_of_total"]
                                for key in expected_keys:
                                    if key in sample_ingredient:
                                        print(f"✅ {key}: Present")
                                    else:
                                        print(f"❌ {key}: Missing in ingredient breakdown")
                            else:
                                print("❌ Detailed cost breakdown is empty or invalid")
                        
                        # Test optimization_tips structure
                        if "optimization_tips" in analysis:
                            print("\n💡 OPTIMIZATION TIPS ANALYSIS:")
                            print("-" * 40)
                            tips = analysis["optimization_tips"]
                            if isinstance(tips, list) and len(tips) > 0:
                                print(f"✅ Optimization tips: {len(tips)} tips provided")
                                sample_tip = tips[0]
                                expected_keys = ["tip", "current_cost", "optimized_cost", "savings", "impact"]
                                for key in expected_keys:
                                    if key in sample_tip:
                                        print(f"✅ {key}: Present")
                                    else:
                                        print(f"❌ {key}: Missing in optimization tip")
                            else:
                                print("❌ Optimization tips are empty or invalid")
                        
                        # Test strategic_recommendations structure
                        if "strategic_recommendations" in analysis:
                            print("\n🎯 STRATEGIC RECOMMENDATIONS ANALYSIS:")
                            print("-" * 40)
                            recommendations = analysis["strategic_recommendations"]
                            if isinstance(recommendations, list) and len(recommendations) > 0:
                                print(f"✅ Strategic recommendations: {len(recommendations)} recommendations")
                                categories = [rec.get("category") for rec in recommendations if "category" in rec]
                                print(f"✅ Categories covered: {categories}")
                            else:
                                print("❌ Strategic recommendations are empty or invalid")
                        
                        # Overall assessment
                        print("\n🎯 OVERALL ASSESSMENT:")
                        print("-" * 40)
                        if all_fields_present:
                            print("✅ ALL ENHANCED FIELDS PRESENT")
                            print("✅ Enhanced FINANCES feature is working correctly")
                            print("✅ Detailed analysis structure verified")
                            return True
                        else:
                            print("❌ SOME ENHANCED FIELDS MISSING")
                            print("❌ Enhanced FINANCES feature needs improvement")
                            return False
                    else:
                        print("❌ Analysis object missing from response")
                        return False
                else:
                    print("❌ Success flag is False")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON Decode Error: {e}")
                print(f"Raw response: {response.text[:500]}...")
                return False
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout (60 seconds)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 ENHANCED FINANCES FEATURE TESTING")
    print("=" * 60)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print()
    
    # Run the enhanced finances test
    success = test_enhanced_finances_feature()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ ENHANCED FINANCES FEATURE: WORKING")
        print("✅ All required enhanced fields verified")
        print("✅ Detailed analysis structure confirmed")
        print("✅ Ready for production use")
    else:
        print("❌ ENHANCED FINANCES FEATURE: ISSUES FOUND")
        print("❌ Some enhanced fields missing or invalid")
        print("❌ Requires investigation and fixes")
    
    print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()