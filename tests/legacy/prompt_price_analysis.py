#!/usr/bin/env python3
"""
Price Analysis - Check AI Prompt vs Reality
"""

def analyze_prompt_pricing():
    """Analyze the pricing in the AI prompt vs real market expectations"""
    
    print("🔍 AI PROMPT PRICING ANALYSIS")
    print("=" * 50)
    
    # From the backend server.py GOLDEN_PROMPT
    prompt_prices = {
        "Куриная грудка": "400-500₽/кг",
        "Говядина премиум": "1000-1200₽/кг",  # This is the issue!
        "Свинина": "350-450₽/кг",
        "Масло растительное": "120-150₽/л",
        "Лук": "40-60₽/кг"
    }
    
    # Real 2025 market expectations from user
    real_market_prices = {
        "Фарш говяжий": "~500₽/кг",
        "Паста": "~80₽/кг", 
        "Масло растительное": "~150₽/л"
    }
    
    print("📋 AI PROMPT PRICES:")
    for item, price in prompt_prices.items():
        print(f"   {item}: {price}")
        
    print("\n📋 REAL MARKET EXPECTATIONS (2025):")
    for item, price in real_market_prices.items():
        print(f"   {item}: {price}")
        
    print("\n🔍 ANALYSIS:")
    print("❌ PROBLEM IDENTIFIED: AI prompt uses 'Говядина премиум: 1000-1200₽/кг'")
    print("   But user expects 'Фарш говяжий: ~500₽/кг'")
    print("   Premium beef ≠ Ground beef (mince)")
    print("")
    print("💡 EXPLANATION:")
    print("   • Premium beef cuts: 1000-1200₽/kg (steaks, tenderloin)")
    print("   • Ground beef (mince): 400-600₽/kg (mixed cuts, processed)")
    print("   • AI is using premium beef pricing for mince!")
    print("")
    print("🔧 SOLUTION:")
    print("   Update AI prompt to include specific mince pricing:")
    print("   'Фарш говяжий: 400-600₽/кг'")
    print("   'Фарш свиной: 300-450₽/кг'")
    print("   'Фарш смешанный: 350-500₽/кг'")
    
    # Calculate what the AI generated
    print("\n📊 CURRENT AI CALCULATION:")
    print("   Moscow coefficient: 1.25x")
    print("   Premium beef base: ~1100₽/kg")
    print("   With Moscow coefficient: 1100 × 1.25 = 1375₽/kg")
    print("   For 150g: 1375 × 0.15 = 206₽ (close to actual 187.5₽)")
    print("   ✅ AI calculation is mathematically correct")
    print("   ❌ But using wrong base price for mince")
    
    print("\n📊 CORRECT CALCULATION SHOULD BE:")
    print("   Mince base price: ~500₽/kg")
    print("   With Moscow coefficient: 500 × 1.25 = 625₽/kg") 
    print("   For 150g: 625 × 0.15 = 94₽ (vs current 187.5₽)")
    print("   💰 This would be 2x cheaper and more realistic")

if __name__ == "__main__":
    analyze_prompt_pricing()