#!/usr/bin/env python3
"""
🎯 RECEPTOR PRO - COMPREHENSIVE CHEF AUDIT SYSTEM
Professional quality assessment of tech cards as requested by expert chef

This test conducts a thorough evaluation of 10 dishes across different complexity levels:
- Simple: Паста Карбонара, Борщ классический
- Medium: Утка по-пекински, Ризотто с грибами трюфелем
- Complex: Beef Wellington, Суфле шоколадное
- Regional: Плов узбекский, Том ям
- Modern: Тартар из тунца, Крем-брюле

Each dish is evaluated on:
- Technical correctness (proportions, timing, KBJU, pricing)
- Culinary logic (sequence, temperatures, ingredient compatibility)
- Practicality (feasibility, ingredient availability, chef tips)
- Content quality (professional language, completeness)
"""

import requests
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple

class ChefAuditSystem:
    def __init__(self):
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.user_id = "chef_audit_2025"
        self.audit_results = {}
        
        # Test dishes organized by complexity
        self.test_dishes = {
            "simple": [
                "Паста Карбонара",
                "Борщ классический"
            ],
            "medium": [
                "Утка по-пекински",
                "Ризотто с грибами трюфелем"
            ],
            "complex": [
                "Beef Wellington",
                "Суфле шоколадное"
            ],
            "regional": [
                "Плов узбекский",
                "Том ям"
            ],
            "modern": [
                "Тартар из тунца",
                "Крем-брюле"
            ]
        }
        
        # Rating criteria weights
        self.criteria_weights = {
            "technical_correctness": 0.3,
            "culinary_logic": 0.3,
            "practicality": 0.2,
            "content_quality": 0.2
        }

    def setup_test_user(self):
        """Setup PRO user for comprehensive testing"""
        print("🔧 Setting up chef audit user...")
        
        # Use a unique email for this test run
        test_email = f"chef_audit_{int(time.time())}@test.com"
        
        # Register user
        user_data = {
            "email": test_email,
            "name": "Chef Audit System",
            "city": "moskva"
        }
        
        try:
            response = requests.post(f"{self.base_url}/register", json=user_data)
            if response.status_code == 200:
                user_info = response.json()
                self.user_id = user_info["id"]
                print(f"✅ User registered with ID: {self.user_id}")
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"⚠️ User setup issue: {e}")
            return False
        
        # Upgrade to PRO for full feature access
        try:
            upgrade_data = {"subscription_plan": "pro"}
            response = requests.post(f"{self.base_url}/upgrade-subscription/{self.user_id}", json=upgrade_data)
            if response.status_code == 200:
                print("✅ Upgraded to PRO subscription")
            else:
                print(f"⚠️ Upgrade failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ Upgrade issue: {e}")
            return False
        
        # Setup kitchen equipment for PRO features
        try:
            equipment_response = requests.get(f"{self.base_url}/kitchen-equipment")
            if equipment_response.status_code == 200:
                equipment = equipment_response.json()
                # Select comprehensive equipment set
                equipment_ids = []
                for category in equipment.values():
                    equipment_ids.extend([item["id"] for item in category[:3]])  # First 3 from each category
                
                equipment_data = {"equipment_ids": equipment_ids}
                response = requests.post(f"{self.base_url}/update-kitchen-equipment/{self.user_id}", json=equipment_data)
                if response.status_code == 200:
                    print(f"✅ Configured {len(equipment_ids)} kitchen equipment items")
                else:
                    print(f"⚠️ Equipment setup failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Equipment setup issue: {e}")
        
        return True

    def generate_tech_card(self, dish_name: str) -> Dict:
        """Generate a tech card for evaluation"""
        print(f"🍳 Generating tech card for: {dish_name}")
        
        data = {
            "dish_name": dish_name,
            "user_id": self.user_id
        }
        
        try:
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Generated tech card for {dish_name}")
                    return {
                        "success": True,
                        "content": result["tech_card"],
                        "id": result["id"]
                    }
                else:
                    print(f"❌ Failed to generate tech card for {dish_name}")
                    return {"success": False, "error": "Generation failed"}
            else:
                print(f"❌ API error for {dish_name}: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Exception generating {dish_name}: {e}")
            return {"success": False, "error": str(e)}

    def evaluate_technical_correctness(self, content: str, dish_name: str) -> Tuple[int, str]:
        """Evaluate technical aspects: proportions, timing, KBJU, pricing"""
        score = 5
        issues = []
        
        # Check for proper ingredient proportions
        if "ингредиенты" in content.lower():
            # Look for realistic portions (150-300g for main dishes)
            portion_match = re.search(r'порция.*?(\d+)\s*г', content, re.IGNORECASE)
            if portion_match:
                portion_size = int(portion_match.group(1))
                if dish_name.lower() in ["десерт", "суфле", "крем-брюле", "тартар"]:
                    if not (80 <= portion_size <= 150):
                        issues.append(f"Неправильный размер порции для десерта: {portion_size}г (должно быть 80-150г)")
                        score -= 1
                elif "суп" in dish_name.lower() or "борщ" in dish_name.lower():
                    if not (250 <= portion_size <= 350):
                        issues.append(f"Неправильный размер порции для супа: {portion_size}г (должно быть 250-350мл)")
                        score -= 1
                else:
                    if not (200 <= portion_size <= 300):
                        issues.append(f"Неправильный размер порции: {portion_size}г (должно быть 200-300г)")
                        score -= 1
        
        # Check for proper timing
        time_match = re.search(r'время.*?(\d+).*?мин', content, re.IGNORECASE)
        if time_match:
            total_time = int(time_match.group(1))
            if dish_name in ["Beef Wellington", "Утка по-пекински", "Плов узбекский"]:
                if total_time < 120:
                    issues.append(f"Слишком короткое время для сложного блюда: {total_time} мин")
                    score -= 1
            elif dish_name in ["Паста Карбонара"]:
                if total_time > 30:
                    issues.append(f"Слишком долгое время для простого блюда: {total_time} мин")
                    score -= 1
        
        # Check for KBJU presence and realism
        kbju_match = re.search(r'кбжу.*?калории.*?(\d+)', content, re.IGNORECASE)
        if kbju_match:
            calories = int(kbju_match.group(1))
            if calories < 100 or calories > 1000:
                issues.append(f"Нереалистичная калорийность: {calories} ккал")
                score -= 1
        else:
            issues.append("Отсутствует информация о КБЖУ")
            score -= 1
        
        # Check pricing logic
        price_match = re.search(r'рекомендуемая цена.*?(\d+)', content, re.IGNORECASE)
        cost_match = re.search(r'себестоимость.*?(\d+)', content, re.IGNORECASE)
        if price_match and cost_match:
            price = int(price_match.group(1))
            cost = int(cost_match.group(1))
            markup = price / cost if cost > 0 else 0
            if markup < 2.5 or markup > 4:
                issues.append(f"Неправильная наценка: {markup:.1f}x (должно быть 2.5-4x)")
                score -= 1
        
        # Check for forbidden phrases
        if "стандартная ресторанная порция" in content:
            issues.append("Найдена запрещенная фраза 'стандартная ресторанная порция'")
            score -= 2
        
        return max(1, score), "; ".join(issues) if issues else "Технически корректно"

    def evaluate_culinary_logic(self, content: str, dish_name: str) -> Tuple[int, str]:
        """Evaluate culinary sequence, temperatures, ingredient compatibility"""
        score = 5
        issues = []
        
        # Check for logical cooking sequence
        if "рецепт" in content.lower():
            steps = re.findall(r'\d+\.\s*([^0-9]+?)(?=\d+\.|$)', content, re.DOTALL)
            if len(steps) < 3:
                issues.append("Слишком мало этапов приготовления")
                score -= 1
            
            # Check for temperature mentions in appropriate dishes
            if dish_name in ["Beef Wellington", "Суфле шоколадное", "Утка по-пекински"]:
                if not re.search(r'\d+°[CF]', content):
                    issues.append("Отсутствуют температурные режимы для сложного блюда")
                    score -= 1
        
        # Check ingredient compatibility for specific dishes
        if dish_name == "Паста Карбонара":
            if "сливки" in content.lower():
                issues.append("Классическая Карбонара не содержит сливки")
                score -= 1
            if not ("гуанчале" in content.lower() or "бекон" in content.lower()):
                issues.append("Отсутствует основной ингредиент - гуанчале или бекон")
                score -= 1
        
        elif dish_name == "Том ям":
            required_ingredients = ["лемонграсс", "галанга", "лайм", "рыбный соус"]
            missing = [ing for ing in required_ingredients if ing not in content.lower()]
            if missing:
                issues.append(f"Отсутствуют ключевые ингредиенты: {', '.join(missing)}")
                score -= 1
        
        elif dish_name == "Ризотто с грибами трюфелем":
            if "арборио" not in content.lower() and "карнароли" not in content.lower():
                issues.append("Неправильный тип риса для ризотто")
                score -= 1
        
        # Check for professional techniques
        techniques = ["обжарить", "тушить", "бланшировать", "пассеровать", "фламбировать"]
        found_techniques = [t for t in techniques if t in content.lower()]
        if len(found_techniques) < 2:
            issues.append("Недостаточно профессиональных техник приготовления")
            score -= 1
        
        return max(1, score), "; ".join(issues) if issues else "Кулинарно логично"

    def evaluate_practicality(self, content: str, dish_name: str) -> Tuple[int, str]:
        """Evaluate feasibility, ingredient availability, chef tips"""
        score = 5
        issues = []
        
        # Check for chef tips and advice
        if "совет" not in content.lower() and "рекомендация" not in content.lower():
            issues.append("Отсутствуют советы от шефа")
            score -= 1
        
        # Check for storage and preparation info
        if "хранение" not in content.lower() and "заготовки" not in content.lower():
            issues.append("Отсутствует информация о заготовках и хранении")
            score -= 1
        
        # Check ingredient availability (exotic ingredients should have alternatives)
        exotic_ingredients = ["трюфель", "фуа-гра", "икра", "лангуст", "морские гребешки"]
        found_exotic = [ing for ing in exotic_ingredients if ing in content.lower()]
        if found_exotic and "альтернатива" not in content.lower():
            issues.append(f"Экзотические ингредиенты без альтернатив: {', '.join(found_exotic)}")
            score -= 1
        
        # Check for equipment requirements vs availability
        if dish_name == "Суфле шоколадное":
            if "водяная баня" not in content.lower() and "пароконвектомат" not in content.lower():
                issues.append("Отсутствует информация о специальном оборудовании для суфле")
                score -= 1
        
        # Check for realistic preparation complexity
        if dish_name in ["Паста Карбонара", "Борщ классический"]:
            if len(re.findall(r'\d+\.', content)) > 8:
                issues.append("Слишком сложная технология для простого блюда")
                score -= 1
        
        return max(1, score), "; ".join(issues) if issues else "Практично и выполнимо"

    def evaluate_content_quality(self, content: str, dish_name: str) -> Tuple[int, str]:
        """Evaluate professional language, completeness, consistency"""
        score = 5
        issues = []
        
        # Check for required sections
        required_sections = ["название", "ингредиенты", "рецепт", "время", "кбжу", "себестоимость"]
        missing_sections = [section for section in required_sections if section not in content.lower()]
        if missing_sections:
            issues.append(f"Отсутствуют разделы: {', '.join(missing_sections)}")
            score -= len(missing_sections) * 0.5
        
        # Check for professional terminology
        professional_terms = ["бланшировать", "пассеровать", "конфи", "жульен", "брунуаз", "шифонад"]
        found_terms = [term for term in professional_terms if term in content.lower()]
        if len(found_terms) < 1:
            issues.append("Недостаточно профессиональной терминологии")
            score -= 0.5
        
        # Check for emoji sections (new golden prompt format)
        emoji_sections = ["💸", "🔥", "💡", "🍷", "📸"]
        found_emojis = [emoji for emoji in emoji_sections if emoji in content]
        if len(found_emojis) < 3:
            issues.append("Неполное использование новой структуры с эмодзи")
            score -= 0.5
        
        # Check for consistency in measurements
        measurements = re.findall(r'(\d+)\s*(г|мл|кг|л|шт)', content)
        if len(measurements) < 5:
            issues.append("Недостаточно детализированных измерений")
            score -= 0.5
        
        # Check for description quality
        if "описание" in content.lower():
            description_match = re.search(r'описание.*?:(.*?)(?=\*\*|$)', content, re.IGNORECASE | re.DOTALL)
            if description_match:
                description = description_match.group(1).strip()
                if len(description) < 100:
                    issues.append("Слишком краткое описание блюда")
                    score -= 0.5
        
        return max(1, score), "; ".join(issues) if issues else "Высокое качество контента"

    def calculate_overall_rating(self, scores: Dict[str, int]) -> Tuple[int, str]:
        """Calculate weighted overall rating"""
        weighted_score = sum(scores[criterion] * self.criteria_weights[criterion] 
                           for criterion in scores)
        
        # Convert to 5-star rating
        stars = round(weighted_score)
        
        # Rating descriptions
        descriptions = {
            5: "⭐⭐⭐⭐⭐ Мишлен уровень - идеальная техкарта",
            4: "⭐⭐⭐⭐ Профессионально - отличная работа",
            3: "⭐⭐⭐ Хорошо - использовать можно",
            2: "⭐⭐ Средне - нужны доработки",
            1: "⭐ Плохо - переделывать"
        }
        
        return stars, descriptions.get(stars, "Неопределенный рейтинг")

    def test_pro_ai_functions(self, tech_card_content: str, dish_name: str) -> Dict:
        """Test PRO AI functions: sales script, food pairing, photo tips"""
        print(f"🤖 Testing PRO AI functions for {dish_name}...")
        
        results = {}
        
        # Test Sales Script Generation
        try:
            data = {"user_id": self.user_id, "tech_card": tech_card_content}
            response = requests.post(f"{self.base_url}/generate-sales-script", json=data)
            if response.status_code == 200:
                script = response.json().get("script", "")
                results["sales_script"] = {
                    "success": True,
                    "quality": "Отличный" if len(script) > 500 else "Средний",
                    "content_preview": script[:200] + "..." if len(script) > 200 else script
                }
            else:
                results["sales_script"] = {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            results["sales_script"] = {"success": False, "error": str(e)}
        
        # Test Food Pairing Generation
        try:
            data = {"user_id": self.user_id, "tech_card": tech_card_content}
            response = requests.post(f"{self.base_url}/generate-food-pairing", json=data)
            if response.status_code == 200:
                pairing = response.json().get("pairing", "")
                results["food_pairing"] = {
                    "success": True,
                    "quality": "Отличный" if len(pairing) > 500 else "Средний",
                    "content_preview": pairing[:200] + "..." if len(pairing) > 200 else pairing
                }
            else:
                results["food_pairing"] = {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            results["food_pairing"] = {"success": False, "error": str(e)}
        
        # Test Photo Tips Generation
        try:
            data = {"user_id": self.user_id, "tech_card": tech_card_content}
            response = requests.post(f"{self.base_url}/generate-photo-tips", json=data)
            if response.status_code == 200:
                tips = response.json().get("tips", "")
                results["photo_tips"] = {
                    "success": True,
                    "quality": "Отличный" if len(tips) > 500 else "Средний",
                    "content_preview": tips[:200] + "..." if len(tips) > 200 else tips
                }
            else:
                results["photo_tips"] = {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            results["photo_tips"] = {"success": False, "error": str(e)}
        
        return results

    def audit_dish(self, dish_name: str, complexity: str) -> Dict:
        """Comprehensive audit of a single dish"""
        print(f"\n🎯 AUDITING: {dish_name} ({complexity.upper()})")
        print("=" * 60)
        
        # Generate tech card
        tech_card_result = self.generate_tech_card(dish_name)
        if not tech_card_result["success"]:
            return {
                "dish_name": dish_name,
                "complexity": complexity,
                "success": False,
                "error": tech_card_result["error"]
            }
        
        content = tech_card_result["content"]
        
        # Evaluate all criteria
        tech_score, tech_comment = self.evaluate_technical_correctness(content, dish_name)
        culinary_score, culinary_comment = self.evaluate_culinary_logic(content, dish_name)
        practical_score, practical_comment = self.evaluate_practicality(content, dish_name)
        quality_score, quality_comment = self.evaluate_content_quality(content, dish_name)
        
        scores = {
            "technical_correctness": tech_score,
            "culinary_logic": culinary_score,
            "practicality": practical_score,
            "content_quality": quality_score
        }
        
        overall_stars, rating_description = self.calculate_overall_rating(scores)
        
        # Test PRO AI functions
        pro_ai_results = self.test_pro_ai_functions(content, dish_name)
        
        # Compile results
        result = {
            "dish_name": dish_name,
            "complexity": complexity,
            "success": True,
            "overall_rating": overall_stars,
            "rating_description": rating_description,
            "detailed_scores": {
                "technical_correctness": {"score": tech_score, "comment": tech_comment},
                "culinary_logic": {"score": culinary_score, "comment": culinary_comment},
                "practicality": {"score": practical_score, "comment": practical_comment},
                "content_quality": {"score": quality_score, "comment": quality_comment}
            },
            "pro_ai_functions": pro_ai_results,
            "tech_card_preview": content[:300] + "..." if len(content) > 300 else content,
            "tech_card_id": tech_card_result["id"]
        }
        
        # Print immediate results
        print(f"📊 РЕЗУЛЬТАТ: {rating_description}")
        print(f"   Техническая корректность: {tech_score}/5 - {tech_comment}")
        print(f"   Кулинарная логика: {culinary_score}/5 - {culinary_comment}")
        print(f"   Практичность: {practical_score}/5 - {practical_comment}")
        print(f"   Качество контента: {quality_score}/5 - {quality_comment}")
        
        return result

    def run_comprehensive_audit(self):
        """Run the complete chef audit on all 10 dishes"""
        print("🎯 RECEPTOR PRO - COMPREHENSIVE CHEF AUDIT")
        print("=" * 70)
        print("Проводим комплексный аудит качества системы как профессиональный шеф-повар")
        print("Тестируем 10 блюд разной сложности по 4 критериям оценки")
        print("=" * 70)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting audit.")
            return {}
        
        # Run audits for all dishes
        all_results = {}
        
        for complexity, dishes in self.test_dishes.items():
            print(f"\n🔥 КАТЕГОРИЯ: {complexity.upper()}")
            print("-" * 40)
            
            category_results = []
            for dish in dishes:
                result = self.audit_dish(dish, complexity)
                category_results.append(result)
                time.sleep(2)  # Rate limiting
            
            all_results[complexity] = category_results
        
        # Generate comprehensive report
        self.generate_final_report(all_results)
        
        return all_results

    def generate_final_report(self, results: Dict):
        """Generate comprehensive final report"""
        print("\n" + "=" * 70)
        print("🎉 ИТОГОВЫЙ ОТЧЕТ ШЕФ-ПОВАРА")
        print("=" * 70)
        
        total_dishes = 0
        total_score = 0
        category_stats = {}
        
        # Analyze results by category
        for complexity, dishes in results.items():
            successful_dishes = [d for d in dishes if d.get("success", False)]
            if successful_dishes:
                avg_rating = sum(d["overall_rating"] for d in successful_dishes) / len(successful_dishes)
                category_stats[complexity] = {
                    "count": len(successful_dishes),
                    "avg_rating": avg_rating,
                    "dishes": successful_dishes
                }
                total_dishes += len(successful_dishes)
                total_score += sum(d["overall_rating"] for d in successful_dishes)
        
        overall_avg = total_score / total_dishes if total_dishes > 0 else 0
        
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Протестировано блюд: {total_dishes}/10")
        print(f"   Средний рейтинг: {overall_avg:.1f}/5 звезд")
        
        # Category breakdown
        print(f"\n📊 РЕЗУЛЬТАТЫ ПО КАТЕГОРИЯМ:")
        for complexity, stats in category_stats.items():
            print(f"   {complexity.upper()}: {stats['avg_rating']:.1f}/5 ({stats['count']} блюд)")
        
        # Detailed dish results
        print(f"\n🍽️ ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for complexity, dishes in results.items():
            print(f"\n{complexity.upper()}:")
            for dish in dishes:
                if dish.get("success", False):
                    print(f"   • {dish['dish_name']}: {dish['rating_description']}")
                    
                    # Show key issues
                    for criterion, details in dish["detailed_scores"].items():
                        if details["score"] < 4:
                            print(f"     ⚠️ {criterion}: {details['comment']}")
                else:
                    print(f"   • {dish['dish_name']}: ❌ ОШИБКА - {dish.get('error', 'Неизвестная ошибка')}")
        
        # PRO AI Functions Summary
        print(f"\n🤖 PRO AI ФУНКЦИИ:")
        pro_success_count = {"sales_script": 0, "food_pairing": 0, "photo_tips": 0}
        pro_total = 0
        
        for complexity, dishes in results.items():
            for dish in dishes:
                if dish.get("success", False) and "pro_ai_functions" in dish:
                    pro_total += 1
                    for func_name, func_result in dish["pro_ai_functions"].items():
                        if func_result.get("success", False):
                            pro_success_count[func_name] += 1
        
        if pro_total > 0:
            print(f"   Скрипты продаж: {pro_success_count['sales_script']}/{pro_total} успешно")
            print(f"   Фудпейринг: {pro_success_count['food_pairing']}/{pro_total} успешно")
            print(f"   Фото-советы: {pro_success_count['photo_tips']}/{pro_total} успешно")
        
        # Recommendations
        print(f"\n💡 РЕКОМЕНДАЦИИ ШЕФ-ПОВАРА:")
        
        if overall_avg >= 4.5:
            print("   ✅ Система работает на мишленовском уровне!")
            print("   ✅ Техкарты готовы для использования в профессиональной кухне")
        elif overall_avg >= 3.5:
            print("   ✅ Хорошее качество техкарт, подходит для большинства ресторанов")
            print("   💡 Рекомендуется доработка деталей для премиум-сегмента")
        elif overall_avg >= 2.5:
            print("   ⚠️ Средний уровень, требуются улучшения")
            print("   💡 Необходимо улучшить техническую точность и кулинарную логику")
        else:
            print("   ❌ Низкое качество, система требует серьезной доработки")
            print("   💡 Критически важно пересмотреть алгоритмы генерации")
        
        # Technical recommendations
        common_issues = {}
        for complexity, dishes in results.items():
            for dish in dishes:
                if dish.get("success", False):
                    for criterion, details in dish["detailed_scores"].items():
                        if details["score"] < 4:
                            issue_key = f"{criterion}: {details['comment'][:50]}..."
                            common_issues[issue_key] = common_issues.get(issue_key, 0) + 1
        
        if common_issues:
            print(f"\n🔧 ЧАСТЫЕ ПРОБЛЕМЫ:")
            for issue, count in sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   • {issue} (встречается {count} раз)")
        
        print("\n" + "=" * 70)
        print("🎯 АУДИТ ЗАВЕРШЕН - Система Receptor Pro протестирована профессиональным шефом")
        print("=" * 70)

def main():
    """Main execution function"""
    audit_system = ChefAuditSystem()
    results = audit_system.run_comprehensive_audit()
    return results

if __name__ == "__main__":
    main()