"""
Retriever: vector search over the MongoDB-backed knowledge base.

Flow:
  1. Load all cases from MongoDB → build FAISS index (once)
  2. On query → embed → FAISS top-k → filter by threshold
  3. On add  → write to MongoDB + append to FAISS in-memory
"""

from rag.embedder import embed_text
from rag.vector_store import VectorStore
from rag.database import get_all_cases, insert_case
from config import TOP_K_RESULTS, SIMILARITY_THRESHOLD

_store: VectorStore | None = None


def _load_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
        cases = get_all_cases()
        if cases:
            _store.build(cases)
    return _store


def retrieve_similar_cases(
    query: str,
    top_k: int = TOP_K_RESULTS,
    min_score: float = SIMILARITY_THRESHOLD,
) -> list[dict]:
    """Return up to top_k cases above the similarity threshold."""
    store = _load_store()
    query_embedding = embed_text(query)
    results = store.search(query_embedding, top_k)
    # Filter out low-relevance noise
    return [r for r in results if r.get("similarity_score", 0) >= min_score]


def add_to_knowledge_base(case: dict) -> str:
    """Persist a new case to MongoDB and update the in-memory FAISS index."""
    case_id = insert_case(case)
    case["case_id"] = case_id
    store = _load_store()
    store.add_case(case)
    return case_id


def reload_store() -> None:
    """Force a full reload from MongoDB (e.g. after bulk import)."""
    global _store
    _store = None
    _load_store()
