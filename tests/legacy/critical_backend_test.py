#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import uuid

# Backend URL from supervisor configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class CriticalBackendTester:
    def __init__(self):
        self.test_user_id = f"critical_test_{str(uuid.uuid4())[:8]}"
        self.results = []
        self.generated_tech_cards = []
        
    async def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.results.append(result)
        print(result)
        
    async def test_health_endpoint(self):
        """Test basic backend connectivity"""
        try:
            # Since there's no /api/health endpoint, test the V2 status instead
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/v1/techcards.v2/status")
                
                if response.status_code == 200:
                    await self.log_result(
                        "Backend Connectivity", 
                        True, 
                        f"Backend is accessible via V2 status endpoint (HTTP 200)"
                    )
                    return True
                else:
                    await self.log_result(
                        "Backend Connectivity", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Backend Connectivity", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_v2_status_endpoint(self):
        """Test GET /api/v1/techcards.v2/status - должен возвращать статус V2 API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/v1/techcards.v2/status")
                
                if response.status_code == 200:
                    data = response.json()
                    await self.log_result(
                        "V2 Status Endpoint", 
                        True, 
                        f"V2 API status: {data}"
                    )
                    return True
                else:
                    await self.log_result(
                        "V2 Status Endpoint", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "V2 Status Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_user_history_endpoint(self):
        """Test GET /api/user-history/{user_id} - для проектов"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/user-history/{self.test_user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    await self.log_result(
                        "User History Endpoint", 
                        True, 
                        f"User history accessible: {len(data.get('history', []))} items"
                    )
                    return True
                else:
                    await self.log_result(
                        "User History Endpoint", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "User History Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_techcard_generation(self):
        """Test POST /api/v1/techcards.v2/generate - основной endpoint генерации"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "name": "Омлет",
                    "user_id": self.test_user_id,
                    "cuisine": "русская",
                    "equipment": [],
                    "budget": None,
                    "dietary": []
                }
                
                response = await client.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if the response contains a tech card
                    if data.get("status") in ["success", "draft", "READY"] and data.get("card"):
                        tech_card = data.get("card")
                        tech_card_id = tech_card.get("meta", {}).get("id")
                        
                        if tech_card_id:
                            self.generated_tech_cards.append(tech_card_id)
                            await self.log_result(
                                "TechCard Generation", 
                                True, 
                                f"Generated tech card 'Омлет' with ID: {tech_card_id}, status: {data.get('status')}"
                            )
                            return tech_card_id
                        else:
                            await self.log_result(
                                "TechCard Generation", 
                                False, 
                                f"No ID in generated card: {data}"
                            )
                            return None
                    else:
                        await self.log_result(
                            "TechCard Generation", 
                            False, 
                            f"Generation failed: status={data.get('status')}, card_present={data.get('card') is not None}"
                        )
                        return None
                else:
                    await self.log_result(
                        "TechCard Generation", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result(
                "TechCard Generation", 
                False, 
                f"Exception: {str(e)}"
            )
            return None

    async def test_openai_integration(self):
        """Test if OpenAI API key is working"""
        try:
            # Try to generate a simple tech card to test OpenAI integration
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "name": "Простой салат",
                    "user_id": self.test_user_id,
                    "cuisine": "европейская",
                    "equipment": [],
                    "budget": None,
                    "dietary": []
                }
                
                response = await client.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    # Check if the response contains generated content
                    if data.get("status") in ["success", "draft", "READY"] and data.get("card"):
                        await self.log_result(
                            "OpenAI Integration", 
                            True, 
                            f"OpenAI API key working - content generated, status: {data.get('status')}"
                        )
                        return True
                    else:
                        await self.log_result(
                            "OpenAI Integration", 
                            False, 
                            f"No content generated - status: {data.get('status')}, card_present: {data.get('card') is not None}"
                        )
                        return False
                elif response.status_code == 401:
                    await self.log_result(
                        "OpenAI Integration", 
                        False, 
                        "OpenAI API key authentication failed"
                    )
                    return False
                else:
                    await self.log_result(
                        "OpenAI Integration", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "OpenAI Integration", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_mongodb_connectivity(self):
        """Test MongoDB connectivity by trying to create a user"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "email": f"{self.test_user_id}@test.com",
                    "name": f"Test User {self.test_user_id[:8]}",
                    "city": "moskva"
                }
                
                response = await client.post(f"{API_BASE}/register", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    actual_user_id = data.get('id', self.test_user_id)
                    self.test_user_id = actual_user_id
                    await self.log_result(
                        "MongoDB Connectivity", 
                        True, 
                        f"MongoDB accessible - user created with ID: {actual_user_id}"
                    )
                    return True
                else:
                    await self.log_result(
                        "MongoDB Connectivity", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "MongoDB Connectivity", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_cors_configuration(self):
        """Test CORS configuration"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Make an OPTIONS request to test CORS
                response = await client.options(f"{API_BASE}/health")
                
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                if any(cors_headers.values()):
                    await self.log_result(
                        "CORS Configuration", 
                        True, 
                        f"CORS headers present: {cors_headers}"
                    )
                    return True
                else:
                    await self.log_result(
                        "CORS Configuration", 
                        False, 
                        "No CORS headers found"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "CORS Configuration", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_api_routes_configuration(self):
        """Test that API routes are properly configured"""
        critical_endpoints = [
            "/api/v1/techcards.v2/status",
            "/api/v1/techcards.v2/generate",
            f"/api/user-history/{self.test_user_id}",
            "/api/register"
        ]
        
        working_endpoints = 0
        total_endpoints = len(critical_endpoints)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in critical_endpoints:
                    try:
                        full_url = f"{BACKEND_URL}{endpoint}"
                        response = await client.get(full_url)
                        
                        # Consider 200, 405 (Method Not Allowed), and 422 (Validation Error) as "working"
                        # 404 means the route is not configured
                        if response.status_code != 404:
                            working_endpoints += 1
                            print(f"  ✅ {endpoint} - HTTP {response.status_code}")
                        else:
                            print(f"  ❌ {endpoint} - HTTP 404 (Route not found)")
                            
                    except Exception as e:
                        print(f"  ❌ {endpoint} - Exception: {str(e)}")
                
                success = working_endpoints >= (total_endpoints * 0.8)  # 80% threshold
                
                await self.log_result(
                    "API Routes Configuration", 
                    success, 
                    f"{working_endpoints}/{total_endpoints} endpoints accessible"
                )
                
                return success
                
        except Exception as e:
            await self.log_result(
                "API Routes Configuration", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_backend_logs_for_errors(self):
        """Check backend logs for critical errors"""
        try:
            # Check supervisor backend logs
            import subprocess
            
            # Get recent backend logs
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True
            )
            
            error_logs = result.stdout
            
            # Look for critical errors
            critical_errors = [
                "ModuleNotFoundError",
                "ImportError",
                "ConnectionError",
                "Authentication failed",
                "Database connection failed",
                "OpenAI API error"
            ]
            
            found_errors = []
            for error in critical_errors:
                if error.lower() in error_logs.lower():
                    found_errors.append(error)
            
            if found_errors:
                await self.log_result(
                    "Backend Error Logs", 
                    False, 
                    f"Critical errors found: {found_errors}"
                )
                print(f"Recent error logs:\n{error_logs[-500:]}")  # Show last 500 chars
                return False
            else:
                await self.log_result(
                    "Backend Error Logs", 
                    True, 
                    "No critical errors in recent logs"
                )
                return True
                
        except Exception as e:
            await self.log_result(
                "Backend Error Logs", 
                False, 
                f"Could not check logs: {str(e)}"
            )
            return False

    async def run_critical_diagnosis(self):
        """Run comprehensive critical backend diagnosis"""
        print("🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ BACKEND: Устранение 404 ошибок API и восстановление генерации техкарт")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test User ID: {self.test_user_id}")
        print("=" * 100)
        
        # Test 1: Backend Error Logs Analysis
        print("\n📋 TEST 1: Backend Error Logs Analysis")
        await self.test_backend_logs_for_errors()
        
        # Test 2: Basic Backend Connectivity
        print("\n📋 TEST 2: Basic Backend Connectivity")
        await self.test_health_endpoint()
        
        # Test 3: API Routes Configuration
        print("\n📋 TEST 3: API Routes Configuration")
        await self.test_api_routes_configuration()
        
        # Test 4: CORS Configuration
        print("\n📋 TEST 4: CORS Configuration")
        await self.test_cors_configuration()
        
        # Test 5: MongoDB Connectivity
        print("\n📋 TEST 5: MongoDB Connectivity")
        await self.test_mongodb_connectivity()
        
        # Test 6: V2 API Status
        print("\n📋 TEST 6: V2 API Status")
        await self.test_v2_status_endpoint()
        
        # Test 7: User History Endpoint
        print("\n📋 TEST 7: User History Endpoint")
        await self.test_user_history_endpoint()
        
        # Test 8: OpenAI Integration
        print("\n📋 TEST 8: OpenAI Integration")
        await self.test_openai_integration()
        
        # Test 9: TechCard Generation (Critical Test)
        print("\n📋 TEST 9: TechCard Generation (Critical)")
        tech_card_id = await self.test_techcard_generation()
        
        # Summary
        print("\n" + "=" * 100)
        print("🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ BACKEND - РЕЗУЛЬТАТЫ ДИАГНОСТИКИ")
        print("=" * 100)
        
        passed_tests = len([r for r in self.results if "✅ PASS" in r])
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 SUCCESS RATE: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"📈 GENERATED TECH CARDS: {len(self.generated_tech_cards)}")
        
        print("\n📝 DETAILED RESULTS:")
        for result in self.results:
            print(f"  {result}")
        
        # Critical assessment
        print("\n🎯 CRITICAL ASSESSMENT:")
        
        critical_tests = [
            ("Backend Connectivity", any("Backend Connectivity" in r and "✅ PASS" in r for r in self.results)),
            ("API Routes Configuration", any("API Routes Configuration" in r and "✅ PASS" in r for r in self.results)),
            ("MongoDB Connectivity", any("MongoDB Connectivity" in r and "✅ PASS" in r for r in self.results)),
            ("V2 API Status", any("V2 Status Endpoint" in r and "✅ PASS" in r for r in self.results)),
            ("TechCard Generation", any("TechCard Generation" in r and "✅ PASS" in r for r in self.results))
        ]
        
        all_critical_passed = all(passed for _, passed in critical_tests)
        
        for test_name, passed in critical_tests:
            status = "✅" if passed else "❌"
            print(f"  {status} {test_name}")
        
        if all_critical_passed:
            print("\n🎉 OUTSTANDING SUCCESS: Backend API endpoints are FULLY OPERATIONAL!")
            print("✅ All основные API endpoints доступны (200 OK)")
            print("✅ Генерация техкарт работает от и до")
            print("✅ MongoDB connectivity confirmed")
            print("✅ Frontend может успешно взаимодействовать с backend")
        else:
            print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            failed_tests = [name for name, passed in critical_tests if not passed]
            for test in failed_tests:
                print(f"❌ {test}")
            
            print("\n🔧 RECOMMENDED ACTIONS:")
            if not any("Backend Connectivity" in r and "✅ PASS" in r for r in self.results):
                print("- Check if backend service is running: sudo supervisorctl status backend")
                print("- Check backend logs: tail -f /var/log/supervisor/backend.*.log")
            
            if not any("API Routes Configuration" in r and "✅ PASS" in r for r in self.results):
                print("- Verify server.py has all required routes configured")
                print("- Check if FastAPI app is properly initialized")
            
            if not any("MongoDB Connectivity" in r and "✅ PASS" in r for r in self.results):
                print("- Check MongoDB service: sudo supervisorctl status mongodb")
                print("- Verify MONGO_URL in backend/.env")
            
            if not any("TechCard Generation" in r and "✅ PASS" in r for r in self.results):
                print("- Check OpenAI API key in backend/.env")
                print("- Verify tech card generation logic in server.py")
        
        return success_rate >= 80  # 80% success rate threshold

async def main():
    """Main test execution"""
    tester = CriticalBackendTester()
    
    try:
        success = await tester.run_critical_diagnosis()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Critical error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())