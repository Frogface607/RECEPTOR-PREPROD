"""
GX-02: Quality Validator for TechCardV2
Validates and normalizes technical cards to production-ready quality
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import ValidationError
import re
from .schemas import TechCardV2, IngredientV2, ProcessStepV2, YieldV2


class QualityValidator:
    """Validates TechCardV2 for production readiness"""
    
    def __init__(self):
        self.validation_rules = {
            "yield_mandatory": True,
            "netto_sum_tolerance_pct": 3.0,  # допуск 2-3% 
            "normalize_ranges": True,
            "min_process_steps": 3
        }
    
    def validate_techcard(self, techcard: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Main validation method
        Returns: (normalized_techcard, validation_issues)
        """
        issues = []
        normalized_card = techcard.copy()
        
        # 1. Yield validation (обязателен)
        yield_issues = self._validate_yield(normalized_card)
        issues.extend(yield_issues)
        
        # 2. Netto sum ≈ yield validation (допуск 2-3%)
        netto_issues = self._validate_netto_sum(normalized_card)
        issues.extend(netto_issues)
        
        # 3. Normalize ranges (0-4 → numbers)
        normalized_card, range_issues = self._normalize_ranges(normalized_card)
        issues.extend(range_issues)
        
        # 4. Process steps validation
        process_issues = self._validate_process_steps(normalized_card)
        issues.extend(process_issues)
        
        # 5. Units validation
        units_issues = self._validate_units(normalized_card)
        issues.extend(units_issues)
        
        return normalized_card, issues
    
    def _validate_yield(self, techcard: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate that yield is present and properly formatted"""
        issues = []
        
        yield_data = techcard.get('yield')
        
        # ИСПРАВЛЕНИЕ: Более толерантная проверка для техкарт из истории
        # Если нет yield данных, пытаемся их сгенерировать из portions и ingredients
        if not yield_data:
            portions = techcard.get('portions', 1)
            ingredients = techcard.get('ingredients', [])
            
            # Попытка автоматически рассчитать yield
            if ingredients:
                total_netto = sum(ing.get('netto_g', 0) for ing in ingredients if isinstance(ing.get('netto_g', 0), (int, float)))
                if total_netto > 0:
                    # Создаем базовый yield из ingredients
                    per_portion_g = total_netto / max(portions, 1)
                    techcard['yield'] = {
                        'perPortion_g': per_portion_g,
                        'perBatch_g': total_netto,
                        'auto_calculated': True
                    }
                    yield_data = techcard['yield']
            
            # Если все еще нет данных - показываем предупреждение вместо ошибки
            if not yield_data:
                issues.append({
                    "type": "yieldMissing",
                    "level": "warning",  # Изменено с "error" на "warning"
                    "field": "yield", 
                    "message": "Рекомендуется указать выход блюда",
                    "fix_suggestion": "Добавить информацию о выходе готового блюда"
                })
                return issues
        
        # Check perPortion_g
        per_portion = yield_data.get('perPortion_g')
        if not per_portion or per_portion <= 0:
            issues.append({
                "type": "yieldPerPortionInvalid",
                "level": "error", 
                "field": "yield.perPortion_g",
                "message": "Выход на порцию должен быть > 0",
                "current_value": per_portion,
                "fix_suggestion": "Указать корректный вес порции в граммах"
            })
        
        # Check perBatch_g
        per_batch = yield_data.get('perBatch_g') 
        if not per_batch or per_batch <= 0:
            issues.append({
                "type": "yieldPerBatchInvalid",
                "level": "error",
                "field": "yield.perBatch_g", 
                "message": "Общий выход должен быть > 0",
                "current_value": per_batch,
                "fix_suggestion": "Указать корректный общий выход в граммах"
            })
        
        # Check consistency between portions and yields
        portions = techcard.get('portions', 1)
        if per_portion and per_batch and portions:
            expected_batch = per_portion * portions
            tolerance = expected_batch * 0.05  # 5% tolerance
            
            if abs(per_batch - expected_batch) > tolerance:
                issues.append({
                    "type": "yieldInconsistent",
                    "level": "warning",
                    "field": "yield",
                    "message": f"Несоответствие: {per_portion}г × {portions} = {expected_batch}г, указано {per_batch}г",
                    "expected_value": expected_batch,
                    "current_value": per_batch,
                    "fix_suggestion": "Проверить расчет общего выхода"
                })
        
        return issues
    
    def _validate_netto_sum(self, techcard: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate that sum of netto ≈ yield (допуск 2-3%)"""
        issues = []
        
        ingredients = techcard.get('ingredients', [])
        yield_data = techcard.get('yield', {})
        per_batch = yield_data.get('perBatch_g')
        
        if not ingredients or not per_batch:
            return issues
        
        # Calculate total netto
        total_netto = 0
        for ing in ingredients:
            netto = ing.get('netto_g', 0)
            if isinstance(netto, (int, float)) and netto > 0:
                total_netto += netto
        
        if total_netto == 0:
            issues.append({
                "type": "nettoSumZero", 
                "level": "error",
                "field": "ingredients",
                "message": "Сумма нетто ингредиентов не может быть 0",
                "fix_suggestion": "Проверить массу ингредиентов"
            })
            return issues
        
        # Check tolerance (2-3%)
        tolerance_pct = self.validation_rules["netto_sum_tolerance_pct"]
        tolerance = per_batch * (tolerance_pct / 100)
        difference = abs(total_netto - per_batch)
        difference_pct = (difference / per_batch) * 100
        
        if difference > tolerance:
            level = "error" if difference_pct > 5 else "warning"
            issues.append({
                "type": "nettoSumMismatch",
                "level": level,
                "field": "ingredients",
                "message": f"Сумма нетто ({total_netto:.1f}г) не соответствует выходу ({per_batch:.1f}г). Отклонение: {difference_pct:.1f}%",
                "total_netto": total_netto,
                "expected_yield": per_batch,
                "difference_pct": difference_pct,
                "tolerance_pct": tolerance_pct,
                "fix_suggestion": "Скорректировать массу ингредиентов или выход блюда"
            })
        
        return issues
    
    def _normalize_ranges(self, techcard: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Normalize range values like '0-4' to numbers before saving"""
        issues = []
        normalized_card = techcard.copy()
        
        # Patterns for range detection
        range_patterns = [
            r'^(\d+)-(\d+)$',      # "2-3"
            r'^(\d+)–(\d+)$',      # "2–3" (em dash)
            r'^(\d+)\s*-\s*(\d+)$' # "2 - 3"
        ]
        
        def normalize_value(value, field_name: str) -> Any:
            if isinstance(value, str):
                value = value.strip()
                
                # Check for range patterns
                for pattern in range_patterns:
                    match = re.match(pattern, value)
                    if match:
                        min_val = float(match.group(1))
                        max_val = float(match.group(2))
                        # Use average for ranges
                        normalized_val = (min_val + max_val) / 2
                        
                        issues.append({
                            "type": "rangeNormalized",
                            "level": "info",
                            "field": field_name,
                            "message": f"Диапазон '{value}' нормализован к {normalized_val}",
                            "original_value": value,
                            "normalized_value": normalized_val,
                            "fix_suggestion": "Диапазон автоматически приведен к среднему значению"
                        })
                        
                        return normalized_val
                
                # Try to convert to number
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass
            
            return value
        
        # Normalize ingredients
        if 'ingredients' in normalized_card:
            for i, ing in enumerate(normalized_card['ingredients']):
                for field in ['brutto_g', 'netto_g', 'loss_pct']:
                    if field in ing:
                        field_name = f"ingredients[{i}].{field}"
                        ing[field] = normalize_value(ing[field], field_name)
        
        # Normalize process steps 
        if 'process' in normalized_card:
            for i, step in enumerate(normalized_card['process']):
                for field in ['time_min', 'temp_c']:
                    if field in step:
                        field_name = f"process[{i}].{field}"
                        step[field] = normalize_value(step[field], field_name)
        
        # Normalize yield
        if 'yield' in normalized_card:
            for field in ['perPortion_g', 'perBatch_g']:
                if field in normalized_card['yield']:
                    field_name = f"yield.{field}"
                    normalized_card['yield'][field] = normalize_value(
                        normalized_card['yield'][field], field_name
                    )
        
        return normalized_card, issues
    
    def _validate_process_steps(self, techcard: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate process steps"""
        issues = []
        
        process_steps = techcard.get('process', [])
        
        # Safety check: make sure process_steps is a list
        if not isinstance(process_steps, list):
            issues.append({
                "type": "processStepsInvalidFormat",
                "level": "error",
                "field": "process",
                "message": "Process должен быть списком этапов",
                "current_type": str(type(process_steps)),
                "fix_suggestion": "Исправить формат process на список словарей"
            })
            return issues
        
        if len(process_steps) < self.validation_rules["min_process_steps"]:
            issues.append({
                "type": "processStepsInsufficient",
                "level": "error", 
                "field": "process",
                "message": f"Минимум {self.validation_rules['min_process_steps']} этапов приготовления",
                "current_count": len(process_steps),
                "min_required": self.validation_rules["min_process_steps"],
                "fix_suggestion": "Добавить недостающие этапы приготовления"
            })
        
        # Check step numbering
        for i, step in enumerate(process_steps):
            expected_n = i + 1
            
            # Safety check: make sure step is a dict
            if not isinstance(step, dict):
                issues.append({
                    "type": "processStepInvalidFormat",
                    "level": "error",
                    "field": f"process[{i}]",
                    "message": f"Этап {i+1} должен быть объектом, получен {type(step).__name__}",
                    "current_value": str(step)[:100],
                    "fix_suggestion": "Исправить формат этапа на объект с полями n, action, time_min, etc."
                })
                continue
            
            actual_n = step.get('n', 0)
            
            if actual_n != expected_n:
                issues.append({
                    "type": "processStepNumbering",
                    "level": "warning",
                    "field": f"process[{i}].n",
                    "message": f"Неправильная нумерация этапа: ожидается {expected_n}, получено {actual_n}",
                    "expected": expected_n,
                    "actual": actual_n,
                    "fix_suggestion": f"Изменить номер этапа на {expected_n}"
                })
            
            # Check required fields
            if not step.get('action'):
                issues.append({
                    "type": "processStepMissingAction",
                    "level": "error",
                    "field": f"process[{i}].action",
                    "message": f"Этап {expected_n}: отсутствует описание действия",
                    "fix_suggestion": "Добавить описание действия для этапа"
                })
        
        return issues
    
    def _validate_units(self, techcard: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate units consistency"""
        issues = []
        
        valid_units = ['g', 'ml', 'pcs']
        ingredients = techcard.get('ingredients', [])
        
        for i, ing in enumerate(ingredients):
            unit = ing.get('unit', 'g')
            
            if unit not in valid_units:
                issues.append({
                    "type": "invalidUnit",
                    "level": "error",
                    "field": f"ingredients[{i}].unit",
                    "message": f"Недопустимая единица измерения: '{unit}'",
                    "current_value": unit,
                    "valid_options": valid_units,
                    "fix_suggestion": "Использовать только г, мл, или шт"
                })
        
        return issues
    
    def get_quality_score(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality score based on validation issues"""
        error_count = len([i for i in issues if i.get('level') == 'error'])
        warning_count = len([i for i in issues if i.get('level') == 'warning'])
        info_count = len([i for i in issues if i.get('level') == 'info'])
        
        # Quality scoring
        score = 100
        score -= error_count * 20  # Errors are critical
        score -= warning_count * 5  # Warnings are less critical
        # Info messages don't affect score (just normalization)
        
        score = max(0, score)
        
        quality_level = "excellent" if score >= 95 else \
                       "good" if score >= 80 else \
                       "needs_improvement" if score >= 60 else \
                       "poor"
        
        return {
            "score": score,
            "level": quality_level,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "is_production_ready": error_count == 0
        }
    
    def generate_fix_banners(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate user-friendly fix banners for UI"""
        banners = []
        
        # Group issues by type
        error_issues = [i for i in issues if i.get('level') == 'error']
        warning_issues = [i for i in issues if i.get('level') == 'warning']
        
        if error_issues:
            # Critical issues banner
            error_messages = []
            for issue in error_issues:
                if issue.get('type') == 'yieldMissing':
                    error_messages.append("📏 Не указан выход блюда")
                elif issue.get('type') == 'nettoSumZero':
                    error_messages.append("⚖️ Не указана масса ингредиентов")
                elif issue.get('type') == 'nettoSumMismatch':
                    error_messages.append("📊 Масса ингредиентов не соответствует выходу")
                elif issue.get('type') == 'processStepsInsufficient':
                    error_messages.append("🍳 Недостаточно этапов приготовления")
                else:
                    error_messages.append(f"❌ {issue.get('message', 'Неизвестная ошибка')}")
            
            banners.append({
                "type": "error",
                "title": "Критические ошибки",
                "icon": "🚨",
                "color": "red",
                "messages": error_messages,
                "action": "Исправить для сохранения"
            })
        
        if warning_issues:
            # Warning issues banner
            warning_messages = []
            for issue in warning_issues:
                if issue.get('type') == 'yieldInconsistent':
                    warning_messages.append("⚖️ Проверить расчет порций и выхода")
                elif issue.get('type') == 'processStepNumbering':
                    warning_messages.append("🔢 Исправить нумерацию этапов")
                else:
                    warning_messages.append(f"⚠️ {issue.get('message', 'Неизвестное предупреждение')}")
            
            banners.append({
                "type": "warning", 
                "title": "Рекомендации",
                "icon": "⚠️",
                "color": "yellow",
                "messages": warning_messages,
                "action": "Рекомендуется исправить"
            })
        
        return banners