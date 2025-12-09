
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from app.core.config import settings
from app.core.database import db
from app.api import chat, venue, iiko, history

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    db.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    db.close()

@app.get("/")
async def root():
    return {"message": "Welcome to RECEPTOR CO-PILOT API v2.0", "status": "online"}


@app.post("/api/admin/reindex")
async def reindex_knowledge_base(background_tasks: BackgroundTasks, secret: str = ""):
    """
    Переиндексировать базу знаний RAG.
    Требует secret key для защиты.
    """
    # Простая защита от случайных вызовов
    if secret != "receptor2025":
        return {"error": "Invalid secret", "status": "denied"}
    
    def run_indexer():
        try:
            from app.services.rag.indexer import index_all_documents, KNOWLEDGE_BASE_PATH
            
            # Подключаемся к MongoDB
            client = MongoClient(settings.mongo_connection_string)
            db_mongo = client[settings.DB_NAME]
            collection = db_mongo["knowledge_base_chunks"]
            
            # Индексируем
            results = index_all_documents(collection, force_reindex=True)
            
            client.close()
            print(f"✅ Indexing complete: {results}")
            return results
        except Exception as e:
            print(f"❌ Indexing error: {e}")
            return {"error": str(e)}
    
    # Запускаем в фоне чтобы не блокировать ответ
    background_tasks.add_task(run_indexer)
    
    return {
        "status": "started",
        "message": "Indexing started in background. Check logs for progress."
    }


@app.get("/api/admin/test-search")
async def test_search(query: str = "авторизация iiko API"):
    """Тестовый поиск для диагностики"""
    try:
        from app.services.rag.search import search_knowledge_base
        from app.services.rag.indexer import get_indexed_chunks
        
        client = MongoClient(settings.mongo_connection_string)
        db_mongo = client[settings.DB_NAME]
        collection = db_mongo["knowledge_base_chunks"]
        
        # Получаем чанки
        chunks = get_indexed_chunks(collection)
        chunks_with_emb = [c for c in chunks if c.get('embedding')]
        
        # Пробуем поиск
        results = search_knowledge_base(query, top_k=5, db_collection=collection)
        
        client.close()
        
        return {
            "query": query,
            "total_chunks_loaded": len(chunks),
            "chunks_with_embeddings": len(chunks_with_emb),
            "results_count": len(results),
            "results": [
                {
                    "source": r.get("source"),
                    "score": r.get("score"),
                    "content_preview": r.get("content", "")[:200]
                }
                for r in results[:5]
            ]
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/admin/index-status")
async def get_index_status():
    """Получить статус индекса базы знаний"""
    try:
        client = MongoClient(settings.mongo_connection_string)
        db_mongo = client[settings.DB_NAME]
        collection = db_mongo["knowledge_base_chunks"]
        
        # Считаем чанки
        total_chunks = collection.count_documents({"indexed": True, "type": {"$ne": "metadata"}})
        
        # Считаем чанки с эмбеддингами
        chunks_with_embeddings = collection.count_documents({
            "indexed": True, 
            "type": {"$ne": "metadata"},
            "embedding": {"$ne": None, "$exists": True, "$not": {"$size": 0}}
        })
        
        # Получаем метаданные по файлам
        metadata_docs = list(collection.find({"type": "metadata"}))
        
        files_info = []
        for doc in metadata_docs:
            files_info.append({
                "source": doc.get("source"),
                "category": doc.get("category"),
                "chunks": doc.get("chunk_count", 0),
                "indexed_at": doc.get("indexed_at")
            })
        
        # Пример чанка для диагностики
        sample_chunk = collection.find_one({"indexed": True, "type": {"$ne": "metadata"}})
        has_embedding_sample = sample_chunk and sample_chunk.get("embedding") is not None if sample_chunk else False
        embedding_length = len(sample_chunk.get("embedding", [])) if sample_chunk and sample_chunk.get("embedding") else 0
        
        client.close()
        
        return {
            "status": "ok",
            "total_chunks": total_chunks,
            "chunks_with_embeddings": chunks_with_embeddings,
            "embedding_coverage": f"{chunks_with_embeddings}/{total_chunks}",
            "sample_has_embedding": has_embedding_sample,
            "sample_embedding_length": embedding_length,
            "files_count": len(files_info),
            "files": files_info
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(venue.router, prefix="/api/venue", tags=["venue"])
app.include_router(iiko.router, prefix="/api/iiko", tags=["iiko"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
