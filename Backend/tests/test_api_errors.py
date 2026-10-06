import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from article_analyzer import clean_json_response

client = TestClient(app)


def test_clean_json_response_markdown_fences():
    raw_input = "```json\n{\"title\": \"Test\", \"summary\": \"Clean JSON\"}\n```"
    cleaned = clean_json_response(raw_input)
    assert cleaned == '{"title": "Test", "summary": "Clean JSON"}'


def test_request_id_middleware():
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-Ms" in response.headers


@patch("routers.documents.scrape_article")
def test_add_document_internal_error_sanitization(mock_scrape):
    mock_scrape.side_effect = Exception("Sensitive DB credentials or internal stack trace line 142")

    response = client.post("/documents/url", json={"url": "https://example.com/error-test"})
    assert response.status_code == 500
    detail = response.json().get("detail", "")
    assert "Sensitive DB credentials" not in detail
    assert detail == "Failed to process article URL due to an internal error."


@patch("routers.documents.analyze_article")
def test_analyze_document_internal_error_sanitization(mock_analyze):
    mock_analyze.side_effect = Exception("Internal vector store memory corruption")

    response = client.post("/documents/analyze", json={"url": "https://example.com/error-test"})
    assert response.status_code == 500
    detail = response.json().get("detail", "")
    assert "memory corruption" not in detail
    assert detail == "Failed to analyze document due to an internal error."
