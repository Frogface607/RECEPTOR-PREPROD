#!/usr/bin/env python3
"""
Comprehensive Enhanced FINANCES Feature Testing
Detailed verification of all enhanced fields and structures
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def comprehensive_finances_test():
    """Comprehensive test of all enhanced FINANCES features"""
    print("🎯 COMPREHENSIVE ENHANCED FINANCES TESTING")
    print("=" * 70)
    
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

**💸 Себестоимость:**

- По ингредиентам: 891 ₽
- Себестоимость 1 порции: 223 ₽
- Рекомендуемая цена (×3): 669 ₽

**КБЖУ на 1 порцию:** Калории 520 ккал | Б 22 г | Ж 28 г | У 45 г"""

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
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        analysis = data.get("analysis", {})
        
        if not data.get("success") or not analysis:
            print("❌ Invalid response structure")
            return False
        
        print("✅ API Response: 200 OK")
        print("✅ Success Flag: True")
        print("✅ Analysis Object: Present")
        
        # Test 1: detailed_cost_breakdown (ingredient-level analysis)
        print("\n🔍 TEST 1: DETAILED COST BREAKDOWN")
        print("-" * 50)
        
        if "detailed_cost_breakdown" in analysis:
            breakdown = analysis["detailed_cost_breakdown"]
            if isinstance(breakdown, list) and len(breakdown) > 0:
                print(f"✅ Ingredient-level analysis: {len(breakdown)} ingredients")
                
                # Check structure of first ingredient
                sample = breakdown[0]
                required_keys = ["ingredient", "quantity", "unit_price", "total_cost", "percent_of_total"]
                all_keys_present = all(key in sample for key in required_keys)
                
                if all_keys_present:
                    print("✅ All required keys present in ingredient breakdown")
                    print(f"   Sample: {sample['ingredient']} - {sample['quantity']} - {sample['total_cost']} ₽ ({sample['percent_of_total']}%)")
                else:
                    print("❌ Missing keys in ingredient breakdown")
                    return False
            else:
                print("❌ Detailed cost breakdown is empty or invalid")
                return False
        else:
            print("❌ detailed_cost_breakdown field missing")
            return False
        
        # Test 2: enhanced cost_breakdown with ingredient lists
        print("\n🔍 TEST 2: ENHANCED COST BREAKDOWN")
        print("-" * 50)
        
        if "cost_breakdown" in analysis:
            cost_breakdown = analysis["cost_breakdown"]
            if isinstance(cost_breakdown, list) and len(cost_breakdown) > 0:
                print(f"✅ Cost breakdown by categories: {len(cost_breakdown)} categories")
                
                # Check structure
                sample = cost_breakdown[0]
                required_keys = ["category", "amount", "percent", "items"]
                all_keys_present = all(key in sample for key in required_keys)
                
                if all_keys_present:
                    print("✅ All required keys present in cost breakdown")
                    print(f"   Sample: {sample['category']} - {sample['amount']} ₽ ({sample['percent']}%) - {len(sample['items'])} items")
                else:
                    print("❌ Missing keys in cost breakdown")
                    return False
            else:
                print("❌ Cost breakdown is empty or invalid")
                return False
        else:
            print("❌ cost_breakdown field missing")
            return False
        
        # Test 3: optimization_tips with current/optimized costs
        print("\n🔍 TEST 3: OPTIMIZATION TIPS")
        print("-" * 50)
        
        if "optimization_tips" in analysis:
            tips = analysis["optimization_tips"]
            if isinstance(tips, list) and len(tips) > 0:
                print(f"✅ Optimization tips: {len(tips)} tips provided")
                
                # Check structure
                sample = tips[0]
                required_keys = ["tip", "current_cost", "optimized_cost", "savings", "impact"]
                all_keys_present = all(key in sample for key in required_keys)
                
                if all_keys_present:
                    print("✅ All required keys present in optimization tips")
                    print(f"   Sample: {sample['current_cost']} → {sample['optimized_cost']} (savings: {sample['savings']})")
                else:
                    print("❌ Missing keys in optimization tips")
                    return False
            else:
                print("❌ Optimization tips are empty or invalid")
                return False
        else:
            print("❌ optimization_tips field missing")
            return False
        
        # Test 4: supplier_recommendations
        print("\n🔍 TEST 4: SUPPLIER RECOMMENDATIONS")
        print("-" * 50)
        
        if "supplier_recommendations" in analysis:
            suppliers = analysis["supplier_recommendations"]
            if isinstance(suppliers, list) and len(suppliers) > 0:
                print(f"✅ Supplier recommendations: {len(suppliers)} recommendations")
                
                # Check structure
                sample = suppliers[0]
                expected_keys = ["category", "current_supplier", "recommended_supplier", "savings_percent", "quality_impact"]
                keys_present = [key for key in expected_keys if key in sample]
                
                if len(keys_present) >= 3:  # At least 3 of the expected keys
                    print("✅ Supplier recommendation structure valid")
                    print(f"   Sample: {sample.get('category', 'N/A')} - {sample.get('savings_percent', 'N/A')} savings")
                else:
                    print("❌ Invalid supplier recommendation structure")
                    return False
            else:
                print("❌ Supplier recommendations are empty or invalid")
                return False
        else:
            print("❌ supplier_recommendations field missing")
            return False
        
        # Test 5: enhanced financial_metrics
        print("\n🔍 TEST 5: ENHANCED FINANCIAL METRICS")
        print("-" * 50)
        
        if "financial_metrics" in analysis:
            metrics = analysis["financial_metrics"]
            if isinstance(metrics, dict) and len(metrics) > 0:
                print(f"✅ Financial metrics: {len(metrics)} metrics provided")
                
                # Check for key metrics
                expected_metrics = ["break_even_portions", "profit_per_portion", "roi_percent", "gross_margin"]
                found_metrics = [metric for metric in expected_metrics if metric in metrics]
                
                if len(found_metrics) >= 2:  # At least 2 key metrics
                    print("✅ Key financial metrics present")
                    for metric in found_metrics:
                        print(f"   {metric}: {metrics[metric]}")
                else:
                    print("❌ Missing key financial metrics")
                    return False
            else:
                print("❌ Financial metrics are empty or invalid")
                return False
        else:
            print("❌ financial_metrics field missing")
            return False
        
        # Test 6: business_intelligence section
        print("\n🔍 TEST 6: BUSINESS INTELLIGENCE")
        print("-" * 50)
        
        if "business_intelligence" in analysis:
            bi = analysis["business_intelligence"]
            if isinstance(bi, dict) and len(bi) > 0:
                print(f"✅ Business intelligence: {len(bi)} insights provided")
                
                # Check for key BI fields
                expected_fields = ["target_customers", "optimal_pricing_strategy", "upsell_opportunities", "profitability_rank"]
                found_fields = [field for field in expected_fields if field in bi]
                
                if len(found_fields) >= 2:  # At least 2 BI insights
                    print("✅ Key business intelligence insights present")
                    for field in found_fields:
                        print(f"   {field}: {bi[field]}")
                else:
                    print("❌ Missing key business intelligence insights")
                    return False
            else:
                print("❌ Business intelligence is empty or invalid")
                return False
        else:
            print("❌ business_intelligence field missing")
            return False
        
        # Test 7: risk_analysis section
        print("\n🔍 TEST 7: RISK ANALYSIS")
        print("-" * 50)
        
        if "risk_analysis" in analysis:
            risk = analysis["risk_analysis"]
            if isinstance(risk, dict) and len(risk) > 0:
                print(f"✅ Risk analysis: {len(risk)} risk factors analyzed")
                
                # Check for key risk fields
                expected_fields = ["price_volatility", "supply_chain_risks", "market_risks", "recommendations"]
                found_fields = [field for field in expected_fields if field in risk]
                
                if len(found_fields) >= 2:  # At least 2 risk categories
                    print("✅ Key risk analysis categories present")
                    for field in found_fields:
                        print(f"   {field}: {type(risk[field]).__name__}")
                else:
                    print("❌ Missing key risk analysis categories")
                    return False
            else:
                print("❌ Risk analysis is empty or invalid")
                return False
        else:
            print("❌ risk_analysis field missing")
            return False
        
        # Test 8: strategic_recommendations with categories
        print("\n🔍 TEST 8: STRATEGIC RECOMMENDATIONS")
        print("-" * 50)
        
        if "strategic_recommendations" in analysis:
            recommendations = analysis["strategic_recommendations"]
            if isinstance(recommendations, list) and len(recommendations) > 0:
                print(f"✅ Strategic recommendations: {len(recommendations)} recommendations")
                
                # Check categories
                categories = [rec.get("category") for rec in recommendations if "category" in rec]
                expected_categories = ["Ценообразование", "Закупки", "Меню"]
                found_categories = [cat for cat in expected_categories if cat in categories]
                
                if len(found_categories) >= 2:  # At least 2 expected categories
                    print("✅ Key strategic recommendation categories present")
                    print(f"   Categories: {categories}")
                else:
                    print("❌ Missing key strategic recommendation categories")
                    return False
            else:
                print("❌ Strategic recommendations are empty or invalid")
                return False
        else:
            print("❌ strategic_recommendations field missing")
            return False
        
        # Final assessment
        print("\n🎯 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        print("✅ ALL 8 ENHANCED FEATURES VERIFIED:")
        print("   1. ✅ Detailed cost breakdown (ingredient-level analysis)")
        print("   2. ✅ Enhanced cost breakdown with ingredient lists")
        print("   3. ✅ Optimization tips with current/optimized costs")
        print("   4. ✅ Supplier recommendations")
        print("   5. ✅ Enhanced financial metrics")
        print("   6. ✅ Business intelligence section")
        print("   7. ✅ Risk analysis section")
        print("   8. ✅ Strategic recommendations with categories")
        print("\n🚀 ENHANCED FINANCES PRO FEATURE: FULLY FUNCTIONAL")
        print("🎉 Ready for production use with comprehensive financial analysis")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 COMPREHENSIVE ENHANCED FINANCES TESTING")
    print("=" * 70)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print()
    
    success = comprehensive_finances_test()
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success

if __name__ == "__main__":
    main()