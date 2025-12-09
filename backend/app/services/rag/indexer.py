"""
Система индексации базы знаний для векторного поиска
Создает и обновляет индекс с эмбеддингами в MongoDB
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

from .chunking import smart_chunk_text
from .embeddings import batch_get_embeddings, get_embedding


# Путь к базе знаний
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_base"

# Маппинг категорий к файлам
CATEGORY_MAP = {
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


def get_category_from_filename(filename: str) -> str:
    """Определить категорию из имени файла"""
    filename_lower = filename.lower()
    
    if 'haccp' in filename_lower or 'sanpin' in filename_lower:
        return 'haccp'
    elif 'hr' in filename_lower:
        return 'hr'
    elif 'financial' in filename_lower or 'roi' in filename_lower:
        return 'finance'
    elif 'smm' in filename_lower or 'marketing' in filename_lower:
        return 'marketing'
    elif 'iiko' in filename_lower or 'technical' in filename_lower:
        return 'iiko'
    else:
        return 'general'


def index_document(
    filepath: Path,
    db_collection,
    force_reindex: bool = False
) -> int:
    """
    Проиндексировать документ (разбить на чанки, создать эмбеддинги, сохранить в БД)
    
    Args:
        filepath: Путь к файлу
        db_collection: MongoDB коллекция для хранения индекса
        force_reindex: Принудительно переиндексировать даже если уже есть
    
    Returns:
        Количество проиндексированных чанков
    """
    if not filepath.exists():
        return 0
    
    filename = filepath.name
    category = get_category_from_filename(filename)
    
    # Проверяем, нужно ли индексировать (для async MongoDB используем await, но здесь синхронная версия)
    # В async версии нужно будет использовать await db_collection.find_one()
    if not force_reindex:
        # Для синхронного использования (если передана синхронная коллекция)
        try:
            if hasattr(db_collection, 'find_one'):
                existing = db_collection.find_one({"source": filename, "type": "metadata"})
                if existing:
                    # Проверяем хеш файла для определения изменений
                    file_hash = _get_file_hash(filepath)
                    if existing.get('file_hash') == file_hash:
                        return existing.get('chunk_count', 0)
        except Exception:
            pass  # Если async коллекция, пропускаем проверку
    
    try:
        # Читаем файл
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Разбиваем на чанки
        # Увеличенный размер для технической документации - чтобы секции не разрезались
        chunks = smart_chunk_text(
            content,
            chunk_size=1800,  # Увеличили для полных секций документации
            chunk_overlap=350,  # Больше overlap для контекста
            min_chunk_size=150
        )
        
        if not chunks:
            return 0
        
        # Получаем эмбеддинги для всех чанков (батчами)
        chunk_texts = [chunk['content'] for chunk in chunks]
        embeddings = batch_get_embeddings(chunk_texts, batch_size=100)
        
        # Удаляем старый индекс для этого файла
        db_collection.delete_many({"source": filename})
        
        # Сохраняем чанки в БД
        chunk_docs = []
        file_hash = _get_file_hash(filepath)
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{filename}_{i}_{chunk['start']}"
            
            chunk_doc = {
                "chunk_id": chunk_id,
                "source": filename,
                "category": category,
                "content": chunk['content'],
                "embedding": embedding if embedding else None,
                "start": chunk['start'],
                "end": chunk['end'],
                "metadata": chunk.get('metadata', {}),
                "indexed": True,
                "indexed_at": datetime.utcnow(),
                "file_hash": file_hash
            }
            
            chunk_docs.append(chunk_doc)
        
        # Вставляем все чанки
        if chunk_docs:
            db_collection.insert_many(chunk_docs)
        
        # Сохраняем метаданные документа
        db_collection.update_one(
            {"source": filename, "type": "metadata"},
            {
                "$set": {
                    "source": filename,
                    "category": category,
                    "chunk_count": len(chunks),
                    "file_hash": file_hash,
                    "indexed": True,
                    "indexed_at": datetime.utcnow(),
                    "type": "metadata"
                }
            },
            upsert=True
        )
        
        return len(chunks)
        
    except Exception as e:
        print(f"Error indexing {filename}: {e}")
        return 0


def index_all_documents(db_collection, force_reindex: bool = False) -> Dict[str, int]:
    """
    Проиндексировать все документы в базе знаний
    
    Args:
        db_collection: MongoDB коллекция
        force_reindex: Принудительно переиндексировать
    
    Returns:
        Словарь {filename: chunk_count}
    """
    if not KNOWLEDGE_BASE_PATH.exists():
        return {}
    
    results = {}
    
    # Находим все .md файлы на диске
    md_files = list(KNOWLEDGE_BASE_PATH.glob("*.md"))
    current_files = {f.name for f in md_files if f.name not in ["README.md", "receptor_master_index.md"]}
    
    # Очищаем файлы которых больше нет на диске
    try:
        indexed_metadata = list(db_collection.find({"type": "metadata"}))
        indexed_sources = {doc.get("source") for doc in indexed_metadata}
        
        # Удаляем из базы файлы которые удалены с диска
        deleted_files = indexed_sources - current_files
        for deleted_file in deleted_files:
            db_collection.delete_many({"source": deleted_file})
            print(f"🗑️ Removed deleted file from index: {deleted_file}")
    except Exception as e:
        print(f"⚠️ Error cleaning old files: {e}")
    
    # Индексируем текущие файлы
    for filepath in md_files:
        if filepath.name == "README.md" or filepath.name == "receptor_master_index.md":
            continue  # Пропускаем служебные файлы
        
        chunk_count = index_document(filepath, db_collection, force_reindex)
        results[filepath.name] = chunk_count
        print(f"✅ Indexed {filepath.name}: {chunk_count} chunks")
    
    return results


def _get_file_hash(filepath: Path) -> str:
    """Вычислить хеш файла для отслеживания изменений"""
    try:
        with open(filepath, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    except Exception:
        return ""


def get_indexed_chunks(
    db_collection,
    categories: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Получить проиндексированные чанки из БД
    
    Args:
        db_collection: MongoDB коллекция
        categories: Фильтр по категориям
        limit: Лимит результатов
    
    Returns:
        Список чанков с эмбеддингами
    """
    query = {"indexed": True, "type": {"$ne": "metadata"}}
    
    if categories:
        query["category"] = {"$in": categories}
    
    cursor = db_collection.find(query)
    
    if limit:
        cursor = cursor.limit(limit)
    
    chunks = []
    for doc in cursor:
        chunks.append({
            'content': doc.get('content', ''),
            'source': doc.get('source', ''),
            'category': doc.get('category', 'general'),
            'embedding': doc.get('embedding'),
            'metadata': doc.get('metadata', {}),
            'chunk_id': doc.get('chunk_id', '')
        })
    
    return chunks

