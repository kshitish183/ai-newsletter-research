import json

from google import genai
from services.scrapper import scrape_article
from models.article import ArticleAnalysis


# Gemini client using ADC + Vertex AI
client = genai.Client(
    vertexai=True,
    project="api-newsletter-research",
    location="us-central1"
)


def analyze_article(url: str) -> ArticleAnalysis:

    # 1. Scrape the article
    article = scrape_article(url)

    title = article["title"]
    content = article["content"]

    # 2. Create prompt
    prompt = f"""
You are an AI research assistant.

Analyze the following article and return ONLY valid JSON.

TITLE:
{title}

ARTICLE:
{content}

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
- Do not use markdown.
- Keep the difficulty as Beginner, Intermediate, or Advanced.
"""

    # 3. Send to Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    # 4. Convert Gemini response into Python dictionary
    data = json.loads(response.text)

    # 5. Validate using Pydantic
    analysis = ArticleAnalysis(**data)

    return analysis


if __name__ == "__main__":

    url = "https://psyche.co/guides/how-to-solve-problems-by-thinking-like-a-detective"

    result = analyze_article(url)

    print("\nARTICLE ANALYSIS\n")

    print(result.model_dump_json(indent=2))