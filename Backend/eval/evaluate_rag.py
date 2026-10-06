import os
import sys
import json
import time
import logging
from pathlib import Path

# Ensure Backend directory is in path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.chunker import chunk_text
from services.vector_store import store_chunks, search_chunks_with_citations
from article_analyzer import answer_article_question

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluator")

# Gemini 2.5 Flash Pricing (per 1M tokens)
INPUT_COST_PER_MILLION = 0.075
OUTPUT_COST_PER_MILLION = 0.30


def estimate_tokens(text: str) -> int:
    """Approximate token count based on character length (~4 chars per token)."""
    return max(1, len(text) // 4)


def run_evaluation(dataset_path: str = None) -> dict:
    if dataset_path is None:
        dataset_path = os.path.join(Path(__file__).parent, "dataset.json")

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print("==================================================")
    print("      RAG BENCHMARK EVALUATION SUITE            ")
    print("==================================================\n")

    total_questions = 0
    recall_at_3_hits = 0
    mrr_sum = 0.0
    grounded_hits = 0
    retrieval_latencies = []
    generation_latencies = []
    total_input_tokens = 0
    total_output_tokens = 0

    results = []

    # Step 1: Pre-index all dataset articles
    for doc in dataset:
        url = doc["url"]
        content = doc["content"]
        chunks = chunk_text(content)
        store_chunks(chunks, document_url=url)
        logger.info(f"Indexed {len(chunks)} chunks for evaluation doc: {doc['title']}")

    # Step 2: Evaluate retrieval & generation for each question
    for doc in dataset:
        url = doc["url"]
        for q_item in doc["questions"]:
            total_questions += 1
            q_text = q_item["question"]
            expected_kws = q_item.get("expected_keywords", [])
            grounding_facts = q_item.get("grounding_facts", [])

            # Retrieval timing
            t0 = time.time()
            citations = search_chunks_with_citations(q_text, document_url=url, n_results=3)
            retrieval_time_ms = (time.time() - t0) * 1000
            retrieval_latencies.append(retrieval_time_ms)

            # Evaluate Recall@3 & MRR
            retrieved_texts = [c["text"].lower() for c in citations]
            hit = False
            first_rank = 0

            for rank_idx, text in enumerate(retrieved_texts, start=1):
                if any(kw.lower() in text for kw in expected_kws):
                    if not hit:
                        hit = True
                        first_rank = rank_idx

            if hit:
                recall_at_3_hits += 1
                mrr_sum += 1.0 / first_rank

            # Generation timing
            t1 = time.time()
            qa_res = answer_article_question(q_text, url=url, title=doc["title"], context=doc["content"])
            gen_time_ms = (time.time() - t1) * 1000
            generation_latencies.append(gen_time_ms)

            ans_str = qa_res.get("answer", "") if isinstance(qa_res, dict) else str(qa_res)

            # Grounding check
            ans_lower = ans_str.lower()
            is_grounded = any(fact.lower() in ans_lower for fact in grounding_facts) if grounding_facts else True
            if is_grounded:
                grounded_hits += 1

            # Token estimation
            input_prompt_chars = sum(len(c["text"]) for c in citations) + len(q_text)
            in_tokens = estimate_tokens(" " * input_prompt_chars)
            out_tokens = estimate_tokens(ans_str)
            total_input_tokens += in_tokens
            total_output_tokens += out_tokens

            results.append({
                "question": q_text,
                "url": url,
                "recall_at_3_hit": hit,
                "rank": first_rank,
                "grounded": is_grounded,
                "retrieval_ms": round(retrieval_time_ms, 2),
                "generation_ms": round(gen_time_ms, 2),
                "answer": ans_str[:150] + "..." if len(ans_str) > 150 else ans_str
            })

    # Summary Metrics Calculation
    recall_at_3 = round((recall_at_3_hits / total_questions) * 100, 2) if total_questions else 0.0
    mrr = round(mrr_sum / total_questions, 4) if total_questions else 0.0
    grounding_accuracy = round((grounded_hits / total_questions) * 100, 2) if total_questions else 0.0
    avg_retrieval_ms = round(sum(retrieval_latencies) / len(retrieval_latencies), 2) if retrieval_latencies else 0.0
    avg_gen_ms = round(sum(generation_latencies) / len(generation_latencies), 2) if generation_latencies else 0.0

    input_cost = (total_input_tokens / 1_000_000) * INPUT_COST_PER_MILLION
    output_cost = (total_output_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION
    total_est_cost = round(input_cost + output_cost, 6)

    report = {
        "total_evaluation_questions": total_questions,
        "metrics": {
            "retrieval_recall_at_3_pct": recall_at_3,
            "mean_reciprocal_rank_mrr": mrr,
            "answer_grounding_accuracy_pct": grounding_accuracy,
            "avg_retrieval_latency_ms": avg_retrieval_ms,
            "avg_generation_latency_ms": avg_gen_ms,
            "total_estimated_cost_usd": f"${total_est_cost:.6f}"
        },
        "token_usage": {
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens
        },
        "detailed_results": results
    }

    report_path = os.path.join(Path(__file__).parent, "eval_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Evaluation Questions: {total_questions}")
    print(f"Retrieval Recall@3:   {recall_at_3}%")
    print(f"Mean Reciprocal Rank: {mrr}")
    print(f"Grounding Accuracy:   {grounding_accuracy}%")
    print(f"Avg Retrieval Time:   {avg_retrieval_ms} ms")
    print(f"Avg Generation Time:  {avg_gen_ms} ms")
    print(f"Est. Token Usage:     In: {total_input_tokens} / Out: {total_output_tokens}")
    print(f"Est. Total Cost:      ${total_est_cost:.6f}")
    print(f"\nSaved detailed evaluation report to: {report_path}\n")

    return report


if __name__ == "__main__":
    run_evaluation()
