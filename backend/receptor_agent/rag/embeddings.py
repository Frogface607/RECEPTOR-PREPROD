"""
Система векторных эмбеддингов для RAG поиска
Использует OpenAI embeddings API для семантического поиска
"""
import os
import hashlib
import json
from typing import List, Optional, Dict
from openai import OpenAI
import numpy as np
from pathlib import Path

# Инициализация OpenAI клиента
openai_api_key = os.environ.get('OPENAI_API_KEY')
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Модель для эмбеддингов (используем small для скорости и экономии)
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions, быстрая и дешевая
# Альтернатива: "text-embedding-3-large" (3072 dimensions, более точная, но дороже)

# Кэш для эмбеддингов (в памяти)
_embedding_cache: Dict[str, List[float]] = {}


def get_embedding(text: str, use_cache: bool = True) -> Optional[List[float]]:
    """
    Получить векторное представление текста через OpenAI embeddings
    
    Args:
        text: Текст для эмбеддинга
        use_cache: Использовать кэш
    
    Returns:
        Список чисел (вектор эмбеддинга) или None
    """
    if not openai_client:
        return None
    
    # Создаем ключ для кэша
    cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    # Проверяем кэш
    if use_cache and cache_key in _embedding_cache:
        return _embedding_cache[cache_key]
    
    try:
        # Получаем эмбеддинг через OpenAI API
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        
        embedding = response.data[0].embedding
        
        # Сохраняем в кэш
        if use_cache:
            _embedding_cache[cache_key] = embedding
        
        return embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Вычислить косинусное сходство между двумя векторами
    
    Args:
        vec1: Первый вектор
        vec2: Второй вектор
    
    Returns:
        Косинусное сходство (от -1 до 1, обычно 0-1)
    """
    if len(vec1) != len(vec2):
        return 0.0
    
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def batch_get_embeddings(texts: List[str], batch_size: int = 100) -> List[Optional[List[float]]]:
    """
    Получить эмбеддинги для списка текстов (батчами для оптимизации)
    
    Args:
        texts: Список текстов
        batch_size: Размер батча
    
    Returns:
        Список эмбеддингов
    """
    if not openai_client:
        return [None] * len(texts)
    
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            response = openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            
            # Кэшируем
            for text, embedding in zip(batch, batch_embeddings):
                cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
                _embedding_cache[cache_key] = embedding
                
        except Exception as e:
            print(f"Error getting batch embeddings: {e}")
            embeddings.extend([None] * len(batch))
    
    return embeddings

