"""
Извлечение цен и КБЖУ из базы знаний для обновления каталога
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge_base"


def extract_prices_from_knowledge_base() -> Dict[str, Dict]:
    """
    Извлекает цены из базы знаний (markdown файлы)
    
    Returns:
        Dict с ценами в формате: {name: {price, unit, category, source}}
    """
    prices = {}
    
    if not KNOWLEDGE_BASE_PATH.exists():
        return prices
    
    # Паттерны для поиска цен
    price_patterns = [
        # Формат: "название: 450₽/кг" или "название — 450₽/кг"
        re.compile(r'([А-Яа-яЁё\s]+?)[:—]\s*(\d+(?:\.\d+)?)\s*₽\s*/?\s*(кг|л|шт|г|мл)', re.IGNORECASE),
        # Формат: "450₽/кг название"
        re.compile(r'(\d+(?:\.\d+)?)\s*₽\s*/?\s*(кг|л|шт|г|мл)\s+([А-Яа-яЁё\s]+)', re.IGNORECASE),
        # Формат: "название: 450 руб/кг"
        re.compile(r'([А-Яа-яЁё\s]+?)[:—]\s*(\d+(?:\.\d+)?)\s*руб\s*/?\s*(кг|л|шт|г|мл)', re.IGNORECASE),
    ]
    
    # Ищем во всех markdown файлах
    for md_file in KNOWLEDGE_BASE_PATH.glob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Определяем категорию из имени файла
            category = "general"
            if "financial" in md_file.name or "roi" in md_file.name:
                category = "finance"
            elif "supplier" in md_file.name.lower():
                category = "supplier"
            
            # Ищем цены
            for pattern in price_patterns:
                matches = pattern.findall(content)
                for match in matches:
                    if len(match) == 3:
                        if match[0].isdigit() or '.' in match[0]:
                            # Формат: цена единица название
                            price = float(match[0])
                            unit = match[1].lower()
                            name = match[2].strip()
                        else:
                            # Формат: название цена единица
                            name = match[0].strip()
                            price = float(match[1])
                            unit = match[2].lower()
                        
                        # Нормализуем единицы
                        unit_map = {
                            'кг': 'kg', 'kg': 'kg',
                            'л': 'l', 'l': 'l', 'литр': 'l',
                            'г': 'g', 'g': 'g', 'грамм': 'g',
                            'мл': 'ml', 'ml': 'ml', 'миллилитр': 'ml',
                            'шт': 'pcs', 'pcs': 'pcs', 'штука': 'pcs'
                        }
                        unit = unit_map.get(unit, 'kg')
                        
                        # Нормализуем название
                        name_normalized = name.lower().strip()
                        
                        # Сохраняем цену (берем последнюю найденную, если дубликаты)
                        prices[name_normalized] = {
                            "name": name,
                            "price": price,
                            "unit": unit,
                            "category": category,
                            "source": f"knowledge_base_{md_file.stem}",
                            "extracted_date": datetime.now().isoformat()
                        }
        
        except Exception as e:
            print(f"Error processing {md_file.name}: {e}")
            continue
    
    return prices


def extract_nutrition_from_knowledge_base() -> Dict[str, Dict]:
    """
    Извлекает КБЖУ из базы знаний
    
    Returns:
        Dict с КБЖУ в формате: {name: {kcal, proteins_g, fats_g, carbs_g}}
    """
    nutrition = {}
    
    if not KNOWLEDGE_BASE_PATH.exists():
        return nutrition
    
    # Паттерны для поиска КБЖУ
    nutrition_patterns = [
        # Формат: "калории: 165 ккал, белки: 31г, жиры: 3.6г, углеводы: 0г"
        re.compile(r'калори[иы]?[:\s]+(\d+(?:\.\d+)?)\s*ккал', re.IGNORECASE),
        re.compile(r'белк[иы]?[:\s]+(\d+(?:\.\d+)?)\s*г', re.IGNORECASE),
        re.compile(r'жир[ыы]?[:\s]+(\d+(?:\.\d+)?)\s*г', re.IGNORECASE),
        re.compile(r'углевод[ыы]?[:\s]+(\d+(?:\.\d+)?)\s*г', re.IGNORECASE),
    ]
    
    # Ищем во всех markdown файлах
    for md_file in KNOWLEDGE_BASE_PATH.glob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ищем блоки с КБЖУ (обычно в таблицах или списках)
            # Ищем строки вида "название: калории X, белки Y..."
            kbju_blocks = re.findall(
                r'([А-Яа-яЁё\s]+?)[:—]\s*(?:калори[иы]?|ккал|КБЖУ).*?(\d+(?:\.\d+)?)\s*ккал.*?(\d+(?:\.\d+)?)\s*г.*?(\d+(?:\.\d+)?)\s*г.*?(\d+(?:\.\d+)?)\s*г',
                content,
                re.IGNORECASE | re.DOTALL
            )
            
            for block in kbju_blocks:
                if len(block) >= 5:
                    name = block[0].strip()
                    # Пытаемся извлечь значения
                    # Это упрощенный парсинг, можно улучшить
                    pass
        
        except Exception as e:
            print(f"Error processing nutrition from {md_file.name}: {e}")
            continue
    
    return nutrition


def merge_with_existing_catalog(
    extracted_prices: Dict[str, Dict],
    existing_price_catalog_path: Path,
    existing_nutrition_catalog_path: Path
) -> tuple[Dict, Dict]:
    """
    Объединяет извлеченные данные с существующими каталогами
    
    Returns:
        (updated_price_catalog, updated_nutrition_catalog)
    """
    # Загружаем существующие каталоги
    price_catalog = {}
    nutrition_catalog = {}
    
    if existing_price_catalog_path.exists():
        with open(existing_price_catalog_path, 'r', encoding='utf-8') as f:
            price_catalog = json.load(f)
    
    if existing_nutrition_catalog_path.exists():
        with open(existing_nutrition_catalog_path, 'r', encoding='utf-8') as f:
            nutrition_catalog = json.load(f)
    
    # Обновляем каталог цен
    if "ingredients" not in price_catalog:
        price_catalog["ingredients"] = {}
    
    # Добавляем новые цены из базы знаний
    for name_normalized, price_data in extracted_prices.items():
        category = price_data.get("category", "general")
        if category not in price_catalog["ingredients"]:
            price_catalog["ingredients"][category] = {}
        
        # Добавляем или обновляем цену
        price_catalog["ingredients"][category][price_data["name"]] = {
            "price": price_data["price"],
            "unit": price_data["unit"],
            "category": category,
            "source": price_data["source"],
            "updated_date": price_data["extracted_date"]
        }
    
    # Обновляем дату обновления каталога
    price_catalog["last_updated"] = datetime.now().isoformat()
    price_catalog["knowledge_base_sync"] = True
    
    return price_catalog, nutrition_catalog


if __name__ == "__main__":
    # Тестирование извлечения
    print("Extracting prices from knowledge base...")
    prices = extract_prices_from_knowledge_base()
    print(f"Found {len(prices)} prices")
    
    for name, data in list(prices.items())[:5]:
        print(f"  {data['name']}: {data['price']}₽/{data['unit']} (from {data['source']})")

