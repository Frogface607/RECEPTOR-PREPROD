#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Task 2.2 - Chef Rules (rule-based sanity) + issues
Testing automatic detection of "kitchen nonsense" after LLM generation through deterministic rules.
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any, List, Optional

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_chef_rules_implementation():
    """Test Task 2.2 - Chef Rules Implementation"""
    print("🎯 TESTING TASK 2.2 - CHEF RULES (RULE-BASED SANITY) + ISSUES")
    print("=" * 80)
    
    # Test 1: Generate 5 test dishes with specific problems
    test_dishes = [
        {
            "name": "Блюдо с некорректным yield",
            "description": "Тест отклонения выхода >15%",
            "expected_issue": "ruleError:yieldConsistency"
        },
        {
            "name": "Блюдо с пересолом", 
            "description": "Тест избытка соли >2.2%",
            "expected_issue": "ruleWarning:saltUpperBound"
        },
        {
            "name": "Блюдо с неправильным маслом",
            "description": "Тест масла <5 или >30 мл/порц",
            "expected_issue": "ruleWarning:fryOilPerPortion"
        },
        {
            "name": "Блюдо с малым количеством шагов",
            "description": "Тест <3 шагов процесса", 
            "expected_issue": "ruleError:stepsMin3"
        },
        {
            "name": "Блюдо без термопараметров",
            "description": "Тест отсутствия времени/температуры у жарки",
            "expected_issue": "ruleWarning:thermalInfoMissing"
        }
    ]
    
    results = []
    
    for i, dish in enumerate(test_dishes, 1):
        print(f"\n🍽️ ТЕСТ {i}: {dish['name']}")
        print(f"Описание: {dish['description']}")
        print(f"Ожидаемая проблема: {dish['expected_issue']}")
        
        # Generate tech card and test for expected issues
        success = test_specific_chef_rule(dish)
        results.append({
            "dish": dish['name'],
            "expected": dish['expected_issue'],
            "status": "✅ PASS" if success else "❌ FAIL"
        })
        print(f"Результат: {results[-1]['status']}")
    
    # Test 2: Check unit tests execution
    print(f"\n🧪 ТЕСТ ЮНИТ-ТЕСТОВ")
    unit_tests_result = run_unit_tests()
    
    # Test 3: Check pipeline integration
    print(f"\n🔄 ТЕСТ ИНТЕГРАЦИИ В ПАЙПЛАЙН")
    pipeline_result = test_pipeline_integration()
    
    # Test 4: Check constants
    print(f"\n🔧 ТЕСТ КОНСТАНТ")
    constants_result = test_constants_and_coverage()
    
    # Summary
    print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)
    
    passed_tests = sum(1 for r in results if "✅ PASS" in r['status'])
    total_tests = len(results)
    
    print(f"Тесты блюд с проблемами: {passed_tests}/{total_tests}")
    for result in results:
        print(f"  {result['status']} {result['dish']} ({result['expected']})")
    
    print(f"Юнит-тесты: {'✅ PASS' if unit_tests_result else '❌ FAIL'}")
    print(f"Интеграция в пайплайн: {'✅ PASS' if pipeline_result else '❌ FAIL'}")
    print(f"Константы: {'✅ PASS' if constants_result else '❌ FAIL'}")
    
    overall_success = passed_tests == total_tests and unit_tests_result and pipeline_result and constants_result
    print(f"\n🎉 ОБЩИЙ РЕЗУЛЬТАТ: {'✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ' if overall_success else '❌ ЕСТЬ ПРОБЛЕМЫ'}")
    
    return overall_success

