"""
iiko XLSX Export для ТТК (технологических карт)
Экспорт TechCardV2 в формат, совместимый с «Импорт справочника (технологические карты)» iikoWeb
"""

from __future__ import annotations
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re
import os

# Используем openpyxl для работы с Excel
try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    # Fallback если openpyxl не установлен
    Workbook = None
    load_workbook = None

from receptor_agent.techcards_v2.schemas import TechCardV2

def get_product_code_from_rms(sku_id: str, rms_service=None) -> str:
    """
    Feature A: Получить числовой код продукта из iiko RMS вместо GUID
    
    Args:
        sku_id: GUID продукта из iiko
        rms_service: Сервис для работы с iiko RMS (опционально)
    
    Returns:
        Числовой код продукта или исходный sku_id если код не найден
    """
    if not sku_id or not rms_service:
        return sku_id or ""
    
    try:
        # Поиск в коллекции products
        product = rms_service.products.find_one({"_id": sku_id})
        if product and product.get('article'):
            # Возвращаем article (числовой код) с сохранением ведущих нулей
            return str(product['article']).zfill(5)  # Минимум 5 цифр с ведущими нулями
        
        # Поиск в коллекции pricing если нет в products
        pricing = rms_service.pricing.find_one({"skuId": sku_id})
        if pricing and pricing.get('article'):
            return str(pricing['article']).zfill(5)
            
    except Exception as e:
        print(f"Error getting product code for {sku_id}: {e}")
    
    return sku_id or ""

# Путь к шаблону iiko
TEMPLATE_PATH = Path(__file__).parent.parent / "data" / "iiko_templates" / "ttk.xlsx"

# Маппинг заголовков iiko (поддержка синонимов)
IIKO_HEADERS = {
    'dish_code': ['Артикул блюда', 'Код блюда'],
    'dish_name': ['Наименование блюда', 'Название блюда'],
    'product_code': ['Артикул продукта', 'Код продукта'],
    'product_name': ['Наименование продукта', 'Название продукта'],
    'brutto': ['Брутто', 'Брутто, г'],
    'loss_pct': ['Потери, %', 'Потери'],
    'netto': ['Нетто', 'Нетто, г'],
    'unit': ['Ед.', 'Единица', 'Ед. изм.'],
    'output_qty': ['Выход готового продукта', 'Выход'],
    'norm': ['Норма закладки'],
    'write_off_method': ['Метод списания'],
    'technology': ['Технология приготовления', 'Технология']
}

def generate_dish_slug(title: str) -> str:
    """Генерирует slug из названия блюда"""
    # Убираем специальные символы и заменяем пробелы на подчеркивания
    slug = re.sub(r'[^\w\s-]', '', title).strip()
    slug = re.sub(r'[-\s]+', '_', slug)
    return slug.upper()[:20]  # Ограничиваем длину

def normalize_unit_to_grams(value: float, unit: str, ingredient_name: str = "") -> float:
    """
    Конвертирует единицы в граммы для iiko
    """
    unit = unit.lower().strip()
    
    # Уже граммы
    if unit in ['г', 'g', 'gram', 'грамм']:
        return value
    
    # Килограммы -> граммы
    elif unit in ['кг', 'kg', 'kilogram', 'килограмм']:
        return value * 1000
    
    # Миллилитры -> граммы (принимаем плотность = 1 для большинства жидкостей)
    elif unit in ['мл', 'ml', 'milliliter', 'миллилитр']:
        # Для масла плотность ≈ 0.9
        if 'масло' in ingredient_name.lower():
            return value * 0.9
        # Для воды и большинства жидкостей плотность = 1
        return value
    
    # Литры -> граммы
    elif unit in ['л', 'l', 'liter', 'литр']:
        return value * 1000  # Принимаем плотность = 1
    
    # Штуки -> граммы (средние веса)
    elif unit in ['шт', 'pcs', 'piece', 'штука']:
        # Стандартные веса продуктов
        piece_weights = {
            'яйцо': 50,      # 50г за яйцо
            'луковица': 150,  # 150г за луковицу
            'морковь': 100,   # 100г за морковь
            'картофель': 120, # 120г за картофелину
            'помидор': 180,   # 180г за помидор
            'огурец': 150,    # 150г за огурец
            'яблоко': 180,    # 180г за яблоко
            'лимон': 130      # 130г за лимон
        }
        
        # Пытаемся найти подходящий вес
        for product, weight in piece_weights.items():
            if product in ingredient_name.lower():
                return value * weight
        
        # Если не нашли - используем средний вес 100г
        return value * 100
    
    # По умолчанию возвращаем как есть
    return value

