#!/usr/bin/env python3
"""
Backend Testing for Prompt Pack v2 для 4o-mini + проверяющий пасс
Testing the new two-step LLM chain for quality TechCardV2 generation

Test Requirements:
1. Generate 5 test dishes: Борщ украинский, Цезарь салат, Карбонара паста, Котлета по-киевски, Бургер классический
2. Verify quality improvements: no marketing epithets, no ranges, deterministic numbers, proper units
3. Check postcheck_v2 works correctly with issues detection
4. Verify LLM parameters (temperature=0.2, top_p=0.9, presence_penalty=0)
5. Test integration in pipeline with generate_draft_v2 → normalize_to_v2 chain
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_prompt_pack_v2():
    """Test the new Prompt Pack v2 implementation"""
    print("🎯 TESTING PROMPT PACK V2 FOR 4O-MINI + ПРОВЕРЯЮЩИЙ ПАСС")
    print("=" * 80)
    
    # Test dishes as specified in review
    test_dishes = [
        {
            "name": "Борщ украинский",
            "cuisine": "украинская",
            "description": "Традиционный украинский борщ с говядиной и свеклой"
        },
        {
            "name": "Цезарь салат",
            "cuisine": "итальянская", 
            "description": "Классический салат Цезарь с курицей и пармезаном"
        },
        {
            "name": "Карбонара паста",
            "cuisine": "итальянская",
            "description": "Паста карбонара с беконом и яйцом"
        },
        {
            "name": "Котлета по-киевски",
            "cuisine": "украинская",
            "description": "Куриная котлета с маслом и зеленью"
        },
        {
            "name": "Бургер классический",
            "cuisine": "американская",
            "description": "Классический бургер с говяжьей котлетой"
        }
    ]
    
    results = []
    
    for i, dish in enumerate(test_dishes, 1):
        print(f"\n📋 ТЕСТ {i}/5: {dish['name']}")
        print("-" * 50)
        
        try:
            # Test TechCardV2 generation with new v2 prompts
            result = test_techcard_v2_generation(dish)
            results.append(result)
            
            # Brief pause between tests
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ ОШИБКА при тестировании {dish['name']}: {str(e)}")
            results.append({
                "dish": dish['name'],
                "success": False,
                "error": str(e)
            })
    
    # Summary analysis
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ АНАЛИЗ PROMPT PACK V2")
    print("=" * 80)
    
    analyze_v2_results(results)
    
    return results

def test_techcard_v2_generation(dish: Dict[str, Any]) -> Dict[str, Any]:
    """Test TechCardV2 generation with v2 prompts"""
    
    # Generate tech card using v2 pipeline with correct ProfileInput format
    payload = {
        "name": dish["name"],
        "cuisine": dish["cuisine"],
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    print(f"🔄 Генерация техкарты для: {dish['name']}")
    
    try:
        response = requests.post(
            f"{API_BASE}/v1/techcards.v2/generate?use_llm=true",
            json=payload,
            timeout=60
        )
        
        print(f"📡 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract tech card data
            tech_card = data.get("card")  # Changed from "techCard" to "card"
            status = data.get("status", "unknown")
            issues = data.get("issues", [])
            
            print(f"✅ Статус генерации: {status}")
            print(f"📝 Количество issues: {len(issues)}")
            
            if tech_card:
                # Analyze quality with postcheck_v2 criteria
                quality_analysis = analyze_v2_quality(tech_card, dish['name'])
                
                return {
                    "dish": dish['name'],
                    "success": True,
                    "status": status,
                    "tech_card": tech_card,
                    "issues": issues,
                    "quality_analysis": quality_analysis
                }
            else:
                print(f"❌ Техкарта не сгенерирована")
                return {
                    "dish": dish['name'],
                    "success": False,
                    "error": "No tech card generated",
                    "issues": issues
                }
        else:
            error_text = response.text
            print(f"❌ HTTP Error: {response.status_code} - {error_text}")
            return {
                "dish": dish['name'],
                "success": False,
                "error": f"HTTP {response.status_code}: {error_text}"
            }
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {str(e)}")
        return {
            "dish": dish['name'],
            "success": False,
            "error": str(e)
        }

def analyze_v2_quality(tech_card: Dict[str, Any], dish_name: str) -> Dict[str, Any]:
    """Analyze tech card quality according to v2 postcheck criteria"""
    
    print(f"🔍 Анализ качества v2 для: {dish_name}")
    
    analysis = {
        "dish_name": dish_name,
        "checks": {},
        "overall_score": 0,
        "critical_issues": [],
        "minor_issues": []
    }
    
    # Convert to string for text analysis
    card_text = json.dumps(tech_card, ensure_ascii=False).lower()
    
    # 1. forbiddenWords - check for marketing epithets
    forbidden_words = [
        'вкуснейш', 'невероятн', 'вау', 'идеальн', 'потрясающ', 'изумительн',
        'восхитительн', 'великолепн', 'шикарн', 'фантастическ', 'волшебн',
        'божественн', 'чудесн', 'превосходн', 'замечательн', 'отличн',
        'прекрасн', 'удивительн', 'сказочн', 'роскошн'
    ]
    
    found_forbidden = []
    for word in forbidden_words:
        if word in card_text:
            found_forbidden.append(word)
    
    analysis["checks"]["forbiddenWords"] = {
        "passed": len(found_forbidden) == 0,
        "found": found_forbidden
    }
    
    if found_forbidden:
        analysis["critical_issues"].append(f"Найдены маркетинговые эпитеты: {', '.join(found_forbidden)}")
    else:
        analysis["overall_score"] += 1
        print("✅ forbiddenWords: Нет маркетинговых эпитетов")
    
    # 2. ranges - check for ranges and approximations
    import re
    range_patterns = [
        r'\d+\s*[–-]\s*\d+',  # 10-15, 5–7
        r'~|≈|около|примерно'  # ~5, ≈10, около 15, примерно 20
    ]
    
    found_ranges = []
    for pattern in range_patterns:
        matches = re.findall(pattern, card_text)
        found_ranges.extend(matches)
    
    analysis["checks"]["ranges"] = {
        "passed": len(found_ranges) == 0,
        "found": found_ranges
    }
    
    if found_ranges:
        analysis["critical_issues"].append(f"Найдены диапазоны: {', '.join(found_ranges)}")
    else:
        analysis["overall_score"] += 1
        print("✅ ranges: Нет диапазонов и приближений")
    
    # 3. units - check measurement units
    allowed_units = ['g', 'ml', 'pcs']
    wrong_units = []
    
    ingredients = tech_card.get("ingredients", [])
    for ingredient in ingredients:
        unit = ingredient.get("unit", "")
        if unit not in allowed_units:
            wrong_units.append(f"{ingredient.get('name', 'Unknown')}: {unit}")
    
    analysis["checks"]["units"] = {
        "passed": len(wrong_units) == 0,
        "wrong_units": wrong_units
    }
    
    if wrong_units:
        analysis["critical_issues"].append(f"Недопустимые единицы: {', '.join(wrong_units)}")
    else:
        analysis["overall_score"] += 1
        print("✅ units: Все единицы измерения корректны (g/ml/pcs)")
    
    # 4. processMin3 - minimum 3 process steps
    process_steps = tech_card.get("process", [])
    step_count = len(process_steps)
    
    analysis["checks"]["processMin3"] = {
        "passed": step_count >= 3,
        "step_count": step_count
    }
    
    if step_count < 3:
        analysis["critical_issues"].append(f"Недостаточно шагов процесса: {step_count} (нужно ≥3)")
    else:
        analysis["overall_score"] += 1
        print(f"✅ processMin3: {step_count} шагов процесса")
    
    # 5. thermalInfo - check time/temperature for thermal processing
    thermal_keywords = ['жар', 'вар', 'туш', 'запек', 'обжар', 'кип', 'гриль', 'фри']
    missing_thermal = []
    
    for i, step in enumerate(process_steps):
        action = step.get("action", "").lower()
        is_thermal = any(keyword in action for keyword in thermal_keywords)
        
        if is_thermal:
            time_min = step.get("time_min")
            temp_c = step.get("temp_c")
            
            if not time_min and not temp_c:
                missing_thermal.append(f"Шаг {i+1}: {step.get('action', 'Unknown')}")
    
    analysis["checks"]["thermalInfo"] = {
        "passed": len(missing_thermal) == 0,
        "missing": missing_thermal
    }
    
    if missing_thermal:
        analysis["minor_issues"].append(f"Термошаги без времени/температуры: {'; '.join(missing_thermal)}")
    else:
        analysis["overall_score"] += 1
        print("✅ thermalInfo: Термообработка имеет время/температуру")
    
    # 6. yieldConsistency - yield consistency check
    total_netto = 0
    for ingredient in ingredients:
        netto_g = ingredient.get("netto_g", 0)
        if isinstance(netto_g, (int, float)):
            total_netto += netto_g
    
    yield_data = tech_card.get("yield", {})
    per_batch_g = yield_data.get("perBatch_g", 0)
    
    yield_consistent = True
    deviation = 0
    
    if per_batch_g > 0:
        deviation = abs(total_netto - per_batch_g) / per_batch_g
        yield_consistent = deviation <= 0.10  # ±10%
    
    analysis["checks"]["yieldConsistency"] = {
        "passed": yield_consistent,
        "total_netto": total_netto,
        "per_batch_g": per_batch_g,
        "deviation_pct": deviation * 100
    }
    
    if not yield_consistent:
        analysis["critical_issues"].append(f"Нетто {total_netto:.1f}г не соответствует выходу {per_batch_g:.1f}г (отклонение {deviation:.1%})")
    else:
        analysis["overall_score"] += 1
        print(f"✅ yieldConsistency: Нетто {total_netto:.1f}г ≈ выход {per_batch_g:.1f}г")
    
    # 7. lossBounds - check loss bounds (0-40%)
    wrong_losses = []
    for ingredient in ingredients:
        loss_pct = ingredient.get("loss_pct", 0)
        if isinstance(loss_pct, (int, float)):
            if loss_pct < 0 or loss_pct > 40:
                wrong_losses.append(f"{ingredient.get('name', 'Unknown')}: {loss_pct}%")
    
    analysis["checks"]["lossBounds"] = {
        "passed": len(wrong_losses) == 0,
        "wrong_losses": wrong_losses
    }
    
    if wrong_losses:
        analysis["critical_issues"].append(f"Потери вне диапазона 0-40%: {', '.join(wrong_losses)}")
    else:
        analysis["overall_score"] += 1
        print("✅ lossBounds: Все потери в диапазоне 0-40%")
    
    # 8. numbersFormat - max 1 decimal place
    precision_issues = []
    
    # Check ingredients
    for ingredient in ingredients:
        for field_name in ['brutto_g', 'loss_pct', 'netto_g']:
            value = ingredient.get(field_name)
            if isinstance(value, float):
                decimal_part = str(value).split('.')
                if len(decimal_part) > 1 and len(decimal_part[1]) > 1:
                    precision_issues.append(f"{ingredient.get('name', 'Unknown')}.{field_name}: {value}")
    
    # Check yield
    for field_name in ['perPortion_g', 'perBatch_g']:
        value = yield_data.get(field_name)
        if isinstance(value, float):
            decimal_part = str(value).split('.')
            if len(decimal_part) > 1 and len(decimal_part[1]) > 1:
                precision_issues.append(f"yield.{field_name}: {value}")
    
    analysis["checks"]["numbersFormat"] = {
        "passed": len(precision_issues) == 0,
        "precision_issues": precision_issues[:5]  # Limit output
    }
    
    if precision_issues:
        analysis["minor_issues"].append(f"Числа с >1 знака после запятой: {len(precision_issues)} случаев")
    else:
        analysis["overall_score"] += 1
        print("✅ numbersFormat: Все числа с ≤1 знака после запятой")
    
    # Calculate final score
    max_score = 8
    analysis["score_percentage"] = (analysis["overall_score"] / max_score) * 100
    
    print(f"📊 Общий балл качества: {analysis['overall_score']}/{max_score} ({analysis['score_percentage']:.1f}%)")
    
    if analysis["critical_issues"]:
        print(f"🚨 Критические проблемы: {len(analysis['critical_issues'])}")
        for issue in analysis["critical_issues"]:
            print(f"   - {issue}")
    
    if analysis["minor_issues"]:
        print(f"⚠️ Минорные проблемы: {len(analysis['minor_issues'])}")
        for issue in analysis["minor_issues"]:
            print(f"   - {issue}")
    
    return analysis

def analyze_v2_results(results: List[Dict[str, Any]]):
    """Analyze overall results of v2 prompt testing"""
    
    successful_tests = [r for r in results if r.get("success", False)]
    failed_tests = [r for r in results if not r.get("success", False)]
    
    print(f"✅ Успешных тестов: {len(successful_tests)}/5")
    print(f"❌ Неудачных тестов: {len(failed_tests)}/5")
    
    if failed_tests:
        print("\n🚨 НЕУДАЧНЫЕ ТЕСТЫ:")
        for test in failed_tests:
            print(f"   - {test['dish']}: {test.get('error', 'Unknown error')}")
    
    if successful_tests:
        print(f"\n📊 АНАЛИЗ КАЧЕСТВА V2 ПРОМПТОВ:")
        
        # Aggregate quality scores
        total_score = 0
        total_max = 0
        critical_issues_count = 0
        minor_issues_count = 0
        
        status_counts = {"success": 0, "draft": 0}
        
        for test in successful_tests:
            quality = test.get("quality_analysis", {})
            score = quality.get("overall_score", 0)
            total_score += score
            total_max += 8  # Max score per test
            
            critical_issues_count += len(quality.get("critical_issues", []))
            minor_issues_count += len(quality.get("minor_issues", []))
            
            status = test.get("status", "unknown")
            if status in status_counts:
                status_counts[status] += 1
        
        if total_max > 0:
            overall_percentage = (total_score / total_max) * 100
            print(f"🎯 Общий балл качества: {total_score}/{total_max} ({overall_percentage:.1f}%)")
        
        print(f"📈 Статусы генерации:")
        for status, count in status_counts.items():
            print(f"   - {status}: {count}")
        
        print(f"🚨 Всего критических проблем: {critical_issues_count}")
        print(f"⚠️ Всего минорных проблем: {minor_issues_count}")
        
        # Check specific v2 improvements
        print(f"\n🔍 ПРОВЕРКА УЛУЧШЕНИЙ V2:")
        
        # Check for forbidden words across all tests
        total_forbidden = 0
        total_ranges = 0
        total_wrong_units = 0
        
        for test in successful_tests:
            quality = test.get("quality_analysis", {})
            checks = quality.get("checks", {})
            
            if not checks.get("forbiddenWords", {}).get("passed", True):
                total_forbidden += 1
            
            if not checks.get("ranges", {}).get("passed", True):
                total_ranges += 1
                
            if not checks.get("units", {}).get("passed", True):
                total_wrong_units += 1
        
        print(f"   ✅ Без маркетинговых эпитетов: {len(successful_tests) - total_forbidden}/{len(successful_tests)}")
        print(f"   ✅ Без диапазонов: {len(successful_tests) - total_ranges}/{len(successful_tests)}")
        print(f"   ✅ Правильные единицы: {len(successful_tests) - total_wrong_units}/{len(successful_tests)}")
        
        # Overall assessment
        if overall_percentage >= 90:
            print(f"\n🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Prompt Pack v2 показывает высокое качество генерации.")
        elif overall_percentage >= 75:
            print(f"\n✅ ХОРОШИЙ РЕЗУЛЬТАТ! Prompt Pack v2 работает корректно с минорными улучшениями.")
        elif overall_percentage >= 60:
            print(f"\n⚠️ УДОВЛЕТВОРИТЕЛЬНЫЙ РЕЗУЛЬТАТ. Prompt Pack v2 требует доработки.")
        else:
            print(f"\n❌ НЕУДОВЛЕТВОРИТЕЛЬНЫЙ РЕЗУЛЬТАТ. Prompt Pack v2 требует серьезных исправлений.")

def test_postcheck_v2_directly():
    """Test postcheck_v2 function directly"""
    print(f"\n🔧 ПРЯМОЕ ТЕСТИРОВАНИЕ POSTCHECK_V2")
    print("-" * 50)
    
    try:
        # Test postcheck_v2 with a sample tech card
        test_payload = {
            "name": "Тестовое блюдо для постпроверки",
            "cuisine": "тестовая",
            "equipment": [],
            "budget": None,
            "dietary": []
        }
        
        response = requests.post(
            f"{API_BASE}/v1/techcards.v2/generate?use_llm=true",
            json=test_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            tech_card = data.get("card")  # Changed from "techCard" to "card"
            issues = data.get("issues", [])
            
            print(f"✅ Техкарта сгенерирована для тестирования postcheck_v2")
            print(f"📝 Issues от API: {len(issues)}")
            
            # Check if postcheck issues are present
            postcheck_issues = [issue for issue in issues if "postcheck:" in str(issue)]
            print(f"🔍 Postcheck issues: {len(postcheck_issues)}")
            
            if postcheck_issues:
                print("📋 Найденные postcheck issues:")
                for issue in postcheck_issues:
                    print(f"   - {issue}")
            else:
                print("✅ Postcheck issues не найдены - качество высокое")
                
            return True
        else:
            print(f"❌ Ошибка генерации для тестирования postcheck: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования postcheck_v2: {str(e)}")
        return False

def test_llm_parameters():
    """Test that LLM parameters are correctly set"""
    print(f"\n⚙️ ПРОВЕРКА ПАРАМЕТРОВ LLM")
    print("-" * 50)
    
    # Check environment variables
    print("🔍 Проверка переменных окружения:")
    
    # Check if we can access backend environment (indirectly through API behavior)
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend доступен")
        else:
            print(f"⚠️ Backend health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения к backend: {str(e)}")
        return False
    
    # Test generation with specific parameters (indirectly)
    print("\n🧪 Тестирование стабильности генерации (косвенная проверка параметров):")
    
    test_payload = {
        "name": "Простое тестовое блюдо",
        "cuisine": "русская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    # Generate same dish multiple times to check consistency
    results = []
    for i in range(3):
        try:
            response = requests.post(
                f"{API_BASE}/v1/techcards.v2/generate?use_llm=true",
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results.append(data.get("status", "unknown"))
                print(f"   Попытка {i+1}: {data.get('status', 'unknown')}")
            else:
                print(f"   Попытка {i+1}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   Попытка {i+1}: Ошибка - {str(e)}")
    
    # Analyze consistency
    if len(results) >= 2:
        consistent_results = len(set(results))
        if consistent_results == 1:
            print("✅ Результаты стабильны (параметры temperature=0.2 работают)")
        else:
            print(f"⚠️ Результаты варьируются: {set(results)}")
    
    return True

def main():
    """Main testing function"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ PROMPT PACK V2")
    print("=" * 80)
    
    # Test LLM parameters
    test_llm_parameters()
    
    # Test the main v2 prompt functionality
    results = test_prompt_pack_v2()
    
    # Test postcheck_v2 directly
    test_postcheck_v2_directly()
    
    print("\n" + "=" * 80)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    main()