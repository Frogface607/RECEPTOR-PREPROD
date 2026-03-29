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

class TechCardEditingTester:
    def __init__(self):
        self.test_user_id = f"edit_test_{str(uuid.uuid4())[:8]}"
        self.results = []
        self.generated_tech_cards = []
        self.test_tech_card_id = None
        
    async def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.results.append(result)
        print(result)
        
    async def create_test_user(self):
        """Create a test user for testing"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "email": f"{self.test_user_id}@test.com",
                    "name": f"Edit Test User {self.test_user_id[:8]}",
                    "city": "moskva"
                }
                
                response = await client.post(f"{API_BASE}/register", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    actual_user_id = data.get('id', self.test_user_id)
                    self.test_user_id = actual_user_id
                    await self.log_result(
                        "Test User Creation", 
                        True, 
                        f"Created user with ID: {actual_user_id}"
                    )
                    return True
                else:
                    await self.log_result(
                        "Test User Creation", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Test User Creation", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_v1_tech_card_generation(self):
        """Test V1 tech card generation using legacy endpoint"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "user_id": self.test_user_id,
                    "dish_name": "Салат Цезарь",
                    "portions": 2,
                    "city": "moskva"
                }
                
                response = await client.post(f"{API_BASE}/generate-tech-card", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    tech_card_id = data.get("id")
                    
                    if tech_card_id:
                        self.generated_tech_cards.append({
                            "id": tech_card_id,
                            "dish_name": payload["dish_name"],
                            "type": "V1",
                            "collection": "tech_cards"
                        })
                        
                        await self.log_result(
                            "V1 Tech Card Generation", 
                            True, 
                            f"Generated V1 tech card with ID: {tech_card_id}"
                        )
                        return tech_card_id
                    else:
                        await self.log_result(
                            "V1 Tech Card Generation", 
                            False, 
                            f"No ID returned: {data}"
                        )
                        return None
                else:
                    await self.log_result(
                        "V1 Tech Card Generation", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result(
                "V1 Tech Card Generation", 
                False, 
                f"Exception: {str(e)}"
            )
            return None

    async def test_v2_tech_card_generation(self):
        """Test POST /api/v1/techcards.v2/generate - Basic tech card generation"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "name": "Борщ украинский с говядиной",
                    "user_id": self.test_user_id,
                    "cuisine": "русская",
                    "equipment": ["плита", "кастрюля"],
                    "budget": 300.0
                }
                
                response = await client.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    if "status" in data and "card" in data:
                        status = data.get("status")
                        card = data.get("card")
                        
                        if status in ["success", "draft", "READY"] and card:
                            # Try to get ID from different possible locations
                            tech_card_id = card.get("id") or card.get("meta", {}).get("id")
                            if tech_card_id:
                                self.test_tech_card_id = tech_card_id
                                self.generated_tech_cards.append({
                                    "id": tech_card_id,
                                    "dish_name": payload["name"],
                                    "type": "V2"
                                })
                                
                                await self.log_result(
                                    "V2 Tech Card Generation", 
                                    True, 
                                    f"Generated tech card with ID: {tech_card_id}, status: {status}"
                                )
                                return tech_card_id
                            else:
                                await self.log_result(
                                    "V2 Tech Card Generation", 
                                    False, 
                                    f"No ID in card data: {card}"
                                )
                        else:
                            await self.log_result(
                                "V2 Tech Card Generation", 
                                False, 
                                f"Invalid status or missing card: status={status}, card={bool(card)}"
                            )
                    else:
                        await self.log_result(
                            "V2 Tech Card Generation", 
                            False, 
                            f"Invalid response structure: {data}"
                        )
                else:
                    await self.log_result(
                        "V2 Tech Card Generation", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            await self.log_result(
                "V2 Tech Card Generation", 
                False, 
                f"Exception: {str(e)}"
            )
        
        return None

    async def test_user_history_endpoint(self):
        """Test GET /api/user-history/{user_id} - Check if tech cards are loading properly"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/user-history/{self.test_user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "history" in data and isinstance(data["history"], list):
                        history = data["history"]
                        tech_cards_count = len([item for item in history if not item.get("is_menu", False)])
                        
                        await self.log_result(
                            "User History Endpoint", 
                            True, 
                            f"Retrieved {len(history)} history items, {tech_cards_count} tech cards"
                        )
                        
                        # Check if our generated tech card is in the history
                        if self.test_tech_card_id:
                            found_card = any(item.get("id") == self.test_tech_card_id for item in history)
                            await self.log_result(
                                "Tech Card in History", 
                                found_card, 
                                f"Generated tech card {'found' if found_card else 'NOT found'} in user history"
                            )
                        
                        return history
                    else:
                        await self.log_result(
                            "User History Endpoint", 
                            False, 
                            f"Invalid response structure: {data}"
                        )
                        return []
                else:
                    await self.log_result(
                        "User History Endpoint", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return []
                    
        except Exception as e:
            await self.log_result(
                "User History Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
            return []

    async def test_edit_tech_card_endpoint_v2(self):
        """Test POST /api/edit-tech-card with V2 tech card - Should fail due to collection mismatch"""
        if not self.test_tech_card_id:
            await self.log_result(
                "Edit Tech Card Endpoint (V2)", 
                False, 
                "No V2 tech card ID available for editing test"
            )
            return False
            
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Test edit request with V2 tech card ID
                edit_payload = {
                    "tech_card_id": self.test_tech_card_id,
                    "edit_instruction": "Увеличить порцию в 2 раза"
                }
                
                response = await client.post(f"{API_BASE}/edit-tech-card", json=edit_payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "success" in data and data["success"]:
                        await self.log_result(
                            "Edit Tech Card Endpoint (V2)", 
                            True, 
                            f"Successfully edited V2 tech card, content length: {len(data.get('tech_card', ''))}"
                        )
                        return True
                    else:
                        await self.log_result(
                            "Edit Tech Card Endpoint (V2)", 
                            False, 
                            f"Success=False or missing: {data}"
                        )
                elif response.status_code == 404 or "Tech card not found" in response.text:
                    await self.log_result(
                        "Edit Tech Card Endpoint (V2)", 
                        False, 
                        f"CRITICAL BUG: V2 tech card not found - Edit endpoint looks in 'tech_cards' collection but V2 cards are in 'user_history'"
                    )
                elif response.status_code == 500 and "Tech card not found" in response.text:
                    await self.log_result(
                        "Edit Tech Card Endpoint (V2)", 
                        False, 
                        f"CRITICAL BUG: V2 tech card not found (500 error) - Edit endpoint collection mismatch"
                    )
                else:
                    await self.log_result(
                        "Edit Tech Card Endpoint (V2)", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            await self.log_result(
                "Edit Tech Card Endpoint (V2)", 
                False, 
                f"Exception: {str(e)}"
            )
            
        return False

    async def test_edit_tech_card_endpoint_v1(self, v1_tech_card_id):
        """Test POST /api/edit-tech-card with V1 tech card - Should work"""
        if not v1_tech_card_id:
            await self.log_result(
                "Edit Tech Card Endpoint (V1)", 
                False, 
                "No V1 tech card ID available for editing test"
            )
            return False
            
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Test edit request with V1 tech card ID
                edit_payload = {
                    "tech_card_id": v1_tech_card_id,
                    "edit_instruction": "Увеличить порцию в 2 раза"
                }
                
                response = await client.post(f"{API_BASE}/edit-tech-card", json=edit_payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "success" in data and data["success"]:
                        if "tech_card" in data and data["tech_card"]:
                            await self.log_result(
                                "Edit Tech Card Endpoint (V1)", 
                                True, 
                                f"Successfully edited V1 tech card, content length: {len(data['tech_card'])}"
                            )
                            return True
                        else:
                            await self.log_result(
                                "Edit Tech Card Endpoint (V1)", 
                                False, 
                                f"Success=True but no tech_card content: {data}"
                            )
                    else:
                        await self.log_result(
                            "Edit Tech Card Endpoint (V1)", 
                            False, 
                            f"Success=False or missing: {data}"
                        )
                elif response.status_code == 404:
                    await self.log_result(
                        "Edit Tech Card Endpoint (V1)", 
                        False, 
                        f"V1 tech card not found (404) - ID may be invalid: {v1_tech_card_id}"
                    )
                else:
                    await self.log_result(
                        "Edit Tech Card Endpoint (V1)", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            await self.log_result(
                "Edit Tech Card Endpoint (V1)", 
                False, 
                f"Exception: {str(e)}"
            )
            
        return False

    async def test_database_connectivity(self):
        """Test database integration by checking tech card persistence"""
        if not self.test_tech_card_id:
            await self.log_result(
                "Database Connectivity", 
                False, 
                "No tech card ID to test database connectivity"
            )
            return False
            
        try:
            # Try to retrieve the tech card through user history to verify database persistence
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/user-history/{self.test_user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    history = data.get("history", [])
                    
                    # Look for our tech card
                    found_card = None
                    for item in history:
                        if item.get("id") == self.test_tech_card_id:
                            found_card = item
                            break
                    
                    if found_card:
                        # Check if the card has proper content
                        content = found_card.get("content", "")
                        if content and len(content) > 100:  # Reasonable content length
                            await self.log_result(
                                "Database Connectivity", 
                                True, 
                                f"Tech card properly persisted with content length: {len(content)}"
                            )
                            return True
                        else:
                            await self.log_result(
                                "Database Connectivity", 
                                False, 
                                f"Tech card found but content too short: {len(content)}"
                            )
                    else:
                        await self.log_result(
                            "Database Connectivity", 
                            False, 
                            f"Tech card not found in database: {self.test_tech_card_id}"
                        )
                else:
                    await self.log_result(
                        "Database Connectivity", 
                        False, 
                        f"Could not retrieve user history: HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            await self.log_result(
                "Database Connectivity", 
                False, 
                f"Exception: {str(e)}"
            )
            
        return False

    async def test_openai_integration(self):
        """Test OpenAI integration by checking if API key is working"""
        try:
            # We'll test this indirectly by trying to generate a simple tech card
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "name": "Простой салат",
                    "user_id": self.test_user_id,
                    "cuisine": "европейская",
                    "equipment": ["нож", "доска"]
                }
                
                response = await client.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") in ["success", "draft", "READY"] and data.get("card"):
                        await self.log_result(
                            "OpenAI Integration", 
                            True, 
                            "OpenAI API successfully generated tech card content"
                        )
                        return True
                    else:
                        await self.log_result(
                            "OpenAI Integration", 
                            False, 
                            f"Generation failed: status={data.get('status')}, issues={data.get('issues', [])}"
                        )
                else:
                    await self.log_result(
                        "OpenAI Integration", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            await self.log_result(
                "OpenAI Integration", 
                False, 
                f"Exception: {str(e)}"
            )
            
        return False

    async def test_edit_request_validation(self):
        """Test EditRequest model validation with various scenarios"""
        test_cases = [
            {
                "name": "Valid Edit Request",
                "payload": {
                    "tech_card_id": "test-id-123",
                    "edit_instruction": "Увеличить порцию в 2 раза"
                },
                "should_pass": True
            },
            {
                "name": "Missing tech_card_id",
                "payload": {
                    "edit_instruction": "Увеличить порцию в 2 раза"
                },
                "should_pass": False
            },
            {
                "name": "Missing edit_instruction",
                "payload": {
                    "tech_card_id": "test-id-123"
                },
                "should_pass": False
            },
            {
                "name": "Empty edit_instruction",
                "payload": {
                    "tech_card_id": "test-id-123",
                    "edit_instruction": ""
                },
                "should_pass": False
            }
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for test_case in test_cases:
                    try:
                        response = await client.post(f"{API_BASE}/edit-tech-card", json=test_case["payload"])
                        
                        if test_case["should_pass"]:
                            # For valid requests, we expect either 200 (success) or 404 (tech card not found)
                            # 404 is acceptable since we're using a fake tech_card_id
                            success = response.status_code in [200, 404]
                        else:
                            # For invalid requests, we expect 422 (validation error)
                            success = response.status_code == 422
                        
                        if success:
                            passed_tests += 1
                            
                    except Exception as e:
                        # If should_pass is False and we get an exception, that might be expected
                        if not test_case["should_pass"]:
                            passed_tests += 1
            
            success_rate = (passed_tests / total_tests) if total_tests > 0 else 0
            await self.log_result(
                "Edit Request Validation", 
                success_rate >= 0.75,  # 75% success rate threshold
                f"Passed {passed_tests}/{total_tests} validation tests ({success_rate:.1%})"
            )
            
        except Exception as e:
            await self.log_result(
                "Edit Request Validation", 
                False, 
                f"Exception during validation testing: {str(e)}"
            )

    async def test_error_handling(self):
        """Test error handling for various edge cases"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test 1: Non-existent tech card ID
                response1 = await client.post(f"{API_BASE}/edit-tech-card", json={
                    "tech_card_id": "non-existent-id-12345",
                    "edit_instruction": "Test edit"
                })
                
                error1_handled = response1.status_code == 404
                
                # Test 2: Non-existent user in user-history
                response2 = await client.get(f"{API_BASE}/user-history/non-existent-user-12345")
                
                error2_handled = response2.status_code in [200, 404]  # Either empty list or 404 is acceptable
                
                # Test 3: Invalid JSON in edit request
                try:
                    response3 = await client.post(f"{API_BASE}/edit-tech-card", content="invalid json")
                    error3_handled = response3.status_code == 422
                except:
                    error3_handled = True  # Exception is also acceptable for invalid JSON
                
                total_errors_handled = sum([error1_handled, error2_handled, error3_handled])
                
                await self.log_result(
                    "Error Handling", 
                    total_errors_handled >= 2,  # At least 2 out of 3 error cases handled properly
                    f"Handled {total_errors_handled}/3 error scenarios properly"
                )
                
        except Exception as e:
            await self.log_result(
                "Error Handling", 
                False, 
                f"Exception during error handling test: {str(e)}"
            )

    async def run_comprehensive_test(self):
        """Run comprehensive tech card editing functionality test"""
        print("🎯 TECH CARD EDITING FUNCTIONALITY COMPREHENSIVE TESTING STARTED")
        print(f"Test User ID: {self.test_user_id}")
        print("=" * 80)
        
        # Test 1: Create test user
        print("\n📋 TEST 1: Create Test User")
        user_created = await self.create_test_user()
        
        # Test 2: Test V1 tech card generation (legacy)
        print("\n📋 TEST 2: V1 Tech Card Generation")
        v1_tech_card_id = await self.test_v1_tech_card_generation()
        
        # Test 3: Test V2 tech card generation (new)
        print("\n📋 TEST 3: V2 Tech Card Generation")
        v2_tech_card_id = await self.test_v2_tech_card_generation()
        self.test_tech_card_id = v2_tech_card_id  # Set for other tests
        
        # Test 4: Test user history endpoint
        print("\n📋 TEST 4: User History Endpoint")
        history = await self.test_user_history_endpoint()
        
        # Test 5: Test database connectivity
        print("\n📋 TEST 5: Database Connectivity")
        db_connected = await self.test_database_connectivity()
        
        # Test 6: Test OpenAI integration
        print("\n📋 TEST 6: OpenAI Integration")
        openai_working = await self.test_openai_integration()
        
        # Test 7: Test edit tech card endpoint with V1 tech card
        print("\n📋 TEST 7: Edit Tech Card Endpoint (V1)")
        v1_edit_working = await self.test_edit_tech_card_endpoint_v1(v1_tech_card_id)
        
        # Test 8: Test edit tech card endpoint with V2 tech card (should fail)
        print("\n📋 TEST 8: Edit Tech Card Endpoint (V2)")
        v2_edit_working = await self.test_edit_tech_card_endpoint_v2()
        
        # Test 9: Test EditRequest validation
        print("\n📋 TEST 9: EditRequest Validation")
        await self.test_edit_request_validation()
        
        # Test 10: Test error handling
        print("\n📋 TEST 10: Error Handling")
        await self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 TECH CARD EDITING TESTING SUMMARY")
        print("=" * 80)
        
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
            ("V1 Tech Card Generation", any("V1 Tech Card Generation" in r and "✅ PASS" in r for r in self.results)),
            ("V2 Tech Card Generation", any("V2 Tech Card Generation" in r and "✅ PASS" in r for r in self.results)),
            ("User History Endpoint", any("User History Endpoint" in r and "✅ PASS" in r for r in self.results)),
            ("Database Connectivity", any("Database Connectivity" in r and "✅ PASS" in r for r in self.results)),
            ("OpenAI Integration", any("OpenAI Integration" in r and "✅ PASS" in r for r in self.results)),
            ("Edit Tech Card Endpoint (V1)", any("Edit Tech Card Endpoint (V1)" in r and "✅ PASS" in r for r in self.results)),
            ("Edit Tech Card Endpoint (V2)", any("Edit Tech Card Endpoint (V2)" in r and "✅ PASS" in r for r in self.results))
        ]
        
        all_critical_passed = all(passed for _, passed in critical_tests)
        
        for test_name, passed in critical_tests:
            status = "✅" if passed else "❌"
            print(f"  {status} {test_name}")
        
        # Detailed diagnosis
        print("\n🔍 DETAILED DIAGNOSIS:")
        
        if not any("V1 Tech Card Generation" in r and "✅ PASS" in r for r in self.results):
            print("❌ CRITICAL: V1 tech card generation is not working")
            
        if not any("V2 Tech Card Generation" in r and "✅ PASS" in r for r in self.results):
            print("❌ CRITICAL: V2 tech card generation is not working - this blocks all editing functionality")
            
        if not any("Edit Tech Card Endpoint (V1)" in r and "✅ PASS" in r for r in self.results):
            print("❌ CRITICAL: Edit endpoint not working with V1 tech cards")
            
        if not any("Edit Tech Card Endpoint (V2)" in r and "✅ PASS" in r for r in self.results):
            print("❌ CRITICAL BUG IDENTIFIED: Edit endpoint cannot find V2 tech cards - Collection mismatch!")
            print("   🔧 ROOT CAUSE: Edit endpoint looks in 'tech_cards' collection but V2 cards are saved in 'user_history'")
            
        if not any("OpenAI Integration" in r and "✅ PASS" in r for r in self.results):
            print("❌ CRITICAL: OpenAI integration failure - check API key and model availability")
            
        if not any("Database Connectivity" in r and "✅ PASS" in r for r in self.results):
            print("❌ CRITICAL: Database connectivity issues - tech cards not persisting properly")
        
        if all_critical_passed:
            print("\n🎉 OUTSTANDING SUCCESS: Tech card editing functionality is FULLY OPERATIONAL!")
            print("✅ Tech card generation working")
            print("✅ Edit endpoint functional")
            print("✅ Database integration working")
            print("✅ OpenAI integration operational")
        else:
            print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            failed_tests = [name for name, passed in critical_tests if not passed]
            for test in failed_tests:
                print(f"❌ {test}")
            
            print("\n🔧 RECOMMENDED ACTIONS:")
            if not any("Edit Tech Card Endpoint (V2)" in r and "✅ PASS" in r for r in self.results):
                print("1. 🚨 URGENT: Fix edit endpoint to support V2 tech cards")
                print("   - Modify /api/edit-tech-card to look in 'user_history' collection for V2 cards")
                print("   - Add logic to detect V2 vs V1 tech cards and query appropriate collection")
                print("   - Update tech card content handling for V2 format")
                
            if not any("OpenAI Integration" in r and "✅ PASS" in r for r in self.results):
                print("2. Check OpenAI API key configuration in backend/.env")
                print("3. Verify GPT-4o-mini model availability")
                print("4. Check OpenAI API quota and billing")
                
            if not any("Database Connectivity" in r and "✅ PASS" in r for r in self.results):
                print("5. Verify MongoDB connection string in backend/.env")
                print("6. Check if collections exist and are accessible")
                
            if not any("Edit Tech Card Endpoint (V1)" in r and "✅ PASS" in r for r in self.results):
                print("7. Check V1 tech card generation and storage")
                print("8. Verify EditRequest model validation")
                print("9. Check EDIT_PROMPT template formatting")
        
        return success_rate >= 60  # 60% success rate threshold for critical functionality

async def main():
    """Main test execution"""
    tester = TechCardEditingTester()
    
    try:
        success = await tester.run_comprehensive_test()
        
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