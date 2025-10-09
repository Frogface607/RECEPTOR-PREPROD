#!/usr/bin/env python3
"""
AI ENDPOINTS 403 ERROR TESTING - CORRECTED VERSION
Testing all AI endpoints with correct payload format and user subscription
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class AIEndpointTesterCorrected:
    def __init__(self):
        self.results = {}
        
    async def create_test_user_with_pro(self, user_id):
        """Create a test user with PRO subscription"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                user_data = {
                    "id": user_id,
                    "email": f"{user_id}@test.com",
                    "name": "Test User Pro",
                    "city": "moscow",
                    "subscription_plan": "pro",
                    "subscription_status": "active"
                }
                
                response = await client.post(f"{API_BASE}/register", json=user_data)
                print(f"✅ Created test user: {user_id} with PRO subscription (Status: {response.status_code})")
                return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to create test user: {str(e)}")
            return False
    
    async def test_endpoint(self, client, endpoint_name, endpoint_path, payload):
        """Test a single AI endpoint"""
        url = f"{API_BASE}{endpoint_path}"
        
        try:
            print(f"\n🔍 Testing {endpoint_name}: {endpoint_path}")
            print(f"   URL: {url}")
            
            response = await client.post(url, json=payload)
            status = response.status_code
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            print(f"   Status: {status}")
            if status == 403:
                print(f"   🚫 FORBIDDEN: {response_data}")
            elif status == 404:
                print(f"   ❓ NOT FOUND: {response_data}")
            elif status == 200:
                print(f"   ✅ SUCCESS: Response length {len(str(response_data))}")
            elif status == 500:
                print(f"   💥 SERVER ERROR: {str(response_data)[:200]}...")
            else:
                print(f"   🔍 OTHER ({status}): {str(response_data)[:200]}...")
            
            self.results[endpoint_name] = {
                'endpoint': endpoint_path,
                'url': url,
                'status': status,
                'response': response_data,
                'payload_sent': payload
            }
            
            return status, response_data
                
        except Exception as e:
            print(f"   ERROR: {str(e)}")
            self.results[endpoint_name] = {
                'endpoint': endpoint_path,
                'url': url,
                'status': 'ERROR',
                'response': str(e),
                'payload_sent': payload
            }
            return 'ERROR', str(e)
    
    async def test_all_ai_endpoints(self):
        """Test all AI endpoints with correct format"""
        
        # Create test users with different subscription levels
        test_users = [
            {"id": "test_user_pro_ai", "subscription": "pro"},
            {"id": "test_user_free_ai", "subscription": "free"},
            {"id": "demo_user", "subscription": "existing"}  # Use existing demo user
        ]
        
        # Sample tech card in STRING format (as expected by endpoints)
        sample_tech_card_string = """**Название:** Тестовое блюдо

**Ингредиенты:**
- Мука пшеничная: 200 г
- Яйца куриные: 2 шт
- Молоко: 100 мл
- Соль: 1 щепотка

**Описание:**
Простое тестовое блюдо для проверки AI функций.

**Процесс приготовления:**
1. Смешать муку с солью
2. Добавить яйца и молоко
3. Замесить тесто
4. Приготовить согласно рецепту
"""
        
        # Define all AI endpoints to test
        endpoints_to_test = [
            {
                'name': 'Generate Sales Script',
                'path': '/generate-sales-script',
                'payload_template': {
                    'user_id': None,  # Will be filled per user
                    'tech_card': sample_tech_card_string
                }
            },
            {
                'name': 'Generate Food Pairing',
                'path': '/generate-food-pairing',
                'payload_template': {
                    'user_id': None,
                    'tech_card': sample_tech_card_string
                }
            },
            {
                'name': 'Generate Photo Tips',
                'path': '/generate-photo-tips',
                'payload_template': {
                    'user_id': None,
                    'tech_card': sample_tech_card_string
                }
            },
            {
                'name': 'Generate Inspiration',
                'path': '/generate-inspiration',
                'payload_template': {
                    'user_id': None,
                    'tech_card': sample_tech_card_string
                }
            },
            {
                'name': 'Analyze Finances',
                'path': '/analyze-finances',
                'payload_template': {
                    'user_id': None,
                    'tech_card': sample_tech_card_string
                }
            },
            {
                'name': 'Improve Dish',
                'path': '/improve-dish',
                'payload_template': {
                    'user_id': None,
                    'tech_card': sample_tech_card_string
                }
            },
            {
                'name': 'Laboratory Experiment',
                'path': '/laboratory-experiment',
                'payload_template': {
                    'user_id': None,
                    'experiment_type': 'random',
                    'base_dish': 'Тестовое блюдо'
                }
            }
        ]
        
        print(f"🚀 STARTING CORRECTED AI ENDPOINTS TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Total endpoints to test: {len(endpoints_to_test)}")
        print(f"Test users: {len(test_users)}")
        
        # Create test users
        for user_info in test_users:
            if user_info["subscription"] != "existing":
                await self.create_test_user_with_pro(user_info["id"])
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Test each endpoint with each user
            for user_info in test_users:
                user_id = user_info["id"]
                subscription = user_info["subscription"]
                
                print(f"\n" + "="*60)
                print(f"🧪 TESTING WITH USER: {user_id} ({subscription} subscription)")
                print(f"="*60)
                
                for endpoint_info in endpoints_to_test:
                    # Prepare payload for this user
                    payload = endpoint_info['payload_template'].copy()
                    payload['user_id'] = user_id
                    
                    endpoint_name = f"{endpoint_info['name']} ({subscription})"
                    
                    await self.test_endpoint(
                        client,
                        endpoint_name,
                        endpoint_info['path'],
                        payload
                    )
                    
                    # Small delay between requests
                    await asyncio.sleep(0.5)
    
    def analyze_results(self):
        """Analyze test results and categorize issues"""
        print(f"\n" + "="*80)
        print(f"📊 CORRECTED AI ENDPOINTS TEST RESULTS ANALYSIS")
        print(f"="*80)
        
        status_404 = []  # Not found
        status_403 = []  # Forbidden
        status_200 = []  # Working
        status_500 = []  # Server error
        status_400 = []  # Bad request
        status_other = []  # Other errors
        
        for name, result in self.results.items():
            status = result['status']
            
            if status == 404:
                status_404.append(name)
            elif status == 403:
                status_403.append(name)
            elif status == 200:
                status_200.append(name)
            elif status == 500:
                status_500.append(name)
            elif status == 400:
                status_400.append(name)
            else:
                status_other.append((name, status))
        
        print(f"\n✅ WORKING ENDPOINTS (HTTP 200): {len(status_200)}")
        for name in status_200:
            print(f"   ✅ {name}")
            
        print(f"\n❌ FORBIDDEN ENDPOINTS (HTTP 403): {len(status_403)}")
        for name in status_403:
            print(f"   🚫 {name}")
            
        print(f"\n❓ NOT FOUND ENDPOINTS (HTTP 404): {len(status_404)}")
        for name in status_404:
            print(f"   ❓ {name}")
            
        print(f"\n💥 SERVER ERROR ENDPOINTS (HTTP 500): {len(status_500)}")
        for name in status_500:
            print(f"   💥 {name}")
            
        print(f"\n🔧 BAD REQUEST ENDPOINTS (HTTP 400): {len(status_400)}")
        for name in status_400:
            print(f"   🔧 {name}")
            
        print(f"\n🔍 OTHER STATUS ENDPOINTS: {len(status_other)}")
        for name, status in status_other:
            print(f"   🔍 {name}: {status}")
        
        # Analyze by subscription type
        print(f"\n" + "="*80)
        print(f"🔬 SUBSCRIPTION-BASED ANALYSIS")
        print(f"="*80)
        
        pro_results = {name: result for name, result in self.results.items() if '(pro)' in name}
        free_results = {name: result for name, result in self.results.items() if '(free)' in name}
        existing_results = {name: result for name, result in self.results.items() if '(existing)' in name}
        
        print(f"\n🏆 PRO SUBSCRIPTION RESULTS:")
        for name, result in pro_results.items():
            status = result['status']
            print(f"   {name}: HTTP {status}")
        
        print(f"\n🆓 FREE SUBSCRIPTION RESULTS:")
        for name, result in free_results.items():
            status = result['status']
            print(f"   {name}: HTTP {status}")
            
        print(f"\n👤 EXISTING USER RESULTS:")
        for name, result in existing_results.items():
            status = result['status']
            print(f"   {name}: HTTP {status}")
        
        # Find working laboratory endpoint
        lab_endpoints = [name for name in self.results.keys() if 'Laboratory' in name]
        print(f"\n🧪 LABORATORY ENDPOINTS ANALYSIS:")
        for name in lab_endpoints:
            result = self.results[name]
            print(f"   {name}: HTTP {result['status']}")
            if result['status'] == 200:
                print(f"      ✅ WORKING - This is the endpoint that works!")
                print(f"      📝 Response preview: {str(result['response'])[:100]}...")
        
        return {
            'working': status_200,
            'forbidden': status_403,
            'not_found': status_404,
            'server_error': status_500,
            'bad_request': status_400,
            'other': status_other,
            'total_tested': len(self.results)
        }
    
    def generate_summary(self):
        """Generate summary for main agent"""
        analysis = self.analyze_results()
        
        print(f"\n" + "="*80)
        print(f"📋 FINAL SUMMARY FOR MAIN AGENT")
        print(f"="*80)
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   • Total AI endpoints tested: {analysis['total_tested']}")
        print(f"   • Working endpoints: {len(analysis['working'])}")
        print(f"   • Forbidden (403) endpoints: {len(analysis['forbidden'])}")
        print(f"   • Not found (404) endpoints: {len(analysis['not_found'])}")
        print(f"   • Server error (500) endpoints: {len(analysis['server_error'])}")
        print(f"   • Bad request (400) endpoints: {len(analysis['bad_request'])}")
        
        if analysis['working']:
            print(f"\n✅ WORKING ENDPOINTS:")
            for endpoint in analysis['working']:
                print(f"   • {endpoint}")
        
        if analysis['forbidden']:
            print(f"\n❌ 403 FORBIDDEN ENDPOINTS:")
            for endpoint in analysis['forbidden']:
                print(f"   • {endpoint}")
                
            # Show sample 403 response
            first_403 = analysis['forbidden'][0]
            response = self.results[first_403]['response']
            print(f"\n   📝 Sample 403 response: {response}")
        
        if analysis['not_found']:
            print(f"\n❓ 404 NOT FOUND ENDPOINTS:")
            for endpoint in analysis['not_found']:
                print(f"   • {endpoint}")
        
        if analysis['server_error']:
            print(f"\n💥 500 SERVER ERROR ENDPOINTS:")
            for endpoint in analysis['server_error']:
                print(f"   • {endpoint}")
        
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        # Check if laboratory works vs others
        lab_working = any('Laboratory' in name for name in analysis['working'])
        others_failing = len(analysis['forbidden']) > 0 or len(analysis['server_error']) > 0
        
        if lab_working and others_failing:
            print(f"   ✅ Laboratory endpoint works - different validation logic")
            print(f"   ❌ Other AI endpoints fail - subscription validation issues")
            print(f"   🔍 Laboratory creates test users automatically")
            print(f"   🔍 Other endpoints require existing PRO users")
        
        if analysis['forbidden']:
            print(f"   🚫 403 errors confirm subscription validation is working")
            print(f"   🚫 Free users are properly blocked from PRO features")
            print(f"   🚫 Some PRO users may not be properly validated")
        
        if analysis['server_error']:
            print(f"   💥 500 errors indicate code bugs in AI endpoints")
            print(f"   💥 Likely related to payload format or internal processing")
        
        print(f"\n💡 RECOMMENDED FIXES:")
        if analysis['forbidden']:
            print(f"   1. ✅ Subscription validation is working correctly")
            print(f"   2. 🔧 Ensure PRO users are properly created and validated")
            print(f"   3. 🔧 Check user subscription status in database")
        
        if analysis['server_error']:
            print(f"   1. 🐛 Fix server errors in AI endpoint code")
            print(f"   2. 🐛 Check payload format expectations")
            print(f"   3. 🐛 Add proper error handling")
        
        if lab_working:
            print(f"   1. ✅ Use laboratory endpoint validation logic as reference")
            print(f"   2. ✅ Laboratory endpoint works correctly")
            print(f"   3. 🔧 Align other endpoints with laboratory validation")

async def main():
    """Main test execution"""
    tester = AIEndpointTesterCorrected()
    
    print("🚀 AI ENDPOINTS 403 ERROR DIAGNOSIS - CORRECTED VERSION")
    print("="*60)
    
    await tester.test_all_ai_endpoints()
    tester.analyze_results()
    tester.generate_summary()
    
    # Save results to file for reference
    with open('/app/ai_endpoints_corrected_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(tester.results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Results saved to: /app/ai_endpoints_corrected_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())