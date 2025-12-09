"""
Operational Rounding v1 (Export & Kitchen View)

Модуль для операционного округления количеств ингредиентов в техкартах.
Цель: убрать «пыльные» количества типа 4.3г в печати и при списаниях iiko,
сохранив точные значения для расчётов и аналитики.

Применяется ТОЛЬКО при экспорте в iiko XLSX и PDF/Kitchen View.
НЕ изменяет хранимые данные в базе.
"""

import logging
import math
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from copy import deepcopy

logger = logging.getLogger(__name__)


@dataclass
class RoundingStep:
    """Шаг округления для определенного диапазона"""
    min_value: float
    max_value: float
    step: float
    unit_type: str  # 'g', 'ml', 'pcs'


class OperationalRoundingRules:
    """
    Правила операционного округления v1
    
    Правила округления (шаги):
    • Сухие (г): < 10г → шаг 0.5г, 10–100г → шаг 1г, > 100г → шаг 5г
    • Жидкости (мл): < 50мл → шаг 1мл, 50–250мл → шаг 5мл, > 250мл → шаг 10мл  
    • Штучные (шт): если SKU допускает дроби → шаг 0.5шт, иначе → 1шт или перевод в граммы
    """
    
    # Правила для сухих продуктов (граммы)
    DRY_RULES = [
        RoundingStep(0, 10, 0.5, 'g'),      # < 10г → шаг 0.5г
        RoundingStep(10, 100, 1.0, 'g'),    # 10–100г → шаг 1г
        RoundingStep(100, float('inf'), 5.0, 'g')  # > 100г → шаг 5г
    ]
    
    # Правила для жидкостей (миллилитры)
    LIQUID_RULES = [
        RoundingStep(0, 50, 1.0, 'ml'),     # < 50мл → шаг 1мл
        RoundingStep(50, 250, 5.0, 'ml'),   # 50–250мл → шаг 5мл
        RoundingStep(250, float('inf'), 10.0, 'ml')  # > 250мл → шаг 10мл
    ]
    
    # Правила для штучных товаров
    PIECE_RULES = [
        RoundingStep(0, float('inf'), 0.5, 'pcs')  # По умолчанию 0.5шт если допускает дроби
    ]
    
    # Нейтральные ингредиенты для балансировки массы (приоритет по порядку)
    NEUTRAL_INGREDIENTS = [
        'вода', 'молоко', 'сливки', 'бульон', 'сок',  # Жидкости
        'гарнир', 'пюре', 'рис', 'картофель', 'макароны',  # Гарниры
        'лук', 'морковь', 'капуста',  # Овощи
        'мука', 'крахмал', 'сахар'  # Основные компоненты
    ]
    
    @classmethod
    def get_rounding_step(cls, value: float, unit: str, 
                         ingredient_name: str = '') -> float:
        """
        Получить шаг округления для значения и единицы измерения
        
        Args:
            value: Значение для округления
            unit: Единица измерения ('g', 'ml', 'pcs', и т.д.)
            ingredient_name: Название ингредиента (для определения типа)
            
        Returns:
            Шаг округления
        """
        # Нормализация единиц измерения
        unit_lower = unit.lower().strip()
        
        # Определение правил по единице измерения
        if unit_lower in ['g', 'г', 'gram', 'грамм', 'kg', 'кг']:
            # Сухие продукты в граммах
            rules = cls.DRY_RULES
            # Конвертируем кг в граммы для правил
            check_value = value * 1000 if unit_lower in ['kg', 'кг'] else value
            
        elif unit_lower in ['ml', 'мл', 'l', 'л', 'liter', 'литр']:
            # Жидкости в миллилитрах
            rules = cls.LIQUID_RULES
            # Конвертируем литры в мл для правил
            check_value = value * 1000 if unit_lower in ['l', 'л', 'liter', 'литр'] else value
            
        elif unit_lower in ['pcs', 'шт', 'штука', 'piece', 'pieces']:
            # Штучные товары
            rules = cls.PIECE_RULES
            check_value = value
            
        else:
            # Неизвестная единица - используем правила для граммов по умолчанию
            logger.warning(f"Unknown unit '{unit}' for ingredient '{ingredient_name}', using gram rules")
            rules = cls.DRY_RULES
            check_value = value
        
        # Находим подходящее правило
        for rule in rules:
            if rule.min_value <= check_value < rule.max_value:
                return rule.step
        
        # Fallback - последнее правило
        return rules[-1].step if rules else 1.0
    
    @classmethod
    def is_neutral_ingredient(cls, ingredient_name: str) -> bool:
        """
        Проверить, является ли ингредиент нейтральным для балансировки
        """
        name_lower = ingredient_name.lower().strip()
        
        for neutral in cls.NEUTRAL_INGREDIENTS:
            if neutral in name_lower:
                return True
        return False


