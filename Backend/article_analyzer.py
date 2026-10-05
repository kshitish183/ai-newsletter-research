import os
import json
import logging
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from google import genai
from services.scrapper import scrape_article
from services.chunker import chunk_text
from services.vector_store import store_chunks, search_chunks
from models.article import ArticleAnalysis

logger = logging.getLogger("article_analyzer")

VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "api-newsletter-research")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_genai_client = None


def get_genai_client():
    global _genai_client
    if _genai_client is not None:
        return _genai_client

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            _genai_client = genai.Client(api_key=api_key)
            logger.info("Initialized GenAI Client with API key.")
            return _genai_client
        except Exception as e:
            logger.warning(f"Could not initialize GenAI Client with API key: {e}")

    try:
        _genai_client = genai.Client(
            vertexai=True,
            project=VERTEX_PROJECT,
            location=VERTEX_LOCATION
        )
        logger.info("Initialized GenAI Client with Vertex AI.")
        return _genai_client
    except Exception as e:
        logger.warning(f"Could not initialize GenAI Vertex client: {e}")
        return None


def generate_content_with_fallback(client, prompt: str, is_json: bool = False) -> Optional[str]:
    if not client:
        return None

    candidate_models = [GEMINI_MODEL, "gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    config = {"response_mime_type": "application/json"} if is_json else None

    for model in models_to_try:
        try:
            kwargs = {"model": model, "contents": prompt}
            if config:
                kwargs["config"] = config
            response = client.models.generate_content(**kwargs)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"GenAI generation failed with model '{model}': {e}")
            continue

    return None


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

    # Index chunks into ChromaDB vector database
    try:
        chunks = chunk_text(content)
        store_chunks(chunks, document_url=url)
    except Exception as e:
        logger.warning(f"Failed to store article chunks in vector store: {e}")

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
    "summary": "A comprehensive, clear article summary of about 250-400 words.",
    "main_idea": "A clear explanation of the central argument in about 100-150 words.",
    "key_insights": [
        "6-8 substantial insights, each explained in 2-3 sentences."
    ],
    "important_concepts": [
        "5-7 concise names of important concepts or frameworks."
    ],
    "practical_takeaways": [
        "5-7 specific, actionable takeaways, each explained in 1-3 sentences."
    ],
    "difficulty": "Beginner"
}}

