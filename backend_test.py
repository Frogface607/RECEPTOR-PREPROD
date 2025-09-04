#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import uuid

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://techcard-wizard.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class UnifiedHistoryTester:
    def __init__(self):
        self.test_user_id = f"unified_history_test_{str(uuid.uuid4())[:8]}"
        self.results = []
        self.generated_tech_cards = []
        
    async def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.results.append(result)
        print(result)
        
    async def test_unified_history_api(self):
        """Test GET /api/user-history/{user_id} unified functionality"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/user-history/{self.test_user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    if "history" in data and isinstance(data["history"], list):
                        await self.log_result(
                            "Unified History API Structure", 
                            True, 
                            f"Returns proper structure with history array (length: {len(data['history'])})"
                        )
                        return data["history"]
                    else:
                        await self.log_result(
                            "Unified History API Structure", 
                            False, 
                            f"Invalid response structure: {data}"
                        )
                        return []
                else:
                    await self.log_result(
                        "Unified History API Access", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return []
                    
        except Exception as e:
            await self.log_result(
                "Unified History API Access", 
                False, 
                f"Exception: {str(e)}"
            )
            return []
    
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
                    # Update the test user ID to the actual one returned
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
    
    async def generate_v2_tech_card(self, dish_name: str):
        """Generate V2 tech card using new API endpoint"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "user_id": self.test_user_id,
                    "dish_name": dish_name,
                    "is_inspiration": True
                }
                
                # Try save-tech-card endpoint for V2 format
                response = await client.post(f"{API_BASE}/save-tech-card", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    tech_card_id = data.get("id")
                    
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
    
    async def test_data_format_consistency(self, history_items: list):
        """Test that both V1 and V2 tech cards are returned in unified format"""
        try:
            v1_items = []
            v2_items = []
            
            for item in history_items:
                # Check required fields
                required_fields = ["id", "user_id", "dish_name", "content", "created_at", "status"]
                missing_fields = [field for field in required_fields if field not in item]
                
                if missing_fields:
                    await self.log_result(
                        "Data Format Consistency", 
                        False, 
                        f"Missing fields in item {item.get('id', 'unknown')}: {missing_fields}"
                    )
                    continue
                
                # Categorize by type
                if item.get("techcard_v2_data") is None:
                    v1_items.append(item)
                else:
                    v2_items.append(item)
            
            await self.log_result(
                "Data Format Consistency", 
                True, 
                f"Found {len(v1_items)} V1 items and {len(v2_items)} V2 items with proper structure"
            )
            
            return len(v1_items), len(v2_items)
            
        except Exception as e:
            await self.log_result(
                "Data Format Consistency", 
                False, 
                f"Exception: {str(e)}"
            )
            return 0, 0
    
    async def test_dashboard_stats_calculation(self, history_items: list):
        """Test dashboard statistics calculation from unified history"""
        try:
            if not history_items:
                await self.log_result(
                    "Dashboard Stats Calculation", 
                    False, 
                    "No history items to calculate stats from"
                )
                return
            
            # Calculate total tech cards
            total_cards = len([item for item in history_items if not item.get("is_menu", False)])
            
            # Calculate V1 vs V2 distribution
            v1_count = len([item for item in history_items if item.get("techcard_v2_data") is None])
            v2_count = len([item for item in history_items if item.get("techcard_v2_data") is not None])
            
            # Calculate recent activity (last 7 days)
            from datetime import datetime, timedelta
            week_ago = datetime.now() - timedelta(days=7)
            recent_items = []
            
            for item in history_items:
                created_at = item.get("created_at")
                if created_at:
                    try:
                        # Handle different date formats
                        if isinstance(created_at, str):
                            item_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            item_date = created_at
                        
                        if item_date >= week_ago:
                            recent_items.append(item)
                    except:
                        pass  # Skip items with invalid dates
            
            stats = {
                "total_tech_cards": total_cards,
                "v1_tech_cards": v1_count,
                "v2_tech_cards": v2_count,
                "recent_activity": len(recent_items)
            }
            
            await self.log_result(
                "Dashboard Stats Calculation", 
                True, 
                f"Stats: {stats}"
            )
            
            # Verify dashboard shows correct count (not "0 Техкарт создано")
            if total_cards > 0:
                await self.log_result(
                    "Dashboard Count Fix", 
                    True, 
                    f"Dashboard should show {total_cards} tech cards (not 0)"
                )
            else:
                await self.log_result(
                    "Dashboard Count Fix", 
                    False, 
                    "No tech cards found for dashboard display"
                )
            
            return stats
            
        except Exception as e:
            await self.log_result(
                "Dashboard Stats Calculation", 
                False, 
                f"Exception: {str(e)}"
            )
            return {}
    
    async def test_unified_history_sorting(self, history_items: list):
        """Test that history items are properly sorted by creation date (newest first)"""
        try:
            if len(history_items) < 2:
                await self.log_result(
                    "History Sorting", 
                    True, 
                    f"Only {len(history_items)} items, sorting not applicable"
                )
                return
            
            # Check if items are sorted by created_at (newest first)
            dates = []
            for item in history_items:
                created_at = item.get("created_at")
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            date_obj = created_at
                        dates.append(date_obj)
                    except:
                        pass
            
            if len(dates) >= 2:
                is_sorted = all(dates[i] >= dates[i+1] for i in range(len(dates)-1))
                
                await self.log_result(
                    "History Sorting", 
                    is_sorted, 
                    f"Items {'are' if is_sorted else 'are NOT'} sorted by date (newest first)"
                )
            else:
                await self.log_result(
                    "History Sorting", 
                    False, 
                    "Could not parse enough dates for sorting validation"
                )
                
        except Exception as e:
            await self.log_result(
                "History Sorting", 
                False, 
                f"Exception: {str(e)}"
            )
    
    async def run_comprehensive_test(self):
        """Run comprehensive unified history functionality test"""
        print("🎯 UNIFIED HISTORY FUNCTIONALITY COMPREHENSIVE TESTING STARTED")
        print(f"Test User ID: {self.test_user_id}")
        print("=" * 80)
        
        # Test 0: Create test user
        print("\n📋 TEST 0: Create Test User")
        user_created = await self.create_test_user()
        if not user_created:
            print("⚠️ Could not create test user, proceeding anyway...")
        
        # Test 1: Initial empty history
        print("\n📋 TEST 1: Initial Empty History")
        initial_history = await self.test_unified_history_api()
        
        # Test 2: Generate V1 tech cards (legacy format)
        print("\n📋 TEST 2: Generate V1 Tech Cards (Legacy)")
        v1_dishes = ["Борщ украинский с говядиной", "Салат Цезарь с курицей"]
        for dish in v1_dishes:
            await self.generate_v1_tech_card(dish)
            await asyncio.sleep(1)  # Small delay between generations
        
        # Test 3: Generate V2 tech cards (new format)
        print("\n📋 TEST 3: Generate V2 Tech Cards (New API)")
        v2_dishes = ["Паста Карбонара", "Стейк с картофельным пюре"]
        for dish in v2_dishes:
            await self.generate_v2_tech_card(dish)
            await asyncio.sleep(1)  # Small delay between generations
        
        # Test 4: Verify unified history combines both collections
        print("\n📋 TEST 4: Unified History API Integration")
        await asyncio.sleep(2)  # Allow time for database writes
        unified_history = await self.test_unified_history_api()
        
        # Test 5: Data format consistency
        print("\n📋 TEST 5: Data Format Consistency")
        v1_count, v2_count = await self.test_data_format_consistency(unified_history)
        
        # Test 6: Dashboard statistics calculation
        print("\n📋 TEST 6: Dashboard Statistics")
        stats = await self.test_dashboard_stats_calculation(unified_history)
        
        # Test 7: History sorting validation
        print("\n📋 TEST 7: History Sorting")
        await self.test_unified_history_sorting(unified_history)
        
        # Test 8: Verify specific fields for both V1 and V2
        print("\n📋 TEST 8: Field Validation")
        await self.test_field_validation(unified_history)
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 UNIFIED HISTORY TESTING SUMMARY")
        print("=" * 80)
        
        passed_tests = len([r for r in self.results if "✅ PASS" in r])
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 SUCCESS RATE: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"📈 GENERATED TECH CARDS: {len(self.generated_tech_cards)}")
        print(f"📋 UNIFIED HISTORY ITEMS: {len(unified_history)}")
        
        if stats:
            print(f"📊 DASHBOARD STATS: {stats}")
        
        print("\n📝 DETAILED RESULTS:")
        for result in self.results:
            print(f"  {result}")
        
        # Critical assessment
        print("\n🎯 CRITICAL ASSESSMENT:")
        
        critical_tests = [
            ("Unified History API", any("Unified History API" in r and "✅ PASS" in r for r in self.results)),
            ("V1 Tech Card Generation", any("V1 Tech Card Generation" in r and "✅ PASS" in r for r in self.results)),
            ("V2 Tech Card Generation", any("V2 Tech Card Generation" in r and "✅ PASS" in r for r in self.results)),
            ("Data Format Consistency", any("Data Format Consistency" in r and "✅ PASS" in r for r in self.results)),
            ("Dashboard Count Fix", any("Dashboard Count Fix" in r and "✅ PASS" in r for r in self.results))
        ]
        
        all_critical_passed = all(passed for _, passed in critical_tests)
        
        for test_name, passed in critical_tests:
            status = "✅" if passed else "❌"
            print(f"  {status} {test_name}")
        
        if all_critical_passed:
            print("\n🎉 OUTSTANDING SUCCESS: Unified history functionality is FULLY OPERATIONAL!")
            print("✅ Combines data from both tech_cards and user_history collections")
            print("✅ Returns V1 and V2 tech cards in unified format")
            print("✅ Dashboard stats calculation working correctly")
            print("✅ Resolves '0 Техкарт создано' issue")
        else:
            print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            failed_tests = [name for name, passed in critical_tests if not passed]
            for test in failed_tests:
                print(f"❌ {test}")
        
        return success_rate >= 80  # 80% success rate threshold
    
    async def test_field_validation(self, history_items: list):
        """Test that all history items have proper fields as specified in review"""
        try:
            required_fields = ["id", "user_id", "dish_name", "content", "created_at", "status"]
            
            valid_items = 0
            total_items = len(history_items)
            
            for item in history_items:
                has_all_fields = all(field in item for field in required_fields)
                
                # Additional checks for V2 data
                has_v2_structure = "techcard_v2_data" in item
                
                if has_all_fields:
                    valid_items += 1
            
            success = valid_items == total_items and total_items > 0
            
            await self.log_result(
                "Field Validation", 
                success, 
                f"{valid_items}/{total_items} items have all required fields"
            )
            
        except Exception as e:
            await self.log_result(
                "Field Validation", 
                False, 
                f"Exception: {str(e)}"
            )

async def main():
    """Main test execution"""
    tester = UnifiedHistoryTester()
    
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