def generate_technology_text(process_steps) -> str:
    """
    Генерирует текст технологии из шагов процесса
    Формат: #{n}. {action} [t={temp_c}°C] [{time_min} мин] [{equipment}]
    """
    if not process_steps:
        return "Технология приготовления не указана"
    
    technology_lines = []
    
    for step in process_steps:
        # Handle both dict and object types
        if hasattr(step, 'n'):
            step_num = step.n
            action = getattr(step, 'action', 'Действие не указано')
            temp_c = getattr(step, 'temp_c', None)
            time_min = getattr(step, 'time_min', None)
            equipment = getattr(step, 'equipment', None)
        else:
            step_num = step.get('n', len(technology_lines) + 1)
            action = step.get('action', 'Действие не указано')
            temp_c = step.get('temp_c')
            time_min = step.get('time_min')
            equipment = step.get('equipment')
        
        # Базовая строка
        line = f"#{step_num}. {action}"
        
        # Добавляем температуру если есть
        if temp_c:
            line += f" [t={temp_c}°C]"
        
        # Добавляем время если есть
        if time_min:
            line += f" [{time_min} мин]"
        
        # Добавляем оборудование если есть
        if equipment:
            if isinstance(equipment, list):
                equipment_str = ', '.join(equipment)
            else:
                equipment_str = str(equipment)
            line += f" [{equipment_str}]"
        
        technology_lines.append(line)
    
    # Объединяем в один текст, ограничиваем 1000 символами
    technology_text = '\n'.join(technology_lines)
    if len(technology_text) > 1000:
        technology_text = technology_text[:997] + "..."
    
    return technology_text