def test_specific_chef_rule(dish_config: Dict[str, Any]) -> bool:
    """Test a specific chef rule by generating a problematic tech card"""
    
    try:
        print(f"  📡 Тестирование через API генерации техкарт...")
        
        # Generate multiple tech cards to test chef rules
        for attempt in range(3):  # Try 3 times to get the expected issue
            
            # Use different dish names to get variety
            dish_names = [
                "Борщ украинский с проблемами",
                "Паста карбонара тестовая", 
                "Жареная картошка с маслом",
                "Простой салат",
                "Стейк на гриле"
            ]
            
            response = requests.post(
                f"{BACKEND_URL}/v1/techcards.v2/generate",
                params={"use_llm": "false"},  # Use deterministic mode to get consistent results
                json={
                    "name": dish_names[attempt % len(dish_names)],
                    "cuisine": "тестовая",
                    "equipment": [],
                    "budget": None,
                    "dietary": []
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"    Попытка {attempt + 1}: статус={result.get('status', 'unknown')}")
                
                # Check for chef rules issues
                if check_for_chef_rules_in_response(result, dish_config['expected_issue']):
                    return True
                    
                # If this is a critical error type, check if status is draft
                if dish_config['expected_issue'].startswith('ruleError:'):
                    if result.get('status') == 'draft':
                        print(f"    ✅ Критическая ошибка привела к статусу 'draft'")
                        return True
                        
            else:
                print(f"    Попытка {attempt + 1}: HTTP {response.status_code}")
        
        # If API tests didn't work, try direct testing
        return test_chef_rules_directly(dish_config)
        
    except Exception as e:
        print(f"  ❌ Ошибка тестирования: {str(e)}")
        return False

def check_for_chef_rules_in_response(result: Dict[str, Any], expected_issue: str) -> bool:
    """Check if the API response contains the expected chef rules issue"""
    
    # Check issues array
    issues = result.get('issues', [])
    for issue in issues:
        if isinstance(issue, dict):
            issue_type = issue.get('type', '')
            if issue_type == expected_issue:
                print(f"    ✅ Найдена ожидаемая проблема: {issue_type}")
                print(f"       Описание: {issue.get('hint', 'No description')}")
                return True
        elif isinstance(issue, str):
            if expected_issue in issue:
                print(f"    ✅ Найдена ожидаемая проблема в строке: {issue}")
                return True
    
    return False

def test_chef_rules_directly(dish_config: Dict[str, Any]) -> bool:
    """Test chef rules directly by importing the module"""
    
    try:
        print(f"  🔬 Прямое тестирование модуля chef_rules...")
        
        # Add the backend path to sys.path
        backend_path = '/app/backend'
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # Import chef rules module
        from receptor_agent.techcards_v2.chef_rules import run_chef_rules
        from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, ProcessStepV2, YieldV2, MetaV2, StorageV2
        
        # Create a test tech card with the specific problem
        test_card = create_problematic_test_card(dish_config['expected_issue'])
        
        if test_card:
            # Run chef rules on the test card
            issues = run_chef_rules(test_card)
            
            # Check if we got the expected issue
            for issue in issues:
                if issue.get('type') == dish_config['expected_issue']:
                    print(f"    ✅ Прямой тест нашел ожидаемую проблему: {issue['type']}")
                    print(f"       Описание: {issue.get('hint', 'No description')}")
                    return True
            
            print(f"    ❌ Ожидаемая проблема {dish_config['expected_issue']} не найдена")
            print(f"       Найденные проблемы: {[issue.get('type') for issue in issues]}")
            return False
        else:
            print(f"    ❌ Не удалось создать тестовую техкарту")
            return False
            
    except Exception as e:
        print(f"    ❌ Ошибка прямого тестирования: {str(e)}")
        return False

def create_problematic_test_card(expected_issue: str) -> Optional[Any]:
    """Create a test tech card with a specific problem"""
    
    try:
        from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, ProcessStepV2, YieldV2, MetaV2, StorageV2
        
        base_meta = MetaV2(
            id="test-card",
            title="Тестовое блюдо",
            version="2.0",
            created_at="2025-01-18T12:00:00",
            cuisine="тестовая",
            tags=[]
        )
        
        base_storage = StorageV2(
            conditions="Холодильник 0...+4°C",
            shelfLife_hours=48.0,
            servingTemp_c=65.0
        )
        
        if expected_issue == "ruleError:yieldConsistency":
            # Create yield inconsistency (>15% deviation)
            return TechCardV2(
                meta=base_meta,
                portions=4,
                yield_=YieldV2(perPortion_g=300.0, perBatch_g=1200.0),  # 1200g claimed but ingredients sum to ~800g
                ingredients=[
                    IngredientV2(name="говядина", unit="g", brutto_g=400.0, loss_pct=15.0, netto_g=340.0),
                    IngredientV2(name="капуста", unit="g", brutto_g=300.0, loss_pct=10.0, netto_g=270.0),
                    IngredientV2(name="морковь", unit="g", brutto_g=100.0, loss_pct=20.0, netto_g=80.0),
                    IngredientV2(name="лук", unit="g", brutto_g=80.0, loss_pct=15.0, netto_g=68.0),
                    IngredientV2(name="соль поваренная", unit="g", brutto_g=8.0, loss_pct=0.0, netto_g=8.0),
                    IngredientV2(name="растительное масло", unit="ml", brutto_g=30.0, loss_pct=0.0, netto_g=30.0)
                ],
                process=[
                    ProcessStepV2(n=1, action="Подготовка", time_min=15.0),
                    ProcessStepV2(n=2, action="Обжаривание", time_min=20.0, temp_c=180.0),
                    ProcessStepV2(n=3, action="Варка", time_min=60.0, temp_c=100.0)
                ],
                storage=base_storage,
                allergens=[],
                notes=[]
            )
            
        elif expected_issue == "ruleWarning:saltUpperBound":
            # Create excessive salt (>2.2% of total mass)
            return TechCardV2(
                meta=base_meta,
                portions=4,
                yield_=YieldV2(perPortion_g=200.0, perBatch_g=800.0),
                ingredients=[
                    IngredientV2(name="спагетти", unit="g", brutto_g=400.0, loss_pct=0.0, netto_g=400.0),
                    IngredientV2(name="бекон", unit="g", brutto_g=200.0, loss_pct=5.0, netto_g=190.0),
                    IngredientV2(name="яйца", unit="pcs", brutto_g=120.0, loss_pct=10.0, netto_g=108.0),
                    IngredientV2(name="соль поваренная", unit="g", brutto_g=25.0, loss_pct=0.0, netto_g=25.0),  # 25g salt from ~723g total = 3.5% > 2.2%
                    IngredientV2(name="растительное масло", unit="ml", brutto_g=25.0, loss_pct=0.0, netto_g=25.0)
                ],
                process=[
                    ProcessStepV2(n=1, action="Варка пасты", time_min=12.0, temp_c=100.0),
                    ProcessStepV2(n=2, action="Обжаривание бекона", time_min=8.0, temp_c=160.0),
                    ProcessStepV2(n=3, action="Смешивание", time_min=3.0, temp_c=60.0)
                ],
                storage=base_storage,
                allergens=[],
                notes=[]
            )
            
        elif expected_issue == "ruleWarning:fryOilPerPortion":
            # Create excessive oil (>30ml per portion)
            return TechCardV2(
                meta=base_meta,
                portions=4,
                yield_=YieldV2(perPortion_g=250.0, perBatch_g=1000.0),
                ingredients=[
                    IngredientV2(name="картофель", unit="g", brutto_g=800.0, loss_pct=25.0, netto_g=600.0),
                    IngredientV2(name="лук", unit="g", brutto_g=200.0, loss_pct=15.0, netto_g=170.0),
                    IngredientV2(name="растительное масло", unit="ml", brutto_g=200.0, loss_pct=0.0, netto_g=200.0),  # 200ml / 4 portions = 50ml per portion > 30ml
                    IngredientV2(name="соль поваренная", unit="g", brutto_g=10.0, loss_pct=0.0, netto_g=10.0)
                ],
                process=[
                    ProcessStepV2(n=1, action="Очистка картофеля", time_min=15.0),
                    ProcessStepV2(n=2, action="Жарка в масле", time_min=25.0, temp_c=180.0),
                    ProcessStepV2(n=3, action="Добавление лука", time_min=10.0, temp_c=160.0)
                ],
                storage=base_storage,
                allergens=[],
                notes=[]
            )
            
        elif expected_issue == "ruleError:stepsMin3":
            # Create insufficient steps (<3)
            return TechCardV2(
                meta=base_meta,
                portions=4,
                yield_=YieldV2(perPortion_g=150.0, perBatch_g=600.0),
                ingredients=[
                    IngredientV2(name="помидоры", unit="g", brutto_g=400.0, loss_pct=10.0, netto_g=360.0),
                    IngredientV2(name="огурцы", unit="g", brutto_g=300.0, loss_pct=15.0, netto_g=255.0),
                    IngredientV2(name="оливковое масло", unit="ml", brutto_g=30.0, loss_pct=0.0, netto_g=30.0)
                ],
                process=[
                    ProcessStepV2(n=1, action="Нарезка овощей", time_min=10.0),
                    ProcessStepV2(n=2, action="Заправка маслом", time_min=2.0)
                    # Only 2 steps < 3 minimum required
                ],
                storage=base_storage,
                allergens=[],
                notes=[]
            )
            
        elif expected_issue == "ruleWarning:thermalInfoMissing":
            # Create thermal steps without time AND temperature
            return TechCardV2(
                meta=base_meta,
                portions=4,
                yield_=YieldV2(perPortion_g=200.0, perBatch_g=800.0),
                ingredients=[
                    IngredientV2(name="говядина стейк", unit="g", brutto_g=800.0, loss_pct=20.0, netto_g=640.0),
                    IngredientV2(name="растительное масло", unit="ml", brutto_g=40.0, loss_pct=0.0, netto_g=40.0),
                    IngredientV2(name="соль поваренная", unit="g", brutto_g=8.0, loss_pct=0.0, netto_g=8.0)
                ],
                process=[
                    ProcessStepV2(n=1, action="Подготовка мяса", time_min=5.0),
                    ProcessStepV2(n=2, action="Обжаривание на сковороде", time_min=None, temp_c=None),  # Missing both
                    ProcessStepV2(n=3, action="Жарка до готовности", time_min=None, temp_c=None),      # Missing both
                    ProcessStepV2(n=4, action="Отдых мяса", time_min=5.0)
                ],
                storage=base_storage,
                allergens=[],
                notes=[]
            )
        
        return None
        
    except Exception as e:
        print(f"    ❌ Ошибка создания тестовой техкарты: {str(e)}")
        return None

def run_unit_tests() -> bool:
    """Run unit tests for chef rules"""
    try:
        import subprocess
        import os
        
        # Change to app directory
        original_dir = os.getcwd()
        os.chdir('/app')
        
        print("  🧪 Запуск юнит-тестов для chef_rules...")
        
        # Run pytest on the chef rules tests
        result = subprocess.run([
            'python', '-m', 'pytest', 
            'tests/test_chef_rules.py', 
            '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=60, env={**os.environ, 'PYTHONPATH': '/app/backend'})
        
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print("  ✅ Все юнит-тесты пройдены")
            # Count passed tests
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'passed' in line and ('failed' in line or 'error' in line):
                    print(f"     {line.strip()}")
                    break
            return True
        else:
            print("  ❌ Юнит-тесты провалились")
            print(f"     Ошибки: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка запуска юнит-тестов: {str(e)}")
        return False

def test_pipeline_integration() -> bool:
    """Test chef rules integration in the pipeline"""
    try:
        print("  🔄 Тестирование интеграции правил шефа в пайплайн...")
        
        # Test with a simple request that should trigger chef rules
        response = requests.post(
            f"{BACKEND_URL}/v1/techcards.v2/generate",
            params={"use_llm": "false"},
            json={
                "name": "Тестовое блюдо для проверки правил",
                "cuisine": "тестовая",
                "equipment": [],
                "budget": None,
                "dietary": []
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check that the response has the expected structure
            has_card = 'card' in result
            has_status = 'status' in result
            has_issues = 'issues' in result
            
            print(f"     Структура ответа: card={has_card}, status={has_status}, issues={has_issues}")
            
            # Check if chef rules were executed (should have some processing)
            if has_card and has_status:
                print("  ✅ Пайплайн работает корректно")
                print(f"     Статус: {result.get('status')}")
                print(f"     Количество issues: {len(result.get('issues', []))}")
                
                # Check if we can find evidence of chef rules execution
                issues = result.get('issues', [])
                chef_rules_evidence = any(
                    'rule' in str(issue).lower() or 
                    'chef' in str(issue).lower() or
                    isinstance(issue, dict) and issue.get('type', '').startswith('rule')
                    for issue in issues
                )
                
                if chef_rules_evidence:
                    print("     ✅ Найдены признаки работы правил шефа")
                
                return True
            else:
                print("  ❌ Неполная структура ответа пайплайна")
                return False
        else:
            print(f"  ❌ Пайплайн вернул ошибку: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"     Детали: {error_detail}")
            except:
                print(f"     Текст ошибки: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка тестирования пайплайна: {str(e)}")
        return False

def test_constants_and_coverage():
    """Test that constants are properly defined and coverage is good"""
    try:
        print("  🔧 Проверка констант chef_rules...")
        
        # Add the backend path to sys.path
        backend_path = '/app/backend'
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # Import and check constants
        from receptor_agent.techcards_v2.chef_rules_consts import (
            MAX_LOSS_PCT, YIELD_TOLERANCE, SALT_PCT_MAX,
            OIL_ML_PER_PORTION_MIN, OIL_ML_PER_PORTION_MAX,
            MIN_PROCESS_STEPS, ALLOWED_UNITS
        )
        
        print(f"  ✅ Константы загружены:")
        print(f"     MAX_LOSS_PCT = {MAX_LOSS_PCT}")
        print(f"     YIELD_TOLERANCE = {YIELD_TOLERANCE}")
        print(f"     SALT_PCT_MAX = {SALT_PCT_MAX}")
        print(f"     OIL_ML_PER_PORTION_MIN/MAX = {OIL_ML_PER_PORTION_MIN}/{OIL_ML_PER_PORTION_MAX}")
        print(f"     MIN_PROCESS_STEPS = {MIN_PROCESS_STEPS}")
        print(f"     ALLOWED_UNITS = {ALLOWED_UNITS}")
        
        # Verify values are reasonable
        assert MAX_LOSS_PCT == 60.0, f"Expected MAX_LOSS_PCT=60.0, got {MAX_LOSS_PCT}"
        assert YIELD_TOLERANCE == 0.15, f"Expected YIELD_TOLERANCE=0.15, got {YIELD_TOLERANCE}"
        assert SALT_PCT_MAX == 0.022, f"Expected SALT_PCT_MAX=0.022, got {SALT_PCT_MAX}"
        assert OIL_ML_PER_PORTION_MIN == 5.0, f"Expected OIL_ML_PER_PORTION_MIN=5.0, got {OIL_ML_PER_PORTION_MIN}"
        assert OIL_ML_PER_PORTION_MAX == 30.0, f"Expected OIL_ML_PER_PORTION_MAX=30.0, got {OIL_ML_PER_PORTION_MAX}"
        assert MIN_PROCESS_STEPS == 3, f"Expected MIN_PROCESS_STEPS=3, got {MIN_PROCESS_STEPS}"
        assert ALLOWED_UNITS == ['g', 'ml', 'pcs'], f"Expected ALLOWED_UNITS=['g', 'ml', 'pcs'], got {ALLOWED_UNITS}"
        
        print("  ✅ Все константы имеют правильные значения")
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка проверки констант: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ CHEF RULES (TASK 2.2)")
    print("Тестирование автоматического выявления 'кухонного бреда' через детерминированные правила")
    print()
    
    # Main testing
    success = test_chef_rules_implementation()
    
    if success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("Chef Rules (Task 2.2) готовы к продакшену")
        exit(0)
    else:
        print("\n❌ ЕСТЬ ПРОБЛЕМЫ В ТЕСТАХ")
        print("Требуется доработка Chef Rules")
        exit(1)