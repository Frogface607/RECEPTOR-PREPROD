#!/usr/bin/env python3
"""
AI-Powered Tech Card Editing V2 Endpoints Testing
=================================================

Comprehensive backend testing for newly implemented AI-powered tech card editing endpoints:
1. POST /api/v1/techcards.v2/edit - Main AI editing endpoint
2. POST /api/v1/techcards.v2/suggest-improvements - AI suggestions endpoint  
3. POST /api/v1/techcards.v2/batch-edit - Batch editing endpoint

Tests cover:
- Basic edit functionality with different edit types
- AI suggestions system
- Batch editing capabilities
- Error handling and validation
- Integration with existing OpenAI setup
- Database persistence and updates
"""

import requests
import json
import time
import os
from datetime import datetime
from pymongo import MongoClient

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_icon} {test_name}")
    if details:
        print(f"    {details}")

def get_sample_techcard():
    """Get a sample V2 tech card from database for testing"""
    try:
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
        db_name = os.getenv('DB_NAME', 'receptor_pro')
        
        client = MongoClient(mongo_url)
        db = client[db_name]
        
        # Find a V2 tech card
        sample_doc = db.user_history.find_one({'techcard_v2_data': {'$exists': True}})
        client.close()
        
        if sample_doc:
            return {
                'id': sample_doc['id'],
                'title': sample_doc['dish_name'],
                'data': sample_doc['techcard_v2_data']
            }
        return None
    except Exception as e:
        log_test("Database Connection", "FAIL", f"Error: {str(e)}")
        return None

