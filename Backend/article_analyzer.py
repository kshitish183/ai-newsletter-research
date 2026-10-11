import os
import json
import logging
import re
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from google import genai
from services.scrapper import scrape_article
from services.chunker import chunk_text
from services.vector_store import store_chunks, search_chunks, has_document_chunks, search_chunks_with_citations
from models.article import ArticleAnalysis


logger = logging.getLogger("article_analyzer")

VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "api-newsletter-research")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

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

    # Only attempt Vertex AI if explicit credentials or flag is provided
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("USE_VERTEX_AI") == "true":
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

    logger.warning(
        "Gemini is unavailable: set GEMINI_API_KEY in Backend/.env or configure "
        "Vertex AI credentials. Article analysis will use the unavailable-model fallback."
    )
    return None



def generate_content_with_fallback(client, prompt: str, is_json: bool = False) -> Optional[str]:
    if not client:
        return None

    candidate_models = [GEMINI_MODEL, "gemini-3.8-flash"]
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
            err_msg = str(e).lower()
            logger.warning(f"GenAI generation failed with model '{model}': {e}")
            if any(term in err_msg for term in ("credential", "auth", "permission", "403", "401", "quota", "project")):
                logger.warning("Authentication/permission error detected; stopping further model fallbacks.")
                break
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


def _clean_generated_text(value: str) -> str:
    boilerplate = re.compile(r"(?:✨?\s*Summarize Key Insights|Explore more by .+|\d+ of \d+ tried|Select a concept to focus it|You may like)", re.I)
    return boilerplate.sub("", value).strip()


def _overlap_ratio(output: str, source: str, n: int = 5) -> float:
    words = lambda text: re.findall(r"[a-z0-9']+", text.lower())
    out_words, src_words = words(output), words(source)
    if len(out_words) < n:
        return 0.0
    source_grams = {tuple(src_words[i:i+n]) for i in range(max(0, len(src_words)-n+1))}
    output_grams = [tuple(out_words[i:i+n]) for i in range(len(out_words)-n+1)]
    return sum(gram in source_grams for gram in output_grams) / len(output_grams)


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
You are writing a beginner-friendly guide card from the article below. Return ONLY valid JSON.

TITLE:
{title}

ARTICLE:
{content}

Use exactly this JSON structure:

{{
    "title": "string",
    "summary": "3-4 sentences in plain, warm language, in your own words.",
    "main_idea": "ONE sentence stating the article's thesis, not an opening anecdote.",
    "key_insights": [
        "Exactly 4 items, each one sentence making a distilled claim."
    ],
    "concepts": [
        {{"name": "Named idea or theory", "one_line_definition": "Plain-language definition"}}
    ],
    "steps": [
        {{"title": "Exercise step", "what_to_do": "What the reader should do"}}
    ],
    "important_concepts": [
        "Short concept labels corresponding to concepts above"
    ],
    "practical_takeaways": [
        "Short actionable steps corresponding to the article's exercises."
    ],
    "difficulty": "Beginner"
}}

