"""Evaluate retrieved evidence and preserve per-query traces."""
import re
from typing import Any


def _normalize_snippet(s: str) -> str:
    """Normalize whitespace and punctuation for robust evidence matching."""
    s = re.sub(r"\s+", " ", s.lower().strip())
    return s


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check source/page and evidence quote in top-3; retain trace and hits."""
    gold_page = int(question.get("gold_page", -1))
    gold_evidence = question.get("evidence_quote", "").strip()
    norm_gold_evidence = _normalize_snippet(gold_evidence)

    hits_eval = []
    hit_at_1 = False
    hit_at_3 = False

    for rank, hit in enumerate(hits, start=1):
        hit_page = int(hit.get("page", -2))
        hit_text = hit.get("text", "")
        norm_hit_text = _normalize_snippet(hit_text)

        page_matched = (hit_page == gold_page)
        # Check if evidence quote is present in the chunk text
        evidence_matched = bool(norm_gold_evidence and norm_gold_evidence in norm_hit_text)
        
        # In case evidence is slightly split across boundaries, check partial overlap
        if not evidence_matched and len(norm_gold_evidence) > 40:
            half_len = len(norm_gold_evidence) // 2
            first_half = norm_gold_evidence[:half_len].strip()
            second_half = norm_gold_evidence[half_len:].strip()
            if first_half in norm_hit_text or second_half in norm_hit_text:
                evidence_matched = True

        is_gold_hit = page_matched and evidence_matched

        if rank == 1 and is_gold_hit:
            hit_at_1 = True
        if rank <= 3 and is_gold_hit:
            hit_at_3 = True

        # Check filter compliance if question had a filter
        filter_compliant = True
        q_filter = question.get("filter")
        if q_filter:
            for fk, fv in q_filter.items():
                chunk_val = str(hit.get(fk) or hit.get("metadata", {}).get(fk, "")).lower()
                if str(fv).lower() not in chunk_val:
                    filter_compliant = False

        hits_eval.append({
            "rank": rank,
            "chunk_id": hit.get("chunk_id"),
            "page": hit_page,
            "score": hit.get("score"),
            "chapter": hit.get("chapter"),
            "page_matched": page_matched,
            "evidence_matched": evidence_matched,
            "is_gold_hit": is_gold_hit,
            "filter_compliant": filter_compliant,
            "text_preview": hit_text[:120] + "..." if len(hit_text) > 120 else hit_text
        })

    return {
        "question_id": question.get("id"),
        "split": question.get("split", "dev"),
        "type": question.get("type", "unknown"),
        "question": question.get("question"),
        "gold_page": gold_page,
        "evidence_quote": gold_evidence,
        "filter": question.get("filter"),
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hits": hits_eval
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1, Evidence Hit@3, and filter compliance by dev/test split."""
    def calc_stats(subset: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(subset)
        if n == 0:
            return {"count": 0, "hit1_count": 0, "hit1_ratio": "0/0", "hit1_pct": 0.0,
                    "hit3_count": 0, "hit3_ratio": "0/0", "hit3_pct": 0.0}

        h1 = sum(1 for t in subset if t["hit_at_1"])
        h3 = sum(1 for t in subset if t["hit_at_3"])

        return {
            "count": n,
            "hit1_count": h1,
            "hit1_ratio": f"{h1}/{n}",
            "hit1_pct": round((h1 / n) * 100, 2),
            "hit3_count": h3,
            "hit3_ratio": f"{h3}/{n}",
            "hit3_pct": round((h3 / n) * 100, 2)
        }

    dev_traces = [t for t in traces if t["split"] == "dev"]
    test_traces = [t for t in traces if t["split"] == "test"]

    # Filter compliance
    filter_traces = [t for t in traces if t.get("filter") is not None]
    compliant_queries = 0
    for t in filter_traces:
        if all(h.get("filter_compliant", True) for h in t.get("hits", [])):
            compliant_queries += 1

    filter_compliance_ratio = f"{compliant_queries}/{len(filter_traces)}" if filter_traces else "N/A"
    filter_compliance_pct = round((compliant_queries / len(filter_traces)) * 100, 2) if filter_traces else 100.0

    return {
        "overall": calc_stats(traces),
        "dev": calc_stats(dev_traces),
        "test": calc_stats(test_traces),
        "filter_compliance": {
            "queries_with_filter": len(filter_traces),
            "compliant_queries": compliant_queries,
            "ratio": filter_compliance_ratio,
            "pct": filter_compliance_pct
        }
    }
