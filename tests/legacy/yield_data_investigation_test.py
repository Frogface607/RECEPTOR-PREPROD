#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import uuid
from motor.motor_asyncio import AsyncIOMotorClient

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
DB_NAME = os.environ.get('DB_NAME', 'receptor_pro')

class YieldDataInvestigator:
    def __init__(self):
        self.test_user_id = f"yield_investigation_{str(uuid.uuid4())[:8]}"
        self.results = []
        self.generated_tech_cards = []
        self.mongo_client = None
        self.db = None
        
    async def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.results.append(result)
        print(result)
        
    async def connect_to_database(self):
        """Connect to MongoDB for direct database inspection"""
        try:
            self.mongo_client = AsyncIOMotorClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            
            # Test connection
            await self.db.command("ping")
            
            await self.log_result(
                "Database Connection", 
                True, 
                f"Connected to MongoDB: {DB_NAME}"
            )
            return True
            
        except Exception as e:
            await self.log_result(
                "Database Connection", 
                False, 
                f"Failed to connect to MongoDB: {str(e)}"
            )
            return False
    
    async def generate_test_tech_card_v2(self, dish_name: str):
        """Generate a V2 tech card with yield data for testing"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "name": dish_name,
                    "cuisine": "русская",
                    "equipment": [],
                    "budget": None,
                    "dietary": [],
                    "user_id": self.test_user_id
                }
                
                # Use the V2 generation endpoint
                response = await client.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if we have a card in the response
                    card_data = data.get("card")
                    if card_data:
                        tech_card_id = card_data.get("meta", {}).get("id")
                        
                        if tech_card_id:
                            self.generated_tech_cards.append({
                                "id": tech_card_id,
                                "dish_name": dish_name,
                                "type": "V2_Generated",
                                "response_data": data
                            })
                            
                            await self.log_result(
                                f"V2 Tech Card Generation ({dish_name})", 
                                True, 
                                f"Generated with ID: {tech_card_id}"
                            )
                            return tech_card_id, data
                        else:
                            await self.log_result(
                                f"V2 Tech Card Generation ({dish_name})", 
                                False, 
                                f"No ID in card meta: {data}"
                            )
                            return None, None
                    else:
                        await self.log_result(
                            f"V2 Tech Card Generation ({dish_name})", 
                            False, 
                            f"No card in response: {data}"
                        )
                        return None, None
                else:
                    await self.log_result(
                        f"V2 Tech Card Generation ({dish_name})", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return None, None
                    
        except Exception as e:
            await self.log_result(
                f"V2 Tech Card Generation ({dish_name})", 
                False, 
                f"Exception: {str(e)}"
            )
            return None, None
    
    async def inspect_database_structure(self, tech_card_id: str):
        """Inspect the actual database structure of saved tech cards"""
        try:
            if self.db is None:
                await self.log_result(
                    "Database Structure Analysis", 
                    False, 
                    "No database connection available"
                )
                return None
            
            # Check user_history collection
            user_history_doc = await self.db.user_history.find_one({"id": tech_card_id})
            
            # Check tech_cards collection (V1)
            tech_cards_doc = await self.db.tech_cards.find_one({"id": tech_card_id})
            
            analysis = {
                "tech_card_id": tech_card_id,
                "found_in_user_history": user_history_doc is not None,
                "found_in_tech_cards": tech_cards_doc is not None,
                "user_history_structure": {},
                "tech_cards_structure": {}
            }
            
            if user_history_doc:
                # Remove MongoDB ObjectId for JSON serialization
                if "_id" in user_history_doc:
                    del user_history_doc["_id"]
                
                analysis["user_history_structure"] = {
                    "has_techcard_v2_data": "techcard_v2_data" in user_history_doc,
                    "techcard_v2_data_type": type(user_history_doc.get("techcard_v2_data")).__name__ if "techcard_v2_data" in user_history_doc else "None",
                    "techcard_v2_data_is_none": user_history_doc.get("techcard_v2_data") is None,
                    "all_fields": list(user_history_doc.keys()),
                    "sample_data": user_history_doc
                }
                
                # Check for yield data specifically
                techcard_v2_data = user_history_doc.get("techcard_v2_data")
                if techcard_v2_data:
                    analysis["yield_analysis"] = {
                        "has_yield_field": "yield" in techcard_v2_data,
                        "yield_data": techcard_v2_data.get("yield"),
                        "yield_type": type(techcard_v2_data.get("yield")).__name__ if "yield" in techcard_v2_data else "None"
                    }
                else:
                    analysis["yield_analysis"] = {
                        "techcard_v2_data_is_none": True,
                        "reason": "techcard_v2_data field is None or missing"
                    }
            
            if tech_cards_doc:
                if "_id" in tech_cards_doc:
                    del tech_cards_doc["_id"]
                analysis["tech_cards_structure"] = {
                    "all_fields": list(tech_cards_doc.keys()),
                    "sample_data": tech_cards_doc
                }
            
            await self.log_result(
                "Database Structure Analysis", 
                True, 
                f"Analyzed structure for tech card {tech_card_id}"
            )
            
            return analysis
            
        except Exception as e:
            await self.log_result(
                "Database Structure Analysis", 
                False, 
                f"Exception: {str(e)}"
            )
            return None
    
    async def test_api_response_structure(self, user_id: str):
        """Test GET /api/user-history/{user_id} response structure"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/user-history/{user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    history = data.get("history", [])
                    
                    analysis = {
                        "total_items": len(history),
                        "items_with_techcard_v2_data": 0,
                        "items_with_yield_data": 0,
                        "yield_data_samples": [],
                        "field_analysis": {}
                    }
                    
                    for i, item in enumerate(history):
                        if "techcard_v2_data" in item and item["techcard_v2_data"] is not None:
                            analysis["items_with_techcard_v2_data"] += 1
                            
                            techcard_v2_data = item["techcard_v2_data"]
                            if "yield" in techcard_v2_data and techcard_v2_data["yield"] is not None:
                                analysis["items_with_yield_data"] += 1
                                analysis["yield_data_samples"].append({
                                    "item_index": i,
                                    "dish_name": item.get("dish_name"),
                                    "yield_data": techcard_v2_data["yield"]
                                })
                    
                    # Check field consistency
                    if history:
                        sample_item = history[0]
                        analysis["field_analysis"] = {
                            "sample_item_fields": list(sample_item.keys()),
                            "has_techcard_v2_data": "techcard_v2_data" in sample_item,
                            "techcard_v2_data_type": type(sample_item.get("techcard_v2_data")).__name__
                        }
                    
                    await self.log_result(
                        "API Response Structure", 
                        True, 
                        f"Analyzed {len(history)} items, {analysis['items_with_yield_data']} have yield data"
                    )
                    
                    return analysis
                else:
                    await self.log_result(
                        "API Response Structure", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result(
                "API Response Structure", 
                False, 
                f"Exception: {str(e)}"
            )
            return None
    
    async def trace_tech_card_generation_pipeline(self, dish_name: str):
        """Trace yield data through the entire tech card generation pipeline"""
        try:
            print(f"\n🔍 TRACING TECH CARD GENERATION PIPELINE FOR: {dish_name}")
            
            # Step 1: Generate tech card
            tech_card_id, generation_response = await self.generate_test_tech_card_v2(dish_name)
            
            if not tech_card_id:
                await self.log_result(
                    "Pipeline Trace - Generation", 
                    False, 
                    "Failed to generate tech card"
                )
                return None
            
            # Step 2: Check generation response for yield data
            yield_in_response = None
            if generation_response and "card" in generation_response:
                card_data = generation_response["card"]
                if card_data and "yield" in card_data:
                    yield_in_response = card_data["yield"]
            
            await self.log_result(
                "Pipeline Trace - Generation Response", 
                yield_in_response is not None, 
                f"Yield data in generation response: {'present' if yield_in_response else 'missing'}"
            )
            
            # Step 3: Wait a moment for database write
            await asyncio.sleep(2)
            
            # Step 4: Check database structure
            db_analysis = await self.inspect_database_structure(tech_card_id)
            
            # Step 5: Check API response
            api_analysis = await self.test_api_response_structure(self.test_user_id)
            
            # Step 6: Compile trace results
            trace_results = {
                "dish_name": dish_name,
                "tech_card_id": tech_card_id,
                "generation_response_has_yield": yield_in_response is not None,
                "generation_yield_data": yield_in_response,
                "database_analysis": db_analysis,
                "api_analysis": api_analysis
            }
            
            # Step 7: Identify where yield data is lost
            yield_lost_at = "unknown"
            if yield_in_response is not None:
                if db_analysis and db_analysis.get("yield_analysis", {}).get("has_yield_field"):
                    if api_analysis and api_analysis["items_with_yield_data"] > 0:
                        yield_lost_at = "nowhere - data preserved"
                    else:
                        yield_lost_at = "API serialization"
                else:
                    yield_lost_at = "database save"
            else:
                yield_lost_at = "generation phase"
            
            await self.log_result(
                "Pipeline Trace - Yield Data Loss Point", 
                yield_lost_at == "nowhere - data preserved", 
                f"Yield data lost at: {yield_lost_at}"
            )
            
            return trace_results
            
        except Exception as e:
            await self.log_result(
                "Pipeline Trace", 
                False, 
                f"Exception: {str(e)}"
            )
            return None
    
    async def analyze_existing_tech_cards(self):
        """Analyze existing tech cards in the database for yield data patterns"""
        try:
            if self.db is None:
                await self.log_result(
                    "Existing Tech Cards Analysis", 
                    False, 
                    "No database connection"
                )
                return None
            
            # Get sample of existing tech cards from user_history
            existing_cards = await self.db.user_history.find().limit(10).to_list(10)
            
            analysis = {
                "total_cards_found": len(existing_cards),
                "cards_with_techcard_v2_data": 0,
                "cards_with_yield_data": 0,
                "yield_data_samples": [],
                "field_structures": []
            }
            
            for i, card in enumerate(existing_cards):
                if "_id" in card:
                    del card["_id"]
                
                # Check for techcard_v2_data
                if "techcard_v2_data" in card and card["techcard_v2_data"] is not None:
                    analysis["cards_with_techcard_v2_data"] += 1
                    
                    techcard_v2_data = card["techcard_v2_data"]
                    
                    # Check for yield data
                    if "yield" in techcard_v2_data and techcard_v2_data["yield"] is not None:
                        analysis["cards_with_yield_data"] += 1
                        analysis["yield_data_samples"].append({
                            "card_index": i,
                            "dish_name": card.get("dish_name", "Unknown"),
                            "yield_data": techcard_v2_data["yield"],
                            "yield_type": type(techcard_v2_data["yield"]).__name__
                        })
                    
                    # Record field structure
                    if isinstance(techcard_v2_data, dict):
                        analysis["field_structures"].append({
                            "card_index": i,
                            "fields": list(techcard_v2_data.keys()),
                            "has_yield": "yield" in techcard_v2_data
                        })
            
            await self.log_result(
                "Existing Tech Cards Analysis", 
                True, 
                f"Analyzed {analysis['total_cards_found']} existing cards, {analysis['cards_with_yield_data']} have yield data"
            )
            
            return analysis
            
        except Exception as e:
            await self.log_result(
                "Existing Tech Cards Analysis", 
                False, 
                f"Exception: {str(e)}"
            )
            return None
    
    async def test_field_naming_consistency(self):
        """Test for field naming inconsistencies (yield vs yield_ vs yieldData)"""
        try:
            # Check all user_history documents for field naming patterns
            if self.db is None:
                await self.log_result(
                    "Field Naming Consistency", 
                    False, 
                    "No database connection"
                )
                return
            
            # Sample some documents from user_history
            sample_docs = await self.db.user_history.find().limit(10).to_list(10)
            
            field_patterns = {
                "yield": 0,
                "yield_": 0,
                "yieldData": 0,
                "other_yield_variants": []
            }
            
            for doc in sample_docs:
                techcard_v2_data = doc.get("techcard_v2_data")
                if techcard_v2_data and isinstance(techcard_v2_data, dict):
                    for field_name in techcard_v2_data.keys():
                        if "yield" in field_name.lower():
                            if field_name == "yield":
                                field_patterns["yield"] += 1
                            elif field_name == "yield_":
                                field_patterns["yield_"] += 1
                            elif field_name == "yieldData":
                                field_patterns["yieldData"] += 1
                            else:
                                field_patterns["other_yield_variants"].append(field_name)
            
            await self.log_result(
                "Field Naming Consistency", 
                True, 
                f"Field patterns found: {field_patterns}"
            )
            
            return field_patterns
            
        except Exception as e:
            await self.log_result(
                "Field Naming Consistency", 
                False, 
                f"Exception: {str(e)}"
            )
            return None
    
    async def test_data_completeness_comparison(self):
        """Compare data completeness between user_history and tech_cards collections"""
        try:
            if self.db is None:
                await self.log_result(
                    "Data Completeness Comparison", 
                    False, 
                    "No database connection"
                )
                return
            
            # Count documents in both collections
            user_history_count = await self.db.user_history.count_documents({})
            tech_cards_count = await self.db.tech_cards.count_documents({})
            
            # Sample documents from both collections
            user_history_sample = await self.db.user_history.find().limit(5).to_list(5)
            tech_cards_sample = await self.db.tech_cards.find().limit(5).to_list(5)
            
            comparison = {
                "user_history_count": user_history_count,
                "tech_cards_count": tech_cards_count,
                "user_history_fields": [],
                "tech_cards_fields": [],
                "yield_data_presence": {
                    "user_history": 0,
                    "tech_cards": 0
                }
            }
            
            # Analyze user_history structure
            for doc in user_history_sample:
                if "_id" in doc:
                    del doc["_id"]
                comparison["user_history_fields"] = list(doc.keys())
                
                techcard_v2_data = doc.get("techcard_v2_data")
                if techcard_v2_data and isinstance(techcard_v2_data, dict) and "yield" in techcard_v2_data:
                    comparison["yield_data_presence"]["user_history"] += 1
                break
            
            # Analyze tech_cards structure
            for doc in tech_cards_sample:
                if "_id" in doc:
                    del doc["_id"]
                comparison["tech_cards_fields"] = list(doc.keys())
                break
            
            await self.log_result(
                "Data Completeness Comparison", 
                True, 
                f"user_history: {user_history_count} docs, tech_cards: {tech_cards_count} docs"
            )
            
            return comparison
            
        except Exception as e:
            await self.log_result(
                "Data Completeness Comparison", 
                False, 
                f"Exception: {str(e)}"
            )
            return None
    
    async def run_comprehensive_investigation(self):
        """Run comprehensive yield data investigation"""
        print("🔍 CRITICAL BUG INVESTIGATION: YIELD DATA UNDEFINED DURING LOADING")
        print(f"Test User ID: {self.test_user_id}")
        print("=" * 80)
        
        # Test 1: Connect to database
        print("\n📋 TEST 1: Database Connection")
        db_connected = await self.connect_to_database()
        
        if not db_connected:
            print("⚠️ Cannot proceed without database connection")
            return False
        
        # Test 2: Analyze existing tech cards
        print("\n📋 TEST 2: Existing Tech Cards Analysis")
        existing_analysis = await self.analyze_existing_tech_cards()
        
        # Test 3: Data completeness comparison
        print("\n📋 TEST 3: Data Completeness Comparison")
        completeness_data = await self.test_data_completeness_comparison()
        
        # Test 4: Field naming consistency check
        print("\n📋 TEST 4: Field Naming Consistency")
        field_patterns = await self.test_field_naming_consistency()
        
        # Test 5: Generate test tech cards and trace pipeline
        print("\n📋 TEST 5: Tech Card Generation Pipeline Trace")
        test_dishes = ["Борщ украинский с говядиной", "Паста Карбонара"]
        
        pipeline_traces = []
        for dish in test_dishes:
            trace_result = await self.trace_tech_card_generation_pipeline(dish)
            if trace_result:
                pipeline_traces.append(trace_result)
            await asyncio.sleep(2)  # Delay between generations
        
        # Test 6: API response analysis
        print("\n📋 TEST 6: API Response Analysis")
        await asyncio.sleep(3)  # Allow time for database writes
        api_analysis = await self.test_api_response_structure(self.test_user_id)
        
        # Summary and analysis
        print("\n" + "=" * 80)
        print("🔍 YIELD DATA INVESTIGATION SUMMARY")
        print("=" * 80)
        
        passed_tests = len([r for r in self.results if "✅ PASS" in r])
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 SUCCESS RATE: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"📈 GENERATED TECH CARDS: {len(self.generated_tech_cards)}")
        
        print("\n📝 DETAILED RESULTS:")
        for result in self.results:
            print(f"  {result}")
        
        # Critical findings
        print("\n🎯 CRITICAL FINDINGS:")
        
        # Database structure analysis
        if completeness_data:
            print(f"📊 Database Collections:")
            print(f"  - user_history: {completeness_data['user_history_count']} documents")
            print(f"  - tech_cards: {completeness_data['tech_cards_count']} documents")
            print(f"  - Yield data presence: user_history={completeness_data['yield_data_presence']['user_history']}, tech_cards={completeness_data['yield_data_presence']['tech_cards']}")
        
        # Field naming patterns
        if field_patterns:
            print(f"📋 Field Naming Patterns:")
            for pattern, count in field_patterns.items():
                if pattern != "other_yield_variants":
                    print(f"  - {pattern}: {count} occurrences")
            if field_patterns["other_yield_variants"]:
                print(f"  - Other variants: {field_patterns['other_yield_variants']}")
        
        # Pipeline trace results
        if pipeline_traces:
            print(f"🔄 Pipeline Trace Results:")
            for trace in pipeline_traces:
                print(f"  - {trace['dish_name']}: Generation={'✅' if trace['generation_response_has_yield'] else '❌'}")
                if trace['database_analysis']:
                    db_yield = trace['database_analysis'].get('yield_analysis', {}).get('has_yield_field', False)
                    print(f"    Database yield: {'✅' if db_yield else '❌'}")
        
        # API analysis
        if api_analysis:
            print(f"🌐 API Response Analysis:")
            print(f"  - Total items: {api_analysis['total_items']}")
            print(f"  - Items with techcard_v2_data: {api_analysis['items_with_techcard_v2_data']}")
            print(f"  - Items with yield data: {api_analysis['items_with_yield_data']}")
        
        # Root cause analysis
        print("\n🚨 ROOT CAUSE ANALYSIS:")
        
        yield_issues_found = []
        
        # Check if yield data is being generated
        generation_issues = sum(1 for trace in pipeline_traces if not trace['generation_response_has_yield'])
        if generation_issues > 0:
            yield_issues_found.append(f"❌ Yield data not generated in {generation_issues}/{len(pipeline_traces)} tech cards")
        
        # Check database storage
        db_issues = sum(1 for trace in pipeline_traces 
                       if trace['database_analysis'] and 
                       not trace['database_analysis'].get('yield_analysis', {}).get('has_yield_field', False))
        if db_issues > 0:
            yield_issues_found.append(f"❌ Yield data not stored in database for {db_issues}/{len(pipeline_traces)} tech cards")
        
        # Check API serialization
        if api_analysis and api_analysis['items_with_techcard_v2_data'] > api_analysis['items_with_yield_data']:
            yield_issues_found.append(f"❌ Yield data lost during API serialization")
        
        if yield_issues_found:
            print("CRITICAL ISSUES IDENTIFIED:")
            for issue in yield_issues_found:
                print(f"  {issue}")
        else:
            print("✅ No critical yield data issues found in current test")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("1. Check TechCardV2 schema yield field serialization")
        print("2. Verify database save operations preserve yield data")
        print("3. Validate API response field mapping")
        print("4. Check for field naming inconsistencies (yield vs yield_)")
        
        # Close database connection
        if self.mongo_client:
            self.mongo_client.close()
        
        return success_rate >= 70  # 70% success rate threshold

async def main():
    """Main investigation execution"""
    investigator = YieldDataInvestigator()
    
    try:
        success = await investigator.run_comprehensive_investigation()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Investigation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Critical error during investigation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())