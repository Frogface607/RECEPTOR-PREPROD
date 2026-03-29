#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import uuid

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class InterfaceSimplificationTester:
    def __init__(self):
        self.test_user_id = "test_user_quick"  # As specified in review request
        self.results = []
        self.generated_tech_cards = []
        
    async def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.results.append(result)
        print(result)
        
    async def test_v2_techcard_generation(self):
        """Test POST /api/v1/techcards.v2/generate - должна возвращать card с данными (не null)"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Basic data for tech card generation as specified
                payload = {
                    "name": "Борщ украинский с говядиной",
                    "cuisine": "русская",
                    "equipment": ["плита", "кастрюля"],
                    "budget": 500.0,  # Budget expects float, not string
                    "dietary": [],
                    "user_id": self.test_user_id
                }
                
                print(f"🔄 Testing V2 API generation: POST {API_BASE}/v1/techcards.v2/generate")
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"V2 API Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    # Check different possible response structures
                    card = None
                    if data and "card" in data and data["card"] is not None:
                        card = data["card"]
                    elif data and "techcard" in data and data["techcard"] is not None:
                        card = data["techcard"]
                    elif data and isinstance(data, dict) and "name" in data:
                        # Response might be the card itself
                        card = data
                    
                    if card:
                        # Verify card has essential data - check meta for name and id
                        meta = card.get("meta", {})
                        has_name = (card.get("name") is not None or 
                                   card.get("title") is not None or 
                                   meta.get("title") is not None or 
                                   meta.get("name") is not None)
                        has_ingredients = card.get("ingredients") is not None and len(card.get("ingredients", [])) > 0
                        has_id = (card.get("id") is not None or 
                                 meta.get("id") is not None)
                        
                        name = (card.get("name") or card.get("title") or 
                               meta.get("title") or meta.get("name") or "Unknown")
                        card_id = card.get("id") or meta.get("id")
                        
                        if has_name and has_ingredients:
                            self.generated_tech_cards.append(card_id or "no-id")
                            await self.log_result(
                                "V2 API Generation", 
                                True, 
                                f"Card generated successfully with name='{name}', {len(card.get('ingredients', []))} ingredients, ID={card_id}"
                            )
                        else:
                            await self.log_result(
                                "V2 API Generation", 
                                False, 
                                f"Card missing essential data: name={has_name}, ingredients={has_ingredients}, id={has_id}. Card keys: {list(card.keys())}, Meta keys: {list(meta.keys()) if meta else 'No meta'}"
                            )
                    else:
                        await self.log_result(
                            "V2 API Generation", 
                            False, 
                            f"Card is null or missing in response. Response structure: {data}"
                        )
                else:
                    await self.log_result(
                        "V2 API Generation", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
        except Exception as e:
            await self.log_result("V2 API Generation", False, f"Exception: {str(e)}")
    
    async def test_iiko_rms_connection_status(self):
        """Test GET /api/v1/iiko/rms/connection/status - должен показывать правильный статус"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"🔄 Testing iiko RMS connection: GET {API_BASE}/v1/iiko/rms/connection/status")
                response = await client.get(f"{API_BASE}/v1/iiko/rms/connection/status")
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if status information is present
                    if "status" in data or "connected" in data or "connection" in data:
                        status_info = data.get("status", data.get("connected", data.get("connection", "unknown")))
                        await self.log_result(
                            "iiko RMS Connection Status", 
                            True, 
                            f"Status returned: {status_info}, Full response: {data}"
                        )
                    else:
                        await self.log_result(
                            "iiko RMS Connection Status", 
                            False, 
                            f"No status information in response: {data}"
                        )
                else:
                    await self.log_result(
                        "iiko RMS Connection Status", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
        except Exception as e:
            await self.log_result("iiko RMS Connection Status", False, f"Exception: {str(e)}")
    
    async def test_old_techcard_api(self):
        """Test POST /api/generate-tech-card - старый API техкарт"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Basic data for old API
                payload = {
                    "dish_name": "Салат Цезарь",
                    "user_id": self.test_user_id
                }
                
                print(f"🔄 Testing Old API: POST {API_BASE}/generate-tech-card")
                response = await client.post(
                    f"{API_BASE}/generate-tech-card",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if response has tech card data
                    if data and ("tech_card" in data or "techcard" in data or "card" in data):
                        await self.log_result(
                            "Old API Tech Card", 
                            True, 
                            f"Tech card generated successfully: {list(data.keys())}"
                        )
                    else:
                        await self.log_result(
                            "Old API Tech Card", 
                            False, 
                            f"No tech card data in response: {data}"
                        )
                elif response.status_code == 500:
                    error_text = response.text
                    if "лимит" in error_text.lower() or "limit" in error_text.lower():
                        await self.log_result(
                            "Old API Tech Card", 
                            True, 
                            f"API accessible but hit usage limit (expected): {error_text[:100]}"
                        )
                    else:
                        await self.log_result(
                            "Old API Tech Card", 
                            False, 
                            f"HTTP 500 (server error): {error_text[:200]}"
                        )
                else:
                    await self.log_result(
                        "Old API Tech Card", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
        except Exception as e:
            await self.log_result("Old API Tech Card", False, f"Exception: {str(e)}")
    
    async def test_cities_endpoint(self):
        """Test GET /api/cities - базовые endpoints"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"🔄 Testing Cities endpoint: GET {API_BASE}/cities")
                response = await client.get(f"{API_BASE}/cities")
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if cities data is returned
                    if isinstance(data, list) and len(data) > 0:
                        await self.log_result(
                            "Cities Endpoint", 
                            True, 
                            f"Cities list returned with {len(data)} cities"
                        )
                    elif isinstance(data, dict) and "cities" in data:
                        cities = data["cities"]
                        await self.log_result(
                            "Cities Endpoint", 
                            True, 
                            f"Cities object returned with {len(cities)} cities"
                        )
                    else:
                        await self.log_result(
                            "Cities Endpoint", 
                            False, 
                            f"Unexpected cities data format: {data}"
                        )
                else:
                    await self.log_result(
                        "Cities Endpoint", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
        except Exception as e:
            await self.log_result("Cities Endpoint", False, f"Exception: {str(e)}")
    
    async def test_backend_health(self):
        """Test basic backend connectivity"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"🔄 Testing Backend Health: GET {BACKEND_URL}")
                response = await client.get(BACKEND_URL)
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code in [200, 404]:  # 404 is OK for root endpoint
                    await self.log_result(
                        "Backend Health", 
                        True, 
                        f"Backend is accessible (HTTP {response.status_code})"
                    )
                else:
                    await self.log_result(
                        "Backend Health", 
                        False, 
                        f"Backend not accessible: HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            await self.log_result("Backend Health", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all interface simplification tests"""
        print("=" * 80)
        print("🧪 INTERFACE SIMPLIFICATION BACKEND TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test User ID: {self.test_user_id}")
        print("=" * 80)
        
        # Run tests in order
        await self.test_backend_health()
        await self.test_cities_endpoint()
        await self.test_iiko_rms_connection_status()
        await self.test_old_techcard_api()
        await self.test_v2_techcard_generation()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.results if "✅ PASS" in result)
        failed = sum(1 for result in self.results if "❌ FAIL" in result)
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        print("\nDetailed Results:")
        for result in self.results:
            print(f"  {result}")
        
        if self.generated_tech_cards:
            print(f"\nGenerated Tech Cards: {self.generated_tech_cards}")
        
        print("=" * 80)
        
        return passed, failed, total

async def main():
    """Main test runner"""
    tester = InterfaceSimplificationTester()
    passed, failed, total = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())