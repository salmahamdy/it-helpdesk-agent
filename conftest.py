import sys
import os
from unittest.mock import MagicMock
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Mock sentence_transformers before any project module imports it ──
# This lets tests run without installing the 2GB+ torch/transformers stack.
_mock_st = MagicMock()


class _FakeSentenceTransformer:
    def __init__(self, *a, **kw):
        pass

    def encode(self, text_or_texts, convert_to_numpy=True, **kw):
        if isinstance(text_or_texts, str):
            np.random.seed(abs(hash(text_or_texts)) % 2**31)
            return np.random.rand(384).astype(np.float32)
        else:
            vecs = []
            for t in text_or_texts:
                np.random.seed(abs(hash(t)) % 2**31)
                vecs.append(np.random.rand(384).astype(np.float32))
            return np.array(vecs)


_mock_st.SentenceTransformer = _FakeSentenceTransformer
sys.modules["sentence_transformers"] = _mock_st
