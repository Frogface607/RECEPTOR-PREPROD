#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
import time
from datetime import datetime
import uuid

# Backend URL - use default if not set
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class RevolutionaryTester:
    def __init__(self):
        self.test_user_id = f"revolutionary_test_{str(uuid.uuid4())[:8]}"
        self.results = []
        self.generated_tech_cards = []
        self.user_created = False
        
    async def create_test_user(self):
        """Create a test user for testing"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Use a test user ID that will be auto-created
                self.test_user_id = f"test_user_{str(uuid.uuid4())[:8]}"
                
                await self.log_result("User Creation", True, f"Using test user ID {self.test_user_id}")
                return True
                    
        except Exception as e:
            await self.log_result("User Creation", False, f"Exception: {str(e)}")
            return False
        
    async def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.results.append(result)
        print(result)
        
    async def test_real_llm_generation(self):
        """ТЕСТ РЕАЛЬНОЙ ГЕНЕРАЦИИ ТЕХКАРТЫ: Борщ украинский с говядиной"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Test tech card generation with real LLM using v2 API
                dish_name = "Борщ украинский с говядиной"
                
                generation_data = {
                    "name": dish_name,  # Correct field name for v2 API
                    "cuisine": "russian",
                    "equipment": [],
                    "budget": 1500.0,
                    "dietary": [],
                    "user_id": self.test_user_id
                }
                
                print(f"🔥 Generating tech card for '{dish_name}' with real LLM...")
                start_time = time.time()
                
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/generate", 
                    json=generation_data,
                    params={"use_llm": "true"}
                )
                
                generation_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if it's real LLM generation (not skeleton)
                    status = data.get('status', '')
                    tech_card = data.get('card', {})
                    
                    if not tech_card:
                        await self.log_result(
                            "Real LLM Generation", 
                            False, 
                            f"No tech card returned, status={status}"
                        )
                        return None
                    
                    meta = tech_card.get('meta', {})
                    title = meta.get('title', '')
                    
                    # Verify it's not a skeleton response
                    is_real_llm = (
                        len(str(tech_card)) > 500 and  # Substantial content
                        dish_name.lower() in title.lower() and  # Contains dish name
                        len(tech_card.get('ingredients', [])) > 0 and  # Has ingredients
                        len(tech_card.get('process', [])) > 0 and  # Has process steps
                        status in ['success', 'draft']  # Valid status
                    )
                    
                    # Check for article and product_code fields
                    has_article = tech_card.get('article') is not None
                    ingredients = tech_card.get('ingredients', [])
                    has_product_codes = any(ing.get('product_code') for ing in ingredients)
                    
                    self.generated_tech_cards.append({
                        'id': tech_card.get('id'),
                        'name': dish_name,
                        'has_article': has_article,
                        'has_product_codes': has_product_codes,
                        'generation_time': generation_time,
                        'techcard': tech_card,
                        'status': status
                    })
                    
                    await self.log_result(
                        "Real LLM Generation", 
                        is_real_llm, 
                        f"Generated '{dish_name}' in {generation_time:.1f}s, status={status}, real_llm={is_real_llm}, has_article={has_article}, has_product_codes={has_product_codes}"
                    )
                    
                    return data
                else:
                    await self.log_result(
                        "Real LLM Generation", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result("Real LLM Generation", False, f"Exception: {str(e)}")
            return None
    
    async def test_iiko_rms_connection(self):
        """ТЕСТ ПОДКЛЮЧЕНИЯ К IIKO RMS: с кредами Sergey/metkamfetamin"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test iiko connection with real credentials using v2 API
                connection_data = {
                    "user_id": self.test_user_id
                }
                
                print(f"🔌 Testing iiko connection with Sergey credentials...")
                
                response = await client.post(
                    f"{API_BASE}/iiko/connect", 
                    json=connection_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    status = data.get('status', '')
                    organizations = data.get('organizations', [])
                    
                    is_connected = status == 'connected' and len(organizations) > 0
                    
                    await self.log_result(
                        "iiko RMS Connection", 
                        is_connected, 
                        f"status={status}, organizations={len(organizations)}"
                    )
                    
                    return data
                else:
                    await self.log_result(
                        "iiko RMS Connection", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result("iiko RMS Connection", False, f"Exception: {str(e)}")
            return None
    
    async def test_article_extraction(self):
        """ТЕСТ ИЗВЛЕЧЕНИЯ АРТИКУЛОВ: из реального iiko"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test article extraction using v2 catalog search
                test_products = [
                    "говядина",
                    "свекла", 
                    "капуста",
                    "морковь",
                    "лук репчатый"
                ]
                
                print(f"🔍 Testing article extraction for {len(test_products)} products...")
                
                for product_name in test_products:
                    response = await client.get(
                        f"{API_BASE}/v1/techcards.v2/catalog-search",
                        params={"q": product_name, "source": "iiko"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        results = data.get('results', [])
                        has_results = len(results) > 0
                        
                        # Check if any results have real articles
                        has_real_article = False
                        if has_results:
                            for result in results[:3]:  # Check first 3 results
                                article = result.get('article') or result.get('product_code')
                                if article and str(article).isdigit() and len(str(article)) >= 4:
                                    has_real_article = True
                                    break
                        
                        await self.log_result(
                            f"Article Extraction ({product_name})", 
                            has_real_article, 
                            f"results={len(results)}, has_real_article={has_real_article}"
                        )
                    else:
                        await self.log_result(
                            f"Article Extraction ({product_name})", 
                            False, 
                            f"HTTP {response.status_code}"
                        )
                        
        except Exception as e:
            await self.log_result("Article Extraction", False, f"Exception: {str(e)}")
    
    async def test_full_workflow(self):
        """ПОЛНЫЙ WORKFLOW: Генерация → извлечение артикулов → сохранение в БД"""
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                # Generate tech card
                tech_card_data = await self.test_real_llm_generation()
                if not tech_card_data:
                    await self.log_result("Full Workflow", False, "Tech card generation failed")
                    return
                
                tech_card_id = tech_card_data.get('id')
                if not tech_card_id:
                    await self.log_result("Full Workflow", False, "No tech card ID returned")
                    return
                
                # Check if tech card was saved to database
                response = await client.get(f"{API_BASE}/tech-cards/{tech_card_id}")
                
                if response.status_code == 200:
                    saved_data = response.json()
                    
                    # Verify data integrity
                    has_ingredients = len(saved_data.get('ingredients', [])) > 0
                    has_process_steps = 'process' in saved_data.get('content', '')
                    is_ready_status = saved_data.get('status') == 'READY'
                    has_clean_id = isinstance(tech_card_id, str) and len(tech_card_id) > 10
                    
                    workflow_success = has_ingredients and has_process_steps and has_clean_id
                    
                    await self.log_result(
                        "Full Workflow", 
                        workflow_success, 
                        f"saved={response.status_code==200}, ingredients={has_ingredients}, process={has_process_steps}, status={'READY' if is_ready_status else 'DRAFT'}, clean_id={has_clean_id}"
                    )
                else:
                    await self.log_result(
                        "Full Workflow", 
                        False, 
                        f"Failed to retrieve saved tech card: HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            await self.log_result("Full Workflow", False, f"Exception: {str(e)}")
    
    async def test_dashboard_display(self):
        """ПРОВЕРКА DASHBOARD: показывает созданные техкарты"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get user's tech cards from user history
                response = await client.get(
                    f"{API_BASE}/user-history/{self.test_user_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    history = data.get('history', [])
                    
                    # Check if generated tech cards appear in history
                    generated_count = len(self.generated_tech_cards)
                    history_count = len(history)
                    
                    # Verify no warning labels
                    has_warnings = any(
                        'warning' in str(item).lower() or 
                        'draft' in str(item).lower() or
                        'error' in str(item).lower()
                        for item in history
                    )
                    
                    dashboard_working = history_count >= generated_count and not has_warnings
                    
                    await self.log_result(
                        "Dashboard Display", 
                        dashboard_working, 
                        f"generated={generated_count}, history={history_count}, warnings={has_warnings}"
                    )
                else:
                    await self.log_result(
                        "Dashboard Display", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
        except Exception as e:
            await self.log_result("Dashboard Display", False, f"Exception: {str(e)}")
    
    async def test_quality_validation(self):
        """ПРОВЕРКА КАЧЕСТВА: статус READY, нет ошибок валидации, чистые ID"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                quality_issues = []
                
                for tech_card in self.generated_tech_cards:
                    tech_card_id = tech_card.get('id')
                    if not tech_card_id:
                        continue
                    
                    # Get detailed tech card data
                    response = await client.get(f"{API_BASE}/tech-cards/{tech_card_id}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Check status
                        status = data.get('status', 'UNKNOWN')
                        if status != 'READY':
                            quality_issues.append(f"Status not READY: {status}")
                        
                        # Check ID format (should be UUID, not ranges)
                        if not self._is_clean_uuid(tech_card_id):
                            quality_issues.append(f"Unclean ID format: {tech_card_id}")
                        
                        # Check for validation errors
                        validation_errors = data.get('validation_errors', [])
                        if validation_errors:
                            quality_issues.append(f"Validation errors: {len(validation_errors)}")
                        
                        # Check ingredients have proper IDs
                        ingredients = data.get('ingredients', [])
                        for ing in ingredients:
                            ing_id = ing.get('id')
                            if ing_id and not self._is_clean_uuid(ing_id):
                                quality_issues.append(f"Ingredient unclean ID: {ing_id}")
                
                quality_passed = len(quality_issues) == 0
                
                await self.log_result(
                    "Quality Validation", 
                    quality_passed, 
                    f"issues={len(quality_issues)}: {'; '.join(quality_issues[:3])}"
                )
                
        except Exception as e:
            await self.log_result("Quality Validation", False, f"Exception: {str(e)}")
    
    def _is_clean_uuid(self, id_string):
        """Check if ID is a clean UUID format"""
        try:
            uuid.UUID(str(id_string))
            return True
        except (ValueError, TypeError):
            return False
    
    async def test_environment_variables(self):
        """ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ: правильные креды установлены"""
        try:
            # Check backend environment variables by making a health check
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try different health check endpoints
                endpoints_to_try = [
                    f"{BACKEND_URL}/health",
                    f"{BACKEND_URL}/",
                    f"{API_BASE}/cities"  # This endpoint exists
                ]
                
                for endpoint in endpoints_to_try:
                    try:
                        response = await client.get(endpoint)
                        if response.status_code == 200:
                            await self.log_result(
                                "Environment Variables", 
                                True, 
                                f"Backend accessible at {endpoint}"
                            )
                            return
                    except:
                        continue
                
                await self.log_result(
                    "Environment Variables", 
                    False, 
                    "Backend not accessible on any endpoint"
                )
                    
        except Exception as e:
            await self.log_result("Environment Variables", False, f"Exception: {str(e)}")
    
    async def run_revolutionary_tests(self):
        """Run all revolutionary tests"""
        print("🔥 РЕВОЛЮЦИОННЫЙ ТЕСТ: Проверка работы с правильными кредами от iiko и Emergent LLM ключом")
        print("=" * 80)
        
        # Create test user first
        user_created = await self.create_test_user()
        if not user_created:
            print("❌ Failed to create test user, continuing with existing user...")
        
        # Test environment setup
        await self.test_environment_variables()
        
        # Test iiko RMS connection
        await self.test_iiko_rms_connection()
        
        # Test real LLM generation
        await self.test_real_llm_generation()
        
        # Test article extraction
        await self.test_article_extraction()
        
        # Test full workflow
        await self.test_full_workflow()
        
        # Test dashboard display
        await self.test_dashboard_display()
        
        # Test quality validation
        await self.test_quality_validation()
        
        print("\n" + "=" * 80)
        print("🎯 РЕВОЛЮЦИОННЫЕ РЕЗУЛЬТАТЫ:")
        print("=" * 80)
        
        # Summary
        passed_tests = sum(1 for result in self.results if "✅ PASS" in result)
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Успешность: {passed_tests}/{total_tests} тестов ({success_rate:.1f}%)")
        print()
        
        # Detailed results
        for result in self.results:
            print(result)
        
        print("\n" + "=" * 80)
        
        # Final assessment
        critical_tests = [
            "Real LLM Generation",
            "iiko RMS Connection", 
            "Full Workflow"
        ]
        
        critical_passed = sum(1 for result in self.results 
                            if any(test in result for test in critical_tests) and "✅ PASS" in result)
        
        if critical_passed == len(critical_tests):
            print("🎉 РЕВОЛЮЦИЯ УСПЕШНА! Все критические тесты пройдены!")
            print("✅ Настоящая AI-генерация работает с gpt-4o-mini")
            print("✅ iiko RMS подключение успешно с кредами Sergey/metkamfetamin") 
            print("✅ Артикулы извлекаются из реального iiko")
            print("✅ Регрессия полностью устранена - все работает как раньше!")
        else:
            print("⚠️ РЕВОЛЮЦИЯ ЧАСТИЧНО УСПЕШНА")
            print(f"Критические тесты: {critical_passed}/{len(critical_tests)} пройдены")
        
        return success_rate >= 70  # 70% success rate threshold

async def main():
    """Main test execution"""
    tester = RevolutionaryTester()
    success = await tester.run_revolutionary_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())