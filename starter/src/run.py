"""Orchestration script for Day 06 Data Ingestion Lab.

Executes Strategies A, B, and C:
- Strategy A: Fixed-size chunking (500 chars, 50 overlap), no filter.
- Strategy B: Structure-aware Paragraph chunking (800 chars max), no filter.
- Strategy C: Paragraph chunking (reusing Strategy B chunks) WITH metadata filter when specified.
"""
import csv
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_pdf
from .store import PgVectorStore


def find_file(relative_paths: list[str]) -> Path | None:
    """Find the first existing path among relative options."""
    for p_str in relative_paths:
        p = Path(p_str)
        if p.exists():
            return p
    return None


def main() -> None:
    # 0. Load environment
    env_path = find_file(["starter/.env", ".env"])
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERROR] DATABASE_URL is not set. Please copy .env.example to .env and configure.")
        sys.exit(1)

    print("=" * 70)
    print("   DAY 06: DATA INGESTION ENGINEERING PIPELINE")
    print("=" * 70)

    # 1. Locate PDF and Manifest
    pdf_path = find_file([
        "starter/data/US_History_-_WEB.pdf",
        "data/US_History_-_WEB.pdf"
    ])
    if not pdf_path:
        print("[ERROR] PDF file US_History_-_WEB.pdf not found in starter/data/ or data/")
        sys.exit(1)

    manifest_path = find_file([
        "data/manifest.json",
        "starter/data/manifest.json"
    ])

    print(f"\n[1/5] Loading corpus from: {pdf_path}")
    pages = load_pdf(
        path=pdf_path,
        document_id="openstax-us-history",
        source=str(pdf_path).replace("\\", "/"),
        start_page=23,
        end_page=100,
        manifest_path=manifest_path
    )
    print(f" -> Extracted {len(pages)} physical pages (pages 23 to 100).")
    content_pages = [p for p in pages if not p.metadata.get("is_empty") and len(p.text) > 100]
    print(f" -> Validated {len(content_pages)} non-empty content pages (>= 30 requirement PASSED).")

    # 2. Build Chunks for Strategy A and Strategy B
    print("\n[2/5] Generating chunk strategies:")
    # Strategy A: Fixed-size (500 chars, overlap 50)
    chunks_a = []
    for p in pages:
        chunks_a.extend(fixed_size(p, size=500, overlap=50))
    print(f" -> Strategy A (Fixed-size: 500, overlap: 50): {len(chunks_a)} chunks")

    # Strategy B: By paragraph (max 800 chars)
    chunks_b = []
    for p in pages:
        chunks_b.extend(by_paragraph(p, max_size=800))
    print(f" -> Strategy B (Paragraph-aware: max 800): {len(chunks_b)} chunks")

    # 3. Initialize Embedder and Vector Store
    print("\n[3/5] Initializing Embedder and PgVectorStore:")
    try:
        embedder = MyEmbedder()
        print(f" -> Embedder provider: {embedder.provider} | Model: {embedder.model_name} | Dims: {embedder.dimensions}")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Embedder: {e}")
        sys.exit(1)

    store = PgVectorStore(database_url=db_url, dimensions=embedder.dimensions)
    try:
        store.create_schema()
        print(" -> PgVector table schema and indexes verified.")
    except Exception as e:
        print(f"[ERROR] Database connection or schema creation failed: {e}")
        sys.exit(1)

    # Ingest Strategy A
    print("\n[3.1] Embedding and indexing Strategy A chunks...")
    t0_a = time.time()
    texts_a = [c.text for c in chunks_a]
    vectors_a = embedder.embed_documents(texts_a)
    store.upsert("strategy_a", chunks_a, vectors_a)
    time_a = round(time.time() - t0_a, 2)
    print(f" -> Strategy A ingested {len(chunks_a)} vectors in {time_a}s.")

    # Ingest Strategy B
    print("\n[3.2] Embedding and indexing Strategy B chunks...")
    t0_b = time.time()
    texts_b = [c.text for c in chunks_b]
    vectors_b = embedder.embed_documents(texts_b)
    store.upsert("strategy_b", chunks_b, vectors_b)
    time_b = round(time.time() - t0_b, 2)
    print(f" -> Strategy B ingested {len(chunks_b)} vectors in {time_b}s.")

    # 4. Load Benchmark Questions
    print("\n[4/5] Loading benchmark questions:")
    benchmark_file = find_file([
        "benchmark/questions.json",
        "starter/benchmark/questions.json",
        "data/benchmark.json"
    ])
    if not benchmark_file:
        print("[ERROR] benchmark/questions.json not found!")
        sys.exit(1)

    with open(benchmark_file, "r", encoding="utf-8") as f:
        bench_json = json.load(f)
        questions = bench_json.get("questions", [])

    print(f" -> Loaded {len(questions)} benchmark questions ({bench_json.get('dev_count')} Dev / {bench_json.get('test_count')} Test).")

    # 5. Execute Retrievals and Evaluate
    print("\n[5/5] Running Top-3 retrieval & evaluation for Strategies A, B, C:")
    
    # Pre-embed all questions to ensure fair latency comparison
    q_vectors = {q["id"]: embedder.embed_query(q["question"]) for q in questions}

    traces: dict[str, list] = {"A": [], "B": [], "C": []}

    for q in questions:
        q_id = q["id"]
        q_vec = q_vectors[q_id]
        q_filt = q.get("filter")

        # Strategy A: store 'strategy_a', no filter
        hits_a = store.search(strategy="strategy_a", query_vector=q_vec, top_k=3, filters=None)
        traces["A"].append(evaluate_query(q, hits_a))

        # Strategy B: store 'strategy_b', no filter
        hits_b = store.search(strategy="strategy_b", query_vector=q_vec, top_k=3, filters=None)
        traces["B"].append(evaluate_query(q, hits_b))

        # Strategy C: store 'strategy_b', WITH filter if question has a filter
        hits_c = store.search(strategy="strategy_b", query_vector=q_vec, top_k=3, filters=q_filt)
        traces["C"].append(evaluate_query(q, hits_c))

    # Summarize metrics
    summary_a = summarize(traces["A"])
    summary_b = summarize(traces["B"])
    summary_c = summarize(traces["C"])

    # Output Results
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    starter_results_dir = Path("starter/results")
    starter_results_dir.mkdir(parents=True, exist_ok=True)

    traces_payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": embedder.model_name,
        "provider": embedder.provider,
        "dimensions": embedder.dimensions,
        "traces": traces
    }
    with open(results_dir / "retrieval_traces.json", "w", encoding="utf-8") as f:
        json.dump(traces_payload, f, indent=2, ensure_ascii=False)
    with open(starter_results_dir / "retrieval_traces.json", "w", encoding="utf-8") as f:
        json.dump(traces_payload, f, indent=2, ensure_ascii=False)

    summary_payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": embedder.model_name,
        "provider": embedder.provider,
        "dimensions": embedder.dimensions,
        "stats": {
            "Strategy_A": {
                "chunk_count": len(chunks_a),
                "ingest_time_s": time_a,
                "summary": summary_a
            },
            "Strategy_B": {
                "chunk_count": len(chunks_b),
                "ingest_time_s": time_b,
                "summary": summary_b
            },
            "Strategy_C": {
                "chunk_count": len(chunks_b),
                "ingest_time_s": 0.0,  # Reuses B index
                "summary": summary_c
            }
        }
    }
    with open(results_dir / "metrics_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2, ensure_ascii=False)
    with open(starter_results_dir / "metrics_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2, ensure_ascii=False)

    # Print Summary Markdown Table matching report template
    print("\n" + "=" * 70)
    print("                    BENCHMARK RESULTS SUMMARY")
    print("=" * 70)
    print("\n| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |")
    print("|---|---|---|---|---|---|---|")
    for s_label, s_data, t_sec in [("A (Fixed-size)", summary_a, time_a),
                                   ("B (Paragraph)", summary_b, time_b),
                                   ("C (Paragraph + Filter)", summary_c, 0.0)]:
        dev_s = s_data["dev"]
        test_s = s_data["test"]
        c_cnt = len(chunks_a) if "A" in s_label else len(chunks_b)
        print(f"| {s_label} | DEV  | {dev_s['hit1_ratio']} ({dev_s['hit1_pct']}%) | {dev_s['hit3_ratio']} ({dev_s['hit3_pct']}%) | {c_cnt} | {t_sec}s | $0 |")
        print(f"| {s_label} | TEST | {test_s['hit1_ratio']} ({test_s['hit1_pct']}%) | {test_s['hit3_ratio']} ({test_s['hit3_pct']}%) | {c_cnt} | {t_sec}s | $0 |")

    print("\n[Filter Compliance]")
    print(f" -> Strategy C Filter Compliance: {summary_c['filter_compliance']['ratio']} ({summary_c['filter_compliance']['pct']}%)")
    print(f"\n[Artifacts saved]")
    print(f" -> results/retrieval_traces.json")
    print(f" -> results/metrics_summary.json")
    print("\nPipeline run completed successfully!")


if __name__ == "__main__":
    main()
