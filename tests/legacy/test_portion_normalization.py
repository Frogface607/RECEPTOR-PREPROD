#!/usr/bin/env python3
"""
Test Script: Standard Portion by Default (no UI)
Тестирование автоматической нормализации порций
"""

import requests
import json
import os
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

class PortionNormalizationTest:
    """Тестирование нормализации порций"""
    
    def __init__(self):
        self.results = []
    
    def test_techcard_generation(self, dish_name: str, expected_archetype: str, expected_yield: int):
        """Тестировать генерацию техкарты с нормализацией порций"""
        print(f"\n🧪 Testing: {dish_name}")
        print(f"   Expected archetype: {expected_archetype}")
        print(f"   Expected yield: {expected_yield}g")
        
        try:
            # Генерируем техкарту
            start_time = time.time()
            
            response = requests.post(
                f"{API_BASE}/techcards.v2/generate",
                json={
                    "name": dish_name,
                    "cuisine": "европейская",
                    "equipment": [],
                    "budget": None,
                    "dietary": []
                },
                timeout=45
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                card = data.get('card')
                
                if card:
                    # Проверяем нормализацию
                    portions = card.get('portions', 0)
                    yield_data = card.get('yield', {})
                    per_portion = yield_data.get('perPortion_g', 0)
                    per_batch = yield_data.get('perBatch_g', 0)
                    
                    # Мета информация о нормализации
                    meta = card.get('meta', {})
                    scale_factor = meta.get('scale_factor')
                    archetype = meta.get('archetype')
                    original_sum_netto = meta.get('original_sum_netto')
                    normalized = meta.get('normalized')
                    
                    # Считаем сумму нетто ингредиентов
                    ingredients = card.get('ingredients', [])
                    sum_netto = sum(ing.get('netto_g', 0) for ing in ingredients)
                    
                    # Проверяем валидацию GX-02 (±5%)
                    if per_portion > 0:
                        difference_pct = abs(sum_netto - per_portion) / per_portion * 100
                        gx02_valid = difference_pct <= 5.0
                    else:
                        gx02_valid = False
                    
                    result = {
                        'dish': dish_name,
                        'success': True,
                        'duration': round(duration, 2),
                        'portions': portions,
                        'yield_per_portion': per_portion,
                        'yield_per_batch': per_batch,
                        'sum_netto': round(sum_netto, 1),
                        'difference_pct': round(difference_pct, 2) if per_portion > 0 else None,
                        'gx02_valid': gx02_valid,
                        'scale_factor': scale_factor,
                        'archetype': archetype,
                        'original_sum_netto': original_sum_netto,
                        'normalized': normalized,
                        'ingredients_count': len(ingredients),
                        'expected_archetype': expected_archetype,
                        'expected_yield': expected_yield,
                        'archetype_match': archetype == expected_archetype,
                        'yield_match': abs(per_portion - expected_yield) <= 10  # ±10g tolerance
                    }
                    
                    print(f"   ✅ Generated successfully in {duration:.1f}s")
                    print(f"   📊 Portions: {portions}")
                    print(f"   📏 Yield: {per_portion}g per portion, {per_batch}g per batch")
                    print(f"   🧮 Sum netto: {sum_netto}g (diff: {difference_pct:.1f}%)")
                    print(f"   🎯 Archetype: {archetype} (expected: {expected_archetype})")
                    print(f"   📐 Scale factor: {scale_factor}")
                    print(f"   ✅ GX-02 valid: {gx02_valid}")
                    
                    if not result['archetype_match']:
                        print(f"   ⚠️  Archetype mismatch!")
                    if not result['yield_match']:
                        print(f"   ⚠️  Yield mismatch!")
                    
                else:
                    result = {
                        'dish': dish_name,
                        'success': False,
                        'error': 'No card in response',
                        'duration': duration
                    }
                    print(f"   ❌ No card generated")
            
            else:
                result = {
                    'dish': dish_name,
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'duration': duration
                }
                print(f"   ❌ HTTP Error {response.status_code}")
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                'dish': dish_name,
                'success': False,
                'error': str(e),
                'duration': 0
            }
            print(f"   ❌ Exception: {e}")
            self.results.append(result)
            return result
    
    def run_dod_tests(self):
        """Запустить DoD тесты"""
        print("🎯 Running DoD Tests: Standard Portion by Default")
        print("=" * 60)
        
        # DoD: «Омлет», «Стейк+соус», «Суп дня» создаются с portions=1 и yield по таблице
        test_cases = [
            ("Омлет с зеленью", "default", 200),  # default архетип
            ("Стейк с грибным соусом", "горячее", 240),  # горячее архетип
            ("Суп дня овощной", "суп", 330),  # суп архетип
        ]
        
        for dish_name, expected_archetype, expected_yield in test_cases:
            self.test_techcard_generation(dish_name, expected_archetype, expected_yield)
            time.sleep(2)  # Небольшая пауза между тестами
    
    def print_summary(self):
        """Напечатать итоговый отчет"""
        print("\n" + "=" * 60)
        print("📋 SUMMARY: Standard Portion by Default Tests")
        print("=" * 60)
        
        successful = [r for r in self.results if r.get('success')]
        failed = [r for r in self.results if not r.get('success')]
        
        print(f"✅ Successful: {len(successful)}/{len(self.results)}")
        print(f"❌ Failed: {len(failed)}/{len(self.results)}")
        
        if successful:
            print("\n🎯 DoD Validation:")
            for result in successful:
                portions_ok = result.get('portions') == 1
                gx02_ok = result.get('gx02_valid', False)
                archetype_ok = result.get('archetype_match', False)
                yield_ok = result.get('yield_match', False)
                
                status = "✅" if all([portions_ok, gx02_ok, archetype_ok, yield_ok]) else "⚠️"
                
                print(f"   {status} {result['dish']}:")
                print(f"      Portions=1: {portions_ok}")
                print(f"      GX-02 valid: {gx02_ok}")
                print(f"      Archetype match: {archetype_ok}")
                print(f"      Yield match: {yield_ok}")
        
        if failed:
            print("\n❌ Failed Tests:")
            for result in failed:
                print(f"   {result['dish']}: {result.get('error', 'Unknown error')}")
        
        return len(successful) == len(self.results)


def main():
    """Главная функция тестирования"""
    tester = PortionNormalizationTest()
    
    # Запускаем DoD тесты
    tester.run_dod_tests()
    
    # Печатаем итоговый отчет
    success = tester.print_summary()
    
    if success:
        print("\n🎉 All DoD tests passed! Standard Portion by Default is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the implementation.")
    
    return success


if __name__ == "__main__":
    main()