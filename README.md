<<<<<<< HEAD
# AI-Newsletter-Research
A full-stack app (React frontend, FastAPI backend) that scrapes web articles, chunks and embeds their content with SentenceTransformers, and stores them in ChromaDB for semantic search, with a Gemini-powered analysis feature.
=======
# AI Knowledge Library

A Python backend for turning web articles into a searchable knowledge library. The project currently supports article scraping, text chunking, semantic embeddings and local vector search, with a separate Gemini-powered article-analysis prototype.

## What has been implemented

- A FastAPI application titled **AI Knowledge Library API**.
- A `POST /documents/url` endpoint that accepts a public article URL and returns its scraped title and paragraph text.
- HTML extraction with `requests` and Beautiful Soup; non-content elements such as scripts, styles, navigation, headers and footers are removed.
- Text cleaning and overlapping chunking (500 characters per chunk with a 50-character overlap).
- Local persistent vector storage using ChromaDB at `Backend/data/chroma`.
- Semantic embeddings and similarity search using SentenceTransformers' `all-MiniLM-L6-v2` model.
- A standalone Gemini / Vertex AI script that produces a structured article analysis: summary, main idea, insights, concepts, practical takeaways and difficulty.

## Architecture

```text
Article URL
    |
    v
Scraper (requests + Beautiful Soup) --> title and paragraph text
    |
    +--> FastAPI response: POST /documents/url
    |
    v
Cleaner and chunker --> overlapping text chunks
    |
    v
SentenceTransformer embeddings --> ChromaDB collection (`articles`)
    |
    v
Semantic similarity search

Standalone path: article URL --> scraper --> Gemini / Vertex AI --> structured analysis
```

## Project structure

```text
Backend/
|-- main.py                    # FastAPI app and current ingestion/search demo
|-- article_analyzer.py        # Gemini / Vertex AI article-analysis prototype
|-- requirements.txt           # Pinned Python dependencies
|-- models/
|   `-- documents.py           # Pydantic request/response models
|-- routers/
|   `-- documents.py           # Document URL endpoint
|-- services/
|   |-- scrapper.py            # Article HTML scraper
|   |-- chunker.py             # Text cleanup and chunking
|   `-- vector_store.py        # ChromaDB and embedding operations
`-- data/chroma/               # Persisted local ChromaDB data
```

## Prerequisites

- Python 3.12 (the existing virtual environment uses Python 3.12).
- Internet access to retrieve articles and download the embedding model on its first use.
- For `article_analyzer.py`: Google Cloud Application Default Credentials with access to Vertex AI, and a Google Cloud project. The script currently names the project `api-newsletter-research` and location `us-central1` directly in code.

## Setup

From the repository root:

```powershell
cd Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell prevents activation, use the virtual environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## API contract

### `POST /documents/url`

Scrapes the supplied public URL and returns the extracted article data.

```json
{
  "url": "https://example.com/article"
}
```

Example request:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/documents/url `
  -ContentType 'application/json' `
  -Body '{"url":"https://example.com/article"}'
```

The route maps invalid URL/input errors to HTTP 422 and page-loading errors to HTTP 502.

### `GET /`

Returns a basic service-status response:

```json
{
  "message": "AI Knowledge Library API is running!"
}
```

## Running the current scripts

The scraper can be run by itself:

```powershell
cd Backend
python services/scrapper.py
```

The analysis prototype can be run after configuring Google Cloud authentication:

```powershell
cd Backend
python article_analyzer.py
```

The intended API command is:

```powershell
cd Backend
uvicorn main:app --reload
```

## Current implementation notes

This is an in-progress backend. A few integration tasks remain before the full API workflow can be started as-is:

- `main.py` runs a hard-coded scrape -> chunk -> store -> search demonstration during import. It accesses `document.title`, but `scrape_article()` currently returns a dictionary, so the application import will fail. The demo should be moved under an `if __name__ == "__main__":` block and use dictionary keys (or the scraper should return a `Document` model).
- The `POST /documents/url` route currently performs scraping only; it does not yet invoke the chunker or vector store.
- `scrape_article()` extracts every paragraph on the page. It does not yet use site-specific article selectors, robots-policy checks, JavaScript rendering, deduplication or richer metadata.
- Re-ingesting the same URL can cause ChromaDB ID conflicts because chunk IDs are derived from the URL and chunk index.
- No automated tests, authentication, rate limiting or persistent application database have been added yet.
- The local `data/chroma` directory is generated application data; it should normally be excluded from source control along with `.venv` and credentials.

## Next steps

1. Make `Document` the single return type across the scraper, API and chunking pipeline.
2. Move the demo code out of FastAPI module import and connect URL ingestion to chunk storage.
3. Add search and analysis endpoints.
4. Make Google Cloud project, region and model settings environment-based.
5. Add tests, validation, logging and production-safe scraping controls.
>>>>>>> 3fa97a1 (Initial commit: scraper, chunker, vector store, article analyzer, React frontend)
