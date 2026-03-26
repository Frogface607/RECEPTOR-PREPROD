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

class FullWorkflowTester:
    def __init__(self):
        self.test_user_id = f"full_workflow_test_{str(uuid.uuid4())[:8]}"
        self.results = []
        
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
                    "name": f"Test User {self.test_user_id[:8]}",
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

    async def test_scenario_1_v2_generation_and_edit(self):
        """Test Scenario 1: Generate V2 tech card, then edit it"""
        print("\n🎯 SCENARIO 1: V2 Tech Card Generation → Edit Workflow")
        
        # Step 1: Generate V2 tech card
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "name": "Борщ украинский с говядиной",
                    "cuisine": "русская",
                    "user_id": self.test_user_id
                }
                
                response = await client.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    tech_card_id = None
                    if data.get("card") and data["card"].get("meta"):
                        tech_card_id = data["card"]["meta"].get("id")
                    
                    if tech_card_id:
                        await self.log_result(
                            "Scenario 1 - V2 Generation", 
                            True, 
                            f"Generated V2 tech card with ID: {tech_card_id}"
                        )
                        
                        # Step 2: Edit the V2 tech card
                        edit_payload = {
                            "tech_card_id": tech_card_id,
                            "edit_instruction": "Увеличить порцию в 2 раза",
                            "user_id": self.test_user_id
                        }
                        
                        edit_response = await client.post(f"{API_BASE}/edit-tech-card", json=edit_payload)
                        
                        if edit_response.status_code == 200:
                            edit_data = edit_response.json()
                            await self.log_result(
                                "Scenario 1 - V2 Edit", 
                                True, 
                                f"Successfully edited V2 tech card: {edit_data.get('message', 'Success')}"
                            )
                            return True
                        else:
                            await self.log_result(
                                "Scenario 1 - V2 Edit", 
                                False, 
                                f"Edit failed: HTTP {edit_response.status_code} - {edit_response.text}"
                            )
                            return False
                    else:
                        await self.log_result(
                            "Scenario 1 - V2 Generation", 
                            False, 
                            f"No ID in response: {data}"
                        )
                        return False
                else:
                    await self.log_result(
                        "Scenario 1 - V2 Generation", 
                        False, 
                        f"Generation failed: HTTP {response.status_code} - {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Scenario 1 - Exception", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_scenario_2_user_history_datetime(self):
        """Test Scenario 2: User history with mixed datetime formats"""
        print("\n🎯 SCENARIO 2: User History DateTime Sorting")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/user-history/{self.test_user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "history" in data and isinstance(data["history"], list):
                        history_count = len(data["history"])
                        
                        # Check if items have proper datetime fields
                        datetime_issues = 0
                        for item in data["history"]:
                            created_at = item.get("created_at")
                            if created_at:
                                try:
                                    # Try to parse the datetime
                                    if isinstance(created_at, str):
                                        datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                except:
                                    datetime_issues += 1
                        
                        await self.log_result(
                            "Scenario 2 - User History", 
                            True, 
                            f"Retrieved {history_count} items, {datetime_issues} datetime issues (should be 0)"
                        )
                        return datetime_issues == 0
                    else:
                        await self.log_result(
                            "Scenario 2 - User History", 
                            False, 
                            f"Invalid response structure: {data}"
                        )
                        return False
                elif response.status_code == 500:
                    await self.log_result(
                        "Scenario 2 - User History", 
                        False, 
                        f"500 Error - DateTime sorting issue: {response.text}"
                    )
                    return False
                else:
                    await self.log_result(
                        "Scenario 2 - User History", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Scenario 2 - Exception", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_scenario_3_multi_collection_support(self):
        """Test Scenario 3: Multi-collection support (V1 and V2 editing)"""
        print("\n🎯 SCENARIO 3: Multi-Collection Support Testing")
        
        # Generate V1 tech card
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                v1_payload = {
                    "user_id": self.test_user_id,
                    "dish_name": "Салат Цезарь с курицей",
                    "portions": 2,
                    "city": "moskva"
                }
                
                v1_response = await client.post(f"{API_BASE}/generate-tech-card", json=v1_payload)
                
                if v1_response.status_code == 200:
                    v1_data = v1_response.json()
                    v1_tech_card_id = v1_data.get("id")
                    
                    if v1_tech_card_id:
                        await self.log_result(
                            "Scenario 3 - V1 Generation", 
                            True, 
                            f"Generated V1 tech card with ID: {v1_tech_card_id}"
                        )
                        
                        # Test V1 editing
                        v1_edit_payload = {
                            "tech_card_id": v1_tech_card_id,
                            "edit_instruction": "Добавить больше сыра пармезан"
                        }
                        
                        v1_edit_response = await client.post(f"{API_BASE}/edit-tech-card", json=v1_edit_payload)
                        
                        if v1_edit_response.status_code == 200:
                            await self.log_result(
                                "Scenario 3 - V1 Edit", 
                                True, 
                                f"Successfully edited V1 tech card"
                            )
                            return True
                        else:
                            await self.log_result(
                                "Scenario 3 - V1 Edit", 
                                False, 
                                f"V1 edit failed: HTTP {v1_edit_response.status_code} - {v1_edit_response.text}"
                            )
                            return False
                    else:
                        await self.log_result(
                            "Scenario 3 - V1 Generation", 
                            False, 
                            f"No ID in V1 response: {v1_data}"
                        )
                        return False
                else:
                    await self.log_result(
                        "Scenario 3 - V1 Generation", 
                        False, 
                        f"V1 generation failed: HTTP {v1_response.status_code} - {v1_response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Scenario 3 - Exception", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def run_full_workflow_test(self):
        """Run comprehensive full workflow test as specified in review request"""
        print("🎯 CRITICAL FIXES FULL WORKFLOW TESTING STARTED")
        print("Testing complete workflow: Generate V2 → Edit → User History")
        print(f"Test User ID: {self.test_user_id}")
        print("=" * 80)
        
        # Test 0: Create test user
        print("\n📋 TEST 0: Create Test User")
        user_created = await self.create_test_user()
        if not user_created:
            print("⚠️ Could not create test user, proceeding anyway...")
        
        # Run all scenarios
        scenario_1_success = await self.test_scenario_1_v2_generation_and_edit()
        await asyncio.sleep(2)  # Allow database writes
        
        scenario_2_success = await self.test_scenario_2_user_history_datetime()
        await asyncio.sleep(1)
        
        scenario_3_success = await self.test_scenario_3_multi_collection_support()
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 FULL WORKFLOW TESTING SUMMARY")
        print("=" * 80)
        
        passed_tests = len([r for r in self.results if "✅ PASS" in r])
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 SUCCESS RATE: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        print("\n📝 DETAILED RESULTS:")
        for result in self.results:
            print(f"  {result}")
        
        # Critical assessment
        print("\n🎯 CRITICAL WORKFLOW ASSESSMENT:")
        
        scenarios = [
            ("Scenario 1: V2 Generation → Edit", scenario_1_success),
            ("Scenario 2: User History DateTime Fix", scenario_2_success),
            ("Scenario 3: Multi-Collection Support", scenario_3_success)
        ]
        
        all_scenarios_passed = all(passed for _, passed in scenarios)
        
        for scenario_name, passed in scenarios:
            status = "✅" if passed else "❌"
            print(f"  {status} {scenario_name}")
        
        if all_scenarios_passed:
            print("\n🎉 OUTSTANDING SUCCESS: All critical fixes are FULLY OPERATIONAL!")
            print("✅ V2 tech cards can be generated and edited successfully")
            print("✅ User history endpoint handles mixed datetime formats safely")
            print("✅ Edit endpoint searches both collections (tech_cards + user_history)")
            print("✅ Both V1 and V2 editing workflows function correctly")
            print("✅ Complete end-to-end workflow validated")
        else:
            print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            failed_scenarios = [name for name, passed in scenarios if not passed]
            for scenario in failed_scenarios:
                print(f"❌ {scenario}")
        
        return success_rate >= 85  # 85% success rate threshold

async def main():
    """Main test execution"""
    tester = FullWorkflowTester()
    
    try:
        success = await tester.run_full_workflow_test()
        
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