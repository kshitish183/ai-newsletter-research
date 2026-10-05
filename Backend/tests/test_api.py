from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI Knowledge Library API is running!"}


def test_ask_endpoint_fallback():
    payload = {
        "question": "What is the core argument of this article?",
        "title": "Understanding Artificial Intelligence",
        "context": "Artificial intelligence is revolutionizing modern computing by automating repetitive tasks and providing deep insights."
    }
    response = client.post("/documents/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0


def test_invalid_url_scrape():
    payload = {"url": "http://127.0.0.1/private"}
    response = client.post("/documents/url", json=payload)
    assert response.status_code == 400
