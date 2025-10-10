# 🏗️ IIKO INTEGRATION DEEP DIVE
## Полный разбор архитектуры экспорта Receptor Pro → IIKO RMS

**Создано:** 2025-10-08  
**Цель:** Полное понимание логики работы системы для partnership with IIKO

---

## 📊 СТРУКТУРА НОМЕНКЛАТУРЫ IIKO

### **Категории в IIKO RMS:**

| Категория | Английское название | Описание | Когда используется |
|-----------|---------------------|----------|-------------------|
| **БЛЮДА** | DISH | Готовая продукция, которую продают гостям | Финальные техкарты (Борщ, Паста, Салат) |
| **ТОВАРЫ** | GOODS | Сырье и ингредиенты для приготовления | Говядина, Морковь, Мука, Масло |
| **ПОЛУФАБРИКАТЫ** | PREPARED | Промежуточные заготовки | Бульон, Тесто, Соус (subRecipes) |
| **МОДИФИКАТОРЫ** | MODIFIER | Дополнения к блюдам | Сыр, Острый соус, Хлеб |
| **ГРУППЫ** | GROUP | Категории для структуры меню | "Супы", "Гарниры", "Десерты" |
| **УСЛУГИ** | SERVICE | Нетоварные позиции | Обслуживание, доставка |

---

## 🔄 ПОЛНЫЙ WORKFLOW ЭКСПОРТА

### **Phase 1: Article Generation**
```
Техкарта V2 → ArticleAllocator → Numeric 5-digit codes
                    ↓
    Блюдо: 10001, 10002, 10003...
    Ингредиенты: 10004, 10005, 10006...
```

**Код:**
```python
# backend/receptor_agent/integrations/article_allocator.py
class ArticleAllocator:
    def allocate_articles(self, entity_ids: List[str]) -> Dict:
        # Генерирует уникальные numeric codes (100001-999999)
        # Проверяет collision с существующими в MongoDB
        # Резервирует артикулы для последующего claim
```

---

### **Phase 2: IIKO RMS Mapping**
```
Numeric Article → IIKO RMS Check → Mapped/Missing
                        ↓
    Found in IIKO RMS ✅ → Use existing SKU
    NOT Found ❌ → Add to Skeleton list
```

**Preflight Check:**
```python
# backend/receptor_agent/routes/export_v2.py
class PreflightOrchestrator:
    async def run_preflight(techcard_ids, organization_id):
        # 1. Load techcards from MongoDB
        # 2. Process dishes (check if article exists in RMS)
        # 3. Process products (fuzzy match by name)
        # 4. Generate missing articles via ArticleAllocator
        # 5. Return preflight report with "found" and "missing"
```

**Preflight Output:**
```json
{
  "found": {
    "dishes": [{"name": "Борщ", "article": "10001", "foundInRMS": true}],
    "products": [{"name": "Говядина", "article": "02323", "skuId": "abc-123"}]
  },
  "missing": {
    "dishes": [{"name": "Паста Карбонара", "article": "10002", "yield": 330}],
    "products": [{"name": "Трюфель", "article": "10003", "unit": "г"}]
  },
  "generated": {
    "dishArticles": ["10002"],
    "productArticles": ["10003"]
  }
}
```

---

### **Phase 3: Skeleton Generation**

#### **A. Dish-Skeletons.xlsx**
**Для чего:** Создать блюдо в IIKO RMS как номенклатуру (категория "Блюда")

**Структура файла:**
```excel
Артикул | Наименование              | Тип  | Ед. выпуска | Выход
10002   | Паста Карбонара с Трюфелем | DISH | кг          | 0.33
```

**Требования:**
- **Тип:** ТОЛЬКО "DISH" (НЕ "Блюдо", не "блюдо")
- **Единицы:** килограммы (конвертация из грамм)
- **Артикул:** @ формат (text) для сохранения ведущих нулей
- **Валидация:** Строгая проверка типов (line 709-711)

