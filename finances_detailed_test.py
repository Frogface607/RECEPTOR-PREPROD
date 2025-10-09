#!/usr/bin/env python3
"""
Detailed FINANCES Feature Response Analysis
"""

import requests
import json
import time

def test_finances_detailed():
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    test_user_id = "test_user_12345"
    
    sample_tech_card = """**Название:** Паста Карбонара на 4 порции

**Категория:** основное

**Описание:** Классическая итальянская паста с беконом, яйцами и пармезаном. Сливочная текстура соуса создается без добавления сливок, только за счет яиц и сыра.

**Ингредиенты:** (на 4 порции)

- Спагетти — 400 г — ~120 ₽
- Бекон — 200 г — ~180 ₽
- Яйца куриные — 4 шт — ~40 ₽
- Пармезан — 100 г — ~250 ₽
- Чеснок — 2 зубчика — ~5 ₽
- Оливковое масло — 30 мл — ~15 ₽
- Черный перец — 2 г — ~3 ₽
- Соль — по вкусу — ~1 ₽

**💸 Себестоимость:**

- По ингредиентам: 614 ₽
- Себестоимость 1 порции: 154 ₽
- Рекомендуемая цена (×3): 462 ₽

**КБЖУ на 1 порцию:** Калории 520 ккал | Б 22 г | Ж 18 г | У 65 г"""

    print("🔍 DETAILED FINANCES ANALYSIS TEST")
    print("=" * 50)
    
    test_data = {
        "user_id": test_user_id,
        "tech_card": sample_tech_card
    }
    
    start_time = time.time()
    response = requests.post(f"{base_url}/analyze-finances", json=test_data)
    response_time = time.time() - start_time
    
    print(f"📊 Status: {response.status_code}")
    print(f"⏱️ Time: {response_time:.2f}s")
    print(f"📄 Size: {len(response.text)} chars")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print("\n📋 FULL RESPONSE STRUCTURE:")
            print("-" * 30)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if "analysis" in data:
                analysis = data["analysis"]
                print(f"\n🎯 KEY FINANCIAL METRICS:")
                print("-" * 30)
                print(f"Dish: {analysis.get('dish_name', 'N/A')}")
                print(f"Total Cost: {analysis.get('total_cost', 'N/A')} ₽")
                print(f"Recommended Price: {analysis.get('recommended_price', 'N/A')} ₽")
                print(f"Margin: {analysis.get('margin_percent', 'N/A')}%")
                print(f"Rating: {analysis.get('profitability_rating', 'N/A')}/5")
                
                # Check for advanced analysis
                advanced_fields = [
                    "cost_breakdown", "optimization_tips", "price_comparison",
                    "seasonal_analysis", "financial_metrics", "strategic_recommendations"
                ]
                
                print(f"\n🔬 ADVANCED ANALYSIS COMPONENTS:")
                print("-" * 30)
                for field in advanced_fields:
                    if field in analysis:
                        print(f"✅ {field}: Present")
                        if isinstance(analysis[field], (list, dict)):
                            print(f"   Type: {type(analysis[field]).__name__}")
                            if isinstance(analysis[field], list):
                                print(f"   Items: {len(analysis[field])}")
                    else:
                        print(f"❌ {field}: Missing")
                        
        except json.JSONDecodeError:
            print("❌ Invalid JSON response")
            print(f"Raw response: {response.text}")
    else:
        print(f"❌ Request failed: {response.text}")

if __name__ == "__main__":
    test_finances_detailed()