"""
iiko Export Builder для TechCardV2
Модуль для создания XLSX файлов с Products и Recipes листами для импорта в iiko
"""

import io
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import xlsxwriter

from ..techcards_v2.schemas import TechCardV2

class IikoExporter:
    """Экспортер техкарт в формат iiko (XLSX с двумя листами)"""
    
    def __init__(self):
        pass
    
    def _convert_to_base_unit(self, amount: float, unit: str) -> Tuple[float, str]:
        """
        Конвертация в базовые единицы iiko
        g → kg, ml → l, pcs → pcs
        """
        if unit == "g":
            return round(amount / 1000.0, 3), "kg"
        elif unit == "ml":
            return round(amount / 1000.0, 3), "l"
        elif unit == "pcs":
            return int(round(amount)), "pcs"
        else:
            # По умолчанию считаем граммы
            return round(amount / 1000.0, 3), "kg"
    
    def _extract_products(self, tech_card: TechCardV2) -> List[Dict[str, Any]]:
        """Извлекает уникальные SKU для Products листа"""
        products = {}
        
        # Получаем дату из costMeta или текущую
        as_of = None
        if tech_card.costMeta and tech_card.costMeta.asOf:
            as_of = tech_card.costMeta.asOf
        else:
            as_of = datetime.now().strftime('%Y-%m-%d')
        
        # Собираем уникальные ингредиенты по SKU
        for ingredient in tech_card.ingredients:
            # Используем SKU или создаем автоматически
            sku_id = ingredient.skuId or f"AUTO_{ingredient.name.upper().replace(' ', '_')}"
            
            if sku_id not in products:
                # Конвертируем единицу в базовую для iiko
                _, base_unit = self._convert_to_base_unit(1.0, ingredient.unit)
                
                # Получаем цену если есть в cost data
                price_per_unit = None
                vat_pct = None
                
                if tech_card.cost:
                    # Пока что не умеем извлекать цену по конкретному ингредиенту
                    # Это будет усредненная цена из общей стоимости
                    if tech_card.cost.rawCost and len(tech_card.ingredients) > 0:
                        # Примерная цена - общая стоимость / количество ингредиентов
                        # В реальности нужна более точная логика
                        pass
                    vat_pct = tech_card.cost.vat_pct
                
                products[sku_id] = {
                    'skuId': sku_id,
                    'canonicalId': ingredient.skuId or ingredient.name.upper().replace(' ', '_'),
                    'name': ingredient.name,
                    'unitBase': base_unit,
                    'pricePerUnit': price_per_unit,  # Пока None
                    'vatPct': vat_pct or 20,  # По умолчанию 20%
                    'asOf': as_of
                }
        
        return list(products.values())
    
    def _extract_recipes(self, tech_card: TechCardV2) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Извлекает рецептуру для Recipes листа
        Возвращает: (recipes_data, issues)
        """
        recipes = []
        issues = []
        
        # Генерируем код блюда
        dish_code = f"DISH_{tech_card.meta.title.upper().replace(' ', '_')}"
        dish_name = tech_card.meta.title
        portion_unit = "portion"
        
        # Выходы
        output_per_portion = tech_card.yield_.perPortion_g
        output_per_batch = tech_card.yield_.perBatch_g
        
        # Проверяем баланс netto
        total_netto = sum(ing.netto_g for ing in tech_card.ingredients)
        yield_mismatch_pct = abs(total_netto - output_per_batch) / output_per_batch * 100
        
        if yield_mismatch_pct > 5.0:
            issues.append({
                "type": "yieldMismatch",
                "expected": output_per_batch,
                "actual": total_netto,
                "mismatch_pct": round(yield_mismatch_pct, 1)
            })
        
        # Формируем строки рецептуры
        for ingredient in tech_card.ingredients:
            # SKU ингредиента
            ingredient_sku = ingredient.skuId
            if not ingredient_sku:
                issues.append({
                    "type": "noSku",
                    "name": ingredient.name
                })
                ingredient_sku = ""  # Пустой SKU, но строку включаем
            
            # Конвертируем netto в базовые единицы
            qty_net, qty_unit = self._convert_to_base_unit(ingredient.netto_g, ingredient.unit)
            
            recipe_row = {
                'dishCode': dish_code,
                'dishName': dish_name,
                'portionUnit': portion_unit,
                'outputPerPortion_g': output_per_portion,
                'outputPerBatch_g': output_per_batch,
                'ingredientSku': ingredient_sku,
                'ingredientName': ingredient.name,
                'qtyNet': qty_net,
                'qtyUnit': qty_unit
            }
            
            recipes.append(recipe_row)
        
        return recipes, issues
    
    def export_to_xlsx(self, tech_card: TechCardV2) -> Tuple[io.BytesIO, List[Dict[str, Any]]]:
        """
        Создает XLSX файл с Products и Recipes листами
        Возвращает: (файловый поток, список issues)
        """
        # Создаем файл в памяти
        output = io.BytesIO()
        
        # Извлекаем данные
        products_data = self._extract_products(tech_card)
        recipes_data, issues = self._extract_recipes(tech_card)
        
        # Создаем XLSX
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # === ЛИСТ PRODUCTS ===
        products_sheet = workbook.add_worksheet('Products')
        
        # Заголовки Products
        products_headers = ['skuId', 'canonicalId', 'name', 'unitBase', 'pricePerUnit', 'vatPct', 'asOf']
        
        # Записываем заголовки
        for col, header in enumerate(products_headers):
            products_sheet.write(0, col, header)
        
        # Записываем данные Products
        for row, product in enumerate(products_data, 1):
            products_sheet.write(row, 0, product['skuId'])
            products_sheet.write(row, 1, product['canonicalId'])
            products_sheet.write(row, 2, product['name'])
            products_sheet.write(row, 3, product['unitBase'])
            products_sheet.write(row, 4, product['pricePerUnit'] or '')
            products_sheet.write(row, 5, product['vatPct'])
            products_sheet.write(row, 6, product['asOf'])
        
        # === ЛИСТ RECIPES ===
        recipes_sheet = workbook.add_worksheet('Recipes')
        
        # Заголовки Recipes
        recipes_headers = ['dishCode', 'dishName', 'portionUnit', 'outputPerPortion_g', 'outputPerBatch_g', 
                          'ingredientSku', 'ingredientName', 'qtyNet', 'qtyUnit']
        
        # Записываем заголовки
        for col, header in enumerate(recipes_headers):
            recipes_sheet.write(0, col, header)
        
        # Записываем данные Recipes
        for row, recipe in enumerate(recipes_data, 1):
            recipes_sheet.write(row, 0, recipe['dishCode'])
            recipes_sheet.write(row, 1, recipe['dishName'])
            recipes_sheet.write(row, 2, recipe['portionUnit'])
            recipes_sheet.write(row, 3, recipe['outputPerPortion_g'])
            recipes_sheet.write(row, 4, recipe['outputPerBatch_g'])
            recipes_sheet.write(row, 5, recipe['ingredientSku'])
            recipes_sheet.write(row, 6, recipe['ingredientName'])
            recipes_sheet.write(row, 7, recipe['qtyNet'])
            recipes_sheet.write(row, 8, recipe['qtyUnit'])
        
        # Автоширина колонок
        for sheet in [products_sheet, recipes_sheet]:
            sheet.set_column('A:Z', 15)
        
        # Закрываем workbook
        workbook.close()
        
        # Возвращаемся в начало потока
        output.seek(0)
        
        return output, issues

def export_techcard_to_iiko(tech_card: TechCardV2) -> Tuple[io.BytesIO, List[Dict[str, Any]]]:
    """
    Функция-обертка для экспорта техкарты в iiko формат
    """
    exporter = IikoExporter()
    return exporter.export_to_xlsx(tech_card)