**Код:**
```python
# backend/receptor_agent/exports/iiko_xlsx.py: 687-910
def create_dish_skeletons_xlsx(dish_codes_mapping, dishes_data):
    VALID_IIKO_DISH_TYPES = {"DISH"}  # ТОЛЬКО это!
    
    for dish in dishes_data:
        dish_type = "DISH"  # Hardcoded, всегда
        
        if dish_type not in VALID_IIKO_DISH_TYPES:
            raise ValueError(f"Недопустимый тип для блюда")
        
        # Конвертация грамм → килограммы
        yield_kg = dish["yield_g"] / 1000.0
        
        ws.cell(column=3, value="DISH")  # Тип
        ws.cell(column=4, value="кг")     # Единица
        ws.cell(column=5, value=yield_kg) # Выход в кг
```

---

#### **B. Product-Skeletons.xlsx**
**Для чего:** Создать ингредиенты в IIKO RMS как номенклатуру (категория "Товары")

**Структура файла:**
```excel
Артикул | Наименование | Ед. изм | Тип   | Группа              | Штрихкод | Поставщик
10003   | Трюфель      | г       | GOODS | Бакалея             |          |
10004   | Пармезан     | г       | GOODS | Молочные продукты   |          |
```

**Группы (автоматические):**
```python
# Line 428-439
if 'мясо' in name or 'курица' in name:
    group = 'Мясо и рыба'
elif 'молоко' in name or 'сыр' in name:
    group = 'Молочные продукты'
elif 'морковь' in name or 'лук' in name:
    group = 'Овощи'
elif 'мука' in name or 'сахар' in name:
    group = 'Бакалея'
else:
    group = 'Сырьё'  # Дефолт
```

**Требования:**
- **Тип:** ТОЛЬКО "GOODS" (НЕ "Товар", не "goods")
- **Единицы:** г/мл (БЕЗ конвертации в кг для продуктов!)
- **Валидация:** Строгая проверка (line 358-366)

**Код:**
```python
# backend/receptor_agent/exports/iiko_xlsx.py: 336-562
def create_product_skeletons_xlsx(missing_ingredients, generated_codes):
    VALID_IIKO_TYPES = {"GOODS", "DISH", "MODIFIER", "PREPARED", "SERVICE"}
    
    for ingredient in missing_ingredients:
        product_type = "GOODS"  # Для ингредиентов всегда GOODS
        
        if product_type not in VALID_IIKO_TYPES:
            raise ValueError(f"Недопустимый тип для продукта")
        
        # БЕЗ конвертации единиц для Product Skeletons
        ws.cell(column=3, value=normalized_unit)  # г, мл, шт
        ws.cell(column=4, value="GOODS")          # Тип
```

---

#### **C. TechCard.xlsx (Main TTK)**
**Для чего:** Сборочная карта (recipe/assembly chart) для IIKO

**Структура файла:**
```excel
Артикул блюда | Наименование блюда        | Артикул продукта | Наименование продукта | Брутто | Потери% | Нетто | Ед. | Выход | Норма | Метод | Технология
10002         | Паста Карбонара с Трюфелем | 10003            | Трюфель              | 0.005  | 0       | 0.005 | кг  | 0.33  | 1     | 1     | #1. Отварить пасту...
10002         | Паста Карбонара с Трюфелем | 10004            | Пармезан             | 0.030  | 0       | 0.030 | кг  | 0.33  | 1     | 1     |
10002         | Паста Карбонара с Трюфелем | 10005            | Паста                | 0.100  | 0       | 0.100 | кг  | 0.33  | 1     | 1     |
```

**Ключевые особенности:**
- **Первая строка:** Артикул блюда (10002) - связывает с Dish Skeleton
- **Каждая строка:** Один ингредиент
- **Единицы:** КИЛОГРАММЫ для всех масс (конвертация!)
- **Технология:** Только в первой строке ингредиента
- **Operational Rounding:** Применяется перед экспортом (опционально)

