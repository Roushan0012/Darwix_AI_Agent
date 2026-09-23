"""
FastAPI Knowledge Base Retrieval Service.
Exposes REST search endpoint with citations for the Question 1 voice agent and evaluation pipelines.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os

from src.kb.schema import SearchResult, KBRecord
from src.kb.store import KnowledgeStore

app = FastAPI(
    title="Darwix AI - Grounded Knowledge Base Service",
    description="Traceable, PII-scrubbed hybrid retrieval service for voice agents & RAG pipelines",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global lazy-loaded store instance
store: Optional[KnowledgeStore] = None

@app.on_event("startup")
def startup_event():
    global store
    data_path = os.path.join("data", "processed", "knowledge_base.json")
    if not os.path.exists(data_path):
        from src.kb.parser import DocumentParser
        parser = DocumentParser()
        parser.ingest_all()
    store = KnowledgeStore.load_from_processed(data_path)
    print("Knowledge store loaded and ready for queries.")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "records_count": len(store.corpus_ids) if store else 0,
        "hybrid_indexer": "ChromaDB + BM25Okapi"
    }

@app.get("/api/kb/search", response_model=List[SearchResult])
def search_knowledge_base(
    query: str = Query(..., description="The user query or voice agent inquiry"),
    top_k: int = Query(3, ge=1, le=10, description="Number of relevant chunks to retrieve"),
    category: Optional[str] = Query(None, description="Optional category filter (e.g. qualification_rules, product_terms)")
):
    """
    Retrieves grounded knowledge chunks with full source attribution and confidence scores.
    """
    global store
    if not store:
        raise HTTPException(status_code=503, detail="Knowledge store not initialized yet")

    try:
        results = store.search(query=query, top_k=top_k)
        if category:
            results = [r for r in results if r.record.category == category]
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kb/records", response_model=List[KBRecord])
def list_all_records():
    """Lists all active traceable records in the knowledge base."""
    global store
    if not store:
        raise HTTPException(status_code=503, detail="Knowledge store not initialized yet")
    return list(store.records_map.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.kb.api:app", host="0.0.0.0", port=8000, reload=False)
