import os
import json
import logging

from google import genai
from services.scrapper import scrape_article
from models.article import ArticleAnalysis

logger = logging.getLogger("article_analyzer")

VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "api-newsletter-research")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Initialize Gemini client lazily or safely
try:
    client = genai.Client(
        vertexai=True,
        project=VERTEX_PROJECT,
        location=VERTEX_LOCATION
    )
except Exception as e:
    logger.warning(f"Could not initialize GenAI Vertex client: {e}")
    client = None


def clean_json_response(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def analyze_article(url: str) -> ArticleAnalysis:
    article = scrape_article(url)

    title = article["title"]
    content = article["content"]

    prompt = f"""
You are an AI research assistant.

Analyze the following article and return ONLY valid JSON.

TITLE:
{title}

ARTICLE:
{content[:8000]}

Use exactly this JSON structure:

{{
    "title": "string",
    "summary": "string",
    "main_idea": "string",
    "key_insights": [
        "insight 1",
        "insight 2"
    ],
    "important_concepts": [
        "concept 1",
        "concept 2"
    ],
    "practical_takeaways": [
        "takeaway 1",
        "takeaway 2"
    ],
    "difficulty": "Beginner"
}}

Rules:
- Return ONLY JSON.
- Do not use markdown fencing.
- Keep difficulty as Beginner, Intermediate, or Advanced.
"""

    if client is not None:
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            cleaned_text = clean_json_response(response.text)
            data = json.loads(cleaned_text)

            data["url"] = url
            if "difficulty" in data and "level" not in data:
                data["level"] = data["difficulty"]
            if "category" not in data:
                data["category"] = "Psyche Guides"

            return ArticleAnalysis(**data)
        except Exception as e:
            logger.warning(f"Vertex AI call failed: {e}. Falling back to extracted article analysis.")

    # Fallback analysis if Gemini Vertex AI is unavailable or fails
    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
    summary = paragraphs[0] if paragraphs else "No summary available."
    main_idea = paragraphs[1] if len(paragraphs) > 1 else summary

    key_insights = paragraphs[2:6] if len(paragraphs) >= 6 else [
        "Key insight 1 from article content.",
        "Key insight 2 from article content."
    ]

    takeaways = paragraphs[6:10] if len(paragraphs) >= 10 else [
        "Takeaway 1: Review main points.",
        "Takeaway 2: Apply concepts in practice."
    ]

    concepts = ["Core Concept 1", "Core Concept 2", "Key Framework"]

    return ArticleAnalysis(
        url=url,
        title=title,
        category="Psyche Guides",
        summary=summary[:500],
        main_idea=main_idea[:300],
        key_insights=key_insights,
        important_concepts=concepts,
        practical_takeaways=takeaways,
        difficulty="Beginner",
        level="Beginner"
    )


def answer_article_question(question: str, url: str = None, title: str = None, context: str = None) -> str:
    if not context and url:
        try:
            scraped = scrape_article(url)
            title = title or scraped["title"]
            context = scraped["content"]
        except Exception:
            pass

    prompt = f"""
You are an AI reading assistant helping a user understand an article.

TITLE: {title or 'Article'}
CONTEXT:
{(context or '')[:4000]}

QUESTION:
{question}

Provide a concise, direct, helpful answer in 2-4 sentences based strictly on the article context.
"""

    if client is not None:
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Vertex AI Q&A failed: {e}. Falling back to default Q&A response.")

    # Fallback Q&A answer if Vertex AI is unavailable
    if context:
        return f"Regarding '{question}': Based on the article '{title or 'Article'}', {context[:250]}..."
    return f"Regarding '{question}': The article provides perspective on this topic within its core insights."


if __name__ == "__main__":
    test_url = "https://psyche.co/guides/how-to-solve-problems-by-thinking-like-a-detective"
    result = analyze_article(test_url)
    print("\nARTICLE ANALYSIS\n")
    print(result.model_dump_json(indent=2))