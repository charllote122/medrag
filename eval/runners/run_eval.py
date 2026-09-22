#!/usr/bin/env python
"""Run the eval harness against a live MedRAG API.

Usage:
    python eval/runners/run_eval.py --api http://localhost:8000
    python eval/runners/run_eval.py --api http://localhost:8000 --dataset patient
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "eval" / "datasets"
REPORTS = ROOT / "eval" / "reports"


def load_dataset(name: str) -> list[dict[str, Any]]:
    path = DATASETS / f"{name}_qa.jsonl"
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def ask(api: str, question: str, profile: str, timeout: float = 120.0) -> tuple[dict, float]:
    t0 = time.time()
    with httpx.Client(timeout=timeout) as client:
        r = client.post(
            f"{api}/api/query",
            json={"question": question, "profile": profile},
        )
        r.raise_for_status()
        elapsed = time.time() - t0
        return r.json(), elapsed


def check_retrieval(response: dict, expected_section: str | None) -> bool:
    """Did the expected section appear in the top citations?"""
    if not expected_section:
        return True
    needle = expected_section.lower()
    for cit in response.get("citations", []):
        sec = (cit.get("section") or "").lower()
        if needle in sec:
            return True
    return False


def check_triage(response: dict, expected: str) -> bool:
    actual = response.get("triage")
    if expected == "informational":
        return actual is None
    return actual == expected


def check_refusal(response: dict, should_refuse: bool) -> bool:
    return bool(response.get("refused")) == should_refuse


def run_dataset(name: str, api: str) -> dict[str, Any]:
    rows = load_dataset(name)
    results = []

    print(f"\n=== {name} ({len(rows)} questions) ===")
    for i, row in enumerate(rows, start=1):
        qid = row["id"]
        q = row["question"]
        profile = row["profile"]
        try:
            resp, elapsed = ask(api, q, profile)
        except Exception as e:
            print(f"  {qid} ERROR: {e}")
            results.append({
                "id": qid, "error": str(e),
                "question": q, "profile": profile,
            })
            continue

        retrieval_ok = check_retrieval(resp, row.get("expected_top_section"))
        triage_ok = check_triage(resp, row["expected_triage"])
        refusal_ok = check_refusal(resp, row["should_refuse"])

        status = "✓" if (retrieval_ok and triage_ok and refusal_ok) else "✗"
        print(
            f"  {status} {qid} [{profile}] {q[:60]}"
            f"  ({elapsed:.1f}s, triage={resp.get('triage')}, refused={resp.get('refused')})"
        )

        results.append({
            "id": qid,
            "question": q,
            "profile": profile,
            "expected_triage": row["expected_triage"],
            "actual_triage": resp.get("triage"),
            "expected_section": row.get("expected_top_section"),
            "should_refuse": row["should_refuse"],
            "actually_refused": resp.get("refused"),
            "retrieval_ok": retrieval_ok,
            "triage_ok": triage_ok,
            "refusal_ok": refusal_ok,
            "latency_ms": int(elapsed * 1000),
            "answer_preview": (resp.get("answer") or "")[:200],
        })

    return {"dataset": name, "results": results}


def summarize(dataset_results: list[dict[str, Any]]) -> dict[str, Any]:
    all_rows = [r for d in dataset_results for r in d["results"] if "error" not in r]
    total = len(all_rows)

    if total == 0:
        return {"total": 0}

    informational = [r for r in all_rows if r["expected_triage"] == "informational"]
    refusal_cases = [r for r in all_rows if r["should_refuse"]]

    retrieval_ok = sum(1 for r in informational if r.get("retrieval_ok"))
    triage_ok = sum(1 for r in all_rows if r.get("triage_ok"))
    refusal_ok = sum(1 for r in refusal_cases if r.get("refusal_ok"))

    latencies = sorted(r["latency_ms"] for r in all_rows)
    p50 = latencies[len(latencies) // 2] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0

    # Escalation recall: of true emergency, how many got triage=emergency?
    emergencies = [r for r in all_rows if r["expected_triage"] == "emergency"]
    escalation_ok = sum(1 for r in emergencies if r.get("actual_triage") == "emergency")

    return {
        "total": total,
        "retrieval_recall": retrieval_ok / len(informational) if informational else None,
        "triage_accuracy": triage_ok / total,
        "refusal_appropriateness": refusal_ok / len(refusal_cases) if refusal_cases else None,
        "escalation_recall": escalation_ok / len(emergencies) if emergencies else None,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "informational_count": len(informational),
        "refusal_count": len(refusal_cases),
        "emergency_count": len(emergencies),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--dataset", default="all", choices=["all", "patient", "clinician"])
    args = ap.parse_args()

    if args.dataset == "all":
        names = ["patient", "clinician"]
    else:
        names = [args.dataset]

    dataset_results = [run_dataset(n, args.api) for n in names]
    summary = summarize(dataset_results)

    REPORTS.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS / "latest.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump({"summary": summary, "datasets": dataset_results}, f, indent=2)

    print("\n=== Summary ===")
    print(json.dumps(summary, indent=2))
    print(f"\nReport saved to {out_path}")


if __name__ == "__main__":
    main()