class OperationalRounder:
    """
    Класс для операционного округления техкарт
    """
    
    def __init__(self, ruleset_version: str = "v1"):
        self.ruleset_version = ruleset_version
        self.rules = OperationalRoundingRules()
    
    def round_value_to_step(self, value: float, step: float) -> float:
        """
        Округлить значение к ближайшему шагу (симметричное округление)
        
        Args:
            value: Исходное значение
            step: Шаг округления
            
        Returns:
            Округленное значение
        """
        if step <= 0:
            return value
        
        # Симметричное округление к ближайшему шагу
        rounded = round(value / step) * step
        
        # Округляем до разумного количества знаков после запятой
        if step >= 1:
            return round(rounded, 0)
        elif step >= 0.1:
            return round(rounded, 1)
        else:
            return round(rounded, 2)
    
    def round_techcard_ingredients(self, techcard: Dict[str, Any], 
                                 target_yield: Optional[float] = None) -> Dict[str, Any]:
        """
        Применить операционное округление к ингредиентам техкарты
        
        Args:
            techcard: Исходная техкарта (НЕ изменяется)
            target_yield: Целевой выход (если None, берется из yield.perPortion_g)
            
        Returns:
            {
                'rounded_techcard': Dict,  # Техкарта с округленными ингредиентами
                'rounding_metadata': Dict  # Метаданные округления для аудита
            }
        """
        # Создаем глубокую копию чтобы не изменять исходную техкарту
        rounded_card = deepcopy(techcard)
        
        # Определяем целевой выход
        if target_yield is None:
            yield_data = techcard.get('yield_', techcard.get('yield', {}))
            target_yield = yield_data.get('perPortion_g', 200.0)
        
        ingredients = rounded_card.get('ingredients', [])
        if not ingredients:
            return {
                'rounded_techcard': rounded_card,
                'rounding_metadata': {
                    'enabled': False,
                    'reason': 'No ingredients found'
                }
            }
        
        # Метаданные округления
        rounding_items = []
        original_sum_netto = 0.0
        rounded_sum_netto = 0.0
        
        # Шаг 1: Округляем все ингредиенты
        for ingredient in ingredients:
            # Поддерживаем оба варианта названий полей
            original_netto = ingredient.get('netto_g') or ingredient.get('netto', 0)
            original_brutto = ingredient.get('brutto_g') or ingredient.get('brutto', 0)
            unit = ingredient.get('unit', 'g')
            name = ingredient.get('name', 'Unknown')
            
            if original_netto <= 0:
                continue
            
            # Получаем шаг округления
            step = self.rules.get_rounding_step(original_netto, unit, name)
            
            # Округляем нетто и брутто
            rounded_netto = self.round_value_to_step(original_netto, step)
            
            # Для брутто сохраняем пропорцию loss_pct
            if original_netto > 0:
                loss_pct = ingredient.get('loss_pct', 0)
                if loss_pct > 0:
                    rounded_brutto = rounded_netto / (1 - loss_pct / 100)
                else:
                    rounded_brutto = rounded_netto
                rounded_brutto = self.round_value_to_step(rounded_brutto, step)
            else:
                rounded_brutto = original_brutto
            
            # Обновляем значения в техкарте
            if 'netto_g' in ingredient:
                ingredient['netto_g'] = rounded_netto
            else:
                ingredient['netto'] = rounded_netto
                
            if 'brutto_g' in ingredient:
                ingredient['brutto_g'] = rounded_brutto
            else:
                ingredient['brutto'] = rounded_brutto
            
            # Сохраняем метаданные если были изменения
            if abs(original_netto - rounded_netto) > 0.001:
                rounding_items.append({
                    'name': name,
                    'unit': unit,
                    'from': round(original_netto, 3),
                    'to': round(rounded_netto, 3),
                    'step': step
                })
            
            original_sum_netto += original_netto
            rounded_sum_netto += rounded_netto
        
        # Шаг 2: Балансировка массы
        delta_g = target_yield - rounded_sum_netto
        balanced_by = []
        
        # Если дельта значительная (> 2% от целевого выхода), пытаемся балансировать
        tolerance_pct = abs(delta_g) / target_yield * 100 if target_yield > 0 else 0
        
        if tolerance_pct > 2.0 and abs(delta_g) > 0.1:
            balanced_by = self._balance_mass(rounded_card['ingredients'], delta_g, target_yield)
            
            # Пересчитываем сумму после балансировки
            rounded_sum_netto = sum(
                (ing.get('netto_g') or ing.get('netto', 0)) 
                for ing in rounded_card['ingredients']
            )
        
        # Финальная проверка GX-02 (должно быть ≤ 5%)
        final_delta_pct = abs(rounded_sum_netto - target_yield) / target_yield * 100 if target_yield > 0 else 0
        
        # Формируем метаданные
        rounding_metadata = {
            'enabled': True,
            'ruleset': self.ruleset_version,
            'items': rounding_items,
            'original_sum_netto': round(original_sum_netto, 1),
            'rounded_sum_netto': round(rounded_sum_netto, 1),
            'target_yield': round(target_yield, 1),
            'delta_g': round(target_yield - rounded_sum_netto, 2),
            'tolerance_pct': round(final_delta_pct, 2),
            'balanced_by': balanced_by,
            'gx02_compliant': final_delta_pct <= 5.0
        }
        
        logger.info(f"Operational rounding applied: {len(rounding_items)} items rounded, "
                   f"delta: {rounding_metadata['delta_g']}g ({rounding_metadata['tolerance_pct']:.1f}%)")
        
        return {
            'rounded_techcard': rounded_card,
            'rounding_metadata': rounding_metadata
        }
    
    def _balance_mass(self, ingredients: List[Dict[str, Any]], 
                     delta_g: float, target_yield: float) -> List[str]:
        """
        Балансировка массы через нейтральные ингредиенты
        
        Args:
            ingredients: Список ингредиентов для корректировки
            delta_g: Дельта в граммах (+ нужно добавить, - нужно убрать)
            target_yield: Целевой выход
            
        Returns:
            Список названий ингредиентов, которые были скорректированы
        """
        balanced_by = []
        
        # Находим нейтральные ингредиенты, отсортированные по приоритету
        neutral_candidates = []
        other_candidates = []
        
        for ingredient in ingredients:
            name = ingredient.get('name', '')
            netto = ingredient.get('netto_g') or ingredient.get('netto', 0)
            
            if netto <= 0:
                continue
                
            if self.rules.is_neutral_ingredient(name):
                neutral_candidates.append(ingredient)
            else:
                other_candidates.append(ingredient)
        
        # Приоритет: сначала нейтральные, потом основные ингредиенты
        candidates = neutral_candidates + other_candidates
        
        # Балансируем через 1-2 ингредиента с наибольшим количеством
        candidates.sort(key=lambda x: -(x.get('netto_g') or x.get('netto', 0)))
        
        remaining_delta = delta_g
        used_candidates = 0
        max_candidates = 2  # Максимум 2 ингредиента для балансировки
        
        for ingredient in candidates:
            if abs(remaining_delta) < 0.1 or used_candidates >= max_candidates:
                break
                
            name = ingredient.get('name', '')
            current_netto = ingredient.get('netto_g') or ingredient.get('netto', 0)
            unit = ingredient.get('unit', 'g')
            
            # Получаем шаг округления для этого ингредиента
            step = self.rules.get_rounding_step(current_netto, unit, name)
            
            # Рассчитываем новое значение
            target_netto = current_netto + remaining_delta
            
            # Ограничиваем изменение разумными пределами (не более 50% от исходного)
            max_change = current_netto * 0.5
            if abs(remaining_delta) > max_change:
                target_netto = current_netto + (max_change if remaining_delta > 0 else -max_change)
            
            # Округляем к ближайшему шагу
            new_netto = self.round_value_to_step(target_netto, step)
            
            # Проверяем что новое значение разумное (> 0)
            if new_netto <= 0:
                continue
            
            # Применяем изменение
            actual_delta = new_netto - current_netto
            
            if 'netto_g' in ingredient:
                ingredient['netto_g'] = new_netto
            else:
                ingredient['netto'] = new_netto
            
            # Корректируем брутто с сохранением loss_pct
            loss_pct = ingredient.get('loss_pct', 0)
            if loss_pct > 0:
                new_brutto = new_netto / (1 - loss_pct / 100)
            else:
                new_brutto = new_netto
            
            new_brutto = self.round_value_to_step(new_brutto, step)
            
            if 'brutto_g' in ingredient:
                ingredient['brutto_g'] = new_brutto
            else:
                ingredient['brutto'] = new_brutto
            
            remaining_delta -= actual_delta
            balanced_by.append(name)
            used_candidates += 1
            
            logger.debug(f"Balanced {name}: {current_netto:.1f}g → {new_netto:.1f}g "
                        f"(delta: {actual_delta:+.1f}g)")
        
        return balanced_by


# Глобальный экземпляр округлителя
_operational_rounder: Optional[OperationalRounder] = None

def get_operational_rounder(ruleset_version: str = "v1") -> OperationalRounder:
    """Получить глобальный экземпляр операционного округлителя"""
    global _operational_rounder
    
    if _operational_rounder is None or _operational_rounder.ruleset_version != ruleset_version:
        _operational_rounder = OperationalRounder(ruleset_version)
    
    return _operational_rounder