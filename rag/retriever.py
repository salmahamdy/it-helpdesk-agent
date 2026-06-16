"""
Retriever: vector search over the MongoDB-backed knowledge base.

Flow:
  1. Load all cases from MongoDB → build FAISS index (once)
  2. On query → embed → FAISS top-k → filter by threshold
  3. On add  → write to MongoDB + append to FAISS in-memory
"""

from rag.embedder import embed_text
from rag.vector_store import VectorStore
from rag.database import get_all_cases, insert_case, update_case
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
    verified_only: bool = True,
) -> list[dict]:
    """Return up to top_k cases above the similarity threshold.

    By default only *verified* cases are returned. This is what breaks the
    self-poisoning loop: agent-generated cases are stored with verified=False,
    so they cannot be retrieved as authoritative context until a human (or a
    separate verification step) promotes them. Pass verified_only=False only
    for admin/debug use.
    """
    store = _load_store()
    query_embedding = embed_text(query)
    # Over-fetch so the verified + threshold filter can still yield up to top_k.
    raw = store.search(query_embedding, top_k * 5)
    filtered = [
        r for r in raw
        if r.get("similarity_score", 0) >= min_score
        and (not verified_only or r.get("verified", False))
    ]
    return filtered[:top_k]


def add_to_knowledge_base(case: dict) -> str:
    """Persist a new case to MongoDB and update the in-memory FAISS index."""
    case_id = insert_case(case)
    case["case_id"] = case_id
    store = _load_store()
    store.add_case(case)
    return case_id


def mark_verified(case_id: str, reviewer: str = "human") -> bool:
    """Promote a queued (verified=False) case so it becomes retrievable.

    Completes the human-in-the-loop: nothing the agent writes is trusted as
    retrieval context until it passes through here. Reloads the in-memory index
    so the change takes effect immediately.
    """
    ok = update_case(
        case_id,
        {"verified": True, "review_status": "approved", "reviewed_by": reviewer},
    )
    if ok:
        reload_store()
    return ok


def reload_store() -> None:
    """Force a full reload from MongoDB (e.g. after bulk import)."""
    global _store
    _store = None
    _load_store()
