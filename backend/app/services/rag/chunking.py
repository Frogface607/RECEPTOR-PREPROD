"""
Умный чанкинг документов для RAG
Разбивает документы на смысловые блоки с перекрытиями и метаданными
"""
import re
from typing import List, Dict, Optional, Any
from pathlib import Path


def smart_chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    min_chunk_size: int = 100
) -> List[Dict[str, Any]]:
    """
    Умное разбиение текста на чанки с учетом структуры
    
    Args:
        text: Текст для разбиения
        chunk_size: Целевой размер чанка (символов)
        chunk_overlap: Перекрытие между чанками (символов)
        min_chunk_size: Минимальный размер чанка
    
    Returns:
        Список чанков с метаданными: {content, start, end, metadata}
    """
    if not text or len(text) < min_chunk_size:
        return [{
            'content': text,
            'start': 0,
            'end': len(text),
            'metadata': {}
        }] if text else []
    
    chunks = []
    
    # Разбиваем по заголовкам (Markdown заголовки)
    sections = re.split(r'\n(#{1,6}\s+.+?)\n', text)
    
    current_section = ""
    current_title = ""
    start_pos = 0
    
    for i, section in enumerate(sections):
        # Проверяем, является ли секция заголовком
        if re.match(r'^#{1,6}\s+', section):
            # Сохраняем предыдущую секцию если она есть
            if current_section and len(current_section) >= min_chunk_size:
                section_chunks = _chunk_section(
                    current_section,
                    current_title,
                    start_pos,
                    chunk_size,
                    chunk_overlap,
                    min_chunk_size
                )
                chunks.extend(section_chunks)
                start_pos += len(current_section)
            
            current_title = section.strip()
            current_section = ""
        else:
            current_section += section
    
    # Обрабатываем последнюю секцию
    if current_section and len(current_section) >= min_chunk_size:
        section_chunks = _chunk_section(
            current_section,
            current_title,
            start_pos,
            chunk_size,
            chunk_overlap,
            min_chunk_size
        )
        chunks.extend(section_chunks)
    
    # Если не удалось разбить по заголовкам, используем простой метод
    if not chunks:
        chunks = _simple_chunk(
            text,
            chunk_size,
            chunk_overlap,
            min_chunk_size
        )
    
    return chunks


def _chunk_section(
    text: str,
    title: str,
    start_pos: int,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int
) -> List[Dict[str, any]]:
    """Разбить секцию на чанки"""
    chunks = []
    
    # Если секция меньше chunk_size, возвращаем целиком
    if len(text) <= chunk_size:
        return [{
            'content': text,
            'start': start_pos,
            'end': start_pos + len(text),
            'metadata': {
                'title': title,
                'type': 'section'
            }
        }]
    
    # Разбиваем на параграфы
    paragraphs = re.split(r'\n\n+', text)
    
    current_chunk = ""
    chunk_start = start_pos
    
    for para in paragraphs:
        # Если добавление параграфа не превысит размер
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += (para + "\n\n" if current_chunk else para)
        else:
            # Сохраняем текущий чанк
            if current_chunk and len(current_chunk) >= min_chunk_size:
                chunks.append({
                    'content': current_chunk.strip(),
                    'start': chunk_start,
                    'end': chunk_start + len(current_chunk),
                    'metadata': {
                        'title': title,
                        'type': 'paragraph_chunk'
                    }
                })
            
            # Начинаем новый чанк с перекрытием
            overlap_text = current_chunk[-chunk_overlap:] if current_chunk else ""
            current_chunk = overlap_text + para
            chunk_start = chunk_start + len(current_chunk) - len(overlap_text) - len(para)
    
    # Сохраняем последний чанк
    if current_chunk and len(current_chunk) >= min_chunk_size:
        chunks.append({
            'content': current_chunk.strip(),
            'start': chunk_start,
            'end': chunk_start + len(current_chunk),
            'metadata': {
                'title': title,
                'type': 'paragraph_chunk'
            }
        })
    
    return chunks


def _simple_chunk(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int
) -> List[Dict[str, any]]:
    """Простое разбиение на чанки с перекрытием"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        
        # Ищем хорошую точку разрыва (конец предложения)
        if end < len(text):
            # Ищем последнюю точку, восклицательный или вопросительный знак
            last_sentence_end = max(
                chunk_text.rfind('.'),
                chunk_text.rfind('!'),
                chunk_text.rfind('?')
            )
            
            if last_sentence_end > chunk_size * 0.5:  # Если нашли в последней половине
                chunk_text = chunk_text[:last_sentence_end + 1]
                end = start + last_sentence_end + 1
        
        if len(chunk_text.strip()) >= min_chunk_size:
            chunks.append({
                'content': chunk_text.strip(),
                'start': start,
                'end': end,
                'metadata': {
                    'type': 'simple_chunk'
                }
            })
        
        # Перекрытие для следующего чанка
        start = end - chunk_overlap
    
    return chunks

