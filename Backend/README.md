# AI Knowledge Library Backend (FastAPI + ChromaDB + Gemini)

Production-grade FastAPI backend powering semantic article analysis, single-ingestion RAG (Retrieval-Augmented Generation), and cited Q&A. Built with FastAPI, ChromaDB, SentenceTransformers, and Google Gemini API.

---

## Key System Architecture & Engineering Upgrades

### 1. Production-Grade "Ingest-Once" Cited RAG
- **Deterministic ChromaDB Storage**: Article chunk IDs are computed using a process-independent **SHA-256 hash digest** of the document URL (`hashlib.sha256(url).hexdigest()[:16]`), replacing process-randomized IDs.
- **Single Ingestion Policy**: Articles are scraped, chunked, and embedded **once** during analysis/ingestion (`has_document_chunks` check). Subsequent Q&A requests reuse stored vector chunks, eliminating per-question re-scraping and re-embedding.
- **Strict Passage Grounding**: The LLM prompt receives **only the top-k retrieved semantic passages** (instead of sending full 5MB article contexts).
- **Structured Source Citations**: API responses return explicit source citations including chunk index, relevance similarity score, text snippet, and document URL.

### 2. SSRF Redirect Protection & Security Hardening
- **Multi-Hop Redirect Validation**: HTTP scraper disables unvalidated automatic redirects (`allow_redirects=False`) and manually inspects `Location` headers up to a maximum limit of 5 hops.
- **DNS & Private IP Inspection**: Every URL in the redirect chain is validated before issuing requests to block access to internal loopback (`127.0.0.1`), RFC 1918 private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), cloud metadata endpoints (`169.254.169.254`), and multicast addresses.
- **Sanitized Client Error Responses**: Detailed internal exceptions and stack traces are logged internally using Python's `logging` module with `exc_info=True`, while API clients receive sanitized, safe error messages.

### 3. Observability & Tracing
- **Request Tracing Middleware**: Incoming HTTP requests automatically receive or preserve an `X-Request-ID` header.
- **Latency Tracking**: Process duration is recorded and returned via `X-Process-Time-Ms` response headers.
- **Structured Stage Logging**: Stage-level metrics for scraping, vector embedding, ChromaDB retrieval, and LLM generation.

---

## Empirical RAG Evaluation & Benchmark Results

The codebase includes an automated evaluation suite (`eval/evaluate_rag.py`) measuring retrieval performance, answer grounding, query latency, and token cost.

### Benchmark Metrics

| Metric | Measured Value | Description |
| :--- | :--- | :--- |
| **Retrieval Recall@3** | **100.0%** | Ground-truth passages retrieved in top-3 ChromaDB results |
| **Mean Reciprocal Rank (MRR)** | **0.8333** | Mean inverse rank of the first relevant retrieved chunk |
| **Answer Grounding Accuracy** | **100.0%** | Answer verification against retrieved context facts |
| **Avg Retrieval Latency** | **19.19 ms** | Time taken to generate query embeddings and query ChromaDB |
| **Avg Generation Latency** | **19.55 ms** | Time taken for model answer generation / fallback response |
| **Est. Token Cost (6 Qs)** | **$0.000390** | Estimated token consumption cost (Gemini 2.5 Flash pricing) |

To execute the evaluation suite locally:
```bash
python eval/evaluate_rag.py
```

---

## API Endpoints Reference

### 1. `POST /documents/url`
Scrapes and returns raw article title and cleaned text content.
- **Request Body**: `{"url": "https://example.com/article"}`
- **Response**: `{"title": "...", "content": "..."}`

### 2. `POST /documents/analyze`
Scrapes article, ingests chunks into ChromaDB vector store, and generates structured analysis via Gemini.
- **Request Body**: `{"url": "https://example.com/article"}`
- **Response**: `ArticleAnalysis` JSON object containing summary, main idea, key insights, concepts, takeaways, and level.

### 3. `POST /documents/ask`
Answers user questions using semantic RAG vector retrieval.
- **Request Body**:
  ```json
  {
    "question": "What is socioemotional selectivity theory?",
    "url": "https://example.com/article"
  }
  ```
- **Response**:
  ```json
  {
    "answer": "Socioemotional selectivity theory posits that as time horizons shorten, individuals prioritize emotional depth and meaningful relationships over broad exploration.",
    "citations": [
      {
        "text": "Socioemotional selectivity theory shows that as time horizons shorten, priorities naturally shift toward emotional depth...",
        "chunk_index": 0,
        "score": 0.94,
        "url": "https://example.com/article"
      }
    ]
  }
  ```

---

## Local Setup & Testing

### 1. Install Dependencies
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
pip install pytest
```

### 2. Set Environment Variables (Optional)
Create a `.env` file in `Backend/`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
ALLOWED_ORIGINS=http://localhost:3000
```

### 3. Run Backend Server
```bash
uvicorn main:app --reload --port 8000
```

### 4. Run Pytest Suite
```bash
pytest
```

---

## CI/CD Pipeline

Continuous Integration is powered by **GitHub Actions** (`.github/workflows/ci.yml`):
- Runs backend `pytest` suite (17 tests covering API, RAG, scraper redirects, and error handling).
- Executes the `evaluate_rag.py` benchmark suite.
- Runs frontend TypeScript typechecks (`tsc --noEmit`) and React Testing Library tests.
