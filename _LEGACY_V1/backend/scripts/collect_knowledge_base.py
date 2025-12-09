"""
Автоматический сбор базы знаний через Perplexity (OpenRouter API)
Собирает актуальную информацию о ресторанном бизнесе в России (2025)
"""
import os
import sys
import asyncio
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json
import time

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Путь к базе знаний
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "data" / "knowledge_base"
KNOWLEDGE_BASE_PATH.mkdir(parents=True, exist_ok=True)

# OpenRouter API
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Попробуем разные модели Perplexity
PERPLEXITY_MODELS = [
    "perplexity/llama-3.1-sonar-large-128k-online",
    "perplexity/llama-3.1-sonar-huge-128k-online",
    "perplexity/llama-3.1-sonar-small-128k-online",
    "perplexity/llama-3-sonar-large-32k-online",
    "perplexity/llama-3.1-sonar-large-128k",
    "perplexity/llama-3.1-sonar-huge-128k"
]

PERPLEXITY_MODEL = PERPLEXITY_MODELS[0]  # По умолчанию первая

# Промпты для каждой категории
PERPLEXITY_PROMPTS = {
    "haccp": """Проведи глубокое исследование актуальных нормативов HACCP и СанПиН для ресторанного бизнеса в России на 2025 год.

ТРЕБОВАНИЯ:
1. Только актуальная информация 2025 года
2. Фокус на российское законодательство (Роспотребнадзор, Минздрав)
3. Структурированный ответ в Markdown формате

ИНФОРМАЦИЯ ДЛЯ СБОРА:
- Система HACCP: требования, внедрение, документооборот
- СанПиН 2.3/2.4 для общественного питания (актуальная редакция 2025)
- Требования к хранению продуктов (температурные режимы, сроки)
- Санитарные требования к персоналу и помещениям
- Документооборот и отчетность для Роспотребнадзора
- Штрафы за нарушения (актуальные суммы 2025)
- Практические чек-листы и шаблоны документов
- Типичные нарушения и как их избежать

ФОРМАТ ОТВЕТА:
Структурированный Markdown с разделами:
- Обзор нормативов
- Требования HACCP
- Требования СанПиН
- Температурные режимы
- Документооборот
- Штрафы и ответственность
- Практические рекомендации

Включи конкретные цифры, даты вступления в силу, номера документов.""",

    "ingredients_prices": """Проведи глубокое исследование актуальных цен на ингредиенты для ресторанов в России на декабрь 2025 года.

ТРЕБОВАНИЯ:
1. Только цены 2025 года, приоритет декабрь 2025
2. Все федеральные округа России
3. Оптовые цены для ресторанов
4. Структурированный ответ в Markdown формате

КАТЕГОРИИ ИНГРЕДИЕНТОВ:
- Мясо и птица (говядина, свинина, курица, индейка)
- Рыба и морепродукты
- Овощи и фрукты (сезонные и импортные)
- Молочные продукты
- Крупы и бобовые
- Специи и приправы
- Масла и жиры
- Полуфабрикаты
- Напитки

ДЛЯ КАЖДОГО РЕГИОНА (Москва, СПб, ЦФО, СЗФО, ЮФО, ПФО, УФО, СФО, ДВФО):
- Средние оптовые цены по категориям
- Крупные поставщики и рынки
- Минимальные партии
- Условия доставки
- Сезонные колебания цен

ФОРМАТ ОТВЕТА:
Структурированный Markdown с таблицами цен по регионам.
Включи конкретные цифры в рублях за кг/л/шт.""",

    "techcards": """Проведи глубокое исследование популярных техкарт и рецептов для ресторанов в России.

ТРЕБОВАНИЯ:
1. Актуальные рецепты 2024-2025 года
2. Фокус на российский рынок
3. Детальные техкарты с точными весами и технологией

КАТЕГОРИИ:
- Русская кухня (борщ, пельмени, блины, щи, котлеты)
- Европейская кухня (паста, пицца, стейки, салаты)
- Азиатская кухня (суши, роллы, вок, том ям)
- Кавказская кухня (шашлык, хинкали, хачапури)
- Фастфуд и стритфуд
- Десерты и выпечка

ДЛЯ КАЖДОГО БЛЮДА:
- Название
- Категория
- Выход (граммы/порции)
- Ингредиенты с точными весами (в граммах)
- Пошаговая технология приготовления
- Температура подачи
- Время приготовления
- КБЖУ (если доступно)
- Особенности для регионов России

ФОРМАТ ОТВЕТА:
Структурированный Markdown с детальными техкартами.
Включи минимум 20-30 популярных блюд.""",

    "hr": """Проведи глубокое исследование HR-процессов и управления персоналом в ресторанном бизнесе России на 2025 год.

ТРЕБОВАНИЯ:
1. Актуальные практики 2024-2025 года
2. Трудовое законодательство РФ
3. Практические инструменты и шаблоны

КАТЕГОРИИ:
- Должностные инструкции (повар, официант, бармен, администратор, шеф-повар)
- Обучение и адаптация персонала
- Системы мотивации и KPI
- Скрипты продаж для официантов
- Управление сменами и графиками
- Решение конфликтов
- Трудовое законодательство РФ для ресторанов
- Зарплаты и компенсации (актуальные цифры 2025)

ФОРМАТ ОТВЕТА:
Структурированный Markdown с:
- Должностными инструкциями
- Шаблонами документов
- Системами мотивации
- Скриптами продаж
- Практическими рекомендациями

Включи конкретные примеры, шаблоны, цифры.""",

    "finance": """Проведи глубокое исследование финансового управления и ценообразования в ресторанном бизнесе России на 2025 год.

ТРЕБОВАНИЯ:
1. Актуальные данные 2025 года
2. Налоговое законодательство РФ
3. Практические методы и формулы

КАТЕГОРИИ:
- Методы расчета себестоимости блюд
- Ценообразование в ресторанах (наценки, маржинальность)
- Управление закупками и складом
- Финансовое планирование и бюджетирование
- Налогообложение (УСН, ОСН, патент) - актуальные ставки 2025
- Региональные особенности ценообразования
- Средние показатели по рынку (food cost, labor cost, etc.)

ФОРМАТ ОТВЕТА:
Структурированный Markdown с:
- Формулами расчета
- Примерами расчетов
- Актуальными налоговыми ставками
- Средними показателями по рынку
- Практическими рекомендациями

Включи конкретные цифры, формулы, примеры.""",

    "marketing": """Проведи глубокое исследование маркетинга и продвижения ресторанов в России на 2025 год.

ТРЕБОВАНИЯ:
1. Актуальные тренды 2025 года
2. Фокус на российский рынок
3. Практические инструменты и кейсы

КАТЕГОРИИ:
- Продвижение в соцсетях (ВК, Telegram, Instagram, Яндекс.Дзен)
- Маркетинговые кампании и акции
- Работа с отзывами (Яндекс, 2ГИС, Google)
- Партнерства и коллаборации
- Работа с блогерами и инфлюенсерами
- Региональный маркетинг
- Лояльность и программы скидок
- Контент-маркетинг для ресторанов

ФОРМАТ ОТВЕТА:
Структурированный Markdown с:
- Стратегиями продвижения
- Практическими примерами
- Метриками эффективности
- Бюджетами и затратами
- Региональными особенностями

Включи конкретные примеры, кейсы, цифры.""",

    "iiko": """Проведи глубокое исследование системы iiko и автоматизации ресторанного бизнеса в России.

ТРЕБОВАНИЯ:
1. Актуальная информация 2025 года
2. Фокус на функционал iiko
3. Практические руководства

КАТЕГОРИИ:
- Документация iiko (основные модули, функции)
- Настройка меню и номенклатуры
- Управление складом и закупками
- Интеграции с другими системами
- Отчетность и аналитика
- API и автоматизация
- Типичные проблемы и решения
- Лучшие практики использования

ФОРМАТ ОТВЕТА:
Структурированный Markdown с:
- Описанием функций
- Инструкциями по настройке
- Примерами использования
- Решениями типичных проблем
- Практическими рекомендациями

Включи конкретные примеры, скриншоты описаний, инструкции.""",

    "regional": """Проведи глубокое исследование региональных особенностей ресторанного бизнеса в России на 2025 год.

ТРЕБОВАНИЯ:
1. Актуальные данные 2025 года
2. Все федеральные округа
3. Конкретные цифры и факты

ДЛЯ КАЖДОГО ФЕДЕРАЛЬНОГО ОКРУГА (ЦФО, СЗФО, ЮФО, ПФО, УФО, СФО, ДВФО):
- Средние цены на аренду помещений
- Средние чеки в ресторанах
- Популярные форматы заведений
- Местные предпочтения в еде
- Сезонность бизнеса
- Уровень конкуренции
- Особенности законодательства
- Крупные игроки рынка

ФОРМАТ ОТВЕТА:
Структурированный Markdown по каждому округу.
Включи конкретные цифры, факты, примеры.""",

    "trends": """Проведи глубокое исследование трендов и инноваций в ресторанном бизнесе на 2025 год.

ТРЕБОВАНИЯ:
1. Актуальные тренды 2025 года
2. Российский и мировой рынок
3. Практические рекомендации

КАТЕГОРИИ:
- Кулинарные тренды (популярные блюда, ингредиенты, техники)
- Тренды обслуживания (форматы, технологии)
- Технологические тренды (автоматизация, AI, доставка)
- Потребительские предпочтения
- Новые форматы ресторанов
- Экологичность и устойчивость

ФОРМАТ ОТВЕТА:
Структурированный Markdown с:
- Описанием трендов
- Примерами реализации
- Прогнозами развития
- Практическими рекомендациями

Включи конкретные примеры, цифры, прогнозы."""
}


