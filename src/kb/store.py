"""
Hybrid Knowledge Base Store (ChromaDB + BM25).
Provides dense semantic search + sparse lexical matching with Reciprocal Rank Fusion (RRF).
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from rank_bm25 import BM25Okapi
import chromadb
from sentence_transformers import SentenceTransformer

from src.kb.schema import KBRecord, SearchResult

class KnowledgeStore:
    def __init__(
        self,
        collection_name: str = "darwix_kb",
        persist_dir: str = ".chroma_kb",
        embedding_model_name: str = "all-MiniLM-L6-v2"
    ):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Initialize ChromaDB client (local persistent)
        self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # 2. Embedding model (Local SentenceTransformer)
        self.encoder = SentenceTransformer(embedding_model_name)
        
        # 3. BM25 Sparse Index State
        self.bm25: Optional[BM25Okapi] = None
        self.records_map: Dict[str, KBRecord] = {}
        self.corpus_ids: List[str] = []

    def index_records(self, records: List[KBRecord]):
        """Indexes records into both ChromaDB and BM25."""
        if not records:
            return

        self.records_map = {r.record_id: r for r in records}
        self.corpus_ids = [r.record_id for r in records]

        # A. Index into ChromaDB
        docs = [f"{r.title}\n{r.content}" for r in records]
        embeddings = self.encoder.encode(docs, normalize_embeddings=True).tolist()
        metadatas = [
            {
                "title": r.title,
                "category": r.category,
                "source": r.source,
                "version": r.version,
                "pii": r.pii
            }
            for r in records
        ]

        # Clear existing or update
        existing_ids = self.collection.get().get("ids", [])
        if existing_ids:
            self.collection.delete(ids=existing_ids)

        self.collection.add(
            ids=self.corpus_ids,
            documents=docs,
            embeddings=embeddings,
            metadatas=metadatas
        )

        # B. Index into BM25
        tokenized_corpus = [doc.lower().split() for doc in docs]
        self.bm25 = BM25Okapi(tokenized_corpus)

        print(f"Successfully indexed {len(records)} records into ChromaDB & BM25 hybrid store.")

    def search(self, query: str, top_k: int = 3, hybrid_weight: float = 0.5) -> List[SearchResult]:
        """
        Executes hybrid search combining BM25 keyword matching and Dense Cosine similarity.
        """
        if not self.records_map:
            raise ValueError("Knowledge store is empty. Ingest records before searching.")

        query_tokens = query.lower().split()
        
        # 1. BM25 scoring
        bm25_scores = self.bm25.get_scores(query_tokens)
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
        normalized_bm25 = {self.corpus_ids[i]: bm25_scores[i] / max_bm25 for i in range(len(self.corpus_ids))}

        # 2. ChromaDB Dense scoring
        query_embedding = self.encoder.encode([query], normalize_embeddings=True).tolist()
        chroma_res = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k * 2, len(self.corpus_ids))
        )
        
        dense_scores = {}
        if chroma_res["ids"] and chroma_res["distances"]:
            for r_id, dist in zip(chroma_res["ids"][0], chroma_res["distances"][0]):
                # Chroma cosine distance is in [0, 2], similarity is 1 - (dist / 2)
                sim = max(0.0, 1.0 - (dist / 2.0))
                dense_scores[r_id] = sim

        # 3. Hybrid Fusion (Weighted linear combination)
        combined_scores = {}
        for r_id in self.corpus_ids:
            b_score = normalized_bm25.get(r_id, 0.0)
            d_score = dense_scores.get(r_id, 0.0)
            combined_scores[r_id] = (1.0 - hybrid_weight) * b_score + hybrid_weight * d_score

        # Sort top K
        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for r_id, score in sorted_ids:
            rec = self.records_map[r_id]
            citation = f"[Source: {rec.source} | RecordID: {rec.record_id} | Version: {rec.version}]"
            results.append(SearchResult(
                record=rec,
                score=round(score, 4),
                retrieval_method="hybrid_bm25_dense",
                citation=citation
            ))

        return results

    @classmethod
    def load_from_processed(cls, json_path: str = "data/processed/knowledge_base.json") -> "KnowledgeStore":
        store = cls()
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        records = [KBRecord(**item) for item in raw_data]
        store.index_records(records)
        return store

if __name__ == "__main__":
    store = KnowledgeStore.load_from_processed()
    test_results = store.search("minimum monthly revenue and operating history")
    for res in test_results:
        print(f"\nScore: {res.score} | {res.citation}")
        print(f"Title: {res.record.title}")
        print(f"Content:\n{res.record.content[:200]}...")
