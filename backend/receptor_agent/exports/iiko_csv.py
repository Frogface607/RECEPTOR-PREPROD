from __future__ import annotations
from io import StringIO, BytesIO
import csv
import zipfile
from typing import List, Tuple, Dict, Any
from receptor_agent.techcards_v2.schemas import TechCardV2

# Минимальный CSV под ручной перенос в iiko Office:
# одна строка на ингредиент блюда, с полями блюда/выхода.
def techcard_to_csv(card: TechCardV2) -> str:
    buf = StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["dish_name","category","ingredient","uom","gross_g","net_g","loss_pct","portion_g","portions"])
    for ing in card.ingredients:
        w.writerow([
            card.meta.title,
            "",  # category не используется в V2
            ing.canonical_id or ing.name,
            ing.unit,
            f"{ing.brutto_g:.2f}",
            f"{ing.netto_g:.2f}",
            f"{ing.loss_pct:.2f}",
            card.yield_.perPortion_g,
            1,  # portions не используется в V2
        ])
    return buf.getvalue()

def generate_iiko_import_csv_zip(cards: List[TechCardV2]) -> Tuple[BytesIO, List[Dict[str, Any]]]:
    """
    Генерирует ZIP архив с products.csv и recipes.csv для импорта в iiko
    
    Args:
        cards: Список техкарт для экспорта
        
    Returns:
        Tuple[BytesIO, List[Dict]]: ZIP файл в памяти и список issues
    """
    issues = []
    
    # Собираем все уникальные ингредиенты для products.csv
    all_ingredients = {}
    dish_codes_used = set()
    
    for card in cards:
        # Генерируем уникальный код блюда
        dish_code = generate_dish_code(card.meta.title, dish_codes_used)
        dish_codes_used.add(dish_code)
        
        for ingredient in card.ingredients:
            # Проверяем наличие SKU
            sku = ingredient.skuId or ingredient.canonical_id
            if not sku:
                sku = f"GENERATED_{ingredient.name.replace(' ', '_').upper()}"
                issues.append({
                    "type": "noSku",
                    "name": ingredient.name,
                    "hint": f"Generated SKU: {sku}",
                    "dish": card.meta.title
                })
            
            # Добавляем ингредиент в общий список (избегаем дубликатов)
            if sku not in all_ingredients:
                all_ingredients[sku] = {
                    "sku": sku,
                    "name": ingredient.name,
                    "unit": normalize_unit_for_iiko(ingredient.unit),
                    "price_per_unit": get_ingredient_price(ingredient, card),
                    "currency": "RUB",
                    "vat_pct": "20.00",
                    "category": determine_ingredient_category(ingredient.name)
                }
    
    # Создаем products.csv с UTF-8 BOM
    products_csv = generate_products_csv(all_ingredients)
    
    # Создаем recipes.csv с UTF-8 BOM
    recipes_csv = generate_recipes_csv(cards, dish_codes_used, issues)
    
    # Создаем ZIP архив
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('products.csv', products_csv)
        zip_file.writestr('recipes.csv', recipes_csv)
    
    zip_buffer.seek(0)
    return zip_buffer, issues

def generate_products_csv(ingredients: Dict[str, Dict]) -> bytes:
    """Генерирует products.csv с UTF-8 BOM"""
    output = StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Заголовки
    writer.writerow(['sku', 'name', 'unit', 'price_per_unit', 'currency', 'vat_pct', 'category'])
    
    # Сортируем по SKU для стабильности
    for sku in sorted(ingredients.keys()):
        ing = ingredients[sku]
        writer.writerow([
            ing['sku'],
            ing['name'], 
            ing['unit'],
            f"{ing['price_per_unit']:.2f}",
            ing['currency'],
            ing['vat_pct'],
            ing['category']
        ])
    
    # Добавляем UTF-8 BOM
    csv_content = output.getvalue()
    return '\ufeff'.encode('utf-8') + csv_content.encode('utf-8')

def generate_recipes_csv(cards: List[TechCardV2], dish_codes_used: set, issues: List[Dict]) -> bytes:
    """Генерирует recipes.csv с UTF-8 BOM"""
    output = StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Заголовки  
    writer.writerow(['dish_code', 'dish_name', 'output_qty', 'output_unit', 'ingredient_sku', 'qty_net', 'loss_pct', 'unit'])
    
    dish_codes_used_list = list(dish_codes_used)
    for idx, card in enumerate(cards):
        dish_code = dish_codes_used_list[idx] if idx < len(dish_codes_used_list) else f"DISH_{idx+1}"
        
        # Рассчитываем выход блюда
        output_qty = card.yield_.perBatch_g if hasattr(card.yield_, 'perBatch_g') else card.yield_.perPortion_g * card.portions
        output_unit = 'g'
        
        for ingredient in card.ingredients:
            # SKU ингредиента
            sku = ingredient.skuId or ingredient.canonical_id
            if not sku:
                sku = f"GENERATED_{ingredient.name.replace(' ', '_').upper()}"
            
            writer.writerow([
                dish_code,
                card.meta.title,
                f"{output_qty:.2f}",
                output_unit,
                sku,
                f"{ingredient.netto_g:.2f}",
                f"{ingredient.loss_pct:.2f}",
                normalize_unit_for_iiko(ingredient.unit)
            ])
    
    # Добавляем UTF-8 BOM
    csv_content = output.getvalue()
    return '\ufeff'.encode('utf-8') + csv_content.encode('utf-8')

