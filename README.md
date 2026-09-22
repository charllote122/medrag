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
