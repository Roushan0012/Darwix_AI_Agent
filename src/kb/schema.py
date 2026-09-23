"""
Traceable Knowledge Base Schema.
Matches the exact schema requirements and field examples specified in Question 2 of the AI Engineer Assessment.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class KBRecord(BaseModel):
    record_id: str = Field(..., description="Unique deterministic identifier (e.g. kb_product_001)")
    title: str = Field(..., description="Canonical title or header of the knowledge chunk")
    content: str = Field(..., description="Cleaned, standardized, grounded text content")
    category: str = Field(..., description="Domain category (e.g. qualification_rules, product_terms, objections, partnership)")
    source: str = Field(..., description="Traceable document reference (filename, section, URL, or page)")
    version: str = Field(default="1.0", description="Policy or document schema version")
    pii: bool = Field(default=False, description="Flag indicating whether content contains unmasked PII (must be False in production)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional contextual attributes (e.g. min_revenue, loan_range)")

class SearchResult(BaseModel):
    record: KBRecord
    score: float = Field(..., description="Relevance similarity score (higher is better)")
    retrieval_method: str = Field(default="hybrid", description="BM25, vector, or hybrid")
    citation: str = Field(..., description="Human-readable citation string with source and record_id")

class RetrievalTestEvaluation(BaseModel):
    query_id: str
    user_question: str
    retrieved_record_id: str
    title: str
    source_reference: str
    relevance_explanation: str
    verdict: str  # "correct" | "partially correct" | "incorrect"
    confidence_score: float
