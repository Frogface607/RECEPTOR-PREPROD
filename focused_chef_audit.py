#!/usr/bin/env python3
"""
🎯 FOCUSED CHEF AUDIT - Testing 5 key dishes for quality assessment
"""

import requests
import json
import re
import time
from datetime import datetime

class FocusedChefAudit:
    def __init__(self):
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.user_id = None
        
        # Focus on 5 representative dishes
        self.test_dishes = [
            {"name": "Паста Карбонара", "complexity": "simple"},
            {"name": "Ризотто с грибами трюфелем", "complexity": "medium"},
            {"name": "Beef Wellington", "complexity": "complex"},
            {"name": "Том ям", "complexity": "regional"},
            {"name": "Тартар из тунца", "complexity": "modern"}
        ]

    def setup_pro_user(self):
        """Setup PRO user for testing"""
        print("🔧 Setting up PRO test user...")
        
        test_email = f"chef_audit_{int(time.time())}@test.com"
        user_data = {
            "email": test_email,
            "name": "Chef Audit Pro",
            "city": "moskva"
        }
        
        # Register user
        response = requests.post(f"{self.base_url}/register", json=user_data)
        if response.status_code != 200:
            print(f"❌ Registration failed: {response.status_code}")
            return False
        
        user_info = response.json()
        self.user_id = user_info["id"]
        print(f"✅ User registered: {self.user_id}")
        
        # Upgrade to PRO
        upgrade_data = {"subscription_plan": "pro"}
        response = requests.post(f"{self.base_url}/upgrade-subscription/{self.user_id}", json=upgrade_data)
        if response.status_code == 200:
            print("✅ Upgraded to PRO")
        
        return True

    def evaluate_tech_card(self, content: str, dish_name: str) -> dict:
        """Evaluate tech card quality as a professional chef"""
        evaluation = {
            "dish_name": dish_name,
            "technical_score": 5,
            "culinary_score": 5,
            "practical_score": 5,
            "content_score": 5,
            "issues": []
        }
        
        # Technical correctness checks
        if not re.search(r'кбжу.*калории.*\d+', content, re.IGNORECASE):
            evaluation["technical_score"] -= 1
            evaluation["issues"].append("Отсутствует КБЖУ")
        
        # Check portion sizes
        portion_match = re.search(r'порция.*?(\d+)\s*г', content, re.IGNORECASE)
        if portion_match:
            portion_size = int(portion_match.group(1))
            if dish_name in ["Тартар из тунца"] and not (80 <= portion_size <= 150):
                evaluation["technical_score"] -= 1
                evaluation["issues"].append(f"Неправильная порция для закуски: {portion_size}г")
            elif dish_name not in ["Тартар из тунца"] and not (200 <= portion_size <= 300):
                evaluation["technical_score"] -= 1
                evaluation["issues"].append(f"Неправильная порция: {portion_size}г")
        
        # Culinary logic checks
        if dish_name == "Паста Карбонара" and "сливки" in content.lower():
            evaluation["culinary_score"] -= 2
            evaluation["issues"].append("Классическая Карбонара не содержит сливки!")
        
        if dish_name == "Том ям":
            required = ["лемонграсс", "галанга", "лайм"]
            missing = [ing for ing in required if ing not in content.lower()]
            if missing:
                evaluation["culinary_score"] -= 1
                evaluation["issues"].append(f"Отсутствуют ключевые ингредиенты: {', '.join(missing)}")
        
        # Practical checks
        if "совет" not in content.lower():
            evaluation["practical_score"] -= 1
            evaluation["issues"].append("Нет советов от шефа")
        
        if "хранение" not in content.lower():
            evaluation["practical_score"] -= 1
            evaluation["issues"].append("Нет информации о хранении")
        
        # Content quality checks
        required_sections = ["название", "ингредиенты", "рецепт", "время"]
        missing = [s for s in required_sections if s not in content.lower()]
        if missing:
            evaluation["content_score"] -= len(missing)
            evaluation["issues"].append(f"Отсутствуют разделы: {', '.join(missing)}")
        
        # Check for forbidden phrase
        if "стандартная ресторанная порция" in content:
            evaluation["technical_score"] -= 2
            evaluation["issues"].append("Найдена запрещенная фраза!")
        
        # Calculate overall rating
        avg_score = (evaluation["technical_score"] + evaluation["culinary_score"] + 
                    evaluation["practical_score"] + evaluation["content_score"]) / 4
        
        if avg_score >= 4.5:
            evaluation["rating"] = "⭐⭐⭐⭐⭐ Мишлен уровень"
        elif avg_score >= 3.5:
            evaluation["rating"] = "⭐⭐⭐⭐ Профессионально"
        elif avg_score >= 2.5:
            evaluation["rating"] = "⭐⭐⭐ Хорошо"
        elif avg_score >= 1.5:
            evaluation["rating"] = "⭐⭐ Средне"
        else:
            evaluation["rating"] = "⭐ Плохо"
        
        evaluation["overall_score"] = avg_score
        
        return evaluation

    def test_pro_ai_functions(self, tech_card: str, dish_name: str) -> dict:
        """Test PRO AI functions"""
        results = {}
        
        # Test sales script
        try:
            data = {"user_id": self.user_id, "tech_card": tech_card}
            response = requests.post(f"{self.base_url}/generate-sales-script", json=data)
            results["sales_script"] = response.status_code == 200
        except:
            results["sales_script"] = False
        
        # Test food pairing
        try:
            data = {"user_id": self.user_id, "tech_card": tech_card}
            response = requests.post(f"{self.base_url}/generate-food-pairing", json=data)
            results["food_pairing"] = response.status_code == 200
        except:
            results["food_pairing"] = False
        
        # Test photo tips
        try:
            data = {"user_id": self.user_id, "tech_card": tech_card}
            response = requests.post(f"{self.base_url}/generate-photo-tips", json=data)
            results["photo_tips"] = response.status_code == 200
        except:
            results["photo_tips"] = False
        
        return results

    def run_focused_audit(self):
        """Run focused audit on 5 key dishes"""
        print("🎯 RECEPTOR PRO - FOCUSED CHEF AUDIT")
        print("=" * 60)
        print("Профессиональная оценка качества техкарт")
        print("=" * 60)
        
        if not self.setup_pro_user():
            print("❌ Failed to setup user")
            return
        
        results = []
        
        for dish_info in self.test_dishes:
            dish_name = dish_info["name"]
            complexity = dish_info["complexity"]
            
            print(f"\n🍳 ТЕСТИРУЕМ: {dish_name} ({complexity.upper()})")
            print("-" * 50)
            
            # Generate tech card
            dish_data = {
                "dish_name": dish_name,
                "user_id": self.user_id
            }
            
            try:
                response = requests.post(f"{self.base_url}/generate-tech-card", json=dish_data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        tech_card = result["tech_card"]
                        print("✅ Техкарта сгенерирована")
                        
                        # Evaluate quality
                        evaluation = self.evaluate_tech_card(tech_card, dish_name)
                        print(f"📊 Оценка: {evaluation['rating']}")
                        
                        if evaluation["issues"]:
                            print("⚠️ Замечания:")
                            for issue in evaluation["issues"]:
                                print(f"   • {issue}")
                        
                        # Test PRO AI functions
                        pro_results = self.test_pro_ai_functions(tech_card, dish_name)
                        pro_success = sum(pro_results.values())
                        print(f"🤖 PRO AI функции: {pro_success}/3 работают")
                        
                        evaluation["pro_ai_results"] = pro_results
                        evaluation["tech_card_preview"] = tech_card[:300] + "..."
                        results.append(evaluation)
                        
                    else:
                        print(f"❌ Ошибка генерации: {result}")
                else:
                    print(f"❌ API ошибка: {response.status_code}")
            except Exception as e:
                print(f"❌ Исключение: {e}")
            
            time.sleep(1)  # Rate limiting
        
        # Generate summary report
        self.generate_summary_report(results)
        
        return results

    def generate_summary_report(self, results):
        """Generate final summary report"""
        print("\n" + "=" * 60)
        print("🎉 ИТОГОВЫЙ ОТЧЕТ ШЕФ-ПОВАРА")
        print("=" * 60)
        
        if not results:
            print("❌ Нет результатов для анализа")
            return
        
        # Calculate statistics
        total_score = sum(r["overall_score"] for r in results)
        avg_score = total_score / len(results)
        
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Протестировано блюд: {len(results)}/5")
        print(f"   Средний рейтинг: {avg_score:.1f}/5 звезд")
        
        # Individual results
        print(f"\n🍽️ РЕЗУЛЬТАТЫ ПО БЛЮДАМ:")
        for result in results:
            print(f"   • {result['dish_name']}: {result['rating']}")
            if result["issues"]:
                for issue in result["issues"][:2]:  # Show top 2 issues
                    print(f"     ⚠️ {issue}")
        
        # PRO AI summary
        pro_ai_stats = {"sales_script": 0, "food_pairing": 0, "photo_tips": 0}
        for result in results:
            if "pro_ai_results" in result:
                for func, success in result["pro_ai_results"].items():
                    if success:
                        pro_ai_stats[func] += 1
        
        print(f"\n🤖 PRO AI ФУНКЦИИ:")
        print(f"   Скрипты продаж: {pro_ai_stats['sales_script']}/{len(results)}")
        print(f"   Фудпейринг: {pro_ai_stats['food_pairing']}/{len(results)}")
        print(f"   Фото-советы: {pro_ai_stats['photo_tips']}/{len(results)}")
        
        # Final recommendation
        print(f"\n💡 ЗАКЛЮЧЕНИЕ ШЕФ-ПОВАРА:")
        if avg_score >= 4.0:
            print("   ✅ Отличное качество! Система готова для профессионального использования")
        elif avg_score >= 3.0:
            print("   ✅ Хорошее качество, подходит для большинства ресторанов")
        elif avg_score >= 2.0:
            print("   ⚠️ Среднее качество, нужны улучшения")
        else:
            print("   ❌ Низкое качество, требуется серьезная доработка")
        
        # Common issues
        all_issues = []
        for result in results:
            all_issues.extend(result["issues"])
        
        if all_issues:
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            print(f"\n🔧 ЧАСТЫЕ ПРОБЛЕМЫ:")
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"   • {issue} (встречается {count} раз)")
        
        print("\n" + "=" * 60)
        print("🎯 ФОКУСИРОВАННЫЙ АУДИТ ЗАВЕРШЕН")
        print("=" * 60)

def main():
    audit = FocusedChefAudit()
    results = audit.run_focused_audit()
    return results

if __name__ == "__main__":
    main()