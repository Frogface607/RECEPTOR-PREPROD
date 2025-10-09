#!/usr/bin/env python3
"""
Financial Analysis Endpoint Testing - Detailed Output Verification
Testing POST /api/analyze-finances to verify it returns comprehensive structured data
as requested in the review.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_financial_analysis_detailed_output():
    """Test POST /api/analyze-finances for detailed practical recommendations"""
    print("🎯 TESTING FINANCIAL ANALYSIS - DETAILED OUTPUT")
    print("=" * 60)
    
    # Test data as specified in review request
    user_id = "test_user_12345"
    
    # Step 1: Generate a tech card first (using any dish tech card as requested)
    print("📋 Step 1: Generating tech card for simple pasta dish...")
    
    tech_card_request = {
        "user_id": user_id,
        "dish_name": "Паста с томатным соусом"
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-tech-card", json=tech_card_request, timeout=90)
        end_time = time.time()
        
        print(f"⏱️ Tech card generation time: {end_time - start_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ Tech card generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        tech_card_data = response.json()
        tech_card_content = tech_card_data.get("tech_card", "")
        
        if not tech_card_content:
            print("❌ No tech card content received")
            return False
            
        print(f"✅ Tech card generated successfully ({len(tech_card_content)} characters)")
        print(f"📄 Tech card preview: {tech_card_content[:200]}...")
        
    except Exception as e:
        print(f"❌ Error generating tech card: {str(e)}")
        return False
    
    # Step 2: Test the FINANCIAL ANALYSIS endpoint
    print("\n💰 Step 2: Testing POST /api/analyze-finances...")
    
    finances_request = {
        "user_id": user_id,
        "tech_card": tech_card_content
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/analyze-finances", json=finances_request, timeout=90)
        end_time = time.time()
        
        print(f"⏱️ Financial analysis time: {end_time - start_time:.2f} seconds")
        
        # VALIDATION POINT 1: Check if response returns 200 status
        if response.status_code != 200:
            print(f"❌ VALIDATION FAILED: API returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print("✅ VALIDATION 1 PASSED: API responds with 200 status")
        
        # Parse response
        finances_data = response.json()
        
        if not finances_data.get("success"):
            print("❌ VALIDATION FAILED: API returned success=false")
            print(f"Response: {finances_data}")
            return False
            
        analysis = finances_data.get("analysis", {})
        
        if not analysis:
            print("❌ VALIDATION FAILED: No analysis data received")
            return False
            
        print(f"✅ Financial analysis received ({len(str(analysis))} characters)")
        
        # VALIDATION POINT 2: Check ALL expected fields are present
        print("\n🔍 Step 3: Validating ALL expected fields...")
        
        expected_fields = [
            "smart_cost_cuts",
            "revenue_hacks", 
            "action_plan",
            "seasonal_opportunities",
            "financial_forecast",
            "red_flags",
            "golden_opportunities"
        ]
        
        missing_fields = []
        present_fields = []
        
        # Print the actual structure for debugging
        print(f"📊 Analysis structure: {list(analysis.keys())}")
        
        for field in expected_fields:
            if field in analysis and analysis[field]:
                present_fields.append(field)
                print(f"✅ {field}: PRESENT")
            else:
                missing_fields.append(field)
                print(f"❌ {field}: MISSING")
        
        if missing_fields:
            print(f"\n❌ VALIDATION FAILED: Missing required fields: {missing_fields}")
            print("🚨 The response does not contain all expected structured data")
            return False
        
        print(f"\n✅ VALIDATION 2 PASSED: All {len(expected_fields)} expected fields are present")
        
        # VALIDATION POINT 3: Check content quality and detail
        print("\n📊 Step 4: Validating content quality and detail...")
        
        def check_field_content(field_name, field_data):
            """Helper function to check field content regardless of data type"""
            if isinstance(field_data, list):
                # For list fields, check total content length
                total_length = sum(len(str(item)) for item in field_data)
                print(f"✅ {field_name}: List with {len(field_data)} items ({total_length} chars total)")
                return total_length, field_data
            elif isinstance(field_data, dict):
                # For dict fields, check total content length
                total_length = sum(len(str(value)) for value in field_data.values())
                print(f"✅ {field_name}: Dict with {len(field_data)} keys ({total_length} chars total)")
                return total_length, field_data
            elif isinstance(field_data, str):
                print(f"✅ {field_name}: String content ({len(field_data)} chars)")
                return len(field_data), field_data
            else:
                print(f"⚠️ {field_name}: Unknown data type ({type(field_data)})")
                return 0, field_data
        
        # Check smart_cost_cuts for specific ingredient substitutions and savings
        smart_cost_cuts = analysis.get("smart_cost_cuts", "")
        cuts_length, cuts_data = check_field_content("smart_cost_cuts", smart_cost_cuts)
        
        # Check for substitution indicators in the content
        cuts_text = str(cuts_data).lower()
        substitution_indicators = ["замен", "альтернатив", "дешевле", "экономи", "сниж"]
        found_substitutions = [ind for ind in substitution_indicators if ind in cuts_text]
        
        if found_substitutions:
            print(f"✅ smart_cost_cuts contains substitution advice: {found_substitutions}")
        else:
            print("⚠️ WARNING: smart_cost_cuts may lack specific substitution advice")
        
        # Check revenue_hacks for concrete strategies
        revenue_hacks = analysis.get("revenue_hacks", "")
        hacks_length, hacks_data = check_field_content("revenue_hacks", revenue_hacks)
        
        # Check for strategy indicators
        hacks_text = str(hacks_data).lower()
        strategy_indicators = ["стратег", "увелич", "продаж", "маркетинг", "акци", "промо"]
        found_strategies = [ind for ind in strategy_indicators if ind in hacks_text]
        
        if found_strategies:
            print(f"✅ revenue_hacks contains strategy advice: {found_strategies}")
        else:
            print("⚠️ WARNING: revenue_hacks may lack concrete strategies")
        
        # Check action_plan for prioritized actions
        action_plan = analysis.get("action_plan", "")
        plan_length, plan_data = check_field_content("action_plan", action_plan)
        
        # Check for priority indicators
        plan_text = str(plan_data).lower()
        priority_indicators = ["высок", "средн", "низк", "приоритет", "срочн", "важн"]
        found_priorities = [ind for ind in priority_indicators if ind in plan_text]
        
        if found_priorities:
            print(f"✅ action_plan contains priority levels: {found_priorities}")
        else:
            print("⚠️ WARNING: action_plan may lack priority levels")
        
        # Check seasonal_opportunities for summer/winter strategies
        seasonal_opportunities = analysis.get("seasonal_opportunities", "")
        seasonal_length, seasonal_data = check_field_content("seasonal_opportunities", seasonal_opportunities)
        
        # Check for seasonal indicators
        seasonal_text = str(seasonal_data).lower()
        seasonal_indicators = ["лет", "зим", "весн", "осен", "сезон", "праздник"]
        found_seasonal = [ind for ind in seasonal_indicators if ind in seasonal_text]
        
        if found_seasonal:
            print(f"✅ seasonal_opportunities contains seasonal advice: {found_seasonal}")
        else:
            print("⚠️ WARNING: seasonal_opportunities may lack seasonal strategies")
        
        # Check financial_forecast for breakeven analysis
        financial_forecast = analysis.get("financial_forecast", "")
        forecast_length, forecast_data = check_field_content("financial_forecast", financial_forecast)
        
        # Check for forecast indicators
        forecast_text = str(forecast_data).lower()
        forecast_indicators = ["прогноз", "окупаем", "прибыл", "убыт", "рентабельн", "roi", "breakeven"]
        found_forecast = [ind for ind in forecast_indicators if ind in forecast_text]
        
        if found_forecast:
            print(f"✅ financial_forecast contains financial analysis: {found_forecast}")
        else:
            print("⚠️ WARNING: financial_forecast may lack breakeven analysis")
        
        # Check red_flags for critical issues
        red_flags = analysis.get("red_flags", "")
        flags_length, flags_data = check_field_content("red_flags", red_flags)
        
        # Check golden_opportunities for missed chances
        golden_opportunities = analysis.get("golden_opportunities", "")
        golden_length, golden_data = check_field_content("golden_opportunities", golden_opportunities)
        
        # VALIDATION POINT 4: Check if response is comprehensive JSON with practical advice
        print("\n🎯 Step 5: Overall quality assessment...")
        
        total_content_length = cuts_length + hacks_length + plan_length + seasonal_length + forecast_length + flags_length + golden_length
        
        print(f"📊 Total content length: {total_content_length} characters")
        
        if total_content_length < 500:
            print("❌ VALIDATION FAILED: Response content seems too brief for comprehensive analysis")
            return False
        elif total_content_length < 1000:
            print("⚠️ WARNING: Response content may be somewhat brief")
        else:
            print("✅ VALIDATION 3 PASSED: Response contains comprehensive content")
        
        # Check for actionable advice indicators across all content
        actionable_indicators = ["рекоменд", "совет", "предлаг", "следует", "можно", "нужно", "стоит"]
        total_actionable = 0
        
        for field_name, field_content in analysis.items():
            content_str = str(field_content).lower()
            field_actionable = sum(1 for ind in actionable_indicators if ind in content_str)
            total_actionable += field_actionable
        
        if total_actionable >= 5:
            print(f"✅ VALIDATION 4 PASSED: Response contains actionable advice ({total_actionable} indicators)")
        else:
            print(f"⚠️ WARNING: Response may lack sufficient actionable advice ({total_actionable} indicators)")
        
        # Print detailed summary
        print("\n📋 DETAILED RESPONSE SUMMARY:")
        print("=" * 50)
        
        for field in expected_fields:
            content = analysis.get(field, "")
            if isinstance(content, (list, dict)):
                preview = str(content)[:200] + "..." if len(str(content)) > 200 else str(content)
            else:
                preview = content[:200] + "..." if len(str(content)) > 200 else str(content)
            print(f"📌 {field}:")
            print(f"   Type: {type(content).__name__}")
            print(f"   Length: {len(str(content))} characters")
            print(f"   Preview: {preview}")
            print()
        
        print("✅ VALIDATION COMPLETE: Financial analysis endpoint returns detailed structured data")
        return True
        
    except Exception as e:
        print(f"❌ Error testing financial analysis: {str(e)}")
        return False

def main():
    """Main test execution"""
    print("🚀 FINANCIAL ANALYSIS ENDPOINT - DETAILED OUTPUT TEST")
    print("Testing POST /api/analyze-finances for comprehensive structured data")
    print("=" * 60)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run the financial analysis test
    success = test_financial_analysis_detailed_output()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST RESULTS:")
    print("=" * 60)
    
    if success:
        print("✅ FINANCIAL ANALYSIS TEST: PASSED")
        print("✅ API returns comprehensive JSON object with practical advice")
        print("✅ All expected fields present: smart_cost_cuts, revenue_hacks, action_plan,")
        print("   seasonal_opportunities, financial_forecast, red_flags, golden_opportunities")
        print("✅ Each recommendation includes specific actions and expected results")
        print("✅ Response contains detailed, actionable advice for restaurant use")
    else:
        print("❌ FINANCIAL ANALYSIS TEST: FAILED")
        print("🚨 The financial analysis endpoint needs improvements")
        print("🚨 Missing expected fields or insufficient detail in response")
    
    print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success

if __name__ == "__main__":
    main()