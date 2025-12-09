#!/usr/bin/env python
"""
Скрипт для индексации базы знаний в MongoDB
Запуск: python scripts/run_indexer.py
"""
import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from app.services.rag.indexer import index_all_documents, KNOWLEDGE_BASE_PATH
from app.core.config import settings


def main():
    print("🚀 RECEPTOR Knowledge Base Indexer")
    print("=" * 50)
    
    # Проверяем путь к базе знаний
    print(f"📁 Knowledge base path: {KNOWLEDGE_BASE_PATH}")
    
    if not KNOWLEDGE_BASE_PATH.exists():
        print(f"❌ Knowledge base folder not found!")
        return
    
    # Список файлов
    md_files = list(KNOWLEDGE_BASE_PATH.glob("*.md"))
    print(f"📄 Found {len(md_files)} markdown files:")
    for f in md_files:
        size_kb = f.stat().st_size / 1024
        print(f"   - {f.name} ({size_kb:.1f} KB)")
    
    print()
    
    # Подключаемся к MongoDB
    print("🔌 Connecting to MongoDB...")
    try:
        mongo_uri = settings.mongo_connection_string
        print(f"   URI: {mongo_uri[:30]}...")
        client = MongoClient(mongo_uri)
        db = client[settings.DB_NAME]
        collection = db["knowledge_base_chunks"]
        
        # Проверяем подключение
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {settings.DB_NAME}")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return
    
    print()
    print("📊 Starting indexing...")
    print("-" * 50)
    
    # Индексируем с force_reindex=True чтобы обновить всё
    results = index_all_documents(collection, force_reindex=True)
    
    print("-" * 50)
    print()
    
    # Итоги
    total_chunks = sum(results.values())
    print(f"✅ Indexing complete!")
    print(f"📊 Total: {len(results)} files, {total_chunks} chunks")
    
    # Проверяем что записалось
    chunk_count = collection.count_documents({"indexed": True, "type": {"$ne": "metadata"}})
    print(f"📦 Chunks in database: {chunk_count}")
    
    # Закрываем соединение
    client.close()
    print("🔌 MongoDB connection closed")


if __name__ == "__main__":
    main()