Rules:
- Return ONLY JSON.
- Do not use markdown fencing.
- Do not copy sentences verbatim. Use retrieved/source text only as context for original writing.
- Synthesize the thesis across the whole article; do not mistake its opening anecdote for its argument.
- Preserve the article's named theories and its actual exercise structure. If a type of content is absent, return an empty array.
- Ground every point in the supplied article. Do not invent facts, quotations, or concepts.
- Exclude website interface text, related links, image captions, and listening-duration labels.
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

                for field in ("summary", "main_idea"):
                    if isinstance(data.get(field), str):
                        data[field] = _clean_generated_text(data[field])
                data["key_insights"] = [_clean_generated_text(x) for x in data.get("key_insights", []) if isinstance(x, str)]
                placeholder_concepts = {"key framework", "core concept 1", "core concept 2", "concept 1", "concept 2"}
                data["important_concepts"] = [
                    concept for concept in data.get("important_concepts", [])
                    if isinstance(concept, str) and concept.strip().lower() not in placeholder_concepts
                ]
                # Reject extractive generations so the deterministic fallback is used.
                generated = " ".join([data.get("main_idea", ""), data.get("summary", ""), *data["key_insights"]])
                if _overlap_ratio(generated, content) > 0.8:
                    raise ValueError("Generated analysis is too close to the source text")
                concepts = data.pop("concepts", [])
                steps = data.pop("steps", [])
                data["concepts"] = concepts if isinstance(concepts, list) else []
                data["steps"] = steps if isinstance(steps, list) else []
                if concepts and not data.get("important_concepts"):
                    data["important_concepts"] = [c.get("name", "") for c in concepts if isinstance(c, dict) and c.get("name")]
                if steps and not data.get("practical_takeaways"):
                    data["practical_takeaways"] = [f"{s.get('title', '')}: {s.get('what_to_do', '')}" for s in steps if isinstance(s, dict)]

                data["url"] = url
                if "difficulty" in data and "level" not in data:
                    data["level"] = data["difficulty"]
                if "category" not in data:
                    data["category"] = "Psyche Guides"

                return ArticleAnalysis(**data)
            except Exception as e:
                logger.warning(f"Failed to parse JSON from GenAI response: {e}")

    # Fallback analysis if Gemini is unavailable or fails
    paragraphs = [p.strip() for p in content.split("\n") if p.strip() and not p.strip().startswith("## ")]
    # A no-model fallback must be honest and must not present copied paragraphs or
    # fabricated concepts as an AI synthesis.
    summary = "An AI summary could not be generated for this article. The extracted article text is available for reading and question answering."
    main_idea = "An AI-generated thesis is unavailable because the language model could not be reached."
    key_insights = []
    takeaways = []
    concepts = []

    return ArticleAnalysis(
        url=url,
        title=title,
        category="Psyche Guides",
        summary=summary[:8000],
        main_idea=main_idea[:800],
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
        return (
            f"I couldn't find a passage about '{concept_name}' in the retrieved text from "
            f"'{title}'. Try asking about a term or idea discussed in the article."
        )


def answer_article_question(question: str, url: str = None, title: str = None, context: str = None) -> dict:
    citations = []
    cleaned_title = title or "Article"

    # Step 1: Ingest once - check if vector store already has chunks for this URL
    if url:
        if not has_document_chunks(url):
            try:
                logger.info(f"Article not found in vector store. Ingesting once: {url}")
                scraped = scrape_article(url)
                cleaned_title = title or scraped.get("title", "Article")
                scraped_content = scraped.get("content", "")
                chunks = chunk_text(scraped_content)
                store_chunks(chunks, document_url=url)
            except Exception as e:
                logger.warning(f"Could not ingest article for Q&A: {e}")
                if not context:
                    raise ValueError("Could not retrieve or index the article to answer this question.") from e
        else:
            logger.info(f"Reusing stored vector chunks for URL: {url}")

    # Step 2: Retrieve semantic passages & citations from ChromaDB
    if url or context:
        try:
            citations = search_chunks_with_citations(question, document_url=url, n_results=3)
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")

    # Very weak matches are often unrelated boilerplate. Don't present them as
    # evidence or cite them as if they support the answer.
    citations = [citation for citation in citations if citation.get("score", 0) >= 0.2]

    # Fallback to chunking provided context if vector store search yielded no citations
    if not citations and context:
        temp_chunks = chunk_text(context)
        citations = [
            {"text": c, "chunk_index": idx, "score": 1.0, "url": url}
            for idx, c in enumerate(temp_chunks[:3])
        ]

    passages = [c["text"] for c in citations]
    rag_passages_str = "\n\n".join(passages) if passages else "No relevant passages found."

    prompt = f"""
You are an AI research assistant helping a user understand an article using Retrieval-Augmented Generation (RAG).

ARTICLE TITLE: {cleaned_title}

MOST RELEVANT RETRIEVED SEMANTIC PASSAGES:
{rag_passages_str}

USER QUESTION:
{question}

Instructions:
1. Provide a concise, clear, and direct answer (2-4 sentences) grounded strictly in the provided retrieved passages.
2. If the user asks about a concept that is NOT discussed in these passages, state clearly that the concept is not covered in the retrieved text.
3. Do not include raw meta-tags, photo credits, or repetitive prefixes.
"""

    client = get_genai_client()
    if client is not None:
        ai_response = generate_content_with_fallback(client, prompt)
        if ai_response:
            return {
                "answer": ai_response,
                "citations": citations
            }

    fallback_text = build_smart_fallback_answer(
        question,
        cleaned_title,
        rag_passages_str if rag_passages_str != "No relevant passages found." else (context or "")
    )
    return {
        "answer": fallback_text,
        "citations": citations
    }


if __name__ == "__main__":
    test_url = "https://psyche.co/ideas/what-does-it-mean-to-have-relationship-ambivalence"
    test_question = "What is relationship ambivalence?"
    ans = answer_article_question(test_question, url=test_url)
    print("\n--- TEST RAG ANSWER ---")
    print("Answer:", ans["answer"])
    print("Citations Count:", len(ans["citations"]))
