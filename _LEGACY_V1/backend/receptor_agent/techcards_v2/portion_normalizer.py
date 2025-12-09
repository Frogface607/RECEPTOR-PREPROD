"""
Standard Portion by Default (no UI)
Автоматическая нормализация ТК на 1 порцию с адекватным выходом
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from ..techcards_v2.schemas import TechCardV2

logger = logging.getLogger(__name__)


class PortionNormalizer:
    """Автоматическая нормализация порций после генерации ТК"""
    
    # Мини-таблица таргетов (жёстко в коде)
    TARGET_YIELDS = {
        # Архетип (эвристика по словам) -> (target_yield, unit)
        'суп': (330, 'мл'),
        'паста': (300, 'г'),
        'горячее': (240, 'г'),
        'салат': (200, 'г'),
        'гарнир': (150, 'г'),
        'соус': (40, 'г'),
        'десерт': (140, 'г'),
        'default': (200, 'г')  # дефолт
    }
    
    # Ключевые слова для определения архетипов
    ARCHETYPE_KEYWORDS = {
        'суп': [
            'суп', 'бульон', 'крем-суп', 'рамен', 'борщ', 'солянка', 'щи', 
            'гаспачо', 'минестроне', 'бисквит', 'похлёбка', 'юшка'
        ],
        'паста': [
            'паста', 'ризотто', 'лапша', 'гречка', 'спагетти', 'пенне', 
            'карбонара', 'болоньезе', 'феттучине', 'тальятелле', 'рамен'
        ],
        'горячее': [
            'горячее', 'стейк', 'рыба', 'курица', 'котлета', 'шницель', 
            'эскалоп', 'филе', 'жаркое', 'рагу', 'мясо', 'говядина', 
            'свинина', 'баранина', 'индейка', 'утка', 'телятина'
        ],
        'салат': [
            'салат', 'микс', 'цезарь', 'греческий', 'оливье', 'винегрет',
            'капрезе', 'руккола', 'айсберг'
        ],
        'гарнир': [
            'гарнир', 'пюре', 'рис', 'картофель', 'овощи', 'брокколи',
            'спаржа', 'кус-кус', 'булгур', 'киноа'
        ],
        'соус': [
            'соус', 'дип', 'крем', 'майонез', 'кетчуп', 'тартар', 
            'голландский', 'бешамель', 'песто', 'чимичурри'
        ],
        'десерт': [
            'десерт', 'чизкейк', 'брауни', 'тирамису', 'панакота', 
            'мусс', 'суфле', 'пудинг', 'торт', 'пирожное'
        ]
    }
    
    def normalize_techcard(self, techcard: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применить нормализацию порций к техкарте
        
        Args:
            techcard: TechCard V2 данные
            
        Returns:
            Нормализованная техкарта с portions=1 и масштабированными ингредиентами
        """
        try:
            logger.info("Starting portion normalization")
            
            # Создаем копию для безопасности
            normalized_card = techcard.copy()
            
            # Определяем архетип блюда
            archetype = self._detect_archetype(normalized_card)
            target_yield, target_unit = self.TARGET_YIELDS.get(archetype, self.TARGET_YIELDS['default'])
            
            logger.info(f"Detected archetype: {archetype}, target: {target_yield} {target_unit}")
            
            # Считаем текущую сумму нетто
            ingredients = normalized_card.get('ingredients', [])
            sum_netto = self._calculate_sum_netto(ingredients)
            
            # Рассчитываем коэффициент масштабирования
            scale_factor = target_yield / max(sum_netto, 1e-6)
            
            logger.info(f"Sum netto: {sum_netto}g, scale factor: {scale_factor:.3f}")
            
            # Масштабируем ингредиенты
            normalized_ingredients = self._scale_ingredients(ingredients, scale_factor)
            
            # Обновляем структуру техкарты
            normalized_card['portions'] = 1
            normalized_card['ingredients'] = normalized_ingredients
            
            # Обновляем yield (используем правильную схему TechCardV2)
            if 'yield_' not in normalized_card:
                normalized_card['yield_'] = {}
            
            normalized_card['yield_']['perPortion_g'] = float(target_yield)
            normalized_card['yield_']['perBatch_g'] = float(target_yield)  # т.к. 1 порция
            
            # Записываем мета-информацию для аудита
            if 'meta' not in normalized_card:
                normalized_card['meta'] = {}
            
            normalized_card['meta']['scale_factor'] = round(scale_factor, 3)
            normalized_card['meta']['archetype'] = archetype
            normalized_card['meta']['original_sum_netto'] = round(sum_netto, 1)
            normalized_card['meta']['normalized'] = True
            
            # Финальная верификация
            final_sum_netto = self._calculate_sum_netto(normalized_ingredients)
            logger.info(f"Final sum netto: {final_sum_netto}g vs target: {target_yield}g")
            
            return normalized_card
            
        except Exception as e:
            logger.error(f"Portion normalization error: {e}")
            # Возвращаем оригинальную карту в случае ошибки
            return techcard
    
    def _detect_archetype(self, techcard: Dict[str, Any]) -> str:
        """
        Определить архетип блюда по ключевым словам в названии/тегах/процессе
        """
        # Собираем текст для анализа
        text_sources = []
        
        # Название блюда
        title = techcard.get('meta', {}).get('title', '')
        if title:
            text_sources.append(title.lower())
        
        # Теги
        tags = techcard.get('meta', {}).get('tags', [])
        if tags and isinstance(tags, list):
            text_sources.extend([tag.lower() for tag in tags if isinstance(tag, str)])
        
        # Описание процесса
        process = techcard.get('process', {})
        if isinstance(process, dict):
            process_steps = process.get('steps', [])
            if isinstance(process_steps, list):
                for step in process_steps:
                    if isinstance(step, dict):
                        action = step.get('action', '')
                        if action:
                            text_sources.append(action.lower())
        
        # Объединяем весь текст
        combined_text = ' '.join(text_sources)
        
        logger.info(f"Analyzing text for archetype: {combined_text[:100]}...")
        
        # Ищем совпадения по архетипам (в порядке приоритета)
        for archetype, keywords in self.ARCHETYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    logger.info(f"Found keyword '{keyword}' for archetype '{archetype}'")
                    return archetype
        
        # Если ничего не найдено, возвращаем дефолт
        logger.info("No archetype detected, using default")
        return 'default'
    
    def _calculate_sum_netto(self, ingredients: List[Dict[str, Any]]) -> float:
        """Посчитать сумму нетто по всем ингредиентам"""
        sum_netto = 0.0
        
        for ingredient in ingredients:
            # Поддерживаем оба варианта названий полей
            netto = ingredient.get('netto_g') or ingredient.get('netto', 0)
            if isinstance(netto, (int, float)) and netto > 0:
                sum_netto += netto
        
        return sum_netto
    
    def _scale_ingredients(self, ingredients: List[Dict[str, Any]], scale_factor: float) -> List[Dict[str, Any]]:
        """
        Масштабировать brutto/netto всех ингредиентов с сохранением loss_pct
        """
        scaled_ingredients = []
        
        for ingredient in ingredients:
            scaled_ingredient = ingredient.copy()
            
            # Масштабируем brutto (поддерживаем оба варианта названий)
            if 'brutto_g' in scaled_ingredient and isinstance(scaled_ingredient['brutto_g'], (int, float)):
                scaled_ingredient['brutto_g'] = round(scaled_ingredient['brutto_g'] * scale_factor, 1)
            elif 'brutto' in scaled_ingredient and isinstance(scaled_ingredient['brutto'], (int, float)):
                scaled_ingredient['brutto'] = round(scaled_ingredient['brutto'] * scale_factor, 1)
            
            # Масштабируем netto (поддерживаем оба варианта названий)
            if 'netto_g' in scaled_ingredient and isinstance(scaled_ingredient['netto_g'], (int, float)):
                scaled_ingredient['netto_g'] = round(scaled_ingredient['netto_g'] * scale_factor, 1)
            elif 'netto' in scaled_ingredient and isinstance(scaled_ingredient['netto'], (int, float)):
                scaled_ingredient['netto'] = round(scaled_ingredient['netto'] * scale_factor, 1)
            
            # ВАЖНО: обновляем единицу измерения на граммы, так как все значения теперь в граммах
            scaled_ingredient['unit'] = 'g'
            
            # loss_pct остается неизменным (как и требуется)
            
            scaled_ingredients.append(scaled_ingredient)
        
        return scaled_ingredients
    
    def validate_normalization(self, techcard: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверить что нормализация прошла корректно
        Должно соответствовать правилу GX-02: |Σнетто − yield| ≤ 5%
        """
        try:
            ingredients = techcard.get('ingredients', [])
            sum_netto = self._calculate_sum_netto(ingredients)
            
            # Поддерживаем оба варианта: прямой yield и алиас yield_
            yield_data = techcard.get('yield_') or techcard.get('yield', {})
            target_yield = yield_data.get('perPortion_g', 0) if isinstance(yield_data, dict) else 0
            
            if target_yield > 0:
                difference_pct = abs(sum_netto - target_yield) / target_yield * 100
                is_valid = difference_pct <= 5.0
                
                return {
                    'valid': is_valid,
                    'sum_netto': round(sum_netto, 1),
                    'target_yield': target_yield,
                    'difference_pct': round(difference_pct, 2),
                    'scale_factor': techcard.get('meta', {}).get('scale_factor'),
                    'archetype': techcard.get('meta', {}).get('archetype')
                }
            
            return {'valid': False, 'error': 'No target yield found'}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}


# Глобальный экземпляр нормализатора
_portion_normalizer: Optional[PortionNormalizer] = None

def get_portion_normalizer() -> PortionNormalizer:
    """Получить глобальный экземпляр нормализатора порций"""
    global _portion_normalizer
    
    if _portion_normalizer is None:
        _portion_normalizer = PortionNormalizer()
    
    return _portion_normalizer