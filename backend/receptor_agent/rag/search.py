"""
Простой текстовый поиск по базе знаний RECEPTOR
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import re

# Путь к базе знаний
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge_base"


def search_knowledge_base(query: str, top_k: int = 5, categories: Optional[List[str]] = None) -> List[Dict[str, any]]:
    """
    Поиск по базе знаний RECEPTOR
    
    Args:
        query: Поисковый запрос
        top_k: Количество результатов
        categories: Фильтр по категориям (haccp, hr, finance, marketing, iiko)
    
    Returns:
        Список результатов с полями: content, source, category, score
    """
    if not KNOWLEDGE_BASE_PATH.exists():
        return []
    
    results = []
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    # Маппинг категорий к файлам
    category_map = {
        'haccp': ['receptor_haccp_sanpin.md'],
        'sanpin': ['receptor_haccp_sanpin.md'],
        'hr': ['receptor_hr_management.md'],
        'finance': ['receptor_financial_roi.md'],
        'roi': ['receptor_financial_roi.md'],
        'marketing': ['receptor_smm_marketing.md'],
        'smm': ['receptor_smm_marketing.md'],
        'iiko': ['receptor_iiko_technical.md'],
        'technical': ['receptor_iiko_technical.md']
    }
    
    # Определяем, какие файлы искать
    files_to_search = []
    if categories:
        for cat in categories:
            if cat.lower() in category_map:
                files_to_search.extend(category_map[cat.lower()])
    else:
        # Ищем во всех файлах
        files_to_search = [f.name for f in KNOWLEDGE_BASE_PATH.glob("*.md")]
    
    # Убираем дубликаты
    files_to_search = list(set(files_to_search))
    
    # Поиск по файлам
    for filename in files_to_search:
        filepath = KNOWLEDGE_BASE_PATH / filename
        if not filepath.exists():
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Определяем категорию из имени файла
            category = 'general'
            if 'haccp' in filename or 'sanpin' in filename:
                category = 'haccp'
            elif 'hr' in filename:
                category = 'hr'
            elif 'financial' in filename or 'roi' in filename:
                category = 'finance'
            elif 'smm' in filename or 'marketing' in filename:
                category = 'marketing'
            elif 'iiko' in filename or 'technical' in filename:
                category = 'iiko'
            
            # Простой поиск по релевантности (количество совпадений слов)
            content_lower = content.lower()
            score = 0
            
            # Подсчет совпадений слов
            for word in query_words:
                if len(word) > 2:  # Игнорируем короткие слова
                    score += content_lower.count(word)
            
            # Бонус за точное совпадение фразы
            if query_lower in content_lower:
                score += 10
            
            if score > 0:
                # Разбиваем на чанки (примерно по 500 символов)
                chunks = []
                chunk_size = 500
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    # Ищем наиболее релевантный чанк
                    chunk_score = 0
                    for word in query_words:
                        if len(word) > 2:
                            chunk_score += chunk.lower().count(word)
                    chunks.append({
                        'content': chunk,
                        'score': chunk_score,
                        'start': i
                    })
                
                # Берем лучший чанк
                best_chunk = max(chunks, key=lambda x: x['score']) if chunks else None
                
                if best_chunk:
                    results.append({
                        'content': best_chunk['content'],
                        'source': filename,
                        'category': category,
                        'score': score + best_chunk['score']
                    })
        
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue
    
    # Сортируем по релевантности и возвращаем top_k
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]


def get_document_content(filename: str) -> Optional[str]:
    """
    Получить полное содержимое документа
    
    Args:
        filename: Имя файла (например, 'receptor_haccp_sanpin.md')
    
    Returns:
        Содержимое файла или None
    """
    filepath = KNOWLEDGE_BASE_PATH / filename
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None

