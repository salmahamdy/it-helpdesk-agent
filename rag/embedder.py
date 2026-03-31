from sentence_transformers import SentenceTransformer
import numpy as np
from config import EMBEDDING_MODEL

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> np.ndarray:
    model = get_model()
    return model.encode(text, convert_to_numpy=True)


def embed_batch(texts: list[str]) -> np.ndarray:
    model = get_model()
    return model.encode(texts, convert_to_numpy=True, batch_size=32, show_progress_bar=False)
