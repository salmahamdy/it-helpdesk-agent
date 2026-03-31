import json
from rag.embedder import embed_text
from rag.vector_store import VectorStore
from config import KNOWLEDGE_BASE_PATH, TOP_K_RESULTS

_store = None


def _load_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
        cases = _load_cases()
        if cases:
            _store.build(cases)
    return _store


def _load_cases() -> list[dict]:
    try:
        with open(KNOWLEDGE_BASE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def retrieve_similar_cases(query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    store = _load_store()
    query_embedding = embed_text(query)
    return store.search(query_embedding, top_k)


def add_to_knowledge_base(case: dict) -> None:
    cases = _load_cases()
    case["id"] = str(len(cases) + 1).zfill(3)
    cases.append(case)
    with open(KNOWLEDGE_BASE_PATH, "w") as f:
        json.dump(cases, f, indent=2)
    store = _load_store()
    store.add_case(case)


def reload_store() -> None:
    global _store
    _store = None
    _load_store()