async def call_perplexity(prompt: str, max_retries: int = 3) -> Optional[str]:
    """Вызвать Perplexity через OpenRouter API"""
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY не найден в переменных окружения")
        return None
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://receptorai.pro",
        "X-Title": "RECEPTOR Knowledge Base Collector"
    }
    
    # Пробуем разные модели, если одна не работает
    for model in PERPLEXITY_MODELS:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 8000,  # Больше токенов для детальных ответов
            "temperature": 0.3  # Более точные ответы
        }
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    print(f"  📡 Запрос к Perplexity ({model}, попытка {attempt + 1}/{max_retries})...")
                    response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if content:
                            print(f"  ✅ Получен ответ ({len(content)} символов) через модель {model}")
                            return content
                        else:
                            print(f"  ⚠️ Пустой ответ от API")
                    elif response.status_code == 404:
                        # Модель не найдена, пробуем следующую
                        print(f"  ⚠️ Модель {model} не найдена, пробуем другую...")
                        break
                    else:
                        error_text = response.text
                        print(f"  ❌ Ошибка API: {response.status_code} - {error_text[:200]}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                print(f"  ❌ Ошибка запроса: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
    
    print(f"  ❌ Все модели Perplexity недоступны. Проверьте доступные модели на openrouter.ai")
    return None


def format_markdown(content: str, category: str, metadata: Dict = None) -> str:
    """Форматировать контент в правильный Markdown формат"""
    metadata = metadata or {}
    
    # Заголовок документа
    category_names = {
        "haccp": "HACCP и СанПиН нормативы",
        "ingredients_prices": "Цены на ингредиенты",
        "techcards": "Техкарты и рецепты",
        "hr": "HR и управление персоналом",
        "finance": "Финансы и ценообразование",
        "marketing": "Маркетинг и продвижение",
        "iiko": "iiko и автоматизация",
        "regional": "Региональные особенности",
        "trends": "Тренды и инновации"
    }
    
    category_name = category_names.get(category, category)
    
    markdown = f"""# {category_name}

**Категория:** {category}
**Дата сбора:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Источник:** Deep Research (GPT-5 / Perplexity)

"""
    
    # Добавляем метаданные если есть
    if metadata:
        markdown += "## Метаданные\n\n"
        for key, value in metadata.items():
            markdown += f"- **{key}:** {value}\n"
        markdown += "\n"
    
    # Добавляем основной контент
    markdown += "---\n\n"
    markdown += content
    markdown += "\n\n---\n\n"
    markdown += f"*Документ собран автоматически через Perplexity API для RECEPTOR Knowledge Base*\n"
    
    return markdown


def get_output_filename(category: str) -> str:
    """Получить имя файла для категории"""
    filename_map = {
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
    return filename_map.get(category, f"receptor_{category}.md")


async def collect_category(category: str, force: bool = False) -> bool:
    """Собрать информацию по одной категории"""
    if category not in PERPLEXITY_PROMPTS:
        print(f"❌ Неизвестная категория: {category}")
        print(f"   Доступные: {', '.join(PERPLEXITY_PROMPTS.keys())}")
        return False
    
    output_file = KNOWLEDGE_BASE_PATH / get_output_filename(category)
    
    # Проверяем, существует ли уже файл
    if output_file.exists() and not force:
        print(f"⚠️  Файл {output_file.name} уже существует. Используй --force для перезаписи")
        return False
    
    print(f"\n📚 Сбор категории: {category}")
    print(f"   Промпт: {len(PERPLEXITY_PROMPTS[category])} символов")
    
    # Вызываем Perplexity
    content = await call_perplexity(PERPLEXITY_PROMPTS[category])
    
    if not content:
        print(f"❌ Не удалось получить данные для категории {category}")
        return False
    
    # Форматируем в Markdown
    formatted_content = format_markdown(content, category)
    
    # Сохраняем файл
    output_file.write_text(formatted_content, encoding='utf-8')
    print(f"✅ Сохранено: {output_file.name} ({len(formatted_content)} символов)")
    
    return True


async def collect_all(force: bool = False):
    """Собрать все категории"""
    print("🚀 Начинаем сбор базы знаний через Perplexity...")
    print(f"📁 Путь сохранения: {KNOWLEDGE_BASE_PATH}")
    print(f"🔑 API ключ: {'✅ Найден' if OPENROUTER_API_KEY else '❌ Не найден'}\n")
    
    if not OPENROUTER_API_KEY:
        print("❌ Необходимо установить OPENROUTER_API_KEY в переменных окружения")
        return
    
    categories = list(PERPLEXITY_PROMPTS.keys())
    print(f"📋 Категорий для сбора: {len(categories)}\n")
    
    results = {}
    for i, category in enumerate(categories, 1):
        print(f"[{i}/{len(categories)}] ", end="")
        success = await collect_category(category, force=force)
        results[category] = success
        
        # Небольшая задержка между запросами
        if i < len(categories):
            await asyncio.sleep(2)
    
    # Итоги
    print("\n" + "="*60)
    print("📊 ИТОГИ СБОРА:")
    print("="*60)
    successful = sum(1 for v in results.values() if v)
    print(f"✅ Успешно: {successful}/{len(categories)}")
    print(f"❌ Ошибок: {len(categories) - successful}/{len(categories)}")
    
    if successful > 0:
        print(f"\n📁 Файлы сохранены в: {KNOWLEDGE_BASE_PATH}")
        print("\n💡 Следующий шаг: запустите индексацию базы знаний")


async def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Сбор базы знаний через Perplexity")
    parser.add_argument(
        "--category",
        type=str,
        help="Категория для сбора (или 'all' для всех)",
        default="all"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Перезаписать существующие файлы"
    )
    
    args = parser.parse_args()
    
    if args.category == "all":
        await collect_all(force=args.force)
    else:
        await collect_category(args.category, force=args.force)


if __name__ == "__main__":
    asyncio.run(main())

