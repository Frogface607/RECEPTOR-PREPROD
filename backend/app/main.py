
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import db
from app.core.logging_config import setup_logging
from app.core.rate_limit import RateLimitMiddleware
from app.api import chat, venue, iiko, history, billing, menu, staff
import logging

# Configure structured logging before anything else
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Rate limiting — 60 requests per minute per IP
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)

# CORS — настраивается через CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    # Валидация настроек при старте
    warnings = settings.validate_for_production()
    for w in warnings:
        logger.warning(w)
    db.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    db.close()

@app.get("/")
async def root():
    return {"message": "Welcome to RECEPTOR CO-PILOT API v2.0", "status": "online"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring and deploy probes."""
    health = {"status": "ok", "version": settings.VERSION}
    try:
        # Quick MongoDB ping
        if db.client:
            db.client.admin.command("ping")
            health["database"] = "connected"
        else:
            health["database"] = "not_initialized"
            health["status"] = "degraded"
    except Exception:
        health["database"] = "unreachable"
        health["status"] = "degraded"
    return health


def _check_admin_secret(secret: str):
    """Проверяет admin-секрет. Вызывает HTTPException при ошибке."""
    if not settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Admin endpoints are disabled. Set ADMIN_SECRET env var.")
    if secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")


@app.get("/api/admin/model-stats")
async def get_model_stats(secret: str = ""):
    """Статистика использования моделей (для мониторинга)"""
    _check_admin_secret(secret)
    from app.services.llm.client import MODEL_CONFIG

    return {
        "available_models": {
            complexity: {
                "model": cfg["model"],
                "description": cfg["description"],
                "cost_input_per_1k": cfg["cost_per_1k_input"],
                "cost_output_per_1k": cfg["cost_per_1k_output"]
            }
            for complexity, cfg in MODEL_CONFIG.items()
        },
        "routing": {
            "simple": "Короткие запросы, поиск, приветствия",
            "standard": "Рецепты, советы, общие вопросы",
            "advanced": "Техкарты, калькуляции, детальные инструкции",
            "expert": "Бизнес-стратегия, глубокий анализ, финмодели"
        }
    }


@app.post("/api/admin/reindex")
async def reindex_knowledge_base(background_tasks: BackgroundTasks, secret: str = ""):
    """
    Переиндексировать базу знаний RAG.
    Требует ADMIN_SECRET для защиты.
    """
    _check_admin_secret(secret)

    def run_indexer():
        try:
            from app.services.rag.indexer import index_all_documents, KNOWLEDGE_BASE_PATH

            collection = db.get_collection("knowledge_base_chunks")
            results = index_all_documents(collection, force_reindex=True)

            logger.info(f"Indexing complete: {results}")
            return results
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            return {"error": str(e)}

    background_tasks.add_task(run_indexer)

    return {
        "status": "started",
        "message": "Indexing started in background. Check logs for progress."
    }


@app.get("/api/admin/test-search")
async def test_search(query: str = "авторизация iiko API", secret: str = ""):
    """Тестовый поиск для диагностики"""
    _check_admin_secret(secret)
    try:
        from app.services.rag.search import search_knowledge_base
        from app.services.rag.indexer import get_indexed_chunks

        collection = db.get_collection("knowledge_base_chunks")

        chunks = get_indexed_chunks(collection)
        chunks_with_emb = [c for c in chunks if c.get('embedding')]

        results = search_knowledge_base(query, top_k=5, db_collection=collection)

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
        logger.error(f"Search error: {e}", exc_info=True)
        return {"error": "Internal search error. Check server logs."}


@app.get("/api/admin/index-status")
async def get_index_status(secret: str = ""):
    """Получить статус индекса базы знаний"""
    _check_admin_secret(secret)
    try:
        collection = db.get_collection("knowledge_base_chunks")

        total_chunks = collection.count_documents({"indexed": True, "type": {"$ne": "metadata"}})

        chunks_with_embeddings = collection.count_documents({
            "indexed": True,
            "type": {"$ne": "metadata"},
            "embedding": {"$ne": None, "$exists": True, "$not": {"$size": 0}}
        })

        metadata_docs = list(collection.find({"type": "metadata"}))

        files_info = []
        for doc in metadata_docs:
            files_info.append({
                "source": doc.get("source"),
                "category": doc.get("category"),
                "chunks": doc.get("chunk_count", 0),
                "indexed_at": doc.get("indexed_at")
            })

        sample_chunk = collection.find_one({"indexed": True, "type": {"$ne": "metadata"}})
        has_embedding_sample = sample_chunk and sample_chunk.get("embedding") is not None if sample_chunk else False
        embedding_length = len(sample_chunk.get("embedding", [])) if sample_chunk and sample_chunk.get("embedding") else 0

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
        logger.error(f"Index status error: {e}", exc_info=True)
        return {"status": "error", "error": "Failed to get index status. Check server logs."}


app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(venue.router, prefix="/api/venue", tags=["venue"])
app.include_router(iiko.router, prefix="/api/iiko", tags=["iiko"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
app.include_router(menu.router, prefix="/api/menu", tags=["menu"])
app.include_router(staff.router, prefix="/api/staff", tags=["staff"])
