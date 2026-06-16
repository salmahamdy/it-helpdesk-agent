from sentence_transformers import SentenceTransformer
import numpy as np
import os
from config import EMBEDDING_MODEL

# Default to CPU. MiniLM is tiny, so CPU is plenty fast and avoids GPU/torch
# kernel-mismatch errors (cudaErrorNoKernelImageForDevice). Set EMBEDDING_DEVICE=cuda
# only if you have a torch build whose kernels match your GPU.
_DEVICE = os.environ.get("EMBEDDING_DEVICE", "cpu")

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL, device=_DEVICE)
    return _model


def embed_text(text: str) -> np.ndarray:
    model = get_model()
    return model.encode(text, convert_to_numpy=True)


def embed_batch(texts: list[str]) -> np.ndarray:
    model = get_model()
    return model.encode(texts, convert_to_numpy=True, batch_size=32, show_progress_bar=False)
