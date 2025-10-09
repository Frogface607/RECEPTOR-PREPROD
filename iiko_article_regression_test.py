#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import uuid
import time

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class IikoArticleRegressionTester:
    def __init__(self):
        self.test_user_id = f"iiko_regression_test_{str(uuid.uuid4())[:8]}"
        self.results = []
        self.generated_tech_cards = []
        self.iiko_connection_status = None
        
    async def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.results.append(result)
        print(result)
        
    async def test_iiko_connection_status(self):
        """Test 1: Check iiko RMS connection status"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check health endpoint for iiko status
                response = await client.get(f"{API_BASE}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    
                    # Look for iiko connection info
                    iiko_status = health_data.get('iiko_connection', {})
                    if iiko_status:
                        self.iiko_connection_status = iiko_status
                        await self.log_result(
                            "IIKo Connection Status", 
                            True, 
                            f"Connection status: {iiko_status.get('status', 'unknown')}, Organization: {iiko_status.get('organization', 'N/A')}"
                        )
                        return True
                    else:
                        await self.log_result(
                            "IIKo Connection Status", 
                            False, 
                            "No iiko connection info in health endpoint"
                        )
                        return False
                else:
                    await self.log_result(
                        "IIKo Connection Status", 
                        False, 
                        f"Health endpoint failed: {response.status_code}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "IIKo Connection Status", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_rms_product_debug_endpoint(self):
        """Test 2: Test GET /api/v1/techcards.v2/debug/rms-product"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test with a sample product search
                test_product = "картофель"
                response = await client.get(f"{API_BASE}/v1/techcards.v2/debug/rms-product", params={
                    "product_name": test_product
                })
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if we get expected fields
                    expected_fields = ['sku_id', 'product_in_products', 'product_in_prices', 'extracted_article']
                    has_fields = all(field in data for field in expected_fields)
                    
                    if has_fields:
                        extracted_article = data.get('extracted_article')
                        await self.log_result(
                            "RMS Product Debug Endpoint", 
                            True, 
                            f"Endpoint accessible, extracted_article: {extracted_article}"
                        )
                        return data
                    else:
                        await self.log_result(
                            "RMS Product Debug Endpoint", 
                            False, 
                            f"Missing expected fields. Got: {list(data.keys())}"
                        )
                        return None
                else:
                    await self.log_result(
                        "RMS Product Debug Endpoint", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result(
                "RMS Product Debug Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
            return None
    
    async def test_tech_card_generation_with_articles(self):
        """Test 3: Generate a simple tech card and check for article extraction"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Generate a simple tech card
                dish_name = "Омлет"
                generation_request = {
                    "dish_name": dish_name,
                    "user_id": self.test_user_id,
                    "venue_type": "restaurant",
                    "cuisine_type": "european"
                }
                
                print(f"🔄 Generating tech card for '{dish_name}'...")
                response = await client.post(f"{API_BASE}/v1/techcards.v2/generate", json=generation_request)
                
                if response.status_code == 200:
                    data = response.json()
                    tech_card_id = data.get('id')
                    
                    if tech_card_id:
                        self.generated_tech_cards.append(tech_card_id)
                        
                        # Check the generated tech card for articles
                        dish_article = data.get('article')
                        ingredients = data.get('ingredients', [])
                        
                        # Count ingredients with and without product_code
                        ingredients_with_code = sum(1 for ing in ingredients if ing.get('product_code'))
                        ingredients_without_code = len(ingredients) - ingredients_with_code
                        
                        # Check if this is the regression issue
                        has_regression = dish_article is None and ingredients_without_code == len(ingredients)
                        
                        if has_regression:
                            await self.log_result(
                                "Tech Card Article Generation", 
                                False, 
                                f"REGRESSION CONFIRMED: dish.article={dish_article}, {ingredients_without_code}/{len(ingredients)} ingredients have product_code=null"
                            )
                        else:
                            await self.log_result(
                                "Tech Card Article Generation", 
                                True, 
                                f"Articles working: dish.article={dish_article}, {ingredients_with_code}/{len(ingredients)} ingredients have product_code"
                            )
                        
                        return {
                            'tech_card_id': tech_card_id,
                            'dish_article': dish_article,
                            'ingredients_count': len(ingredients),
                            'ingredients_with_code': ingredients_with_code,
                            'has_regression': has_regression,
                            'full_data': data
                        }
                    else:
                        await self.log_result(
                            "Tech Card Article Generation", 
                            False, 
                            "No tech card ID returned"
                        )
                        return None
                else:
                    await self.log_result(
                        "Tech Card Article Generation", 
                        False, 
                        f"Generation failed: HTTP {response.status_code}: {response.text[:200]}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result(
                "Tech Card Article Generation", 
                False, 
                f"Exception: {str(e)}"
            )
            return None
    
    async def test_article_generation_pipeline(self):
        """Test 4: Check if article generation is called in the pipeline"""
        try:
            # This test will analyze the tech card generation response for timing metadata
            # that indicates whether article generation logic was executed
            
            tech_card_result = await self.test_tech_card_generation_with_articles()
            
            if tech_card_result and tech_card_result.get('full_data'):
                data = tech_card_result['full_data']
                
                # Look for timing metadata that indicates article generation was attempted
                timing_meta = data.get('meta', {})
                article_generation_time = timing_meta.get('article_generation_ms')
                
                if article_generation_time is not None:
                    await self.log_result(
                        "Article Generation Pipeline", 
                        True, 
                        f"Article generation code executed (took {article_generation_time}ms)"
                    )
                    
                    # But check if it actually populated the fields
                    if tech_card_result.get('has_regression'):
                        await self.log_result(
                            "Article Generation Logic", 
                            False, 
                            f"Article generation runs but doesn't populate fields (timing: {article_generation_time}ms)"
                        )
                    else:
                        await self.log_result(
                            "Article Generation Logic", 
                            True, 
                            f"Article generation working correctly (timing: {article_generation_time}ms)"
                        )
                    
                    return True
                else:
                    await self.log_result(
                        "Article Generation Pipeline", 
                        False, 
                        "No article_generation_ms timing found in response metadata"
                    )
                    return False
            else:
                await self.log_result(
                    "Article Generation Pipeline", 
                    False, 
                    "Could not analyze pipeline - no tech card data"
                )
                return False
                
        except Exception as e:
            await self.log_result(
                "Article Generation Pipeline", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_export_workflow_with_articles(self):
        """Test 5: Test export workflow to see if it handles missing articles"""
        try:
            if not self.generated_tech_cards:
                await self.log_result(
                    "Export Workflow Test", 
                    False, 
                    "No tech cards available for export testing"
                )
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to export the generated tech card
                tech_card_id = self.generated_tech_cards[0]
                
                response = await client.post(f"{API_BASE}/v1/techcards.v2/export/enhanced/iiko.xlsx", json={
                    "techcard_ids": [tech_card_id],
                    "operational_rounding": True
                })
                
                if response.status_code == 200:
                    # Check if we got an Excel file
                    content_type = response.headers.get('content-type', '')
                    if 'spreadsheet' in content_type or 'excel' in content_type:
                        await self.log_result(
                            "Export Workflow Test", 
                            True, 
                            f"Export successful despite missing articles (content-type: {content_type})"
                        )
                        return True
                    else:
                        await self.log_result(
                            "Export Workflow Test", 
                            False, 
                            f"Export returned non-Excel content: {content_type}"
                        )
                        return False
                elif response.status_code == 422:
                    # Validation error - might be due to missing articles
                    error_data = response.json()
                    await self.log_result(
                        "Export Workflow Test", 
                        False, 
                        f"Export blocked by validation: {error_data.get('detail', 'Unknown error')}"
                    )
                    return False
                else:
                    await self.log_result(
                        "Export Workflow Test", 
                        False, 
                        f"Export failed: HTTP {response.status_code}: {response.text[:200]}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Export Workflow Test", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_configuration_analysis(self):
        """Test 6: Analyze configuration for iiko integration"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check if there are any configuration endpoints
                response = await client.get(f"{API_BASE}/config")
                
                if response.status_code == 200:
                    config_data = response.json()
                    
                    # Look for iiko-related configuration
                    iiko_config = {}
                    for key, value in config_data.items():
                        if 'iiko' in key.lower():
                            iiko_config[key] = value
                    
                    if iiko_config:
                        await self.log_result(
                            "Configuration Analysis", 
                            True, 
                            f"Found iiko configuration: {list(iiko_config.keys())}"
                        )
                        return iiko_config
                    else:
                        await self.log_result(
                            "Configuration Analysis", 
                            False, 
                            "No iiko configuration found in /api/config"
                        )
                        return None
                else:
                    await self.log_result(
                        "Configuration Analysis", 
                        False, 
                        f"Config endpoint not accessible: HTTP {response.status_code}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_result(
                "Configuration Analysis", 
                False, 
                f"Exception: {str(e)}"
            )
            return None
    
    async def run_comprehensive_diagnosis(self):
        """Run all diagnostic tests"""
        print("🚨 URGENT REGRESSION DIAGNOSIS: Критический анализ проблемы с извлечением артикулов из iiko")
        print("=" * 80)
        
        # Test 1: IIKo Connection
        print("\n1. ТЕСТ ПОДКЛЮЧЕНИЯ К IIKO:")
        await self.test_iiko_connection_status()
        
        # Test 2: RMS Product Debug
        print("\n2. ТЕСТ ИЗВЛЕЧЕНИЯ АРТИКУЛОВ:")
        rms_result = await self.test_rms_product_debug_endpoint()
        
        # Test 3: Tech Card Generation
        print("\n3. ТЕСТ ГЕНЕРАЦИИ ТЕХКАРТЫ:")
        generation_result = await self.test_tech_card_generation_with_articles()
        
        # Test 4: Pipeline Analysis
        print("\n4. ДИАГНОСТИКА PIPELINE:")
        await self.test_article_generation_pipeline()
        
        # Test 5: Export Workflow
        print("\n5. ТЕСТ ЭКСПОРТА:")
        await self.test_export_workflow_with_articles()
        
        # Test 6: Configuration
        print("\n6. АНАЛИЗ КОНФИГУРАЦИИ:")
        config_result = await self.test_configuration_analysis()
        
        # Summary
        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.results if "✅ PASS" in result)
        total_tests = len(self.results)
        
        print(f"Пройдено тестов: {passed_tests}/{total_tests}")
        print("\nДетальные результаты:")
        for result in self.results:
            print(f"  {result}")
        
        # Root cause analysis
        print("\n" + "=" * 80)
        print("АНАЛИЗ ПЕРВОПРИЧИНЫ:")
        print("=" * 80)
        
        if generation_result and generation_result.get('has_regression'):
            print("🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА:")
            print(f"  - Блюдо: article = {generation_result.get('dish_article')}")
            print(f"  - Ингредиенты: {generation_result.get('ingredients_with_code')}/{generation_result.get('ingredients_count')} имеют product_code")
            print("  - Это точно соответствует описанной регрессии!")
            
            if rms_result:
                print(f"\n🔍 RMS DEBUG ENDPOINT:")
                print(f"  - Доступен: ✅")
                print(f"  - Извлекает артикулы: {rms_result.get('extracted_article', 'N/A')}")
            
            print(f"\n📊 СТАТУС ПОДКЛЮЧЕНИЯ IIKO:")
            if self.iiko_connection_status:
                print(f"  - Статус: {self.iiko_connection_status.get('status', 'unknown')}")
                print(f"  - Организация: {self.iiko_connection_status.get('organization', 'N/A')}")
            else:
                print("  - Информация недоступна")
                
        else:
            print("✅ Регрессия не обнаружена или тесты не завершились")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'has_regression': generation_result.get('has_regression', False) if generation_result else False,
            'iiko_connection': self.iiko_connection_status,
            'rms_debug_result': rms_result,
            'generation_result': generation_result,
            'config_result': config_result,
            'all_results': self.results
        }

async def main():
    """Main test execution"""
    tester = IikoArticleRegressionTester()
    
    try:
        diagnosis_result = await tester.run_comprehensive_diagnosis()
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"/app/iiko_article_regression_diagnosis_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(diagnosis_result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Результаты сохранены в: {results_file}")
        
        # Return exit code based on results
        if diagnosis_result['has_regression']:
            print("\n🚨 КРИТИЧЕСКАЯ РЕГРЕССИЯ ОБНАРУЖЕНА!")
            return 1
        else:
            print("\n✅ Регрессия не обнаружена")
            return 0
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка диагностики: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)