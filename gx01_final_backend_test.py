#!/usr/bin/env python3
"""
GX-01-FINAL COMPREHENSIVE TESTING - ПРИЁМОЧНЫЕ КРИТЕРИИ

Детальное тестирование финальной версии стабилизированной генерации с проверкой всех приёмочных критериев:

1. КОНТРАКТ ОТВЕТА СТАБИЛЕН
2. ПРОИЗВОДИТЕЛЬНОСТЬ  
3. NORMALIZE-FALLBACK
4. SKELETON-FALLBACK (симуляция LLM timeout)
5. VALIDATION ERROR CHECKS
6. SANITIZE PURITY

Testing methodology:
- Проверяем каждое блюдо отдельно
- Измеряем время каждого запроса  
- Анализируем структуру responses
- Тестируем edge cases и fallback scenarios
- Проверяем логи на отсутствие errors
"""

import requests
import json
import time
import os
import sys
from typing import Dict, List, Any
import statistics

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

class GX01FinalTester:
    def __init__(self):
        self.results = []
        self.timings = []
        self.errors = []
        
    def log(self, message: str, level: str = "INFO"):
        """Логирование с временной меткой"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_dish_generation(self, dish_name: str) -> Dict[str, Any]:
        """Тестирует генерацию одного блюда с полным анализом"""
        self.log(f"🍽️ Testing dish: {dish_name}")
        
        start_time = time.time()
        
        try:
            # Отправляем запрос на генерацию
            payload = {
                "name": dish_name,
                "cuisine": "международная",
                "equipment": [],
                "budget": None,
                "dietary": []
            }
            
            response = requests.post(
                f"{API_BASE}/techcards.v2/generate",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60  # 60 секунд timeout
            )
            
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            # Анализируем ответ
            result = {
                "dish": dish_name,
                "duration_ms": duration_ms,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "success": False,
                "issues": []
            }
            
            if response.status_code != 200:
                result["issues"].append(f"HTTP {response.status_code}: {response.text[:200]}")
                return result
                
            # Проверяем Content-Type
            if "application/json" not in result["content_type"]:
                result["issues"].append(f"Wrong Content-Type: {result['content_type']}")
                return result
                
            # Парсим JSON
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                result["issues"].append(f"JSON decode error: {e}")
                return result
                
            result["response_data"] = data
            
            # GX-01-FINAL: Проверяем контракт ответа
            contract_issues = self._validate_response_contract(data)
            result["issues"].extend(contract_issues)
            
            # GX-01-FINAL: Проверяем timings в meta
            timings_issues = self._validate_timings(data)
            result["issues"].extend(timings_issues)
            
            # GX-01-FINAL: Проверяем поля nutrition/cost
            fields_issues = self._validate_required_fields(data)
            result["issues"].extend(fields_issues)
            
            # GX-01-FINAL: Проверяем статус (только success/draft)
            status_issues = self._validate_status(data)
            result["issues"].extend(status_issues)
            
            result["success"] = len(result["issues"]) == 0
            self.timings.append(duration_ms)
            
            if result["success"]:
                self.log(f"✅ {dish_name}: {duration_ms}ms - SUCCESS")
            else:
                self.log(f"❌ {dish_name}: {duration_ms}ms - FAILED: {'; '.join(result['issues'])}")
                
            return result
            
        except requests.exceptions.Timeout:
            result = {
                "dish": dish_name,
                "duration_ms": 60000,  # timeout
                "success": False,
                "issues": ["Request timeout (60s)"]
            }
            self.log(f"⏰ {dish_name}: TIMEOUT")
            return result
            
        except Exception as e:
            result = {
                "dish": dish_name,
                "duration_ms": int((time.time() - start_time) * 1000),
                "success": False,
                "issues": [f"Exception: {str(e)}"]
            }
            self.log(f"💥 {dish_name}: EXCEPTION: {e}")
            return result
    
    def _validate_response_contract(self, data: Dict[str, Any]) -> List[str]:
        """GX-01-FINAL: Проверяем стабильность контракта ответа"""
        issues = []
        
        # Обязательные поля верхнего уровня
        required_fields = ["status", "card", "issues"]
        for field in required_fields:
            if field not in data:
                issues.append(f"Missing required field: {field}")
                
        return issues
    
    def _validate_timings(self, data: Dict[str, Any]) -> List[str]:
        """GX-01-FINAL: Проверяем наличие всех timings в meta"""
        issues = []
        
        if "card" not in data or not data["card"]:
            return ["No card in response"]
            
        card = data["card"]
        if "meta" not in card:
            return ["No meta in card"]
            
        meta = card["meta"]
        if "timings" not in meta:
            issues.append("Missing meta.timings field")
            return issues
            
        timings = meta["timings"]
        
        # GX-01-FINAL: Обязательные timing ключи
        required_timings = [
            "llm_draft_ms", "llm_normalize_ms", "validate_ms", 
            "chef_rules_ms", "contentcheck_ms", "cost_ms", 
            "nutrition_ms", "sanitize_ms", "total_ms"
        ]
        
        for timing_key in required_timings:
            if timing_key not in timings:
                issues.append(f"Missing timing: {timing_key}")
            elif not isinstance(timings[timing_key], (int, float)):
                issues.append(f"Invalid timing type for {timing_key}: {type(timings[timing_key])}")
                
        return issues
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> List[str]:
        """GX-01-FINAL: Проверяем что nutrition/cost всегда объекты (не null)"""
        issues = []
        
        if "card" not in data or not data["card"]:
            return ["No card in response"]
            
        card = data["card"]
        
        # nutrition должно быть объектом
        if "nutrition" not in card:
            issues.append("Missing nutrition field")
        elif card["nutrition"] is None:
            issues.append("nutrition field is null (must be object)")
        elif not isinstance(card["nutrition"], dict):
            issues.append(f"nutrition must be object, got {type(card['nutrition'])}")
            
        # cost должно быть объектом
        if "cost" not in card:
            issues.append("Missing cost field")
        elif card["cost"] is None:
            issues.append("cost field is null (must be object)")
        elif not isinstance(card["cost"], dict):
            issues.append(f"cost must be object, got {type(card['cost'])}")
            
        return issues
    
    def _validate_status(self, data: Dict[str, Any]) -> List[str]:
        """GX-01-FINAL: Проверяем что статус только success/draft, никогда failed"""
        issues = []
        
        status = data.get("status")
        if status not in ["success", "draft"]:
            issues.append(f"Invalid status: {status} (must be 'success' or 'draft')")
            
        return issues
    
    def test_performance_metrics(self):
        """GX-01-FINAL: Анализируем производительность"""
        self.log("📊 Analyzing performance metrics...")
        
        if not self.timings:
            self.log("❌ No timing data available")
            return
            
        # Вычисляем метрики
        p50 = statistics.median(self.timings)
        p95 = statistics.quantiles(self.timings, n=20)[18] if len(self.timings) >= 20 else max(self.timings)
        avg = statistics.mean(self.timings)
        
        self.log(f"⏱️ Performance metrics:")
        self.log(f"   Average: {avg:.0f}ms")
        self.log(f"   p50: {p50:.0f}ms (target: ≤20000ms)")
        self.log(f"   p95: {p95:.0f}ms (target: ≤30000ms)")
        
        # GX-01-FINAL: Проверяем соответствие целям
        performance_ok = True
        if p50 > 20000:
            self.log(f"⚠️ p50 exceeds target: {p50:.0f}ms > 20000ms")
            performance_ok = False
        if p95 > 30000:
            self.log(f"⚠️ p95 exceeds target: {p95:.0f}ms > 30000ms")
            performance_ok = False
            
        if performance_ok:
            self.log("✅ Performance targets met")
        else:
            self.log("❌ Performance targets not met")
            
        return {
            "avg_ms": avg,
            "p50_ms": p50,
            "p95_ms": p95,
            "p50_target_met": p50 <= 20000,
            "p95_target_met": p95 <= 30000
        }
    
    def test_normalize_fallback(self):
        """GX-01-FINAL: Тестируем normalize-fallback с проблемным названием"""
        self.log("🔄 Testing normalize-fallback mechanism...")
        
        # Проблемное название блюда
        problematic_dish = "Абракадабра блюдо 123 с несуществующими ингредиентами"
        
        result = self.test_dish_generation(problematic_dish)
        
        # Анализируем результат
        if not result["success"]:
            self.log(f"❌ Normalize-fallback test failed: {result['issues']}")
            return False
            
        # Проверяем что вернулся draft статус
        response_data = result.get("response_data", {})
        status = response_data.get("status")
        
        if status == "draft":
            self.log("✅ Normalize-fallback working: returned draft status")
            
            # Проверяем что калькуляторы работают
            card = response_data.get("card", {})
            if card.get("nutrition") and card.get("cost"):
                self.log("✅ Calculators working in fallback mode")
                return True
            else:
                self.log("❌ Calculators not working in fallback mode")
                return False
        else:
            self.log(f"❌ Expected draft status, got: {status}")
            return False
    
    def test_skeleton_fallback(self):
        """GX-01-FINAL: Тестируем skeleton-fallback (симуляция LLM timeout)"""
        self.log("🦴 Testing skeleton-fallback mechanism...")
        
        # Сохраняем оригинальный API key
        original_key = os.environ.get('OPENAI_API_KEY')
        
        try:
            # Временно отключаем LLM
            if original_key:
                os.environ['OPENAI_API_KEY_DISABLED'] = original_key
                del os.environ['OPENAI_API_KEY']
                self.log("🔌 Temporarily disabled OPENAI_API_KEY")
            
            # Тестируем генерацию без LLM
            test_dish = "Тестовое блюдо"
            result = self.test_dish_generation(test_dish)
            
            # Восстанавливаем API key
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key
                if 'OPENAI_API_KEY_DISABLED' in os.environ:
                    del os.environ['OPENAI_API_KEY_DISABLED']
                self.log("🔌 Restored OPENAI_API_KEY")
            
            # Анализируем результат
            if not result["success"]:
                self.log(f"❌ Skeleton-fallback test failed: {result['issues']}")
                return False
                
            response_data = result.get("response_data", {})
            status = response_data.get("status")
            
            if status == "draft":
                self.log("✅ Skeleton-fallback working: returned draft status")
                
                # Проверяем что есть issue о недоступности LLM или другие fallback индикаторы
                issues = response_data.get("issues", [])
                card = response_data.get("card", {})
                
                # Ищем признаки fallback режима
                llm_issue_found = any("LLM" in str(issue) or "disabled" in str(issue) or "fallback" in str(issue).lower() for issue in issues)
                
                # Также проверяем что техкарта имеет признаки skeleton/fallback
                ingredients = card.get("ingredients", [])
                is_skeleton = len(ingredients) <= 3  # Skeleton обычно имеет минимальные ингредиенты
                
                if llm_issue_found or is_skeleton:
                    self.log("✅ Skeleton-fallback mechanism working (draft status + minimal structure)")
                    return True
                else:
                    self.log(f"❌ Skeleton-fallback not clearly indicated. Issues: {issues[:2]}")
                    return False
            else:
                self.log(f"❌ Expected draft status, got: {status}")
                return False
                
        except Exception as e:
            # Восстанавливаем API key в случае ошибки
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key
                if 'OPENAI_API_KEY_DISABLED' in os.environ:
                    del os.environ['OPENAI_API_KEY_DISABLED']
            self.log(f"💥 Skeleton-fallback test exception: {e}")
            return False
    
    def test_validation_errors(self):
        """GX-01-FINAL: Проверяем отсутствие validation errors"""
        self.log("🔍 Checking for validation errors in results...")
        
        validation_errors = []
        
        for result in self.results:
            response_data = result.get("response_data", {})
            issues = response_data.get("issues", [])
            
            # Ищем специфические validation errors
            for issue in issues:
                issue_str = str(issue)
                if "object has no field" in issue_str:
                    validation_errors.append(f"{result['dish']}: {issue_str}")
                elif "Input should be a valid dictionary" in issue_str:
                    validation_errors.append(f"{result['dish']}: {issue_str}")
                elif "Field nutrition:" in issue_str and "dictionary" in issue_str:
                    validation_errors.append(f"{result['dish']}: {issue_str}")
                elif "Field cost:" in issue_str and "dictionary" in issue_str:
                    validation_errors.append(f"{result['dish']}: {issue_str}")
        
        if validation_errors:
            self.log("❌ Validation errors found:")
            for error in validation_errors:
                self.log(f"   {error}")
            return False
        else:
            self.log("✅ No validation errors found")
            return True
    
    def test_sanitize_purity(self):
        """GX-01-FINAL: Проверяем что sanitize не ломает структуру техкарт"""
        self.log("🧹 Testing sanitize purity...")
        
        # Проверяем что все успешные техкарты прошли полный цикл без validation errors
        successful_cards = [r for r in self.results if r["success"]]
        
        if not successful_cards:
            self.log("❌ No successful cards to test sanitize purity")
            return False
            
        sanitize_issues = []
        
        for result in successful_cards:
            response_data = result.get("response_data", {})
            card = response_data.get("card", {})
            
            # Проверяем основные поля после sanitize
            required_fields = ["meta", "portions", "yield", "ingredients", "process", "storage", "nutrition", "cost"]
            for field in required_fields:
                if field not in card:
                    sanitize_issues.append(f"{result['dish']}: Missing field after sanitize: {field}")
                    
            # Проверяем что meta.timings присутствует
            if "meta" in card and "timings" not in card["meta"]:
                sanitize_issues.append(f"{result['dish']}: Missing meta.timings after sanitize")
        
        if sanitize_issues:
            self.log("❌ Sanitize purity issues found:")
            for issue in sanitize_issues:
                self.log(f"   {issue}")
            return False
        else:
            self.log("✅ Sanitize purity verified - no structure damage")
            return True
    
    def run_comprehensive_test(self):
        """Запускает полное тестирование GX-01-FINAL"""
        self.log("🚀 Starting GX-01-FINAL comprehensive testing...")
        
        # 1. КОНТРАКТ ОТВЕТА СТАБИЛЕН - тестируем разные блюда как указано в review
        test_dishes = [
            "Борщ украинский",
            "Цезарь салат", 
            "Карбонара паста"
        ]
        
        self.log("1️⃣ Testing response contract stability...")
        for dish in test_dishes:
            result = self.test_dish_generation(dish)
            self.results.append(result)
        
        # 2. ПРОИЗВОДИТЕЛЬНОСТЬ
        self.log("2️⃣ Testing performance metrics...")
        performance_result = self.test_performance_metrics()
        
        # 3. NORMALIZE-FALLBACK
        self.log("3️⃣ Testing normalize-fallback...")
        normalize_ok = self.test_normalize_fallback()
        
        # 4. SKELETON-FALLBACK
        self.log("4️⃣ Testing skeleton-fallback...")
        skeleton_ok = self.test_skeleton_fallback()
        
        # 5. VALIDATION ERROR CHECKS
        self.log("5️⃣ Testing validation errors...")
        validation_ok = self.test_validation_errors()
        
        # 6. SANITIZE PURITY
        self.log("6️⃣ Testing sanitize purity...")
        sanitize_ok = self.test_sanitize_purity()
        
        # 7. ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ ИЗ REVIEW REQUEST
        self.log("7️⃣ Additional acceptance criteria checks...")
        additional_ok = self.test_additional_criteria()
        
        # Итоговый отчет
        self.log("📋 GX-01-FINAL TEST SUMMARY:")
        self.log("=" * 50)
        
        successful_dishes = sum(1 for r in self.results if r["success"])
        total_dishes = len(self.results)
        
        self.log(f"✅ Successful dish generations: {successful_dishes}/{total_dishes}")
        
        if performance_result:
            p50_ok = performance_result["p50_target_met"]
            p95_ok = performance_result["p95_target_met"]
            self.log(f"⏱️ Performance p50: {'✅' if p50_ok else '❌'} ({performance_result['p50_ms']:.0f}ms)")
            self.log(f"⏱️ Performance p95: {'✅' if p95_ok else '❌'} ({performance_result['p95_ms']:.0f}ms)")
        
        self.log(f"🔄 Normalize-fallback: {'✅' if normalize_ok else '❌'}")
        self.log(f"🦴 Skeleton-fallback: {'✅' if skeleton_ok else '❌'}")
        self.log(f"🔍 Validation errors: {'✅' if validation_ok else '❌'}")
        self.log(f"🧹 Sanitize purity: {'✅' if sanitize_ok else '❌'}")
        self.log(f"📋 Additional criteria: {'✅' if additional_ok else '❌'}")
        
        # Общий результат
        all_tests_passed = (
            successful_dishes == total_dishes and
            (not performance_result or (performance_result["p50_target_met"] and performance_result["p95_target_met"])) and
            normalize_ok and
            skeleton_ok and
            validation_ok and
            sanitize_ok and
            additional_ok
        )
        
        if all_tests_passed:
            self.log("🎉 ALL GX-01-FINAL ACCEPTANCE CRITERIA PASSED!")
            return True
        else:
            self.log("❌ Some GX-01-FINAL acceptance criteria failed")
            return False
    
    def test_additional_criteria(self):
        """Дополнительные проверки из review request"""
        self.log("📋 Testing additional acceptance criteria...")
        
        issues_found = []
        
        # Проверяем что все responses имеют правильный Content-Type
        for result in self.results:
            content_type = result.get("content_type", "")
            if "application/json; charset=utf-8" not in content_type:
                issues_found.append(f"{result['dish']}: Wrong Content-Type: {content_type}")
        
        # Проверяем что все timings в разумных пределах
        for result in self.results:
            if result["success"]:
                response_data = result.get("response_data", {})
                card = response_data.get("card", {})
                timings = card.get("meta", {}).get("timings", {})
                
                # Проверяем что total_ms соответствует измеренному времени
                total_ms = timings.get("total_ms", 0)
                measured_ms = result.get("duration_ms", 0)
                
                # Допускаем разницу до 1000ms (сетевые задержки)
                if abs(total_ms - measured_ms) > 1000:
                    issues_found.append(f"{result['dish']}: Timing mismatch: total_ms={total_ms}, measured={measured_ms}")
        
        # Проверяем что статус никогда не "failed"
        for result in self.results:
            response_data = result.get("response_data", {})
            status = response_data.get("status")
            if status == "failed":
                issues_found.append(f"{result['dish']}: Status is 'failed' (should be 'success' or 'draft')")
        
        if issues_found:
            self.log("❌ Additional criteria issues:")
            for issue in issues_found:
                self.log(f"   {issue}")
            return False
        else:
            self.log("✅ All additional criteria passed")
            return True

def main():
    """Основная функция тестирования"""
    print("GX-01-FINAL COMPREHENSIVE TESTING")
    print("=" * 50)
    
    tester = GX01FinalTester()
    success = tester.run_comprehensive_test()
    
    # Возвращаем код выхода
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()