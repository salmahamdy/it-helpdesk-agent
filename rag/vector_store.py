"""
FAISS vector store with cosine similarity (normalized inner product).
"""

import faiss
import numpy as np
from rag.embedder import embed_batch, embed_text


class VectorStore:
    def __init__(self):
        self.index: faiss.IndexFlatIP | None = None
        self.cases: list[dict] = []
        self.dimension: int = 384

    def build(self, cases: list[dict]) -> None:
        self.cases = list(cases)
        texts = [c["issue"] for c in cases]  # embed issue only — matches user queries better
        embeddings = embed_batch(texts).astype(np.float32)
        faiss.normalize_L2(embeddings)  # normalize so inner product = cosine similarity
        self.dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> list[dict]:
        if self.index is None or self.index.ntotal == 0:
            return []
        query = query_embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.cases):
                case = self.cases[idx].copy()
                case["similarity_score"] = float(score)  # cosine similarity, 0-1
                results.append(case)
        return results

    def add_case(self, case: dict) -> None:
        text = case["issue"]
        embedding = embed_text(text).astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(embedding)
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embedding)
        self.cases.append(case)
