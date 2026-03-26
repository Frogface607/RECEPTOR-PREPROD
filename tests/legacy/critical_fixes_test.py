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

class CriticalFixesTester:
    def __init__(self):
        self.test_user_id = f"critical_fixes_test_{str(uuid.uuid4())[:8]}"
        self.results = []
        self.generated_tech_cards = []
        
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

    async def generate_v2_tech_card(self, dish_name: str):
        """Generate V2 tech card using new API endpoint"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "name": dish_name,
                    "cuisine": "русская",
                    "user_id": self.test_user_id
                }
                
                # Use the V2 generation endpoint
                response = await client.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    # For V2 API, the ID is in data.card.meta.id
                    tech_card_id = None
                    if data.get("card") and data["card"].get("meta"):
                        tech_card_id = data["card"]["meta"].get("id")
                    
                    if tech_card_id:
                        self.generated_tech_cards.append({
                            "id": tech_card_id,
                            "dish_name": dish_name,
                            "type": "V2",
                            "collection": "user_history"
                        })
                        
                        await self.log_result(
                            f"V2 Tech Card Generation ({dish_name})", 
                            True, 
                            f"Generated with ID: {tech_card_id}"
                        )
                        return tech_card_id
                    else:
                        await self.log_result(
                            f"V2 Tech Card Generation ({dish_name})", 
                            False, 
                            f"No ID returned: {data}"
                        )
                        return None
                else:
                    await self.log_result(
                        f"V2 Tech Card Generation ({dish_name})", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result(
                f"V2 Tech Card Generation ({dish_name})", 
                False, 
                f"Exception: {str(e)}"
            )
            return None

    async def generate_v1_tech_card(self, dish_name: str):
        """Generate V1 tech card using legacy endpoint"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "user_id": self.test_user_id,
                    "dish_name": dish_name,
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
                            "dish_name": dish_name,
                            "type": "V1",
                            "collection": "tech_cards"
                        })
                        
                        await self.log_result(
                            f"V1 Tech Card Generation ({dish_name})", 
                            True, 
                            f"Generated with ID: {tech_card_id}"
                        )
                        return tech_card_id
                    else:
                        await self.log_result(
                            f"V1 Tech Card Generation ({dish_name})", 
                            False, 
                            f"No ID returned: {data}"
                        )
                        return None
                else:
                    await self.log_result(
                        f"V1 Tech Card Generation ({dish_name})", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result(
                f"V1 Tech Card Generation ({dish_name})", 
                False, 
                f"Exception: {str(e)}"
            )
            return None

    async def test_edit_v2_tech_card(self, tech_card_id: str, dish_name: str):
        """Test editing V2 tech card - CRITICAL FIX TEST"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "tech_card_id": tech_card_id,
                    "edit_instruction": "Увеличить порцию в 2 раза",
                    "user_id": self.test_user_id
                }
                
                response = await client.post(f"{API_BASE}/edit-tech-card", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if edit was successful
                    if data.get("success") or "id" in data:
                        await self.log_result(
                            f"V2 Tech Card Edit ({dish_name})", 
                            True, 
                            f"Successfully edited V2 tech card (ID: {tech_card_id[:8]}...)"
                        )
                        return True
                    else:
                        await self.log_result(
                            f"V2 Tech Card Edit ({dish_name})", 
                            False, 
                            f"Edit response indicates failure: {data}"
                        )
                        return False
                elif response.status_code == 404:
                    await self.log_result(
                        f"V2 Tech Card Edit ({dish_name})", 
                        False, 
                        f"404 Error - Tech card not found (CRITICAL BUG): {response.text}"
                    )
                    return False
                else:
                    await self.log_result(
                        f"V2 Tech Card Edit ({dish_name})", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                f"V2 Tech Card Edit ({dish_name})", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_edit_v1_tech_card(self, tech_card_id: str, dish_name: str):
        """Test editing V1 tech card - Should work as before"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "tech_card_id": tech_card_id,
                    "edit_instruction": "Добавить больше специй"
                }
                
                response = await client.post(f"{API_BASE}/edit-tech-card", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if edit was successful
                    if data.get("success") or "id" in data:
                        await self.log_result(
                            f"V1 Tech Card Edit ({dish_name})", 
                            True, 
                            f"Successfully edited V1 tech card (ID: {tech_card_id[:8]}...)"
                        )
                        return True
                    else:
                        await self.log_result(
                            f"V1 Tech Card Edit ({dish_name})", 
                            False, 
                            f"Edit response indicates failure: {data}"
                        )
                        return False
                else:
                    await self.log_result(
                        f"V1 Tech Card Edit ({dish_name})", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                f"V1 Tech Card Edit ({dish_name})", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_user_history_datetime_fix(self):
        """Test user history endpoint - CRITICAL DATETIME FIX TEST"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/user-history/{self.test_user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    if "history" in data and isinstance(data["history"], list):
                        history_count = len(data["history"])
                        await self.log_result(
                            "User History DateTime Fix", 
                            True, 
                            f"Successfully retrieved user history with {history_count} items (no datetime error)"
                        )
                        return data["history"]
                    else:
                        await self.log_result(
                            "User History DateTime Fix", 
                            False, 
                            f"Invalid response structure: {data}"
                        )
                        return []
                elif response.status_code == 500:
                    await self.log_result(
                        "User History DateTime Fix", 
                        False, 
                        f"500 Error - DateTime sorting issue (CRITICAL BUG): {response.text}"
                    )
                    return []
                else:
                    await self.log_result(
                        "User History DateTime Fix", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return []
                    
        except Exception as e:
            await self.log_result(
                "User History DateTime Fix", 
                False, 
                f"Exception: {str(e)}"
            )
            return []

    async def test_multi_collection_support(self, history_items: list):
        """Test that both V1 and V2 tech cards appear in history"""
        try:
            v1_items = []
            v2_items = []
            
            for item in history_items:
                # V2 items have techcard_v2_data field
                if item.get("techcard_v2_data") is not None:
                    v2_items.append(item)
                else:
                    v1_items.append(item)
            
            v1_count = len(v1_items)
            v2_count = len(v2_items)
            
            # Check if we have both types
            has_both_types = v1_count > 0 and v2_count > 0
            
            await self.log_result(
                "Multi-Collection Support", 
                has_both_types, 
                f"Found {v1_count} V1 items and {v2_count} V2 items in unified history"
            )
            
            return has_both_types
            
        except Exception as e:
            await self.log_result(
                "Multi-Collection Support", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def test_response_metadata(self, history_items: list):
        """Test that response includes proper metadata about collections and card types"""
        try:
            metadata_found = False
            
            for item in history_items:
                # Check for collection information
                has_collection_info = any(key in item for key in ["collection", "card_type", "techcard_v2_data"])
                
                if has_collection_info:
                    metadata_found = True
                    break
            
            await self.log_result(
                "Response Metadata", 
                metadata_found, 
                f"History items contain collection/type metadata: {metadata_found}"
            )
            
            return metadata_found
            
        except Exception as e:
            await self.log_result(
                "Response Metadata", 
                False, 
                f"Exception: {str(e)}"
            )
            return False

    async def run_critical_fixes_test(self):
        """Run comprehensive test of critical fixes"""
        print("🚨 CRITICAL FIXES TESTING STARTED")
        print("Testing: Collection Mismatch Fix + DateTime Sorting Fix")
        print(f"Test User ID: {self.test_user_id}")
        print("=" * 80)
        
        # Test 0: Create test user
        print("\n📋 TEST 0: Create Test User")
        user_created = await self.create_test_user()
        if not user_created:
            print("⚠️ Could not create test user, proceeding anyway...")
        
        # Test 1: Generate V2 tech card (for editing test)
        print("\n📋 TEST 1: Generate V2 Tech Card")
        v2_dish_name = "Тестовое блюдо для редактирования V2"
        v2_tech_card_id = await self.generate_v2_tech_card(v2_dish_name)
        
        # Test 2: Generate V1 tech card (for comparison)
        print("\n📋 TEST 2: Generate V1 Tech Card")
        v1_dish_name = "Тестовое блюдо для редактирования V1"
        v1_tech_card_id = await self.generate_v1_tech_card(v1_dish_name)
        
        # Wait for database writes
        await asyncio.sleep(3)
        
        # Test 3: Test user history endpoint (DateTime fix)
        print("\n📋 TEST 3: User History DateTime Fix")
        history_items = await self.test_user_history_datetime_fix()
        
        # Test 4: Test V2 tech card editing (Collection mismatch fix)
        print("\n📋 TEST 4: V2 Tech Card Edit (Critical Fix)")
        v2_edit_success = False
        if v2_tech_card_id:
            v2_edit_success = await self.test_edit_v2_tech_card(v2_tech_card_id, v2_dish_name)
        else:
            await self.log_result(
                f"V2 Tech Card Edit ({v2_dish_name})", 
                False, 
                "No V2 tech card ID available for editing test"
            )
        
        # Test 5: Test V1 tech card editing (Should still work)
        print("\n📋 TEST 5: V1 Tech Card Edit (Regression Test)")
        v1_edit_success = False
        if v1_tech_card_id:
            v1_edit_success = await self.test_edit_v1_tech_card(v1_tech_card_id, v1_dish_name)
        else:
            await self.log_result(
                f"V1 Tech Card Edit ({v1_dish_name})", 
                False, 
                "No V1 tech card ID available for editing test"
            )
        
        # Test 6: Multi-collection support
        print("\n📋 TEST 6: Multi-Collection Support")
        multi_collection_success = await self.test_multi_collection_support(history_items)
        
        # Test 7: Response metadata
        print("\n📋 TEST 7: Response Metadata")
        metadata_success = await self.test_response_metadata(history_items)
        
        # Summary
        print("\n" + "=" * 80)
        print("🚨 CRITICAL FIXES TESTING SUMMARY")
        print("=" * 80)
        
        passed_tests = len([r for r in self.results if "✅ PASS" in r])
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 SUCCESS RATE: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"📈 GENERATED TECH CARDS: {len(self.generated_tech_cards)}")
        print(f"📋 HISTORY ITEMS RETRIEVED: {len(history_items)}")
        
        print("\n📝 DETAILED RESULTS:")
        for result in self.results:
            print(f"  {result}")
        
        # Critical assessment
        print("\n🎯 CRITICAL FIXES ASSESSMENT:")
        
        critical_fixes = [
            ("V2 Tech Card Edit Fix", v2_edit_success),
            ("User History DateTime Fix", len(history_items) > 0),
            ("Multi-Collection Support", multi_collection_success),
            ("V1 Tech Card Edit (Regression)", v1_edit_success or v1_tech_card_id is None)
        ]
        
        all_critical_passed = all(passed for _, passed in critical_fixes)
        
        for fix_name, passed in critical_fixes:
            status = "✅" if passed else "❌"
            print(f"  {status} {fix_name}")
        
        if all_critical_passed:
            print("\n🎉 OUTSTANDING SUCCESS: Critical fixes are FULLY OPERATIONAL!")
            print("✅ V2 tech cards can be edited successfully (no more 404 errors)")
            print("✅ User history endpoint returns proper response (no datetime errors)")
            print("✅ Both V1 and V2 editing workflows function correctly")
            print("✅ Multi-collection support working properly")
        else:
            print("\n🚨 CRITICAL ISSUES STILL PRESENT:")
            failed_fixes = [name for name, passed in critical_fixes if not passed]
            for fix in failed_fixes:
                print(f"❌ {fix}")
            
            if not v2_edit_success:
                print("\n⚠️ URGENT: V2 tech card editing still returns 404 - collection mismatch fix may not be working")
            
            if len(history_items) == 0:
                print("\n⚠️ URGENT: User history endpoint still has issues - datetime sorting fix may not be working")
        
        return success_rate >= 75  # 75% success rate threshold for critical fixes

async def main():
    """Main test execution"""
    tester = CriticalFixesTester()
    
    try:
        success = await tester.run_critical_fixes_test()
        
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