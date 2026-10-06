import os
import hashlib
import logging
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("vector_store")

_embedding_model = None
_chroma_client = None
_collection = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer embedding model: {e}")
            _embedding_model = None
    return _embedding_model


def get_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data", "chroma")
        os.makedirs(data_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=data_dir)
        _collection = _chroma_client.get_or_create_collection(name="articles")
        return _collection
    except Exception as e:
        logger.warning(f"Could not initialize ChromaDB PersistentClient: {e}")
        return None


def get_url_hash(document_url: str) -> str:
    """Generate a stable, process-independent SHA-256 hash for Chroma chunk IDs."""
    return hashlib.sha256(document_url.encode("utf-8")).hexdigest()[:16]


def has_document_chunks(document_url: str) -> bool:
    """Check if the vector store already contains chunks for the given document URL."""
    if not document_url:
        return False
    collection = get_collection()
    if collection is None:
        return False
    try:
        results = collection.get(where={"url": document_url}, limit=1)
        ids = results.get("ids", [])
        return len(ids) > 0
    except Exception as e:
        logger.warning(f"Error checking document chunks in ChromaDB: {e}")
        return False


def store_chunks(chunks: list[str], document_url: str):
    if not chunks or not document_url:
        return

    collection = get_collection()
    model = get_embedding_model()

    if collection is None or model is None:
        logger.warning("Vector store or embedding model unavailable; skipping chunk storage.")
        return

    try:
        embeddings = model.encode(chunks).tolist()
        url_hash = get_url_hash(document_url)
        ids = [f"{url_hash}-{i}" for i in range(len(chunks))]
        metadatas = [{"url": document_url, "chunk_index": i} for i in range(len(chunks))]

        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.info(f"Stored {len(chunks)} chunks in vector store for URL: {document_url}")
    except Exception as e:
        logger.warning(f"Error storing chunks in ChromaDB: {e}")


def search_chunks_with_citations(query: str, document_url: str = None, n_results: int = 3) -> List[Dict[str, Any]]:
    """Search vector store and return detailed chunk metadata & similarity distance for citations."""
    collection = get_collection()
    model = get_embedding_model()

    if collection is None or model is None:
        return []

    try:
        query_embedding = model.encode([query]).tolist()
        where_filter = {"url": document_url} if document_url else None

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        citations = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            chunk_idx = meta.get("chunk_index", 0) if isinstance(meta, dict) else 0
            url = meta.get("url", document_url) if isinstance(meta, dict) else document_url
            # Calculate a normalized similarity score from distance (lower distance = higher similarity)
            similarity = round(max(0.0, 1.0 - (dist / 2.0)), 4) if dist is not None else 1.0
            citations.append({
                "text": doc,
                "chunk_index": chunk_idx,
                "score": similarity,
                "url": url
            })
        return citations
    except Exception as e:
        logger.warning(f"Error querying ChromaDB vector store: {e}")
        return []


def search_chunks(query: str, document_url: str = None, n_results: int = 3) -> list[str]:
    citations = search_chunks_with_citations(query, document_url=document_url, n_results=n_results)
    return [c["text"] for c in citations]