**Код:**
```python
# backend/receptor_agent/exports/iiko_xlsx.py: 1042-1420
def create_iiko_ttk_xlsx(card: TechCardV2, export_options):
    # 1. Operational Rounding (если включено)
    if operational_rounding_enabled:
        working_card = rounder.round_techcard_ingredients(card_dict)
    
    # 2. Dish Code (из preflight или ArticleAllocator)
    dish_code = dish_codes_mapping.get(dish_title)
    
    # 3. Заполнение ингредиентов
    for ingredient in working_card.ingredients:
        # Get product_code from preflight or allocate new
        product_code = ingredient.product_code or allocate_new()
        
        # Конвертация грамм → килограммы для экспорта
        brutto_g_raw = normalize_unit_to_grams(ingredient.brutto_g, ingredient.unit)
        netto_g_raw = normalize_unit_to_grams(ingredient.netto_g, ingredient.unit)
        
        brutto_kg = brutto_g_raw / 1000.0
        netto_kg = netto_g_raw / 1000.0
        
        row_data = [
            dish_code,           # Артикул блюда
            dish_name,           # Наименование блюда
            product_code,        # Артикул продукта
            ingredient.name,     # Наименование продукта
            brutto_kg,           # Брутто (кг!)
            loss_pct,            # Потери, %
            netto_kg,            # Нетто (кг!)
            "кг",                # Единица (кг!)
            output_qty_kg,       # Выход (кг!)
            1,                   # Норма закладки
            1,                   # Метод списания
            technology_text      # Технология (только первая строка)
        ]
```

---

### **Phase 4: ZIP Archive Creation**

**DualExporter:**
```python
# backend/receptor_agent/routes/export_v2.py: 436-676
class DualExporter:
    async def create_zip_export(techcard_ids, operational_rounding, preflight_result):
        # 1. Create TTK XLSX (main tech cards)
        ttk_buffer = await _create_ttk_xlsx(techcard_ids, operational_rounding, preflight_result)
        
        # 2. Create Dish-Skeletons.xlsx (missing dishes)
        if preflight_result["missing"]["dishes"]:
            dish_buffer = await _create_dish_skeletons_xlsx(missing_dishes)
        
        # 3. Create Product-Skeletons.xlsx (missing products)
        if preflight_result["missing"]["products"]:
            product_buffer = await _create_product_skeletons_xlsx(missing_products)
        
        # 4. ZIP all files
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("TechCards.xlsx", ttk_buffer.getvalue())
            zf.writestr("Dish-Skeletons.xlsx", dish_buffer.getvalue())
            zf.writestr("Product-Skeletons.xlsx", product_buffer.getvalue())
        
        # 5. Claim generated articles (make permanent)
        await _claim_generated_articles(preflight_result, organization_id)
        
        return zip_buffer
```

**ZIP Structure:**
```
iiko_export_20251008.zip
├── TechCards.xlsx          # Основные техкарты (1-N блюд)
├── Dish-Skeletons.xlsx     # Новые блюда для импорта (если есть missing)
└── Product-Skeletons.xlsx  # Новые продукты для импорта (если есть missing)
```

---

## 📥 IMPORT WORKFLOW В IIKO

### **Правильный порядок импорта:**

#### **Step 1: Import Skeletons First**
```
IIKO RMS → Импорт → Выбрать Product-Skeletons.xlsx
                ↓
    Создаются номенклатуры в категории "ТОВАРЫ"
    Артикулы: 10003 (Трюфель), 10004 (Пармезан)
```

```
IIKO RMS → Импорт → Выбрать Dish-Skeletons.xlsx
                ↓
    Создаются номенклатуры в категории "БЛЮДА"
    Артикул: 10002 (Паста Карбонара с Трюфелем)
```

**ВАЖНО:** Skeletons нужны ТОЛЬКО для новых номенклатур!  
Если продукт уже есть в IIKO → используем его существующий артикул → skeleton НЕ нужен!

---

#### **Step 2: Import TechCard (Assembly Chart)**
```
IIKO RMS → Импорт → Выбрать TechCards.xlsx
                ↓
    Создается сборочная карта для блюда 10002
    Связывает блюдо с ингредиентами по артикулам
    
    10002 (Блюдо) состоит из:
    → 10003 (Трюфель) - 5г
    → 10004 (Пармезан) - 30г
    → 10005 (Паста) - 100г
```

---

## 🔧 КРИТИЧНЫЕ ТРЕБОВАНИЯ IIKO

