"""
Продвинутый гибридный RAG поиск по базе знаний RECEPTOR
Использует векторный поиск, ключевые слова и BM25 для максимальной релевантности
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import re

from .vector_search import HybridSearch
from .indexer import get_indexed_chunks, index_all_documents, CATEGORY_MAP

# Путь к базе знаний
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_base"

# Глобальный экземпляр поиска
_hybrid_search = HybridSearch(vector_weight=0.7, keyword_weight=0.2, bm25_weight=0.1)


def search_knowledge_base(
    query: str,
    top_k: int = 5,
    categories: Optional[List[str]] = None,
    db_collection=None,
    use_vector_search: bool = True
) -> List[Dict[str, any]]:
    """
    Продвинутый гибридный поиск по базе знаний RECEPTOR
    
    Args:
        query: Поисковый запрос
        top_k: Количество результатов
        categories: Фильтр по категориям (haccp, hr, finance, marketing, iiko)
        db_collection: MongoDB коллекция с проиндексированными чанками
        use_vector_search: Использовать векторный поиск (True) или только текстовый (False)
    
    Returns:
        Список результатов с полями: content, source, category, score, vector_score, keyword_score, bm25_score
    """
    if not KNOWLEDGE_BASE_PATH.exists():
        return []
    
    # Если есть MongoDB коллекция и векторный поиск включен, используем его
    if db_collection is not None and use_vector_search:
        try:
            # Получаем проиндексированные чанки
            indexed_chunks = get_indexed_chunks(db_collection, categories=categories)
            
            if indexed_chunks and any(chunk.get('embedding') for chunk in indexed_chunks):
                # Используем гибридный поиск
                results = _hybrid_search.search(query, indexed_chunks, top_k=top_k)
                return results
            else:
                # Если нет эмбеддингов, используем fallback
                print("No embeddings found in indexed chunks, using text search fallback")
        except Exception as e:
            print(f"Error in vector search, falling back to text search: {e}")
    
    # Fallback: простой текстовый поиск (для обратной совместимости)
    return _simple_text_search(query, top_k, categories)


def _simple_text_search(
    query: str,
    top_k: int,
    categories: Optional[List[str]]
) -> List[Dict[str, any]]:
    """
    Простой текстовый поиск (fallback, для обратной совместимости)
    """
    results = []
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    # Определяем, какие файлы искать
    files_to_search = []
    if categories:
        for cat in categories:
            if cat.lower() in CATEGORY_MAP:
                files_to_search.extend(CATEGORY_MAP[cat.lower()])
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
            from .indexer import get_category_from_filename
            category = get_category_from_filename(filename)
            
            # Простой поиск по релевантности
            content_lower = content.lower()
            score = 0
            
            # Подсчет совпадений слов
            for word in query_words:
                if len(word) > 2:
                    score += content_lower.count(word)
            
            # Бонус за точное совпадение фразы
            if query_lower in content_lower:
                score += 10
            
            if score > 0:
                # Разбиваем на чанки
                chunks = []
                chunk_size = 500
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
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
                        'score': score + best_chunk['score'],
                        'vector_score': 0.0,
                        'keyword_score': score / 10.0 if score > 0 else 0.0,
                        'bm25_score': 0.0
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
