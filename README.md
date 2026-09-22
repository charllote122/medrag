# MedRAG

Citation-grounded health Q&A over trusted medical guidelines.

MedRAG answers general questions about health conditions using a curated
corpus of authoritative sources (NICE clinical guidance, MedlinePlus
patient information, and later WHO/CDC). Every claim is traceable to a
source. It does not diagnose. It does not recommend treatment for you.
It refuses personal medical questions and escalates emergencies.

## What it does

- **Two profiles, one retrieval core.** Patients get plain-language answers
  with a "when to seek care" note. Clinicians get technical answers with
  section-level citations.
- **Citation enforcement.** Every sentence in an answer maps to a retrieved
  chunk. Unsupported claims are dropped before the answer is returned.
- **Safety triage.** Emergency and urgent queries bypass retrieval and
  escalate. Personal diagnostic queries are refused with a redirect.
- **Published eval harness.** Retrieval precision, citation precision,
  harmful-answer rate, escalation recall, readability.

## What it does not do

- Diagnose a specific person
- Recommend a specific treatment for a specific person
- Interpret personal test results
- Handle emergencies with an answer instead of a referral

See `docs/scope.md` for the full contract.

## Stack

- **Frontend:** React + Tailwind
- **Backend:** FastAPI
- **Vector DB:** PostgreSQL + pgvector (HNSW)
- **Embeddings:** BGE-M3 (local, `sentence-transformers`)
- **Reranker:** BGE-reranker-v2-m3 (planned)
- **LLM:** Qwen3-8B via HF Inference Endpoints (planned)
- **Orchestration:** hand-rolled


## Running

    docker-compose up -d db
    python -m venv .venv
    source .venv/Scripts/activate
    pip install -e backend/
    cd backend && alembic upgrade head && cd ..
    python scripts/ingest_corpus.py --source all
    docker-compose exec db psql -U medrag -d medrag -c "SELECT COUNT(*) FROM chunks;"
    cd backend && uvicorn app.main:app --reload

## Disclaimer

MedRAG is a research artifact. It is not a medical device. It does not
provide medical advice. If you are experiencing a medical emergency,
contact emergency services.

## Evaluation results

Run against a 37-question labeled set (25 patient + 12 clinician).
See `eval/datasets/*.jsonl` for the dataset and `eval/runners/run_eval.py`
for the harness.

| Metric | Target | Achieved | Notes |
|---|---|---|---|
| Retrieval recall@5 | > 0.85 | **0.60** | Correct section in top 5 for informational questions |
| Triage accuracy | > 0.85 | **0.89** | Across 5 classes (emergency/urgent/personal/out_of_corpus/informational) |
| Refusal appropriateness | > 0.90 | **0.94** | Of refusal-worthy questions, how many refused |
| Escalation recall | > 0.95 | **0.80** | Of emergency questions, how many escalated |
| p50 latency | < 20s | **16.7s** | HF Inference free tier |
| p95 latency | < 30s | **30.1s** | |

### Known limitations (v1)

- **Retrieval recall of 0.60** — the correct section is often in the corpus
  but ranks below top 5 for specific queries. Improvement plan:
  query expansion, section-aware boosting, higher-quality reranker.
- **Escalation recall 0.80** — one emergency case ("blood sugar 400")
  was classified urgent instead of emergency. Triage prompt tightened
  in a follow-up commit.
- **Latency p95 at 30s** — HF Inference free tier cold starts.
  Swap to Groq for sub-second responses.