Rules:
- Return ONLY JSON.
- Do not use markdown fencing.
- Follow the requested counts and lengths; provide enough detail to explain the article rather than using short fragments.
- Cover the article from beginning to conclusion, including its major arguments, supporting evidence, examples, and important qualifications.
- Ground every point in the supplied article. Do not invent facts, quotations, or concepts.
- Exclude website interface text, audio player labels, and listening-duration labels from the analysis.
- Keep important concept entries short because they will be displayed as selectable labels.
- Keep difficulty as Beginner, Intermediate, or Advanced.
"""

    client = get_genai_client()
    if client is not None:
        raw_response = generate_content_with_fallback(client, prompt, is_json=True)
        if raw_response:
            try:
                cleaned_text = clean_json_response(raw_response)
                data = json.loads(cleaned_text)

                data["url"] = url
                if "difficulty" in data and "level" not in data:
                    data["level"] = data["difficulty"]
                if "category" not in data:
                    data["category"] = "Psyche Guides"

                return ArticleAnalysis(**data)
            except Exception as e:
                logger.warning(f"Failed to parse JSON from GenAI response: {e}")

    # Fallback analysis if Gemini is unavailable or fails
    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
    if len(paragraphs) > 8:
        summary_paragraphs = [
            paragraphs[round(index * (len(paragraphs) - 1) / 7)]
            for index in range(8)
        ]
    else:
        summary_paragraphs = paragraphs
    summary = "\n\n".join(summary_paragraphs) if summary_paragraphs else "No summary available."
    main_idea = paragraphs[0] if len(paragraphs) > 0 else summary

    key_insights = paragraphs[1:5] if len(paragraphs) >= 5 else [
        "Key insight 1 from article content.",
        "Key insight 2 from article content."
    ]

    takeaways = paragraphs[5:9] if len(paragraphs) >= 9 else [
        "Takeaway 1: Review main points.",
        "Takeaway 2: Apply concepts in practice."
    ]

    concepts = ["Core Concept 1", "Core Concept 2", "Key Framework"]

    return ArticleAnalysis(
        url=url,
        title=title,
        category="Psyche Guides",
        summary=summary[:8000],
        main_idea=main_idea[:300],
        key_insights=key_insights,
        important_concepts=concepts,
        practical_takeaways=takeaways,
        difficulty="Beginner",
        level="Beginner"
    )


def build_smart_fallback_answer(question: str, title: str, context: str) -> str:
    paragraphs = [p.strip() for p in context.split("\n") if p.strip()]
    if not paragraphs:
        return f"Regarding '{question}': The article '{title}' does not contain sufficient text."

    stop_words = {
        "explain", "in", "simple", "terms", "what", "is", "a", "an", "the",
        "does", "mean", "how", "to", "of", "and", "or", "for", "with", "about",
        "critiqued", "concepts"
    }
    raw_words = re.findall(r"\w+", question.lower())
    keywords = [w for w in raw_words if len(w) > 2 and w not in stop_words]

    matched_paragraphs = []
    if keywords:
        for p in paragraphs:
            p_lower = p.lower()
            matches = sum(1 for kw in keywords if kw in p_lower)
            if matches > 0:
                matched_paragraphs.append((matches, p))
        matched_paragraphs.sort(key=lambda x: x[0], reverse=True)

    if matched_paragraphs:
        best_paras = [item[1] for item in matched_paragraphs[:2]]
        return f"Based on the article '{title}':\n\n" + "\n\n".join(best_paras)
    else:
        concept_match = re.search(r'Explain "(.*?)"', question) or re.search(r'Explain (.*)', question)
        concept_name = concept_match.group(1) if concept_match else question
        first_meaningful_para = paragraphs[0] if paragraphs else ""
        return (
            f"The concept '{concept_name}' was not specifically found in the article '{title}'. "
            f"The article primarily discusses: {first_meaningful_para[:250]}..."
        )


def answer_article_question(question: str, url: str = None, title: str = None, context: str = None) -> str:
    if url:
        try:
            scraped = scrape_article(url)
            title = title or scraped["title"]
            context = scraped["content"]

            try:
                chunks = chunk_text(context)
                store_chunks(chunks, document_url=url)
            except Exception as e:
                logger.warning(f"Failed to store article chunks in vector store: {e}")
        except Exception as e:
            logger.warning(f"Could not retrieve article for Q&A: {e}")
            if not context:
                raise ValueError("Could not retrieve the article to answer this question.") from e

    cleaned_title = title or "Article"
    cleaned_context = context or ""

    # Perform semantic RAG vector retrieval using ChromaDB
    relevant_chunks = []
    if url:
        try:
            relevant_chunks = search_chunks(question, document_url=url, n_results=3)
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")

    rag_passages_str = "\n\n".join(relevant_chunks) if relevant_chunks else ""

    prompt = f"""
You are an AI reading assistant helping a user understand an article using Retrieval-Augmented Generation (RAG).

ARTICLE TITLE: {cleaned_title}

MOST RELEVANT SEMANTIC PASSAGES (RAG RETRIEVAL):
{rag_passages_str if rag_passages_str else 'N/A'}

FULL ARTICLE CONTEXT:
{cleaned_context}

USER QUESTION:
{question}

Instructions:
1. Provide a concise, clear, and direct answer (2-4 sentences) grounded strictly in the provided article content and semantic passages.
2. If the user asks about a concept that is NOT discussed in this article, state clearly that the concept is not covered in this article, and briefly explain what the article *does* cover.
3. Do not include raw meta-tags, photo credits, or repetitive prefixes.
"""

    client = get_genai_client()
    if client is not None:
        ai_response = generate_content_with_fallback(client, prompt)
        if ai_response:
            return ai_response

    return build_smart_fallback_answer(question, cleaned_title, cleaned_context)


if __name__ == "__main__":
    test_url = "https://psyche.co/ideas/what-does-it-mean-to-have-relationship-ambivalence"
    test_question = "What is relationship ambivalence?"
    ans = answer_article_question(test_question, url=test_url)
    print("\n--- TEST RAG ANSWER ---")
    print(ans)