### **1. Типы данных (СТРОГАЯ ВАЛИДАЦИЯ)**

❌ **НЕПРАВИЛЬНО:**
```python
product_type = "Товар"  # Русский текст
dish_type = "блюдо"     # lowercase
```

✅ **ПРАВИЛЬНО:**
```python
product_type = "GOODS"  # Uppercase English
dish_type = "DISH"      # Uppercase English
```

**Код валидации:**
```python
# Line 358-366 (Products)
VALID_IIKO_TYPES = {
    "GOODS",      # Товар (основной тип для ингредиентов)
    "DISH",       # Блюдо
    "MODIFIER",   # Модификатор
    "GROUP",      # Группа товаров
    "SERVICE",    # Услуга
    "PREPARED"    # Полуфабрикат
}

# Line 709-711 (Dishes)
VALID_IIKO_DISH_TYPES = {
    "DISH"  # Только это для блюд!
}
```

---

### **2. Единицы измерения**

**Internal (V2 TechCard):**
```json
{
  "brutto_g": 100,
  "netto_g": 80,
  "unit": "г"
}
```

**Export to IIKO (TTK):**
```excel
Брутто: 0.1 кг
Нетто: 0.08 кг
Ед.: кг
```

**Конвертация:**
```python
# Line 938-987: normalize_unit_to_grams
def normalize_unit_to_grams(value, unit, ingredient_name):
    if unit in ['кг', 'kg']:
        return value * 1000  # кг → г
    elif unit in ['л', 'l']:
        return value * 1000  # л → мл → г (плотность=1)
    elif unit in ['шт', 'pcs']:
        # Средние веса продуктов
        if 'яйцо' in ingredient_name:
            return value * 50
        elif 'луковица' in ingredient_name:
            return value * 150
        # ... и т.д.
    return value

# Then convert grams to kilograms for export:
brutto_kg = brutto_g / 1000.0
netto_kg = netto_g / 1000.0
```

**ВАЖНО:**
- **Product Skeletons:** НЕ конвертируем (оставляем г/мл)
- **Dish Skeletons:** Конвертируем (кг)
- **TechCard (TTK):** Конвертируем (кг)

---

### **3. Артикулы (Article Codes)**

❌ **НЕПРАВИЛЬНО:**
```python
product_code = "abc-123-def-456"  # GUID
dish_code = "DISH_CARBONARA"      # String slug
```

✅ **ПРАВИЛЬНО:**
```python
product_code = "10003"  # 5-digit numeric
dish_code = "10002"     # 5-digit numeric
```

**Excel форматирование:**
```python
# Line 1396-1397
cell.number_format = '@'  # Text format для сохранения ведущих нулей
# Это критично! Иначе Excel превратит 02323 → 2323
```

**ArticleAllocator генерирует:**
```python
# backend/receptor_agent/integrations/article_allocator.py
article_range = (100001, 999999)  # 6-digit range
# Проверяет collision с existing articles в MongoDB
# Резервирует временно (TTL = 1 hour)
# Claim делает permanent после успешного экспорта
```

---

### **4. КБЖУ (Nutrition) и Технология**

**TechCard includes:**
```excel
Технология приготовления:
#1. Отварить пасту [t=100°C] [8 мин] [Кастрюля]
#2. Обжарить бекон [t=180°C] [5 мин] [Сковорода]
#3. Смешать с соусом [t=60°C] [2 мин] [Сковорода]
#4. Добавить тертый трюфель [Разделочная доска]
```

**Формат:**
```python
# Line 989-1040: generate_technology_text
f"#{step_num}. {action} [t={temp_c}°C] [{time_min} мин] [{equipment}]"
```

**КБЖУ хранится в meta но НЕ экспортируется в IIKO XLSX:**
```json
{
  "nutrition": {
    "energy_kcal": 667,
    "protein_g": 25,
    "fat_g": 42,
    "carbs_g": 45
  }
}
```

---

## 🧪 OPERATIONAL ROUNDING

**Для чего:** Округление для удобства кухни (0.033 кг → 0.035 кг)

