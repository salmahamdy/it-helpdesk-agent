import faiss
import numpy as np
from rag.embedder import embed_batch


class VectorStore:
    def __init__(self):
        self.index = None
        self.cases = []
        self.dimension = 384

    def build(self, cases: list[dict]) -> None:
        self.cases = cases
        texts = [c["issue"] + " " + c.get("resolution", "") for c in cases]
        embeddings = embed_batch(texts).astype(np.float32)
        self.dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> list[dict]:
        if self.index is None or self.index.ntotal == 0:
            return []
        query = query_embedding.astype(np.float32).reshape(1, -1)
        distances, indices = self.index.search(query, min(top_k, self.index.ntotal))
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.cases):
                case = self.cases[idx].copy()
                case["similarity_score"] = float(1 / (1 + dist))
                results.append(case)
        return results

    def add_case(self, case: dict) -> None:
        text = case["issue"] + " " + case.get("resolution", "")
        from rag.embedder import embed_text
        embedding = embed_text(text).astype(np.float32).reshape(1, -1)
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embedding)
        self.cases.append(case)