def test_edit_endpoint_basic():
    """Test basic AI editing functionality"""
    log_test("=== TESTING POST /api/v1/techcards.v2/edit ===", "INFO")
    
    # Get sample tech card
    sample_card = get_sample_techcard()
    if not sample_card:
        log_test("Get Sample Tech Card", "FAIL", "No V2 tech cards found in database")
        return False
    
    log_test("Get Sample Tech Card", "PASS", f"Using: {sample_card['title']} (ID: {sample_card['id']})")
    
    # Test 1: Basic modification
    try:
        payload = {
            "tech_card_id": sample_card['id'],
            "edit_instruction": "Увеличить порцию в 2 раза",
            "user_id": "test_user",
            "edit_type": "modify"
        }
        
        response = requests.post(f"{API_BASE}/techcards.v2/edit", json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success' and result.get('updated_card'):
                log_test("Basic Edit (Modify)", "PASS", f"Changes: {len(result.get('changes_made', []))}")
                
                # Verify structure
                updated_card = result['updated_card']
                required_fields = ['meta', 'portions', 'yield_', 'ingredients', 'process', 'nutrition', 'cost']
                missing_fields = [field for field in required_fields if field not in updated_card]
                
                if not missing_fields:
                    log_test("Response Structure Validation", "PASS", "All required fields present")
                else:
                    log_test("Response Structure Validation", "FAIL", f"Missing fields: {missing_fields}")
                    
                return True
            else:
                log_test("Basic Edit (Modify)", "FAIL", f"Invalid response structure: {result}")
                return False
        else:
            log_test("Basic Edit (Modify)", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("Basic Edit (Modify)", "FAIL", f"Exception: {str(e)}")
        return False

def test_edit_types():
    """Test different edit types"""
    sample_card = get_sample_techcard()
    if not sample_card:
        return False
    
    edit_types = [
        ("optimize", "Оптимизировать рецепт для снижения себестоимости"),
        ("suggest_alternatives", "Предложить альтернативы для аллергиков"),
        ("adjust_portions", "Изменить на 4 порции")
    ]
    
    for edit_type, instruction in edit_types:
        try:
            payload = {
                "tech_card_id": sample_card['id'],
                "edit_instruction": instruction,
                "user_id": "test_user",
                "edit_type": edit_type
            }
            
            response = requests.post(f"{API_BASE}/techcards.v2/edit", json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    changes = result.get('changes_made', [])
                    suggestions = result.get('ai_suggestions', [])
                    log_test(f"Edit Type: {edit_type}", "PASS", 
                           f"Changes: {len(changes)}, Suggestions: {len(suggestions)}")
                else:
                    log_test(f"Edit Type: {edit_type}", "FAIL", f"Status: {result.get('status')}")
            else:
                log_test(f"Edit Type: {edit_type}", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            log_test(f"Edit Type: {edit_type}", "FAIL", f"Exception: {str(e)}")

def test_suggest_improvements_endpoint():
    """Test AI suggestions endpoint"""
    log_test("=== TESTING POST /api/v1/techcards.v2/suggest-improvements ===", "INFO")
    
    sample_card = get_sample_techcard()
    if not sample_card:
        return False
    
    suggestion_types = ["ingredients", "process", "cost", "nutrition", "all"]
    
    for suggestion_type in suggestion_types:
        try:
            payload = {
                "tech_card_id": sample_card['id'],
                "suggestion_type": suggestion_type
            }
            
            response = requests.post(f"{API_BASE}/techcards.v2/suggest-improvements", json=payload, timeout=45)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    suggestions = result.get('suggestions', [])
                    log_test(f"Suggestions ({suggestion_type})", "PASS", 
                           f"Generated {len(suggestions)} suggestions")
                    
                    # Validate suggestion structure
                    if suggestions:
                        first_suggestion = suggestions[0]
                        required_keys = ['type', 'title', 'suggestion', 'impact']
                        if all(key in first_suggestion for key in required_keys):
                            log_test(f"Suggestion Structure ({suggestion_type})", "PASS", 
                                   f"Valid structure: {first_suggestion['type']}")
                        else:
                            log_test(f"Suggestion Structure ({suggestion_type})", "FAIL", 
                                   f"Missing keys in: {first_suggestion}")
                else:
                    log_test(f"Suggestions ({suggestion_type})", "FAIL", f"Status: {result.get('status')}")
            else:
                log_test(f"Suggestions ({suggestion_type})", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            log_test(f"Suggestions ({suggestion_type})", "FAIL", f"Exception: {str(e)}")

def test_batch_edit_endpoint():
    """Test batch editing functionality"""
    log_test("=== TESTING POST /api/v1/techcards.v2/batch-edit ===", "INFO")
    
    # Get multiple tech cards for batch testing
    try:
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
        db_name = os.getenv('DB_NAME', 'receptor_pro')
        
        client = MongoClient(mongo_url)
        db = client[db_name]
        
        # Get multiple V2 tech cards
        sample_docs = list(db.user_history.find({'techcard_v2_data': {'$exists': True}}).limit(3))
        client.close()
        
        if len(sample_docs) < 2:
            log_test("Get Multiple Tech Cards", "FAIL", "Need at least 2 tech cards for batch testing")
            return False
        
        tech_card_ids = [doc['id'] for doc in sample_docs]
        log_test("Get Multiple Tech Cards", "PASS", f"Found {len(tech_card_ids)} cards")
        
        # Test batch edit
        payload = {
            "tech_card_ids": tech_card_ids,
            "edit_instruction": "Добавить соль по вкусу в каждое блюдо",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{API_BASE}/techcards.v2/batch-edit", json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                processed = result.get('processed', 0)
                successful = result.get('successful', 0)
                failed = result.get('failed', 0)
                
                log_test("Batch Edit Processing", "PASS", 
                       f"Processed: {processed}, Success: {successful}, Failed: {failed}")
                
                # Validate results structure
                results = result.get('results', [])
                if len(results) == len(tech_card_ids):
                    log_test("Batch Edit Results", "PASS", f"All {len(results)} cards processed")
                    
                    # Check individual results
                    success_count = len([r for r in results if r.get('status') == 'success'])
                    if success_count > 0:
                        log_test("Batch Edit Success Rate", "PASS", 
                               f"{success_count}/{len(results)} cards successfully edited")
                        return True
                    else:
                        log_test("Batch Edit Success Rate", "FAIL", "No cards successfully edited")
                        return False
                else:
                    log_test("Batch Edit Results", "FAIL", 
                           f"Expected {len(tech_card_ids)} results, got {len(results)}")
                    return False
            else:
                log_test("Batch Edit Processing", "FAIL", f"Status: {result.get('status')}")
                return False
        else:
            log_test("Batch Edit Processing", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("Batch Edit Processing", "FAIL", f"Exception: {str(e)}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    log_test("=== TESTING ERROR HANDLING ===", "INFO")
    
    # Test 1: Invalid tech card ID
    try:
        payload = {
            "tech_card_id": "invalid-uuid-12345",
            "edit_instruction": "Test instruction",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{API_BASE}/techcards.v2/edit", json=payload, timeout=30)
        
        if response.status_code == 404:
            log_test("Invalid Tech Card ID", "PASS", "Correctly returned 404")
        else:
            log_test("Invalid Tech Card ID", "FAIL", f"Expected 404, got {response.status_code}")
            
    except Exception as e:
        log_test("Invalid Tech Card ID", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: Missing required fields
    try:
        payload = {
            "tech_card_id": "",  # Empty ID
            "edit_instruction": "",  # Empty instruction
        }
        
        response = requests.post(f"{API_BASE}/techcards.v2/edit", json=payload, timeout=30)
        
        if response.status_code == 400:
            log_test("Missing Required Fields", "PASS", "Correctly returned 400")
        else:
            log_test("Missing Required Fields", "FAIL", f"Expected 400, got {response.status_code}")
            
    except Exception as e:
        log_test("Missing Required Fields", "FAIL", f"Exception: {str(e)}")
    
    # Test 3: Invalid suggestion type
    try:
        sample_card = get_sample_techcard()
        if sample_card:
            payload = {
                "tech_card_id": sample_card['id'],
                "suggestion_type": "invalid_type"
            }
            
            response = requests.post(f"{API_BASE}/techcards.v2/suggest-improvements", json=payload, timeout=30)
            
            # Should still work but with default behavior
            if response.status_code == 200:
                log_test("Invalid Suggestion Type", "PASS", "Handled gracefully")
            else:
                log_test("Invalid Suggestion Type", "WARN", f"HTTP {response.status_code}")
                
    except Exception as e:
        log_test("Invalid Suggestion Type", "FAIL", f"Exception: {str(e)}")

def test_openai_integration():
    """Test OpenAI integration and model configuration"""
    log_test("=== TESTING OPENAI INTEGRATION ===", "INFO")
    
    # Check environment variables
    openai_key = os.getenv('OPENAI_API_KEY')
    model = os.getenv('TECHCARDS_V2_MODEL', 'gpt-4o-mini')
    
    if openai_key:
        log_test("OpenAI API Key", "PASS", f"Key present (length: {len(openai_key)})")
    else:
        log_test("OpenAI API Key", "FAIL", "OPENAI_API_KEY not found")
        return False
    
    log_test("Model Configuration", "PASS", f"Using model: {model}")
    
    # Test actual AI integration with a simple edit
    sample_card = get_sample_techcard()
    if sample_card:
        try:
            payload = {
                "tech_card_id": sample_card['id'],
                "edit_instruction": "Добавить щепотку черного перца",
                "user_id": "test_user",
                "edit_type": "modify"
            }
            
            start_time = time.time()
            response = requests.post(f"{API_BASE}/techcards.v2/edit", json=payload, timeout=60)
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    response_time = end_time - start_time
                    log_test("AI Integration Test", "PASS", 
                           f"Response time: {response_time:.2f}s")
                    
                    # Check if changes were made
                    changes = result.get('changes_made', [])
                    if changes:
                        log_test("AI Change Analysis", "PASS", f"Detected changes: {changes}")
                    else:
                        log_test("AI Change Analysis", "WARN", "No changes detected")
                        
                    return True
                else:
                    log_test("AI Integration Test", "FAIL", f"Status: {result.get('status')}")
                    return False
            else:
                log_test("AI Integration Test", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            log_test("AI Integration Test", "FAIL", f"Exception: {str(e)}")
            return False
    
    return False

def test_database_persistence():
    """Test database updates after editing"""
    log_test("=== TESTING DATABASE PERSISTENCE ===", "INFO")
    
    sample_card = get_sample_techcard()
    if not sample_card:
        return False
    
    try:
        # Get original data
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
        db_name = os.getenv('DB_NAME', 'receptor_pro')
        
        client = MongoClient(mongo_url)
        db = client[db_name]
        
        original_doc = db.user_history.find_one({"id": sample_card['id']})
        original_updated_at = original_doc.get('updated_at')
        
        # Perform edit
        payload = {
            "tech_card_id": sample_card['id'],
            "edit_instruction": "Добавить тестовый ингредиент для проверки персистентности",
            "user_id": "test_user",
            "edit_type": "modify"
        }
        
        response = requests.post(f"{API_BASE}/techcards.v2/edit", json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                # Check database was updated
                updated_doc = db.user_history.find_one({"id": sample_card['id']})
                new_updated_at = updated_doc.get('updated_at')
                
                if new_updated_at != original_updated_at:
                    log_test("Database Update Timestamp", "PASS", "Timestamp updated")
                else:
                    log_test("Database Update Timestamp", "FAIL", "Timestamp not updated")
                
                # Check if edit metadata was saved
                if updated_doc.get('last_edit_instruction'):
                    log_test("Edit Metadata Persistence", "PASS", "Edit instruction saved")
                else:
                    log_test("Edit Metadata Persistence", "FAIL", "Edit instruction not saved")
                
                # Check if V2 data was updated
                if updated_doc.get('techcard_v2_data'):
                    log_test("V2 Data Persistence", "PASS", "V2 data updated")
                    client.close()
                    return True
                else:
                    log_test("V2 Data Persistence", "FAIL", "V2 data not found")
                    client.close()
                    return False
            else:
                log_test("Database Persistence Test", "FAIL", f"Edit failed: {result.get('status')}")
                client.close()
                return False
        else:
            log_test("Database Persistence Test", "FAIL", f"HTTP {response.status_code}")
            client.close()
            return False
            
    except Exception as e:
        log_test("Database Persistence Test", "FAIL", f"Exception: {str(e)}")
        if 'client' in locals():
            client.close()
        return False

def main():
    """Run comprehensive AI-powered tech card editing tests"""
    print("🚀 AI-POWERED TECH CARD EDITING V2 COMPREHENSIVE TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test results tracking
    test_results = []
    
    # Run all tests
    tests = [
        ("Basic Edit Functionality", test_edit_endpoint_basic),
        ("Edit Types Testing", test_edit_types),
        ("AI Suggestions Endpoint", test_suggest_improvements_endpoint),
        ("Batch Edit Endpoint", test_batch_edit_endpoint),
        ("Error Handling", test_error_handling),
        ("OpenAI Integration", test_openai_integration),
        ("Database Persistence", test_database_persistence)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            log_test(f"{test_name} (Exception)", "FAIL", str(e))
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL AI-POWERED TECH CARD EDITING ENDPOINTS ARE FULLY OPERATIONAL!")
        print("✅ Main edit endpoint working with all edit types")
        print("✅ AI suggestions system functional")
        print("✅ Batch editing capabilities operational")
        print("✅ Error handling robust")
        print("✅ OpenAI integration stable")
        print("✅ Database persistence confirmed")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review issues above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)