def create_iiko_ttk_xlsx(card: TechCardV2, 
                        export_options: Dict[str, Any] = None) -> Tuple[BytesIO, List[Dict[str, Any]]]:
    """
    Создать iiko XLSX файл для импорта технологических карт
    WITH iiko Import Reliability — Product Codes & Dish Skeletons
    
    Args:
        card: Техкарта в формате TechCardV2
        export_options: Опции экспорта:
            - use_product_codes: bool = True - использовать коды товаров вместо GUID
            - dish_codes_mapping: Dict[str, str] - маппинг блюд к кодам
    
    Returns:
        (BytesIO buffer, issues list)
    """
    if not export_options:
        export_options = {}
    
    # Feature A: Product Code toggle (по умолчанию включен)
    use_product_codes = export_options.get('use_product_codes', True)
    dish_codes_mapping = export_options.get('dish_codes_mapping', {})
    rms_service = export_options.get('rms_service')  # Для получения кодов продуктов
    
    if not Workbook:
        raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")
    
    issues = []
    
    # Пытаемся загрузить шаблон, если не получается - создаем новый
    wb = None
    if TEMPLATE_PATH.exists():
        try:
            wb = load_workbook(TEMPLATE_PATH)
            ws = wb.active
        except Exception as e:
            print(f"Failed to load template {TEMPLATE_PATH}: {e}")
            wb = None
    
    if wb is None:
        # Создаем новую книгу с правильными заголовками
        wb = Workbook()
        ws = wb.active
        ws.title = "ТТК"
        
        # Заголовки в правильном порядке
        headers = [
            'Артикул блюда',
            'Наименование блюда', 
            'Артикул продукта',
            'Наименование продукта',
            'Брутто',
            'Потери, %',
            'Нетто',
            'Ед.',
            'Выход готового продукта',
            'Норма закладки',
            'Метод списания',
            'Технология приготовления'
        ]
        
        # Записываем заголовки
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
    
    else:
        ws = wb.active
    
    # Генерируем данные для экспорта
    # Feature A: Use dish_codes_mapping if provided
    dish_code = dish_codes_mapping.get(card.meta.title)
    if not dish_code:
        dish_code = card.meta.get('dish_code') if hasattr(card.meta, 'dish_code') else None
    if not dish_code:
        dish_slug = generate_dish_slug(card.meta.title)
        dish_code = f"DISH_{dish_slug}"
    
    dish_name = card.meta.title
    
    # Рассчитываем выход готового продукта
    output_qty = getattr(card.yield_, 'perBatch_g', 0) if hasattr(card, 'yield_') and card.yield_ else 0
    if not output_qty and hasattr(card, 'yield_') and card.yield_:
        # Если нет perBatch_g, рассчитываем из порций
        portions = getattr(card, 'portions', 1)
        per_portion = getattr(card.yield_, 'perPortion_g', 0)
        output_qty = portions * per_portion if per_portion else 0
    
    # Генерируем технологию приготовления
    technology_text = ""
    if hasattr(card, 'process') and card.process:
        technology_text = generate_technology_text(card.process)
    
    # Заполняем данные по ингредиентам
    row = 2  # Начинаем со второй строки (первая - заголовки)
    
    for ingredient in card.ingredients:
        # Артикул продукта
        # Feature A: Product Code toggle
        if use_product_codes:
            product_code = ingredient.skuId
            if not product_code:
                # Генерируем артикул если отсутствует
                ingredient_slug = generate_dish_slug(ingredient.name)
                product_code = f"GENERATED_{ingredient_slug}"
                issues.append({
                    "type": "noSku",
                    "name": ingredient.name,
                    "hint": f"Generated SKU: {product_code}",
                    "dish": card.meta.title
                })
        else:
            # Используем GUID вместо кодов товаров
            product_code = getattr(ingredient, 'guid', ingredient.skuId or f"GUID_{generate_dish_slug(ingredient.name)}")
        
        # Обработка подрецептов
        if hasattr(ingredient, 'subRecipe') and ingredient.subRecipe:
            # Для подрецептов используем их dish_code как артикул продукта
            sub_recipe_code = getattr(ingredient.subRecipe, 'dish_code', None)
            if sub_recipe_code and use_product_codes:
                product_code = sub_recipe_code
            elif not use_product_codes:
                # Используем GUID для подрецептов
                product_code = getattr(ingredient.subRecipe, 'guid', sub_recipe_code or f"SUBGUID_{generate_dish_slug(ingredient.name)}")
            else:
                issues.append({
                    "type": "subRecipeNoCode",
                    "name": ingredient.name,
                    "hint": "Sub-recipe missing dish_code",
                    "dish": card.meta.title
                })
        
        # Конвертируем единицы в граммы
        brutto_g = round(normalize_unit_to_grams(
            getattr(ingredient, 'brutto_g', 0), 
            getattr(ingredient, 'unit', 'g'), 
            ingredient.name
        ), 1)
        
        netto_g = round(normalize_unit_to_grams(
            getattr(ingredient, 'netto_g', 0), 
            getattr(ingredient, 'unit', 'g'), 
            ingredient.name
        ), 1)
        
        loss_pct = round(getattr(ingredient, 'loss_pct', 0), 1)
        
        # Заполняем строку
        row_data = [
            dish_code,                    # Артикул блюда
            dish_name,                    # Наименование блюда
            product_code,                 # Артикул продукта
            ingredient.name,              # Наименование продукта
            brutto_g,                     # Брутто
            loss_pct,                     # Потери, %
            netto_g,                      # Нетто
            'г',                          # Ед. (всегда граммы)
            round(output_qty, 1),         # Выход готового продукта
            1,                            # Норма закладки
            1,                            # Метод списания
            technology_text if row == 2 else ""  # Технология (только для первой строки)
        ]
        
        # Записываем данные в ячейки
        for col, value in enumerate(row_data, 1):
            ws.cell(row=row, column=col).value = value
        
        row += 1
    
    # Автоширина колонок
    for col in range(1, 13):  # 12 колонок
        column_letter = get_column_letter(col)
        max_length = 0
        for row_cells in ws[f"{column_letter}1:{column_letter}{row-1}"]:
            for cell in row_cells:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
        adjusted_width = min(max_length + 2, 50)  # Максимум 50 символов
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Сохраняем в BytesIO
    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    
    return excel_buffer, issues


def export_techcard_to_iiko_xlsx(card: TechCardV2, export_options: Dict[str, Any] = None) -> bytes:
    """
    Wrapper function for round-trip tests compatibility
    Returns just the Excel bytes
    """
    buffer, issues = create_iiko_ttk_xlsx(card, export_options)
    return buffer.getvalue()