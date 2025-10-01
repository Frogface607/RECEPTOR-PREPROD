#!/usr/bin/env python3
"""
AI ENDPOINTS 403 ERROR TESTING
Testing all AI endpoints to identify which return 403 vs 404 errors
and find why laboratory works while others don't.
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-menu-wizard.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class AIEndpointTester:
    def __init__(self):
        self.results = {}
        self.test_user_id = "test_user_ai_endpoints"
        
    async def test_endpoint(self, client, endpoint_name, endpoint_path, payload):
        """Test a single AI endpoint"""
        url = f"{API_BASE}{endpoint_path}"
        
        try:
            print(f"\n🔍 Testing {endpoint_name}: {endpoint_path}")
            print(f"   URL: {url}")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(url, json=payload)
            status = response.status_code
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            print(f"   Status: {status}")
            print(f"   Response: {str(response_data)[:200]}...")
            
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
        """Test all AI endpoints found in the backend"""
        
        # Sample tech card data for testing
        sample_tech_card = {
            "name": "Тестовое блюдо",
            "ingredients": [
                {"name": "Мука", "quantity": 200, "unit": "г"},
                {"name": "Яйца", "quantity": 2, "unit": "шт"}
            ],
            "description": "Тестовое описание блюда"
        }
        
        # Define all AI endpoints to test
        endpoints_to_test = [
            {
                'name': 'Generate Sales Script',
                'path': '/generate-sales-script',
                'payload': {
                    'user_id': self.test_user_id,
                    'tech_card': sample_tech_card
                }
            },
            {
                'name': 'Generate Food Pairing',
                'path': '/generate-food-pairing',
                'payload': {
                    'user_id': self.test_user_id,
                    'tech_card': sample_tech_card
                }
            },
            {
                'name': 'Generate Photo Tips',
                'path': '/generate-photo-tips',
                'payload': {
                    'user_id': self.test_user_id,
                    'tech_card': sample_tech_card
                }
            },
            {
                'name': 'Generate Inspiration',
                'path': '/generate-inspiration',
                'payload': {
                    'user_id': self.test_user_id,
                    'tech_card': sample_tech_card
                }
            },
            {
                'name': 'Analyze Finances',
                'path': '/analyze-finances',
                'payload': {
                    'user_id': self.test_user_id,
                    'tech_card': sample_tech_card
                }
            },
            {
                'name': 'Improve Dish',
                'path': '/improve-dish',
                'payload': {
                    'user_id': self.test_user_id,
                    'tech_card': sample_tech_card
                }
            },
            {
                'name': 'Laboratory Experiment (WORKING)',
                'path': '/laboratory-experiment',
                'payload': {
                    'user_id': self.test_user_id,
                    'experiment_type': 'random',
                    'base_dish': 'Тестовое блюдо'
                }
            },
            {
                'name': 'Save Laboratory Experiment',
                'path': '/save-laboratory-experiment',
                'payload': {
                    'user_id': self.test_user_id,
                    'experiment_data': {
                        'name': 'Тестовый эксперимент',
                        'description': 'Описание эксперимента'
                    }
                }
            }
        ]
        
        print(f"🚀 STARTING AI ENDPOINTS TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User ID: {self.test_user_id}")
        print(f"Total endpoints to test: {len(endpoints_to_test)}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint_info in endpoints_to_test:
                await self.test_endpoint(
                    client,
                    endpoint_info['name'],
                    endpoint_info['path'],
                    endpoint_info['payload']
                )
                
                # Small delay between requests
                await asyncio.sleep(0.5)
    
    def analyze_results(self):
        """Analyze test results and categorize issues"""
        print(f"\n" + "="*80)
        print(f"📊 AI ENDPOINTS TEST RESULTS ANALYSIS")
        print(f"="*80)
        
        status_404 = []  # Not found
        status_403 = []  # Forbidden
        status_200 = []  # Working
        status_500 = []  # Server error
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
            
        print(f"\n🔍 OTHER STATUS ENDPOINTS: {len(status_other)}")
        for name, status in status_other:
            print(f"   🔍 {name}: {status}")
        
        # Detailed analysis
        print(f"\n" + "="*80)
        print(f"🔬 DETAILED ANALYSIS")
        print(f"="*80)
        
        # Find working laboratory endpoint
        lab_endpoints = [name for name in self.results.keys() if 'Laboratory' in name]
        print(f"\n🧪 LABORATORY ENDPOINTS:")
        for name in lab_endpoints:
            result = self.results[name]
            print(f"   {name}: HTTP {result['status']}")
            if result['status'] == 200:
                print(f"      ✅ WORKING - This is the endpoint that works!")
            
        # Analyze 403 errors
        if status_403:
            print(f"\n🚫 403 FORBIDDEN ANALYSIS:")
            print(f"   These endpoints require PRO subscription validation")
            print(f"   User ID used: {self.test_user_id}")
            
            # Check first 403 response for details
            first_403 = status_403[0]
            response = self.results[first_403]['response']
            print(f"   Sample 403 response: {response}")
        
        # Compare working vs non-working
        if status_200 and status_403:
            print(f"\n🔍 DIFFERENCE ANALYSIS:")
            working = status_200[0]
            failing = status_403[0]
            
            print(f"   WORKING: {working}")
            print(f"   FAILING: {failing}")
            print(f"   ")
            print(f"   The key difference is likely in subscription validation logic.")
            print(f"   Laboratory endpoint may have different or more lenient validation.")
        
        return {
            'working': status_200,
            'forbidden': status_403,
            'not_found': status_404,
            'server_error': status_500,
            'other': status_other,
            'total_tested': len(self.results)
        }
    
    def generate_summary(self):
        """Generate summary for main agent"""
        analysis = self.analyze_results()
        
        print(f"\n" + "="*80)
        print(f"📋 SUMMARY FOR MAIN AGENT")
        print(f"="*80)
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   • Total AI endpoints tested: {analysis['total_tested']}")
        print(f"   • Working endpoints: {len(analysis['working'])}")
        print(f"   • Forbidden (403) endpoints: {len(analysis['forbidden'])}")
        print(f"   • Not found (404) endpoints: {len(analysis['not_found'])}")
        
        if analysis['working']:
            print(f"\n✅ WORKING ENDPOINTS:")
            for endpoint in analysis['working']:
                print(f"   • {endpoint}")
        
        if analysis['forbidden']:
            print(f"\n❌ 403 FORBIDDEN ENDPOINTS:")
            for endpoint in analysis['forbidden']:
                print(f"   • {endpoint}")
        
        if analysis['not_found']:
            print(f"\n❓ 404 NOT FOUND ENDPOINTS:")
            for endpoint in analysis['not_found']:
                print(f"   • {endpoint}")
        
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        if analysis['forbidden']:
            print(f"   • 403 errors are caused by PRO subscription validation")
            print(f"   • These endpoints check user.subscription_plan in ['pro', 'business']")
            print(f"   • Test user '{self.test_user_id}' may not have proper subscription")
        
        if analysis['working']:
            print(f"   • Working endpoints have different validation logic")
            print(f"   • Laboratory endpoint creates test users automatically")
            print(f"   • Laboratory has more lenient subscription checking")
        
        print(f"\n💡 RECOMMENDED FIXES:")
        if analysis['forbidden']:
            print(f"   1. Check user creation logic for test users")
            print(f"   2. Ensure test users get PRO subscription by default")
            print(f"   3. Review subscription validation consistency across endpoints")
            print(f"   4. Consider making AI features available to all users or fix validation")

async def main():
    """Main test execution"""
    tester = AIEndpointTester()
    
    print("🚀 AI ENDPOINTS 403 ERROR DIAGNOSIS")
    print("="*50)
    
    await tester.test_all_ai_endpoints()
    tester.analyze_results()
    tester.generate_summary()
    
    # Save results to file for reference
    with open('/app/ai_endpoints_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(tester.results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Results saved to: /app/ai_endpoints_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())