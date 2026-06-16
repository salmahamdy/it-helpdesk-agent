import os

# ── Groq LLM ──────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_API_GOES_HERE")
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_TEMPERATURE = 0.2
GROQ_MAX_TOKENS = 1024

# ── Embeddings ────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── Retrieval ─────────────────────────────────────────────
TOP_K_RESULTS = 3
SIMILARITY_THRESHOLD = 0.35  # cosine similarity cutoff (0-1)

# ── Knowledge-base learning loop ──────────────────────────
# A case is queued for human review only if the model's self-reported
# confidence clears this bar. Confidence NO LONGER makes a case retrievable
# on its own — only human verification does (see retriever.verified_only).
MIN_CONFIDENCE_TO_SAVE = 0.75
# Top retrieval similarity at/above which an answer is considered "grounded"
# in an existing verified case. Stored as provenance to help triage review.
GROUNDING_THRESHOLD = 0.50
 

# ── MongoDB ───────────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "it_helpdesk")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "cases")

# ── Legacy JSON path (used only for migration) ───────────
KNOWLEDGE_BASE_PATH = os.path.join(
    os.path.dirname(__file__), "memory", "knowledge_base.json"
)