**Когда применяется:** Опционально при экспорте (по умолчанию включено)

```python
# Line 1068-1129
if operational_rounding_enabled:
    rounder = get_operational_rounder()
    rounding_result = rounder.round_techcard_ingredients(card_dict)
    working_card = TechCardV2.model_validate(rounded_dict)
    
    # Логируем delta
    logger.info(f"Operational rounding: {len(items)} ingredients, delta: {delta_g}g")
```

**Правила:**
```python
# backend/receptor_agent/techcards_v2/operational_rounding.py
class OperationalRoundingRules:
    - < 1g     → 0.1g increments   (0.7g → 0.7g)
    - 1-10g    → 1g increments     (3.7g → 4g)
    - 10-100g  → 5g increments     (33g → 35g)
    - 100-500g → 10g increments    (147g → 150g)
    - > 500g   → 50g increments    (580g → 600g)
```

---

## 🔍 FUZZY MATCHING

**Проблема:** Ингредиент "Говядина вырезка" в техкарте, но в IIKO RMS только "Говядина"

**Решение:**
```python
# backend/receptor_agent/integrations/iiko_rms_service.py: fuzzy_match_ingredient
from difflib import SequenceMatcher

def fuzzy_match_ingredient(ingredient_name, iiko_products):
    best_match = None
    best_score = 0.0
    
    for product in iiko_products:
        score = SequenceMatcher(None, ingredient_name.lower(), product["name"].lower()).ratio()
        
        if score > best_score:
            best_score = score
            best_match = product
    
    # Threshold: 0.7 (70% similarity)
    if best_score >= 0.7:
        return best_match
    
    return None
```

**Примеры:**
```
"Говядина вырезка" → "Говядина" (score: 0.82) ✅
"Масло сливочное 82%" → "Масло сливочное" (score: 0.89) ✅
"Трюфель белый" → "Белый гриб" (score: 0.45) ❌ (нужен skeleton)
```

---

## 🐛 ИЗВЕСТНЫЕ ПРОБЛЕМЫ И ФИКСЫ

### **1. MongoDB DB Name Length > 63 символов**

**Проблема:**
```
InvalidName: db name must be at most 63 characters, found: 68
```

**Причина:** Парсинг DB name из MONGO_URL с query params

**Фикс:**
```python
# backend/receptor_agent/integrations/article_allocator.py: Line 114
db_name = os.environ.get('DB_NAME', 'receptor_pro').strip('"')

# Валидация и truncate
if len(db_name) > 63:
    logger.warning(f"DB name too long ({len(db_name)}), truncating to 63 chars")
    db_name = db_name[:63]
```

**Status:** ✅ FIXED

---

### **2. SKU Mappings не сохраняются в MongoDB**

**Проблема:** После автомаппинга и reload техкарты из истории - mappings lost

**Причина:** `product_code` не сохраняется в `techcards_v2` collection

**Требуется:** Обновить endpoint `/api/v2/techcards/:id/ingredients/:idx` для сохранения `product_code`

**Status:** ⚠️ PENDING

---

### **3. Auto-mapping не обновляет UI после первого раза**

**Проблема:** "⚠ Без SKU: 9" остается даже после успешного маппинга (console показывает 9 accepted)

**Причина:** State не обновляется после API response в `App.js`

**Требуется:** Добавить `setTcV2(updatedTechcard)` после успешного response

**Status:** ⚠️ PENDING

---

### **4. КБЖУ Overcalculation (4669 kcal для пасты)**

**Проблема:** Pasta Carbonara показывает 4669 kcal вместо ~700 kcal

**Причина:** Возможно суммирование на 100г вместо на порцию, или некорректные данные в nutrition DB

**Требуется:** Проверить `backend/receptor_agent/techcards_v2/nutrition_calculator.py`

**Status:** ⚠️ PENDING

---

## 📚 КЛЮЧЕВЫЕ ФАЙЛЫ

### **Backend (Python/FastAPI):**

