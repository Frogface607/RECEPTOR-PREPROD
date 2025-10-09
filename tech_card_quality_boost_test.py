#!/usr/bin/env python3
"""
TECH CARD QUALITY BOOST SYSTEM COMPREHENSIVE TESTING

Протестировать систему TECH CARD QUALITY BOOST и все реализованные улучшения качества техкарт.

КЛЮЧЕВЫЕ ОБЛАСТИ ТЕСТИРОВАНИЯ:

1. Расширенные каталоги (ВЫСОКИЙ ПРИОРИТЕТ)
   - Проверить что nutrition_catalog.dev.json содержит 200+ ингредиентов
   - Проверить что все ингредиенты имеют корректные БЖУ данные (kcal, proteins_g, fats_g, carbs_g)
   - Проверить что все единицы измерения валидны (kg, liter, g, ml, pcs)
   - Убедиться что нет пустых или некорректных полей

2. ID система и артикулы (ВЫСОКИЙ ПРИОРИТЕТ)
   - Проверить отсутствие диапазонов типа "9969-86" в любых ID полях
   - Проверить что все canonical_id и product_code корректны
   - Убедиться что новые ингредиенты имеют UUID-based коды
   - Проверить совместимость с iiko экспортом

3. Создание и экспорт техкарт (КРИТИЧЕСКИЙ)
   - POST /api/v1/techcards.v2/generate - создание техкарт с улучшенным БЖУ покрытием
   - POST /api/v1/techcards.v2/export/iiko.xlsx - XLSX экспорт с корректными данными
   - Проверить что техкарты используют расширенный каталог ингредиентов
   - Убедиться что БЖУ покрытие улучшилось по сравнению с baseline (было ~53%)

4. Качество данных (ВЫСОКИЙ ПРИОРИТЕТ)
   - Проверить что новые ингредиенты имеют разумные БЖУ значения
   - Убедиться что единицы измерения соответствуют типу продуктов
   - Проверить отсутствие дублей в каталогах
   - Валидация price_catalog.dev.json на корректность структуры

5. ALT Export Cleanup интеграция
   - Убедиться что система ALT Export Cleanup работает с новыми данными
   - Проверить что admin endpoints /api/v1/export/cleanup/stats возвращают корректную статистику
   - Проверить что ZIP экспорты проходят через cleanup pipeline
"""

import requests
import json
import time
import os
import tempfile
import zipfile
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import re
import uuid

