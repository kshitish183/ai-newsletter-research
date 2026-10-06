import uuid
import pytest
from unittest.mock import patch
from services.vector_store import get_url_hash, has_document_chunks, store_chunks, search_chunks_with_citations
from article_analyzer import answer_article_question


def test_stable_sha256_url_hash():
    url1 = "https://example.com/article-1"
    url2 = "https://example.com/article-1"
    url3 = "https://example.com/article-2"

    hash1 = get_url_hash(url1)
    hash2 = get_url_hash(url2)
    hash3 = get_url_hash(url3)

    assert hash1 == hash2, "Identical URLs must yield identical deterministic hashes"
    assert hash1 != hash3, "Different URLs must yield different hashes"
    assert len(hash1) == 16, "Hash length should be 16 characters"


def test_vector_store_ingest_and_check():
    unique_id = str(uuid.uuid4())[:8]
    test_url = f"https://example.com/test-rag-ingest-{unique_id}"
    chunks = [
        "Artificial intelligence models process vast amounts of unstructured data.",
        "Retrieval-Augmented Generation combines search with neural language generation."
    ]

    # Before storing
    assert has_document_chunks(test_url) is False

    # Store chunks
    store_chunks(chunks, document_url=test_url)

    # After storing
    assert has_document_chunks(test_url) is True

    # Search with citations
    citations = search_chunks_with_citations("data processing", document_url=test_url, n_results=1)
    assert len(citations) == 1
    assert "Artificial intelligence" in citations[0]["text"]
    assert citations[0]["score"] >= 0.0


@patch("article_analyzer.scrape_article")
def test_ingest_once_and_reuse_chunks(mock_scrape):
    mock_scrape.return_value = {
        "title": "Cached Article",
        "content": "This is a test article for verifying single-ingestion behavior in RAG pipeline."
    }

    unique_id = str(uuid.uuid4())[:8]
    test_url = f"https://example.com/ingest-once-test-{unique_id}"

    # First Q&A call - should trigger scrape_article
    res1 = answer_article_question("What is this article?", url=test_url)
    assert mock_scrape.call_count == 1
    assert "answer" in res1
    assert "citations" in res1

    # Second Q&A call - should NOT trigger scrape_article because chunks are stored
    res2 = answer_article_question("Explain the test article", url=test_url)
    assert mock_scrape.call_count == 1  # Still 1, did not re-scrape!
    assert "answer" in res2
