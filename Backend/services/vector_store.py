import os
import logging
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


def store_chunks(chunks: list[str], document_url: str):
    if not chunks:
        return

    collection = get_collection()
    model = get_embedding_model()

    if collection is None or model is None:
        logger.warning("Vector store or embedding model unavailable; skipping chunk storage.")
        return

    try:
        embeddings = model.encode(chunks).tolist()
        url_hash = abs(hash(document_url))
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


def search_chunks(query: str, document_url: str = None, n_results: int = 3) -> list[str]:
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
            where=where_filter
        )

        documents = results.get("documents", [])
        if documents and len(documents) > 0:
            return documents[0]
        return []
    except Exception as e:
        logger.warning(f"Error querying ChromaDB vector store: {e}")
        return []