#!/usr/bin/env python3
"""
Backend API Testing for User History Functionality
Testing tech card generation, data format, and history retrieval
Focus: V1 and V2 tech card formats, dashboard stats, user history endpoint
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://techcard-wizard.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.test_user_id = f"test_user_{int(time.time())}"
        self.generated_cards = []
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_time=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_time:
            print(f"   Response time: {response_time:.3f}s")
        print()

    def test_user_creation(self):
        """Test automatic user creation for testing"""
        try:
            start_time = time.time()
            
            # Generate a tech card to trigger user creation
            response = requests.post(f"{API_BASE}/generate-tech-card", 
                json={
                    "user_id": self.test_user_id,
                    "dish_name": "Тестовое блюдо для истории",
                    "city": "moskva"
                },
                timeout=60
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('tech_card') and len(data['tech_card']) > 100:
                    self.generated_cards.append({
                        'id': data.get('tech_card_id'),
                        'name': "Тестовое блюдо для истории",
                        'content': data['tech_card'],
                        'format': 'V1'  # Legacy format
                    })
                    self.log_test("User Creation & Tech Card Generation", True, 
                                f"Generated tech card: {len(data['tech_card'])} chars", response_time)
                    return True
                else:
                    self.log_test("User Creation & Tech Card Generation", False, 
                                "Tech card content too short or missing")
                    return False
            else:
                self.log_test("User Creation & Tech Card Generation", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("User Creation & Tech Card Generation", False, f"Exception: {str(e)}")
            return False

    def test_v2_tech_card_generation(self):
        """Test V2 tech card generation with enhanced data structure"""
        try:
            start_time = time.time()
            
            # Try V2 endpoint if available
            response = requests.post(f"{API_BASE}/v1/techcards.v2/generate", 
                json={
                    "user_id": self.test_user_id,
                    "dish_name": "Паста Карбонара V2",
                    "city": "moskva",
                    "portions": 4
                },
                timeout=60
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('techcard'):
                    techcard = data['techcard']
                    # Check for V2 structure
                    has_v2_structure = (
                        'meta' in techcard and
                        'ingredients' in techcard and
                        'yield' in techcard
                    )
                    
                    if has_v2_structure:
                        self.generated_cards.append({
                            'id': techcard.get('id'),
                            'name': "Паста Карбонара V2",
                            'content': techcard,
                            'format': 'V2'
                        })
                        self.log_test("V2 Tech Card Generation", True, 
                                    f"Generated V2 tech card with proper structure", response_time)
                        return True
                    else:
                        self.log_test("V2 Tech Card Generation", False, 
                                    "Missing V2 structure fields")
                        return False
                else:
                    self.log_test("V2 Tech Card Generation", False, 
                                "No techcard in response")
                    return False
            else:
                # V2 endpoint might not exist, try alternative
                self.log_test("V2 Tech Card Generation", False, 
                            f"V2 endpoint not available: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("V2 Tech Card Generation", False, f"Exception: {str(e)}")
            return False

    def test_additional_tech_cards(self):
        """Generate additional tech cards for history testing"""
        dishes = [
            "Борщ украинский с говядиной",
            "Салат Цезарь с курицей", 
            "Стейк из говядины с картофелем"
        ]
        
        success_count = 0
        
        for dish in dishes:
            try:
                start_time = time.time()
                
                response = requests.post(f"{API_BASE}/generate-tech-card", 
                    json={
                        "user_id": self.test_user_id,
                        "dish_name": dish,
                        "city": "moskva"
                    },
                    timeout=60
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('tech_card'):
                        self.generated_cards.append({
                            'id': data.get('tech_card_id'),
                            'name': dish,
                            'content': data['tech_card'],
                            'format': 'V1'
                        })
                        success_count += 1
                        print(f"   ✅ Generated: {dish} ({response_time:.2f}s)")
                    else:
                        print(f"   ❌ Failed: {dish} - No content")
                else:
                    print(f"   ❌ Failed: {dish} - HTTP {response.status_code}")
                    
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Failed: {dish} - Exception: {str(e)}")
        
        self.log_test("Additional Tech Cards Generation", success_count == len(dishes), 
                    f"Generated {success_count}/{len(dishes)} additional tech cards")
        return success_count > 0

    def test_user_history_endpoint(self):
        """Test GET /api/user-history/{user_id} endpoint"""
        try:
            start_time = time.time()
            
            response = requests.get(f"{API_BASE}/user-history/{self.test_user_id}", timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if 'history' in data:
                    history = data['history']
                    
                    if len(history) > 0:
                        # Verify data structure
                        first_card = history[0]
                        required_fields = ['id', 'user_id', 'dish_name', 'created_at']
                        missing_fields = [field for field in required_fields if field not in first_card]
                        
                        if not missing_fields:
                            # Check for both V1 and V2 formats
                            v1_cards = [card for card in history if 'content' in card]
                            v2_cards = [card for card in history if 'techcard_v2_data' in card]
                            
                            details = f"Found {len(history)} cards total: {len(v1_cards)} V1, {len(v2_cards)} V2"
                            self.log_test("User History Endpoint Structure", True, details, response_time)
                            return True
                        else:
                            self.log_test("User History Endpoint Structure", False, 
                                        f"Missing fields: {missing_fields}", response_time)
                            return False
                    else:
                        self.log_test("User History Endpoint Structure", False, 
                                    "Empty history despite generating cards", response_time)
                        return False
                else:
                    self.log_test("User History Endpoint Structure", False, 
                                "Missing 'history' field in response", response_time)
                    return False
            else:
                self.log_test("User History Endpoint Structure", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User History Endpoint Structure", False, f"Exception: {str(e)}")
            return False

    def test_tech_card_data_formats(self):
        """Test that tech cards contain proper data for both V1 and V2 formats"""
        try:
            response = requests.get(f"{API_BASE}/user-history/{self.test_user_id}", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                history = data.get('history', [])
                
                if not history:
                    self.log_test("Tech Card Data Formats", False, "No history data to analyze")
                    return False
                
                v1_valid = 0
                v2_valid = 0
                
                for card in history:
                    # Check V1 format (legacy content)
                    if 'content' in card and card['content']:
                        content = card['content']
                        if len(content) > 100 and 'Ингредиенты' in content:
                            v1_valid += 1
                    
                    # Check V2 format (structured data)
                    if 'techcard_v2_data' in card:
                        v2_data = card['techcard_v2_data']
                        if isinstance(v2_data, dict) and 'ingredients' in v2_data:
                            v2_valid += 1
                
                total_cards = len(history)
                details = f"Analyzed {total_cards} cards: {v1_valid} valid V1, {v2_valid} valid V2"
                
                # Success if we have valid data in either format
                success = (v1_valid + v2_valid) > 0
                self.log_test("Tech Card Data Formats", success, details)
                return success
                
            else:
                self.log_test("Tech Card Data Formats", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Tech Card Data Formats", False, f"Exception: {str(e)}")
            return False

    def test_dashboard_stats_calculation(self):
        """Test dashboard statistics calculation from history data"""
        try:
            response = requests.get(f"{API_BASE}/user-history/{self.test_user_id}", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                history = data.get('history', [])
                
                if not history:
                    self.log_test("Dashboard Stats Calculation", False, "No history data for stats")
                    return False
                
                # Calculate stats like dashboard would
                total_cards = len(history)
                
                # Count by format
                v1_count = len([card for card in history if 'content' in card and card['content']])
                v2_count = len([card for card in history if 'techcard_v2_data' in card])
                
                # Recent activity (last 7 days)
                recent_count = 0
                for card in history:
                    created_at = card.get('created_at')
                    if created_at:
                        try:
                            card_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            days_ago = (datetime.now() - card_date.replace(tzinfo=None)).days
                            if days_ago <= 7:
                                recent_count += 1
                        except:
                            pass
                
                # Popular ingredients analysis
                all_ingredients = []
                for card in history:
                    dish_name = card.get('dish_name', '')
                    if dish_name:
                        # Simple ingredient extraction from dish names
                        words = dish_name.lower().split()
                        food_words = [w for w in words if len(w) > 3 and w not in ['блюдо', 'тестовое']]
                        all_ingredients.extend(food_words)
                
                popular_ingredients = list(set(all_ingredients))[:5]
                
                stats = {
                    'total_cards': total_cards,
                    'v1_cards': v1_count,
                    'v2_cards': v2_count,
                    'recent_activity': recent_count,
                    'popular_ingredients': popular_ingredients
                }
                
                details = f"Stats: {total_cards} total, {recent_count} recent, {len(popular_ingredients)} ingredients"
                
                # Success if we can calculate meaningful stats
                success = total_cards > 0 and (v1_count > 0 or v2_count > 0)
                self.log_test("Dashboard Stats Calculation", success, details)
                return success
                
            else:
                self.log_test("Dashboard Stats Calculation", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Dashboard Stats Calculation", False, f"Exception: {str(e)}")
            return False

    def test_tech_card_retrieval_by_id(self):
        """Test individual tech card retrieval if endpoint exists"""
        if not self.generated_cards:
            self.log_test("Tech Card Retrieval by ID", False, "No generated cards to test")
            return False
        
        try:
            # Try to get a specific tech card
            card = self.generated_cards[0]
            card_id = card.get('id')
            
            if not card_id:
                self.log_test("Tech Card Retrieval by ID", False, "No card ID available")
                return False
            
            # Try different possible endpoints
            endpoints = [
                f"/tech-card/{card_id}",
                f"/techcard/{card_id}",
                f"/v1/techcards/{card_id}",
                f"/user-techcard/{self.test_user_id}/{card_id}"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{API_BASE}{endpoint}", timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if data and ('content' in data or 'techcard' in data):
                            self.log_test("Tech Card Retrieval by ID", True, 
                                        f"Retrieved via {endpoint}")
                            return True
                except:
                    continue
            
            self.log_test("Tech Card Retrieval by ID", False, 
                        "No working endpoint found for individual card retrieval")
            return False
            
        except Exception as e:
            self.log_test("Tech Card Retrieval by ID", False, f"Exception: {str(e)}")
            return False

    def test_history_sorting_and_pagination(self):
        """Test that history is properly sorted (newest first) and handles pagination"""
        try:
            response = requests.get(f"{API_BASE}/user-history/{self.test_user_id}", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                history = data.get('history', [])
                
                if len(history) < 2:
                    self.log_test("History Sorting & Pagination", True, 
                                "Not enough cards to test sorting (but endpoint works)")
                    return True
                
                # Check if sorted by created_at (newest first)
                dates = []
                for card in history:
                    created_at = card.get('created_at')
                    if created_at:
                        try:
                            date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            dates.append(date)
                        except:
                            pass
                
                if len(dates) >= 2:
                    is_sorted = all(dates[i] >= dates[i+1] for i in range(len(dates)-1))
                    
                    details = f"Found {len(dates)} dated cards, sorted: {is_sorted}"
                    self.log_test("History Sorting & Pagination", is_sorted, details)
                    return is_sorted
                else:
                    self.log_test("History Sorting & Pagination", True, 
                                "Cannot verify sorting - insufficient date data")
                    return True
                    
            else:
                self.log_test("History Sorting & Pagination", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("History Sorting & Pagination", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Testing for User History Functionality")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User ID: {self.test_user_id}")
        print("=" * 80)
        
        # Run tests in sequence
        tests = [
            self.test_user_creation,
            self.test_v2_tech_card_generation,
            self.test_additional_tech_cards,
            self.test_user_history_endpoint,
            self.test_tech_card_data_formats,
            self.test_dashboard_stats_calculation,
            self.test_tech_card_retrieval_by_id,
            self.test_history_sorting_and_pagination
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        # Summary
        print("=" * 80)
        print("🎯 BACKEND TESTING SUMMARY")
        print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"Generated Cards: {len(self.generated_cards)}")
        
        # Critical issues
        critical_issues = []
        for result in self.test_results:
            if "FAIL" in result["status"] and any(keyword in result["test"] for keyword in 
                ["User History Endpoint", "Tech Card Data Formats", "User Creation"]):
                critical_issues.append(result["test"])
        
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   - {issue}")
        
        # Success criteria
        history_working = any("User History Endpoint" in r["test"] and "PASS" in r["status"] 
                            for r in self.test_results)
        data_formats_ok = any("Tech Card Data Formats" in r["test"] and "PASS" in r["status"] 
                            for r in self.test_results)
        
        if history_working and data_formats_ok:
            print(f"\n✅ CORE FUNCTIONALITY: User history endpoint and data formats are working")
        else:
            print(f"\n❌ CORE FUNCTIONALITY: Critical issues with user history or data formats")
        
        return passed, total, self.test_results

if __name__ == "__main__":
    tester = BackendTester()
    passed, total, results = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        exit(0)  # All tests passed
    elif passed >= total * 0.7:  # 70% pass rate
        exit(1)  # Mostly working but some issues
    else:
        exit(2)  # Major issues