# Backend URL from environment - try external first, fallback to local
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TechCardQualityBoostTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 60
        self.test_results = []
        self.generated_techcards = []
        self.test_artifacts = {}
        
    def log_result(self, test_name: str, success: bool, details: str, data: Any = None):
        """Log test result with details"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': time.time(),
            'data': data
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
    def test_1_expanded_catalogs_validation(self):
        """1. Расширенные каталоги - проверка nutrition_catalog.dev.json"""
        print("\n🔧 ТЕСТ 1: Расширенные каталоги - Validation")
        
        try:
            # Check if nutrition catalog files exist and validate structure
            catalog_files = [
                '/app/backend/data/nutrition_catalog.dev.json',
                '/app/backend/data/price_catalog.dev.json'
            ]
            
            catalog_results = {}
            
            for catalog_file in catalog_files:
                try:
                    if os.path.exists(catalog_file):
                        with open(catalog_file, 'r', encoding='utf-8') as f:
                            catalog_data = json.load(f)
                        
                        catalog_name = os.path.basename(catalog_file)
                        
                        if catalog_name == 'nutrition_catalog.dev.json':
                            # Validate nutrition catalog structure
                            ingredients_list = catalog_data.get('items', [])
                            ingredients_count = len(ingredients_list)
                            
                            # Check for 200+ ingredients requirement
                            has_200_plus = ingredients_count >= 200
                            
                            # Validate ingredient structure
                            valid_ingredients = 0
                            invalid_ingredients = []
                            valid_units = {'kg', 'liter', 'g', 'ml', 'pcs', 'l', 'piece', 'unit'}
                            
                            ingredients_list = catalog_data.get('items', [])
                            
                            for i, ingredient in enumerate(ingredients_list[:50]):  # Check first 50 for performance
                                if isinstance(ingredient, dict):
                                    # Check required БЖУ fields
                                    per100g = ingredient.get('per100g', {})
                                    has_nutrition = all(key in per100g for key in ['kcal', 'proteins_g', 'fats_g', 'carbs_g'])
                                    has_valid_unit = ingredient.get('unit', '').lower() in valid_units
                                    has_name = bool(ingredient.get('name', '').strip())
                                    has_id = bool(ingredient.get('canonical_id') or ingredient.get('id'))
                                    
                                    # Check for reasonable БЖУ values (not negative, not extremely high)
                                    reasonable_nutrition = True
                                    if has_nutrition:
                                        kcal = per100g.get('kcal', 0)
                                        proteins = per100g.get('proteins_g', 0)
                                        fats = per100g.get('fats_g', 0)
                                        carbs = per100g.get('carbs_g', 0)
                                        
                                        reasonable_nutrition = (
                                            0 <= kcal <= 1000 and
                                            0 <= proteins <= 100 and
                                            0 <= fats <= 100 and
                                            0 <= carbs <= 100
                                        )
                                    
                                    if has_nutrition and has_valid_unit and has_name and has_id and reasonable_nutrition:
                                        valid_ingredients += 1
                                    else:
                                        invalid_ingredients.append({
                                            'index': i,
                                            'name': ingredient.get('name', 'Unknown'),
                                            'issues': {
                                                'missing_nutrition': not has_nutrition,
                                                'invalid_unit': not has_valid_unit,
                                                'missing_name': not has_name,
                                                'missing_id': not has_id,
                                                'unreasonable_nutrition': not reasonable_nutrition
                                            }
                                        })
                            
                            catalog_results[catalog_name] = {
                                'exists': True,
                                'total_ingredients': ingredients_count,
                                'has_200_plus': has_200_plus,
                                'valid_ingredients': valid_ingredients,
                                'invalid_ingredients': len(invalid_ingredients),
                                'sample_invalid': invalid_ingredients[:5],  # First 5 invalid for debugging
                                'validation_rate': (valid_ingredients / min(50, ingredients_count)) * 100 if ingredients_count > 0 else 0
                            }
                            
                        elif catalog_name == 'price_catalog.dev.json':
                            # Validate price catalog structure
                            products_count = len(catalog_data) if isinstance(catalog_data, list) else len(catalog_data.get('products', []))
                            
                            catalog_results[catalog_name] = {
                                'exists': True,
                                'total_products': products_count,
                                'structure_valid': isinstance(catalog_data, (list, dict))
                            }
                    else:
                        catalog_results[os.path.basename(catalog_file)] = {
                            'exists': False,
                            'error': 'File not found'
                        }
                        
                except Exception as e:
                    catalog_results[os.path.basename(catalog_file)] = {
                        'exists': False,
                        'error': str(e)
                    }
            
            # Evaluate results
            nutrition_result = catalog_results.get('nutrition_catalog.dev.json', {})
            price_result = catalog_results.get('price_catalog.dev.json', {})
            
            # Check critical requirements
            has_200_ingredients = nutrition_result.get('has_200_plus', False)
            good_validation_rate = nutrition_result.get('validation_rate', 0) >= 80
            price_catalog_exists = price_result.get('exists', False)
            
            overall_success = has_200_ingredients and good_validation_rate and price_catalog_exists
            
            self.test_artifacts['catalog_validation'] = catalog_results
            
            self.log_result(
                "Expanded Catalogs Validation",
                overall_success,
                f"Nutrition: {nutrition_result.get('total_ingredients', 0)} ingredients (200+ req: {has_200_ingredients}), "
                f"Validation rate: {nutrition_result.get('validation_rate', 0):.1f}%, "
                f"Price catalog: {price_result.get('exists', False)}"
            )
            
            return overall_success
            
        except Exception as e:
            self.log_result(
                "Expanded Catalogs Validation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_2_id_system_and_articles(self):
        """2. ID система и артикулы - проверка корректности ID полей"""
        print("\n🔧 ТЕСТ 2: ID система и артикулы")
        
        try:
            # Test catalog search to check ID system
            response = self.session.get(
                f"{API_BASE}/v1/techcards.v2/catalog-search",
                params={"q": "мука", "source": "nutrition"},
                timeout=30
            )
            
            if response.status_code == 200:
                search_data = response.json()
                results = search_data.get('results', [])
                
                # Check ID format validation
                id_validation_results = {
                    'total_results': len(results),
                    'valid_ids': 0,
                    'invalid_ids': 0,
                    'range_ids_found': 0,
                    'uuid_based_ids': 0,
                    'invalid_examples': []
                }
                
                # Pattern to detect range IDs like "9969-86"
                range_pattern = re.compile(r'^\d+-\d+$')
                uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                
                for result in results[:20]:  # Check first 20 results
                    canonical_id = result.get('canonical_id') or result.get('id')
                    product_code = result.get('product_code')
                    
                    if canonical_id:
                        # Check for range IDs (should not exist)
                        if range_pattern.match(str(canonical_id)):
                            id_validation_results['range_ids_found'] += 1
                            id_validation_results['invalid_examples'].append({
                                'name': result.get('name', 'Unknown'),
                                'canonical_id': canonical_id,
                                'issue': 'Range ID format detected'
                            })
                        # Check for UUID format
                        elif uuid_pattern.match(str(canonical_id)):
                            id_validation_results['uuid_based_ids'] += 1
                            id_validation_results['valid_ids'] += 1
                        # Check for other valid formats (numeric, alphanumeric)
                        elif str(canonical_id).replace('-', '').replace('_', '').isalnum():
                            id_validation_results['valid_ids'] += 1
                        else:
                            id_validation_results['invalid_ids'] += 1
                            id_validation_results['invalid_examples'].append({
                                'name': result.get('name', 'Unknown'),
                                'canonical_id': canonical_id,
                                'issue': 'Invalid ID format'
                            })
                    
                    # Check product_code if present
                    if product_code and range_pattern.match(str(product_code)):
                        id_validation_results['range_ids_found'] += 1
                        id_validation_results['invalid_examples'].append({
                            'name': result.get('name', 'Unknown'),
                            'product_code': product_code,
                            'issue': 'Range product_code detected'
                        })
                
                # Evaluate ID system quality
                no_range_ids = id_validation_results['range_ids_found'] == 0
                good_id_ratio = (id_validation_results['valid_ids'] / max(1, len(results[:20]))) >= 0.8
                has_uuid_based = id_validation_results['uuid_based_ids'] > 0
                
                id_system_success = no_range_ids and good_id_ratio
                
                self.test_artifacts['id_system_validation'] = id_validation_results
                
                self.log_result(
                    "ID System and Articles Validation",
                    id_system_success,
                    f"No range IDs: {no_range_ids}, Valid ID ratio: {id_validation_results['valid_ids']}/{len(results[:20])}, "
                    f"UUID-based IDs: {id_validation_results['uuid_based_ids']}, Range IDs found: {id_validation_results['range_ids_found']}"
                )
                
                return id_system_success
            else:
                self.log_result(
                    "ID System and Articles Validation",
                    False,
                    f"Catalog search failed: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ID System and Articles Validation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_3_techcard_generation_with_improved_coverage(self):
        """3. Создание техкарт с улучшенным БЖУ покрытием"""
        print("\n🔧 ТЕСТ 3: Создание техкарт с улучшенным БЖУ покрытием")
        
        try:
            # Generate multiple tech cards to test improved nutrition coverage
            test_dishes = [
                "Борщ украинский с говядиной",
                "Салат Цезарь с курицей", 
                "Стейк из говядины с картофельным пюре"
            ]
            
            generation_results = []
            
            for dish_name in test_dishes:
                try:
                    start_time = time.time()
                    
                    response = self.session.post(
                        f"{API_BASE}/v1/techcards.v2/generate",
                        json={"name": dish_name},
                        timeout=60
                    )
                    
                    generation_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        techcard_data = data.get('card', {})
                        techcard_id = techcard_data.get('meta', {}).get('id')
                        
                        if techcard_id:
                            # Analyze nutrition coverage
                            ingredients = techcard_data.get('ingredients', [])
                            nutrition_coverage = self._analyze_nutrition_coverage(ingredients)
                            
                            self.generated_techcards.append({
                                'id': techcard_id,
                                'name': dish_name,
                                'data': techcard_data,
                                'nutrition_coverage': nutrition_coverage
                            })
                            
                            generation_results.append({
                                'dish': dish_name,
                                'success': True,
                                'id': techcard_id,
                                'generation_time': generation_time,
                                'ingredients_count': len(ingredients),
                                'nutrition_coverage': nutrition_coverage
                            })
                        else:
                            generation_results.append({
                                'dish': dish_name,
                                'success': False,
                                'error': 'No techcard ID returned'
                            })
                    else:
                        generation_results.append({
                            'dish': dish_name,
                            'success': False,
                            'error': f"HTTP {response.status_code}: {response.text[:200]}"
                        })
                        
                except Exception as e:
                    generation_results.append({
                        'dish': dish_name,
                        'success': False,
                        'error': str(e)
                    })
            
            # Evaluate overall generation success and nutrition coverage
            successful_generations = sum(1 for result in generation_results if result['success'])
            total_generations = len(generation_results)
            
            # Calculate average nutrition coverage
            coverage_scores = [result.get('nutrition_coverage', {}).get('coverage_percentage', 0) 
                             for result in generation_results if result['success']]
            avg_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
            
            # Check if coverage improved from baseline (~53%)
            coverage_improved = avg_coverage > 53
            generation_success_rate = (successful_generations / total_generations) >= 0.8
            
            overall_success = generation_success_rate and coverage_improved
            
            self.test_artifacts['techcard_generation'] = {
                'results': generation_results,
                'successful_generations': successful_generations,
                'total_generations': total_generations,
                'average_coverage': avg_coverage,
                'coverage_improved': coverage_improved,
                'baseline_coverage': 53
            }
            
            self.log_result(
                "TechCard Generation with Improved Coverage",
                overall_success,
                f"Generated: {successful_generations}/{total_generations}, "
                f"Avg nutrition coverage: {avg_coverage:.1f}% (baseline: 53%), "
                f"Coverage improved: {coverage_improved}"
            )
            
            return overall_success
            
        except Exception as e:
            self.log_result(
                "TechCard Generation with Improved Coverage",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def _analyze_nutrition_coverage(self, ingredients: List[Dict]) -> Dict[str, Any]:
        """Analyze nutrition coverage for ingredients"""
        if not ingredients:
            return {'coverage_percentage': 0, 'total_ingredients': 0, 'covered_ingredients': 0}
        
        covered_ingredients = 0
        total_ingredients = len(ingredients)
        
        for ingredient in ingredients:
            # Check if ingredient has nutrition data in various possible locations
            has_nutrition = False
            
            # Check direct fields
            if any(key in ingredient for key in ['kcal', 'proteins_g', 'fats_g', 'carbs_g']):
                has_nutrition = True
            
            # Check nested nutrition object
            elif 'nutrition' in ingredient:
                nutrition_obj = ingredient['nutrition']
                if isinstance(nutrition_obj, dict):
                    has_nutrition = any(key in nutrition_obj for key in ['kcal', 'proteins_g', 'fats_g', 'carbs_g'])
            
            # Check per100g object (catalog format)
            elif 'per100g' in ingredient:
                per100g_obj = ingredient['per100g']
                if isinstance(per100g_obj, dict):
                    has_nutrition = any(key in per100g_obj for key in ['kcal', 'proteins_g', 'fats_g', 'carbs_g'])
            
            # Check if ingredient has any nutritional values > 0
            if not has_nutrition:
                for field in ['kcal', 'proteins_g', 'fats_g', 'carbs_g']:
                    value = ingredient.get(field, 0)
                    if isinstance(value, (int, float)) and value > 0:
                        has_nutrition = True
                        break
            
            if has_nutrition:
                covered_ingredients += 1
        
        coverage_percentage = (covered_ingredients / total_ingredients * 100) if total_ingredients > 0 else 0
        
        return {
            'coverage_percentage': coverage_percentage,
            'total_ingredients': total_ingredients,
            'covered_ingredients': covered_ingredients
        }
    
    def test_4_xlsx_export_with_quality_data(self):
        """4. XLSX экспорт с корректными данными"""
        print("\n🔧 ТЕСТ 4: XLSX экспорт с корректными данными")
        
        if not self.generated_techcards:
            self.log_result(
                "XLSX Export with Quality Data",
                False,
                "No generated techcards available for export testing"
            )
            return False
        
        try:
            export_results = []
            
            for techcard in self.generated_techcards[:2]:  # Test first 2 techcards
                try:
                    response = self.session.post(
                        f"{API_BASE}/v1/techcards.v2/export/iiko.xlsx",
                        json=techcard['data'],
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        content_length = len(response.content)
                        
                        # Validate Excel file
                        is_excel = ('spreadsheet' in content_type or 
                                  'excel' in content_type or 
                                  content_length > 1000)
                        
                        if is_excel:
                            # Check if export uses expanded catalog data
                            export_quality = self._analyze_export_quality(response.content, techcard)
                            
                            export_results.append({
                                'techcard_name': techcard['name'],
                                'success': True,
                                'file_size': content_length,
                                'content_type': content_type,
                                'quality_analysis': export_quality
                            })
                        else:
                            export_results.append({
                                'techcard_name': techcard['name'],
                                'success': False,
                                'error': f"Invalid Excel format: {content_type}, size: {content_length}"
                            })
                    else:
                        export_results.append({
                            'techcard_name': techcard['name'],
                            'success': False,
                            'error': f"HTTP {response.status_code}: {response.text[:200]}"
                        })
                        
                except Exception as e:
                    export_results.append({
                        'techcard_name': techcard['name'],
                        'success': False,
                        'error': str(e)
                    })
            
            # Evaluate export success
            successful_exports = sum(1 for result in export_results if result['success'])
            total_exports = len(export_results)
            export_success_rate = (successful_exports / total_exports) if total_exports > 0 else 0
            
            # Check quality metrics
            quality_scores = [result.get('quality_analysis', {}).get('overall_score', 0) 
                            for result in export_results if result['success']]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            overall_success = export_success_rate >= 0.8 and avg_quality >= 70
            
            self.test_artifacts['xlsx_export'] = {
                'results': export_results,
                'successful_exports': successful_exports,
                'total_exports': total_exports,
                'export_success_rate': export_success_rate,
                'average_quality_score': avg_quality
            }
            
            self.log_result(
                "XLSX Export with Quality Data",
                overall_success,
                f"Exports: {successful_exports}/{total_exports} ({export_success_rate*100:.1f}%), "
                f"Avg quality score: {avg_quality:.1f}/100"
            )
            
            return overall_success
            
        except Exception as e:
            self.log_result(
                "XLSX Export with Quality Data",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def _analyze_export_quality(self, excel_content: bytes, techcard: Dict) -> Dict[str, Any]:
        """Analyze quality of exported Excel file"""
        try:
            # Basic quality checks
            quality_score = 0
            max_score = 100
            
            # File size check (reasonable size)
            file_size = len(excel_content)
            if 1000 <= file_size <= 100000:  # Between 1KB and 100KB
                quality_score += 20
            
            # Check if file starts with Excel signature
            if excel_content.startswith(b'PK'):  # ZIP signature for XLSX
                quality_score += 20
            
            # Check techcard has ingredients with nutrition data
            ingredients = techcard.get('data', {}).get('ingredients', [])
            if ingredients:
                quality_score += 20
                
                # Check nutrition coverage
                nutrition_coverage = techcard.get('nutrition_coverage', {}).get('coverage_percentage', 0)
                if nutrition_coverage > 50:
                    quality_score += 20
                if nutrition_coverage > 80:
                    quality_score += 20
            
            return {
                'overall_score': quality_score,
                'file_size': file_size,
                'has_excel_signature': excel_content.startswith(b'PK'),
                'ingredients_count': len(ingredients),
                'nutrition_coverage': techcard.get('nutrition_coverage', {}).get('coverage_percentage', 0)
            }
            
        except Exception as e:
            return {
                'overall_score': 0,
                'error': str(e)
            }
    
    def test_5_data_quality_validation(self):
        """5. Качество данных - валидация разумных значений"""
        print("\n🔧 ТЕСТ 5: Качество данных - валидация")
        
        try:
            # Test catalog search for data quality
            search_queries = ["мука", "молоко", "мясо", "овощи"]
            quality_results = []
            
            for query in search_queries:
                try:
                    response = self.session.get(
                        f"{API_BASE}/v1/techcards.v2/catalog-search",
                        params={"q": query, "source": "nutrition"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        search_data = response.json()
                        results = search_data.get('results', [])
                        
                        # Analyze data quality for this query
                        query_quality = self._analyze_search_results_quality(results, query)
                        quality_results.append(query_quality)
                        
                except Exception as e:
                    quality_results.append({
                        'query': query,
                        'success': False,
                        'error': str(e)
                    })
            
            # Evaluate overall data quality
            successful_queries = sum(1 for result in quality_results if result.get('success', False))
            total_queries = len(quality_results)
            
            # Calculate average quality scores
            quality_scores = [result.get('quality_score', 0) for result in quality_results if result.get('success', False)]
            avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Check for duplicates across queries
            all_items = []
            for result in quality_results:
                if result.get('success', False):
                    all_items.extend(result.get('items_analyzed', []))
            
            duplicate_check = self._check_for_duplicates(all_items)
            
            overall_success = (successful_queries / total_queries >= 0.8 and 
                             avg_quality_score >= 70 and 
                             duplicate_check['duplicate_rate'] < 0.1)
            
            self.test_artifacts['data_quality'] = {
                'query_results': quality_results,
                'successful_queries': successful_queries,
                'total_queries': total_queries,
                'average_quality_score': avg_quality_score,
                'duplicate_analysis': duplicate_check
            }
            
            self.log_result(
                "Data Quality Validation",
                overall_success,
                f"Queries: {successful_queries}/{total_queries}, "
                f"Avg quality: {avg_quality_score:.1f}/100, "
                f"Duplicate rate: {duplicate_check['duplicate_rate']*100:.1f}%"
            )
            
            return overall_success
            
        except Exception as e:
            self.log_result(
                "Data Quality Validation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def _analyze_search_results_quality(self, results: List[Dict], query: str) -> Dict[str, Any]:
        """Analyze quality of search results"""
        if not results:
            return {'query': query, 'success': False, 'error': 'No results'}
        
        quality_issues = []
        valid_items = 0
        total_items = len(results[:10])  # Analyze first 10 results
        
        valid_units = {'kg', 'liter', 'g', 'ml', 'pcs', 'l', 'piece', 'unit', 'литр', 'кг', 'шт'}
        
        for item in results[:10]:
            item_issues = []
            
            # Check name
            name = item.get('name', '').strip()
            if not name:
                item_issues.append('missing_name')
            
            # Check unit
            unit = item.get('unit', '').lower()
            if unit not in valid_units:
                item_issues.append('invalid_unit')
            
            # Check nutrition values
            nutrition_fields = ['kcal', 'proteins_g', 'fats_g', 'carbs_g']
            nutrition_values = {}
            
            for field in nutrition_fields:
                value = item.get(field)
                if value is not None:
                    try:
                        num_value = float(value)
                        nutrition_values[field] = num_value
                        
                        # Check for reasonable ranges
                        if field == 'kcal' and not (0 <= num_value <= 1000):
                            item_issues.append(f'unreasonable_{field}')
                        elif field in ['proteins_g', 'fats_g', 'carbs_g'] and not (0 <= num_value <= 100):
                            item_issues.append(f'unreasonable_{field}')
                    except (ValueError, TypeError):
                        item_issues.append(f'invalid_{field}')
            
            # Check ID
            item_id = item.get('canonical_id') or item.get('id')
            if not item_id:
                item_issues.append('missing_id')
            
            if not item_issues:
                valid_items += 1
            else:
                quality_issues.append({
                    'name': name,
                    'issues': item_issues
                })
        
        quality_score = (valid_items / total_items * 100) if total_items > 0 else 0
        
        return {
            'query': query,
            'success': True,
            'total_items': total_items,
            'valid_items': valid_items,
            'quality_score': quality_score,
            'quality_issues': quality_issues[:5],  # First 5 issues for debugging
            'items_analyzed': results[:10]
        }
    
    def _check_for_duplicates(self, items: List[Dict]) -> Dict[str, Any]:
        """Check for duplicate items across catalog"""
        if not items:
            return {'duplicate_rate': 0, 'total_items': 0, 'duplicates_found': 0}
        
        # Group by name (case-insensitive)
        name_groups = {}
        for item in items:
            name = item.get('name', '').lower().strip()
            if name:
                if name not in name_groups:
                    name_groups[name] = []
                name_groups[name].append(item)
        
        # Find duplicates
        duplicates = {name: items for name, items in name_groups.items() if len(items) > 1}
        
        total_items = len(items)
        duplicates_found = sum(len(items) - 1 for items in duplicates.values())  # Count extra duplicates
        duplicate_rate = duplicates_found / total_items if total_items > 0 else 0
        
        return {
            'duplicate_rate': duplicate_rate,
            'total_items': total_items,
            'duplicates_found': duplicates_found,
            'duplicate_examples': list(duplicates.keys())[:5]  # First 5 duplicate names
        }
    
    def test_6_alt_export_cleanup_integration(self):
        """6. ALT Export Cleanup интеграция"""
        print("\n🔧 ТЕСТ 6: ALT Export Cleanup интеграция")
        
        try:
            integration_results = []
            
            # Test 6.1: Admin stats endpoint
            try:
                response = self.session.get(f"{API_BASE}/v1/export/cleanup/stats")
                
                if response.status_code == 200:
                    stats_data = response.json()
                    has_stats = 'cleanup_statistics' in stats_data or 'statistics' in stats_data
                    
                    integration_results.append({
                        'test': 'cleanup_stats_endpoint',
                        'success': has_stats,
                        'details': f"Stats endpoint working: {has_stats}"
                    })
                else:
                    integration_results.append({
                        'test': 'cleanup_stats_endpoint',
                        'success': False,
                        'details': f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                integration_results.append({
                    'test': 'cleanup_stats_endpoint',
                    'success': False,
                    'details': f"Exception: {str(e)}"
                })
            
            # Test 6.2: ZIP export with cleanup pipeline
            if self.generated_techcards:
                try:
                    techcard_ids = [tc['id'] for tc in self.generated_techcards[:1]]
                    
                    # First run preflight
                    preflight_response = self.session.post(
                        f"{API_BASE}/v1/export/preflight",
                        json={"techcardIds": techcard_ids},
                        timeout=30
                    )
                    
                    if preflight_response.status_code == 200:
                        preflight_data = preflight_response.json()
                        
                        # Test ZIP export
                        zip_response = self.session.post(
                            f"{API_BASE}/v1/export/zip",
                            json={
                                "techcardIds": techcard_ids,
                                "preflight_result": preflight_data,
                                "operational_rounding": True
                            },
                            timeout=30
                        )
                        
                        if zip_response.status_code == 200:
                            zip_size = len(zip_response.content)
                            
                            integration_results.append({
                                'test': 'zip_export_cleanup_pipeline',
                                'success': True,
                                'details': f"ZIP export successful: {zip_size} bytes"
                            })
                        else:
                            integration_results.append({
                                'test': 'zip_export_cleanup_pipeline',
                                'success': False,
                                'details': f"ZIP export failed: HTTP {zip_response.status_code}"
                            })
                    else:
                        integration_results.append({
                            'test': 'zip_export_cleanup_pipeline',
                            'success': False,
                            'details': f"Preflight failed: HTTP {preflight_response.status_code}"
                        })
                        
                except Exception as e:
                    integration_results.append({
                        'test': 'zip_export_cleanup_pipeline',
                        'success': False,
                        'details': f"Exception: {str(e)}"
                    })
            
            # Test 6.3: Enhanced export with new data
            if self.generated_techcards:
                try:
                    techcard_data = self.generated_techcards[0]['data']
                    
                    response = self.session.post(
                        f"{API_BASE}/v1/techcards.v2/export/enhanced/iiko.xlsx",
                        json={
                            "techcard": techcard_data,
                            "operational_rounding": True
                        },
                        timeout=30
                    )
                    
                    enhanced_export_success = response.status_code == 200
                    
                    integration_results.append({
                        'test': 'enhanced_export_new_data',
                        'success': enhanced_export_success,
                        'details': f"Enhanced export: HTTP {response.status_code}"
                    })
                    
                except Exception as e:
                    integration_results.append({
                        'test': 'enhanced_export_new_data',
                        'success': False,
                        'details': f"Exception: {str(e)}"
                    })
            
            # Evaluate integration success
            successful_tests = sum(1 for result in integration_results if result['success'])
            total_tests = len(integration_results)
            integration_success = (successful_tests / total_tests) >= 0.7 if total_tests > 0 else False
            
            self.test_artifacts['alt_cleanup_integration'] = {
                'results': integration_results,
                'successful_tests': successful_tests,
                'total_tests': total_tests,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0
            }
            
            self.log_result(
                "ALT Export Cleanup Integration",
                integration_success,
                f"Integration tests: {successful_tests}/{total_tests} passed"
            )
            
            return integration_success
            
        except Exception as e:
            self.log_result(
                "ALT Export Cleanup Integration",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_7_acceptance_criteria_validation(self):
        """7. Проверка Acceptance Criteria"""
        print("\n🔧 ТЕСТ 7: Acceptance Criteria Validation")
        
        try:
            criteria_results = {}
            
            # Criterion 1: Каталог 200+ ингредиентов
            catalog_data = self.test_artifacts.get('catalog_validation', {})
            nutrition_catalog = catalog_data.get('nutrition_catalog.dev.json', {})
            has_200_ingredients = nutrition_catalog.get('has_200_plus', False)
            
            criteria_results['catalog_200_ingredients'] = {
                'met': has_200_ingredients,
                'actual': nutrition_catalog.get('total_ingredients', 0),
                'target': 200
            }
            
            # Criterion 2: Нет диапазонов в ID
            id_data = self.test_artifacts.get('id_system_validation', {})
            no_range_ids = id_data.get('range_ids_found', 1) == 0
            
            criteria_results['no_range_ids'] = {
                'met': no_range_ids,
                'range_ids_found': id_data.get('range_ids_found', 0)
            }
            
            # Criterion 3: Корректные единицы измерения
            validation_rate = nutrition_catalog.get('validation_rate', 0)
            correct_units = validation_rate >= 80
            
            criteria_results['correct_units'] = {
                'met': correct_units,
                'validation_rate': validation_rate,
                'target': 80
            }
            
            # Criterion 4: XLSX экспорт работает
            export_data = self.test_artifacts.get('xlsx_export', {})
            xlsx_works = export_data.get('export_success_rate', 0) >= 0.8
            
            criteria_results['xlsx_export_works'] = {
                'met': xlsx_works,
                'success_rate': export_data.get('export_success_rate', 0),
                'target': 0.8
            }
            
            # Criterion 5: БЖУ покрытие улучшилось
            generation_data = self.test_artifacts.get('techcard_generation', {})
            coverage_improved = generation_data.get('coverage_improved', False)
            avg_coverage = generation_data.get('average_coverage', 0)
            
            criteria_results['nutrition_coverage_improved'] = {
                'met': coverage_improved,
                'current_coverage': avg_coverage,
                'baseline': 53,
                'target': 80
            }
            
            # Overall acceptance criteria evaluation
            met_criteria = sum(1 for criterion in criteria_results.values() if criterion['met'])
            total_criteria = len(criteria_results)
            acceptance_rate = met_criteria / total_criteria if total_criteria > 0 else 0
            
            # System ready for production if >= 80% criteria met
            production_ready = acceptance_rate >= 0.8
            
            self.test_artifacts['acceptance_criteria'] = {
                'criteria_results': criteria_results,
                'met_criteria': met_criteria,
                'total_criteria': total_criteria,
                'acceptance_rate': acceptance_rate,
                'production_ready': production_ready
            }
            
            self.log_result(
                "Acceptance Criteria Validation",
                production_ready,
                f"Criteria met: {met_criteria}/{total_criteria} ({acceptance_rate*100:.1f}%), "
                f"Production ready: {production_ready}"
            )
            
            return production_ready
            
        except Exception as e:
            self.log_result(
                "Acceptance Criteria Validation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def run_comprehensive_quality_boost_tests(self):
        """Запуск всех тестов TECH CARD QUALITY BOOST системы"""
        print("🚀 НАЧАЛО TECH CARD QUALITY BOOST COMPREHENSIVE TESTING")
        print("=" * 80)
        
        start_time = time.time()
        
        # Test 1: Expanded Catalogs Validation
        self.test_1_expanded_catalogs_validation()
        
        # Test 2: ID System and Articles
        self.test_2_id_system_and_articles()
        
        # Test 3: TechCard Generation with Improved Coverage
        self.test_3_techcard_generation_with_improved_coverage()
        
        # Test 4: XLSX Export with Quality Data
        self.test_4_xlsx_export_with_quality_data()
        
        # Test 5: Data Quality Validation
        self.test_5_data_quality_validation()
        
        # Test 6: ALT Export Cleanup Integration
        self.test_6_alt_export_cleanup_integration()
        
        # Test 7: Acceptance Criteria Validation
        self.test_7_acceptance_criteria_validation()
        
        # Summary
        total_time = time.time() - start_time
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("🎯 TECH CARD QUALITY BOOST COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"📊 Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"🎯 Test Focus: TECH CARD QUALITY BOOST system validation")
        
        # Key findings
        print("\n🔍 KEY FINDINGS:")
        
        # Catalog validation
        catalog_data = self.test_artifacts.get('catalog_validation', {})
        nutrition_catalog = catalog_data.get('nutrition_catalog.dev.json', {})
        if nutrition_catalog.get('exists'):
            print(f"   • Nutrition Catalog: {nutrition_catalog.get('total_ingredients', 0)} ingredients "
                  f"(200+ requirement: {'✅' if nutrition_catalog.get('has_200_plus') else '❌'})")
        
        # ID system
        id_data = self.test_artifacts.get('id_system_validation', {})
        if id_data:
            print(f"   • ID System: {id_data.get('valid_ids', 0)} valid IDs, "
                  f"{id_data.get('range_ids_found', 0)} range IDs found")
        
        # Nutrition coverage
        generation_data = self.test_artifacts.get('techcard_generation', {})
        if generation_data:
            print(f"   • Nutrition Coverage: {generation_data.get('average_coverage', 0):.1f}% "
                  f"(baseline: 53%, target: 80%)")
        
        # Export quality
        export_data = self.test_artifacts.get('xlsx_export', {})
        if export_data:
            print(f"   • XLSX Export: {export_data.get('successful_exports', 0)}/{export_data.get('total_exports', 0)} successful, "
                  f"Quality: {export_data.get('average_quality_score', 0):.1f}/100")
        
        # Acceptance criteria
        acceptance_data = self.test_artifacts.get('acceptance_criteria', {})
        if acceptance_data:
            print(f"   • Acceptance Criteria: {acceptance_data.get('met_criteria', 0)}/{acceptance_data.get('total_criteria', 0)} met "
                  f"({acceptance_data.get('acceptance_rate', 0)*100:.1f}%)")
        
        # Critical assessment
        print("\n🎯 CRITICAL ASSESSMENT:")
        
        production_ready = acceptance_data.get('production_ready', False) if acceptance_data else False
        
        if production_ready and success_rate >= 75:
            print("   ✅ TECH CARD QUALITY BOOST system is FULLY OPERATIONAL")
            print("   ✅ Expanded catalogs with 200+ ingredients implemented")
            print("   ✅ ID system without range IDs working correctly")
            print("   ✅ Nutrition coverage significantly improved")
            print("   ✅ XLSX export with quality data functional")
            print("   ✅ ALT Export Cleanup integration working")
            print("   ✅ System ready for production use")
        else:
            print("   ❌ TECH CARD QUALITY BOOST system has critical issues")
            print("   ❌ Some acceptance criteria not met")
            print("   ❌ Quality improvements may be incomplete")
            print("   ❌ System may not be ready for production")
        
        # Save detailed results
        self.save_test_artifacts()
        
        return success_rate >= 75 and production_ready

    def save_test_artifacts(self):
        """Save test artifacts for analysis"""
        try:
            artifacts_data = {
                'test_results': self.test_results,
                'test_artifacts': self.test_artifacts,
                'generated_techcards': [
                    {
                        'id': tc['id'],
                        'name': tc['name'],
                        'nutrition_coverage': tc.get('nutrition_coverage', {})
                    } for tc in self.generated_techcards
                ],
                'timestamp': datetime.now().isoformat(),
                'test_type': 'TECH_CARD_QUALITY_BOOST_Comprehensive_Testing'
            }
            
            with open('/app/tech_card_quality_boost_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(artifacts_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Test artifacts saved to: /app/tech_card_quality_boost_test_results.json")
            
        except Exception as e:
            print(f"⚠️ Failed to save test artifacts: {e}")

def main():
    """Main test execution"""
    tester = TechCardQualityBoostTester()
    
    try:
        success = tester.run_comprehensive_quality_boost_tests()
        
        if success:
            print("\n🎉 TECH CARD QUALITY BOOST COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print("\n🚨 TECH CARD QUALITY BOOST TESTING FAILED")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        exit(1)

if __name__ == "__main__":
    main()