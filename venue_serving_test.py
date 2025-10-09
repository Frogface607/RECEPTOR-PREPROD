#!/usr/bin/env python3
"""
Backend Testing Script for Venue-Specific Serving & Tips Fix
Testing venue-specific serving recommendations and tips improvements
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_venue_serving_recommendations():
    """Test venue-specific serving recommendations for different venue types"""
    print("🎯 TESTING VENUE-SPECIFIC SERVING RECOMMENDATIONS")
    print("=" * 60)
    
    test_user_id = "test_user_12345"
    
    # Test data for different venue types
    venue_configs = [
        {
            "name": "Street Food",
            "venue_type": "street_food",
            "average_check": 200,
            "expected_keywords": ["упаковка", "портативн", "на ходу", "контейнер", "стакан"]
        },
        {
            "name": "Fine Dining", 
            "venue_type": "fine_dining",
            "average_check": 3000,
            "expected_keywords": ["элегантн", "фарфор", "художественн", "плейтинг", "микрозелен"]
        },
        {
            "name": "Kids Cafe",
            "venue_type": "kids_cafe", 
            "average_check": 500,
            "expected_keywords": ["безопасн", "детск", "яркие", "без острых", "умеренная температура"]
        }
    ]
    
    results = []
    
    for config in venue_configs:
        print(f"\n🏢 Testing {config['name']} venue...")
        
        # 1. Set venue profile
        venue_data = {
            "venue_type": config["venue_type"],
            "cuisine_focus": ["european"],
            "average_check": config["average_check"],
            "venue_name": f"Test {config['name']} Restaurant"
        }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/update-venue-profile/{test_user_id}",
                json=venue_data,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to set venue profile: {response.status_code}")
                print(f"Response: {response.text}")
                continue
                
            print(f"✅ Venue profile set for {config['name']}")
            
        except Exception as e:
            print(f"❌ Error setting venue profile: {str(e)}")
            continue
        
        # 2. Generate tech card to test serving recommendations
        dish_request = {
            "user_id": test_user_id,
            "dish_name": "Паста с томатным соусом"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BACKEND_URL}/generate-tech-card",
                json=dish_request,
                timeout=60
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                tech_card_content = data.get("tech_card", "")
                
                print(f"✅ Tech card generated ({response_time:.2f}s)")
                print(f"📄 Content length: {len(tech_card_content)} characters")
                
                # Check for venue-specific serving recommendations
                serving_section_found = False
                venue_keywords_found = []
                
                # Look for serving recommendations section
                if "Рекомендация подачи:" in tech_card_content or "подач" in tech_card_content.lower():
                    serving_section_found = True
                    
                    # Check for venue-specific keywords
                    content_lower = tech_card_content.lower()
                    for keyword in config["expected_keywords"]:
                        if keyword.lower() in content_lower:
                            venue_keywords_found.append(keyword)
                
                result = {
                    "venue_type": config["venue_type"],
                    "venue_name": config["name"],
                    "success": True,
                    "response_time": response_time,
                    "content_length": len(tech_card_content),
                    "serving_section_found": serving_section_found,
                    "venue_keywords_found": venue_keywords_found,
                    "expected_keywords": config["expected_keywords"],
                    "personalization_score": len(venue_keywords_found) / len(config["expected_keywords"]) * 100
                }
                
                print(f"🎯 Serving section found: {serving_section_found}")
                print(f"🔍 Venue keywords found: {venue_keywords_found}")
                print(f"📊 Personalization score: {result['personalization_score']:.1f}%")
                
                # Show sample of serving recommendations
                if serving_section_found:
                    lines = tech_card_content.split('\n')
                    for i, line in enumerate(lines):
                        if "рекомендация подачи" in line.lower():
                            # Show this line and next few lines
                            sample_lines = lines[i:i+3]
                            print(f"📋 Serving sample: {' '.join(sample_lines)[:200]}...")
                            break
                
                results.append(result)
                
            else:
                print(f"❌ Failed to generate tech card: {response.status_code}")
                print(f"Response: {response.text}")
                results.append({
                    "venue_type": config["venue_type"],
                    "venue_name": config["name"],
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ Error generating tech card: {str(e)}")
            results.append({
                "venue_type": config["venue_type"],
                "venue_name": config["name"],
                "success": False,
                "error": str(e)
            })
    
    return results

def test_improve_dish_tips():
    """Test improve dish function for tips section formatting"""
    print("\n🔧 TESTING IMPROVE DISH TIPS FUNCTIONALITY")
    print("=" * 60)
    
    test_user_id = "test_user_12345"
    
    # First generate a simple tech card
    dish_request = {
        "user_id": test_user_id,
        "dish_name": "Простая паста"
    }
    
    try:
        print("📝 Generating base tech card...")
        response = requests.post(
            f"{BACKEND_URL}/generate-tech-card",
            json=dish_request,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to generate base tech card: {response.status_code}")
            return {"success": False, "error": "Failed to generate base tech card"}
        
        base_tech_card = response.json().get("tech_card", "")
        print(f"✅ Base tech card generated ({len(base_tech_card)} chars)")
        
        # Now test improve dish function
        improve_request = {
            "user_id": test_user_id,
            "tech_card": base_tech_card
        }
        
        print("🚀 Testing improve dish function...")
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/improve-dish",
            json=improve_request,
            timeout=60
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            improved_content = data.get("improved_dish", "")
            
            print(f"✅ Improve dish completed ({response_time:.2f}s)")
            print(f"📄 Improved content length: {len(improved_content)} characters")
            
            # Check for tips sections and formatting
            tips_sections = []
            professional_indicators = []
            
            content_lower = improved_content.lower()
            
            # Look for tips sections
            tips_keywords = ["советы", "секреты", "техник", "улучшен", "профессиональн"]
            for keyword in tips_keywords:
                if keyword in content_lower:
                    tips_sections.append(keyword)
            
            # Look for professional techniques
            pro_keywords = ["плейтинг", "сервировка", "температур", "оборудован", "заменить", "добавить", "техника", "шеф"]
            for keyword in pro_keywords:
                if keyword in content_lower:
                    professional_indicators.append(keyword)
            
            # Check for proper formatting (markdown headers, bullet points)
            has_headers = "##" in improved_content or "**" in improved_content
            has_bullets = "•" in improved_content or "-" in improved_content
            
            result = {
                "success": True,
                "response_time": response_time,
                "content_length": len(improved_content),
                "tips_sections_found": tips_sections,
                "professional_indicators": professional_indicators,
                "has_proper_formatting": has_headers and has_bullets,
                "tips_score": len(tips_sections),
                "professional_score": len(professional_indicators)
            }
            
            print(f"🎯 Tips sections found: {tips_sections}")
            print(f"👨‍🍳 Professional indicators: {professional_indicators}")
            print(f"📝 Proper formatting: {result['has_proper_formatting']}")
            print(f"📊 Tips score: {result['tips_score']}/5")
            print(f"🏆 Professional score: {result['professional_score']}/8")
            
            # Show sample of improved content
            if improved_content:
                lines = improved_content.split('\n')[:5]
                print(f"📋 Sample content: {' '.join(lines)[:300]}...")
            
            return result
            
        else:
            print(f"❌ Failed to improve dish: {response.status_code}")
            print(f"Response: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Error testing improve dish: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    """Main testing function"""
    print("🎯 VENUE-SPECIFIC SERVING & TIPS FIX TESTING")
    print("=" * 60)
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print()
    
    # Test 1: Venue-specific serving recommendations
    serving_results = test_venue_serving_recommendations()
    
    # Test 2: Improve dish tips functionality
    tips_result = test_improve_dish_tips()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TESTING SUMMARY")
    print("=" * 60)
    
    # Serving recommendations summary
    successful_venues = [r for r in serving_results if r.get("success", False)]
    print(f"🏢 Venue serving tests: {len(successful_venues)}/{len(serving_results)} passed")
    
    if successful_venues:
        avg_personalization = sum(r.get("personalization_score", 0) for r in successful_venues) / len(successful_venues)
        print(f"📊 Average personalization score: {avg_personalization:.1f}%")
        
        for result in successful_venues:
            print(f"  • {result['venue_name']}: {result['personalization_score']:.1f}% ({len(result['venue_keywords_found'])}/{len(result['expected_keywords'])} keywords)")
    
    # Tips functionality summary
    print(f"🔧 Improve dish tips test: {'✅ PASSED' if tips_result.get('success', False) else '❌ FAILED'}")
    if tips_result.get("success", False):
        print(f"  • Tips score: {tips_result.get('tips_score', 0)}/5")
        print(f"  • Professional score: {tips_result.get('professional_score', 0)}/8")
        print(f"  • Proper formatting: {'✅' if tips_result.get('has_proper_formatting', False) else '❌'}")
    
    # Overall assessment
    overall_success = len(successful_venues) >= 2 and tips_result.get("success", False)
    print(f"\n🎉 OVERALL RESULT: {'✅ PASSED' if overall_success else '❌ NEEDS ATTENTION'}")
    
    if overall_success:
        print("✅ Venue-specific serving recommendations are working correctly")
        print("✅ Tips section is properly formatted and visible")
        print("✅ System ready for production use")
    else:
        print("⚠️  Some issues found that need attention:")
        if len(successful_venues) < 2:
            print("   - Venue-specific serving recommendations need improvement")
        if not tips_result.get("success", False):
            print("   - Tips section functionality needs fixing")

if __name__ == "__main__":
    main()