| Файл | Назначение | Ключевые функции |
|------|-----------|-----------------|
| `routes/export_v2.py` | Orchestration экспорта | `PreflightOrchestrator`, `DualExporter` |
| `exports/iiko_xlsx.py` | Генерация XLSX файлов | `create_iiko_ttk_xlsx`, `create_dish_skeletons_xlsx`, `create_product_skeletons_xlsx` |
| `integrations/article_allocator.py` | Генерация numeric articles | `allocate_articles`, `claim_articles` |
| `integrations/iiko_rms_service.py` | Подключение к IIKO RMS | `fetch_product_catalog`, `fuzzy_match_ingredient` |
| `integrations/iiko_rms_client.py` | IIKO API client | `authorize`, `get_nomenclature` |
| `techcards_v2/operational_rounding.py` | Округление для кухни | `get_operational_rounder` |

### **Frontend (React):**

| Файл | Назначение | Ключевые компоненты |
|------|-----------|---------------------|
| `frontend/src/App.js` | Монолитный UI | `IIKOExportModal`, `MappingPanel`, `TechCardV2Viewer` |

---

## 🎯 BEST PRACTICES

### **Для разработчиков:**

1. **Всегда валидировать типы:** DISH / GOODS (строгие uppercase English)
2. **Конвертировать единицы:** г → кг для экспорта в TTK
3. **Использовать @ формат:** Сохранение ведущих нулей в Excel
4. **Запускать Preflight:** Перед экспортом для проверки маппингов
5. **Claim articles:** После успешного экспорта делать permanent

### **Для шефов (пользователей):**

1. **Порядок импорта в IIKO:**
   - Сначала Product-Skeletons.xlsx → создать товары
   - Потом Dish-Skeletons.xlsx → создать блюда
   - В конце TechCards.xlsx → связать все вместе

2. **Если продукт уже есть в IIKO:**
   - Используйте автомаппинг (fuzzy match 70% threshold)
   - Или вручную выберите из каталога
   - Skeleton НЕ нужен!

3. **Operational Rounding:**
   - Включайте для удобства кухни (35г вместо 33.4г)
   - Можно отключить для точности

---

## 🚀 ROADMAP

### **Приоритет 1 (КРИТИЧНО):**
- [ ] Фикс SKU mappings persistence в MongoDB
- [ ] Фикс UI state update после автомаппинга
- [ ] Проверка КБЖУ calculation accuracy

### **Приоритет 2 (ВАЖНО):**
- [ ] Улучшение fuzzy matching (NLP, синонимы)
- [ ] Bulk export (multiple техкарт в один ZIP)
- [ ] Validation UI перед экспортом (preview)

### **Приоритет 3 (УЛУЧШЕНИЯ):**
- [ ] Поддержка PREPARED (полуфабрикаты/subRecipes)
- [ ] Импорт обратно из IIKO (sync changes)
- [ ] History: отслеживание версий техкарт

---

## 📞 SUPPORT

**Для IIKO Partnership:**
- Документация: [iiko API docs](https://api-ru.iiko.services/)
- Формат импорта: XLSX (assembly charts)
- Типы номенклатуры: DISH, GOODS, PREPARED
- Единицы: килограммы (для масс)

**Контакт Receptor Pro:**
- Email: 607orlov@gmail.com
- Platform: receptorai.pro
- IIKO Demo: edison-bar.iiko.it

---

## ✅ SUMMARY

**Receptor Pro → IIKO workflow:**
```
V2 TechCard → Article Allocation → Preflight Check → 
  → Dish/Product Skeletons (if missing) → 
    → TechCard.xlsx (assembly chart) → 
      → ZIP Export → 
        → IIKO RMS Import (3 steps)
```

**Ключевые требования:**
- ✅ Numeric articles (5-digit codes)
- ✅ Type validation (DISH/GOODS uppercase)
- ✅ Unit conversion (г → кг for export)
- ✅ @ format (preserve leading zeros)
- ✅ Fuzzy matching (70% threshold)
- ✅ Operational rounding (optional)

**Результат:**
- 📊 Professional tech cards ready for IIKO
- 🏢 Seamless integration with IIKO RMS
- 🚀 Partnership-ready platform

---

**Created with ❤️ for RECEPTOR PRO IIKO Partnership**


