import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_TEMPERATURE = 0.2
GROQ_MAX_TOKENS = 1024

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_RESULTS = 3

KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), "memory", "knowledge_base.json")
