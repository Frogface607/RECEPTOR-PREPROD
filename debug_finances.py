#!/usr/bin/env python3
"""
Debug Enhanced FINANCES Feature - Check raw_analysis content
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def debug_finances_response():
    """Debug the finances response to see raw_analysis content"""
    print("🔍 DEBUGGING ENHANCED FINANCES RESPONSE")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    tech_card_content = """**Название:** Паста Карбонара на 4 порции

**Категория:** основное

**Описание:** Классическая итальянская паста с беконом, яйцами и пармезаном.

**Ингредиенты:** (на 4 порции)

- Спагетти — 400 г — ~120 ₽
- Бекон гуанчале — 200 г — ~400 ₽
- Яйца куриные (желтки) — 4 шт — ~40 ₽
- Пармезан тертый — 100 г — ~300 ₽
- Черный перец — 2 г — ~5 ₽
- Соль — 3 г — ~1 ₽
- Оливковое масло — 30 мл — ~25 ₽

**💸 Себестоимость:**

- По ингредиентам: 891 ₽
- Себестоимость 1 порции: 223 ₽
- Рекомендуемая цена (×3): 669 ₽"""

    try:
        response = requests.post(
            f"{BACKEND_URL}/analyze-finances",
            json={
                "user_id": user_id,
                "tech_card": tech_card_content
            },
            timeout=60
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            analysis = data.get("analysis", {})
            
            print(f"📋 Full Analysis Keys: {list(analysis.keys())}")
            
            # Check if there's raw_analysis content
            if "raw_analysis" in analysis:
                print("\n📄 RAW ANALYSIS CONTENT:")
                print("-" * 40)
                raw_content = analysis["raw_analysis"]
                print(raw_content[:1000] + "..." if len(raw_content) > 1000 else raw_content)
                
                # Try to parse as JSON
                print("\n🔍 ATTEMPTING JSON PARSE:")
                print("-" * 40)
                try:
                    parsed_json = json.loads(raw_content)
                    print("✅ Raw analysis is valid JSON!")
                    print(f"📋 JSON Keys: {list(parsed_json.keys())}")
                    
                    # Check for enhanced fields in the JSON
                    enhanced_fields = [
                        "detailed_cost_breakdown",
                        "cost_breakdown", 
                        "optimization_tips",
                        "supplier_recommendations",
                        "financial_metrics",
                        "business_intelligence",
                        "risk_analysis",
                        "strategic_recommendations"
                    ]
                    
                    print("\n🔍 ENHANCED FIELDS IN RAW JSON:")
                    print("-" * 40)
                    for field in enhanced_fields:
                        if field in parsed_json:
                            field_data = parsed_json[field]
                            if isinstance(field_data, list):
                                print(f"✅ {field}: Present ({len(field_data)} items)")
                            elif isinstance(field_data, dict):
                                print(f"✅ {field}: Present ({len(field_data)} keys)")
                            else:
                                print(f"✅ {field}: Present")
                        else:
                            print(f"❌ {field}: MISSING")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Raw analysis is not valid JSON: {e}")
                    print("Raw content might be plain text instead of JSON")
            else:
                print("❌ No raw_analysis field found")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_finances_response()