def generate_dish_code(dish_name: str, used_codes: set) -> str:
    """Генерирует уникальный код блюда для iiko"""
    # Базовый код из названия
    base_code = dish_name.replace(' ', '_').replace(',', '').replace('.', '').upper()[:20]
    
    # Если код уже использован, добавляем номер
    code = base_code
    counter = 1
    while code in used_codes:
        code = f"{base_code}_{counter}"
        counter += 1
    
    return code

def normalize_unit_for_iiko(unit: str) -> str:
    """Нормализует единицы измерения для iiko"""
    unit = unit.lower().strip()
    
    # Маппинг на стандартные единицы iiko
    unit_mapping = {
        'г': 'г',
        'g': 'г', 
        'gram': 'г',
        'грамм': 'г',
        'кг': 'кг',
        'kg': 'кг',
        'kilogram': 'кг',
        'килограмм': 'кг',
        'мл': 'мл',
        'ml': 'мл',
        'milliliter': 'мл',
        'миллилитр': 'мл',
        'л': 'л',
        'l': 'л',
        'liter': 'л',
        'литр': 'л',
        'шт': 'шт',
        'pcs': 'шт',
        'piece': 'шт',
        'штука': 'шт'
    }
    
    return unit_mapping.get(unit, 'г')  # По умолчанию граммы

def get_ingredient_price(ingredient, card: TechCardV2) -> float:
    """Получает цену ингредиента из техкарты или устанавливает по умолчанию"""
    # Пытаемся получить цену из cost калькуляций карты
    if hasattr(card, 'cost') and card.cost and hasattr(card.cost, 'rawCost'):
        # Примерная цена за грамм из общей стоимости
        total_netto = sum(ing.netto_g for ing in card.ingredients)
        if total_netto > 0 and card.cost.rawCost:
            avg_price_per_g = card.cost.rawCost / total_netto
            return avg_price_per_g * ingredient.netto_g / ingredient.netto_g  # Цена за единицу
        
    # Fallback цены по категориям
    fallback_prices = {
        'мясо': 500.0,     # RUB/kg
        'рыба': 400.0,     # RUB/kg  
        'овощи': 100.0,    # RUB/kg
        'молочные': 150.0, # RUB/kg
        'зерновые': 80.0,  # RUB/kg
        'специи': 1000.0,  # RUB/kg
        'масло': 200.0,    # RUB/kg
    }
    
    # Простое определение категории по названию
    name_lower = ingredient.name.lower()
    for category, price in fallback_prices.items():
        if any(word in name_lower for word in get_category_keywords(category)):
            return price / 1000  # Конвертируем в цену за грамм
    
    return 0.15  # Дефолт 150 RUB/kg = 0.15 RUB/g

def determine_ingredient_category(ingredient_name: str) -> str:
    """Определяет категорию ингредиента для iiko"""
    name_lower = ingredient_name.lower()
    
    categories = {
        'Мясо': ['говядина', 'свинина', 'баранина', 'телятина', 'мясо'],
        'Птица': ['курица', 'индейка', 'утка', 'гусь', 'филе'],  
        'Рыба': ['рыба', 'треска', 'лосось', 'судак', 'семга', 'тунец'],
        'Овощи': ['лук', 'морковь', 'картофель', 'капуста', 'томат', 'огурец', 'перец'],
        'Молочные': ['молоко', 'сметана', 'творог', 'сыр', 'кефир', 'йогурт'],
        'Зерновые': ['рис', 'гречка', 'пшено', 'овес', 'мука', 'хлеб'],
        'Специи': ['соль', 'перец', 'специи', 'приправа', 'лавровый', 'чеснок'],
        'Масло': ['масло', 'жир'],
        'Напитки': ['сок', 'вода', 'чай', 'кофе', 'напиток']
    }
    
    for category, keywords in categories.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
            
    return 'Прочее'

def get_category_keywords(category: str) -> List[str]:
    """Возвращает ключевые слова для определения категории"""
    keywords_map = {
        'мясо': ['говядина', 'свинина', 'баранина', 'телятина', 'мясо'],
        'рыба': ['рыба', 'треска', 'лосось', 'судак', 'семга'],
        'овощи': ['лук', 'морковь', 'картофель', 'капуста', 'томат'],
        'молочные': ['молоко', 'сметана', 'творог', 'сыр'],
        'зерновые': ['рис', 'гречка', 'мука', 'хлеб'],
        'специи': ['соль', 'перец', 'специи', 'приправа'],
        'масло': ['масло', 'жир']
    }
    return keywords_map.get(category, [])