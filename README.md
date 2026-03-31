# IT Help Desk Agent

RAG-powered IT support agent using Groq LLM, FAISS, and Streamlit.

## Project Structure

```
it-helpdesk-agent/
├── app.py                   # Streamlit UI
├── config.py                # API keys & model config
├── requirements.txt
├── rag/
│   ├── embedder.py          # sentence-transformers wrapper
│   ├── vector_store.py      # FAISS index
│   └── retriever.py        # load, search, persist cases
├── agent/
│   ├── prompt.py            # RAG prompt builder
│   ├── llm.py               # Groq API client
│   └── helpdesk_agent.py    # orchestration
├── memory/
│   └── knowledge_base.json  # seed + learned cases
└── utils/
    └── helpers.py           # display utilities
```

## Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Groq API key

Get a free key at https://console.groq.com

**Linux / macOS:**
```bash
export GROQ_API_KEY=your_key_here
```

**Windows (CMD):**
```cmd
set GROQ_API_KEY=your_key_here
```

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your_key_here"
```

### 3. Run the app

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## How It Works

1. User submits an IT issue via the text area
2. Issue is converted to a vector embedding (all-MiniLM-L6-v2)
3. FAISS retrieves top-3 similar resolved cases from knowledge_base.json
4. Retrieved cases + issue are injected into a structured prompt
5. Groq LLM (llama-3.1-8b-instant) returns a strict JSON response
6. Response is displayed with resolution steps, commands, and metrics
7. New case is appended to knowledge_base.json and indexed in FAISS

