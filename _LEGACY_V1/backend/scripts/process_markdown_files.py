"""
Обработка готовых Markdown файлов от ChatGPT
Добавляет метаданные, теги, индексацию для RAG системы
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import re

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

# Путь к базе знаний
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "data" / "knowledge_base"
KNOWLEDGE_BASE_PATH.mkdir(parents=True, exist_ok=True)

# Маппинг категорий к правильным именам файлов
CATEGORY_FILENAME_MAP = {
    "haccp": "receptor_haccp_sanpin.md",
    "ingredients_prices": "receptor_ingredients_prices.md",
    "techcards": "receptor_techcards.md",
    "hr": "receptor_hr_management.md",
    "finance": "receptor_financial_roi.md",
    "marketing": "receptor_smm_marketing.md",
    "iiko": "receptor_iiko_technical.md",
    "regional": "receptor_regional_specs.md",
    "trends": "receptor_trends_2025.md"
}

# Теги для категорий
CATEGORY_TAGS = {
    "haccp": ["#HACCP", "#СанПиН", "#Нормативы", "#Роспотребнадзор", "#Безопасность"],
    "ingredients_prices": ["#Цены", "#Ингредиенты", "#Поставщики", "#Регионы"],
    "techcards": ["#Техкарты", "#Рецепты", "#Блюда", "#Кухня"],
    "hr": ["#HR", "#Персонал", "#Обучение", "#Мотивация", "#KPI"],
    "finance": ["#Финансы", "#Ценообразование", "#Налоги", "#ROI", "#Себестоимость"],
    "marketing": ["#Маркетинг", "#SMM", "#Продвижение", "#Реклама"],
    "iiko": ["#iiko", "#Автоматизация", "#Интеграции", "#API"],
    "regional": ["#Регионы", "#Москва", "#СПб", "#Федеральные_округа"],
    "trends": ["#Тренды", "#Инновации", "#2025", "#Прогнозы"]
}


def detect_category_from_content(content: str) -> str:
    """Определить категорию из содержимого файла"""
    content_lower = content.lower()
    
    # Ключевые слова для каждой категории
    category_keywords = {
        "haccp": ["haccp", "санпин", "роспотребнадзор", "норматив", "санитарн", "безопасность пищевых"],
        "ingredients_prices": ["цена", "ингредиент", "поставщик", "рубль", "стоимость", "опт"],
        "techcards": ["техкарт", "рецепт", "блюдо", "ингредиент", "выход", "технология приготовления"],
        "hr": ["персонал", "сотрудник", "обучение", "мотивация", "kpi", "должностная инструкция"],
        "finance": ["финанс", "цена", "себестоимость", "наценка", "налог", "roi", "прибыль"],
        "marketing": ["маркетинг", "smm", "продвижение", "реклама", "соцсет", "блогер"],
        "iiko": ["iiko", "автоматизация", "api", "интеграция", "система управления"],
        "regional": ["регион", "москва", "спб", "федеральный округ", "город"],
        "trends": ["тренд", "инновация", "прогноз", "2025", "будущее", "развитие"]
    }
    
    scores = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        scores[category] = score
    
    # Возвращаем категорию с наибольшим счетом
    if scores:
        return max(scores, key=scores.get)
    return "general"


def extract_category_from_metadata(content: str) -> str:
    """Извлечь категорию из метаданных файла"""
    # Ищем строку **Категория:** в начале файла
    match = re.search(r'\*\*Категория:\*\*\s*(\w+)', content, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def add_metadata_and_tags(filepath: Path, category: str = None) -> str:
    """Обработать Markdown файл: добавить метаданные, теги, обновить структуру"""
    
    # Читаем файл
    content = filepath.read_text(encoding='utf-8')
    
    # Определяем категорию
    if not category:
        category = extract_category_from_metadata(content) or detect_category_from_content(content)
    
    # Получаем правильное имя файла
    target_filename = CATEGORY_FILENAME_MAP.get(category, f"receptor_{category}.md")
    target_filepath = KNOWLEDGE_BASE_PATH / target_filename
    
    # Извлекаем заголовок (первая строка с #)
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Документ"
    
    # Формируем улучшенный контент
    processed_content = f"""# {title}

**Категория:** {category}
**Дата обработки:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Источник:** Deep Research (GPT-5)
**Версия:** 2.0 (обновлено 2025-12-07)

---

"""
    
    # Убираем старые метаданные если есть
    lines = content.split('\n')
    skip_metadata = False
    for i, line in enumerate(lines):
        # Пропускаем старые метаданные
        if line.strip().startswith('**Категория:**') or line.strip().startswith('**Дата'):
            skip_metadata = True
            continue
        if skip_metadata and (line.strip() == '' or line.startswith('---')):
            skip_metadata = False
            if line.startswith('---'):
                continue
        if not skip_metadata:
            processed_content += line + '\n'
    
    # Добавляем теги в конец
    tags = CATEGORY_TAGS.get(category, [])
    if tags:
        processed_content += f"\n\n---\n\n**ТЕГИ:** {' '.join(tags)}\n"
    
    # Добавляем информацию для RAG
    processed_content += f"""
**RAG МЕТАДАННЫЕ:**
- Категория для поиска: `{category}`
- Дата актуализации: 2025-12-07
- Готово для индексации: ✅

*Документ обработан и подготовлен для RECEPTOR Knowledge Base*
"""
    
    # Сохраняем в правильный файл
    # Если файл существует, добавляем к нему с разделителем
    if target_filepath.exists():
        existing_content = target_filepath.read_text(encoding='utf-8')
        # Добавляем новый контент с разделителем
        final_content = existing_content + "\n\n" + "="*80 + "\n\n" + processed_content
    else:
        final_content = processed_content
    
    target_filepath.write_text(final_content, encoding='utf-8')
    
    return str(target_filepath), category


def process_file(input_filepath: str, category: str = None):
    """Обработать один файл"""
    filepath = Path(input_filepath)
    
    if not filepath.exists():
        print(f"❌ Файл не найден: {filepath}")
        return False
    
    print(f"📄 Обработка файла: {filepath.name}")
    
    try:
        output_path, detected_category = add_metadata_and_tags(filepath, category)
        print(f"✅ Обработано!")
        print(f"   Категория: {detected_category}")
        print(f"   Сохранено в: {Path(output_path).name}")
        return True
    except Exception as e:
        print(f"❌ Ошибка обработки: {str(e)}")
        return False


def process_directory(directory: str):
    """Обработать все .md файлы в директории"""
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"❌ Директория не найдена: {dir_path}")
        return
    
    md_files = list(dir_path.glob("*.md"))
    
    if not md_files:
        print(f"⚠️  Markdown файлы не найдены в {dir_path}")
        return
    
    print(f"📁 Найдено файлов: {len(md_files)}\n")
    
    for i, filepath in enumerate(md_files, 1):
        print(f"[{i}/{len(md_files)}] ", end="")
        process_file(str(filepath))
        print()


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Обработка Markdown файлов для RECEPTOR Knowledge Base")
    parser.add_argument(
        "input",
        type=str,
        help="Путь к файлу .md или директории с файлами"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Категория (haccp, ingredients_prices, techcards, hr, finance, marketing, iiko, regional, trends)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        process_file(str(input_path), args.category)
    elif input_path.is_dir():
        process_directory(str(input_path))
    else:
        print(f"❌ Путь не найден: {input_path}")


if __name__ == "__main__":
    main()

