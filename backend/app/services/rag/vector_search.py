"""
Векторный поиск с гибридным подходом (векторный + ключевые слова + BM25)
"""
import os
import re
import math
from typing import List, Dict, Optional, Tuple
from collections import Counter
import numpy as np

from .embeddings import get_embedding, cosine_similarity, batch_get_embeddings
from .chunking import smart_chunk_text


class HybridSearch:
    """
    Гибридный поиск: комбинация векторного поиска, ключевых слов и BM25
    """
    
    def __init__(self, vector_weight: float = 0.7, keyword_weight: float = 0.2, bm25_weight: float = 0.1):
        """
        Args:
            vector_weight: Вес векторного поиска (семантика)
            keyword_weight: Вес поиска по ключевым словам
            bm25_weight: Вес BM25 (классическая релевантность)
        """
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.bm25_weight = bm25_weight
    
    def search(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Гибридный поиск по чанкам
        
        Args:
            query: Поисковый запрос
            chunks: Список чанков с эмбеддингами
            top_k: Количество результатов
        
        Returns:
            Отсортированные результаты с комбинированным скором
        """
        if not chunks:
            return []
        
        # Получаем эмбеддинг запроса
        query_embedding = get_embedding(query)
        
        # Если нет эмбеддинга, используем только текстовый поиск
        if not query_embedding:
            return self._keyword_search(query, chunks, top_k)
        
        results = []
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        # Вычисляем скоры для каждого чанка
        for chunk in chunks:
            chunk_embedding = chunk.get('embedding')
            chunk_content = chunk.get('content', '')
            chunk_lower = chunk_content.lower()
            
            # 1. Векторный скор (семантическое сходство)
            vector_score = 0.0
            if chunk_embedding:
                vector_score = cosine_similarity(query_embedding, chunk_embedding)
                # Нормализуем к 0-1 (cosine similarity уже в этом диапазоне)
                vector_score = max(0.0, vector_score)
            
            # 2. Ключевые слова скор
            keyword_score = self._calculate_keyword_score(query_words, chunk_lower)
            
            # 3. BM25 скор
            bm25_score = self._calculate_bm25_score(query_words, chunk_content, chunks)
            
            # Комбинированный скор
            combined_score = (
                self.vector_weight * vector_score +
                self.keyword_weight * keyword_score +
                self.bm25_weight * bm25_score
            )
            
            results.append({
                'content': chunk_content,
                'source': chunk.get('source', ''),
                'category': chunk.get('category', 'general'),
                'score': combined_score,
                'vector_score': vector_score,
                'keyword_score': keyword_score,
                'bm25_score': bm25_score,
                'metadata': chunk.get('metadata', {})
            })
        
        # Сортируем и возвращаем top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _calculate_keyword_score(self, query_words: set, text: str) -> float:
        """Вычислить скор по ключевым словам"""
        if not query_words:
            return 0.0
        
        text_words = set(re.findall(r'\w+', text.lower()))
        
        # Количество совпадающих слов
        matches = len(query_words & text_words)
        
        # Нормализуем к 0-1
        return min(1.0, matches / len(query_words))
    
    def _calculate_bm25_score(
        self,
        query_words: set,
        document: str,
        all_documents: List[Dict]
    ) -> float:
        """
        Вычислить BM25 скор (классическая релевантность)
        
        BM25 формула учитывает:
        - Частоту термина в документе
        - Обратную частоту термина в коллекции
        - Длину документа
        """
        if not query_words:
            return 0.0
        
        k1 = 1.5  # Параметр насыщения частоты
        b = 0.75  # Параметр длины документа
        avg_doc_length = sum(len(d.get('content', '')) for d in all_documents) / len(all_documents) if all_documents else 1
        doc_length = len(document)
        
        # Вычисляем IDF для каждого слова запроса
        doc_words = re.findall(r'\w+', document.lower())
        doc_word_counts = Counter(doc_words)
        
        score = 0.0
        for word in query_words:
            if len(word) < 3:  # Игнорируем короткие слова
                continue
            
            # Частота термина в документе
            tf = doc_word_counts.get(word.lower(), 0)
            
            # Количество документов, содержащих термин
            df = sum(1 for d in all_documents if word.lower() in d.get('content', '').lower())
            
            # IDF (Inverse Document Frequency)
            if df > 0:
                idf = math.log((len(all_documents) - df + 0.5) / (df + 0.5))
            else:
                idf = 0
            
            # BM25 формула
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
            
            score += idf * (numerator / denominator) if denominator > 0 else 0
        
        # Нормализуем к 0-1 (примерно)
        return min(1.0, score / 10.0)  # Делим на 10 для нормализации
    
    def _keyword_search(self, query: str, chunks: List[Dict], top_k: int) -> List[Dict]:
        """Простой поиск по ключевым словам (fallback)"""
        query_words = set(re.findall(r'\w+', query.lower()))
        results = []
        
        for chunk in chunks:
            chunk_content = chunk.get('content', '')
            keyword_score = self._calculate_keyword_score(query_words, chunk_content)
            
            if keyword_score > 0:
                results.append({
                    'content': chunk_content,
                    'source': chunk.get('source', ''),
                    'category': chunk.get('category', 'general'),
                    'score': keyword_score,
                    'vector_score': 0.0,
                    'keyword_score': keyword_score,
                    'bm25_score': 0.0,
                    'metadata': chunk.get('metadata', {})
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

