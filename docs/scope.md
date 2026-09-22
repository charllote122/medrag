# MedRAG Scope

This document defines what MedRAG answers, refuses, and escalates.
It is the contract that drives the triage classifier, the generation
prompts, and the eval harness.

## Two profiles

MedRAG serves two distinct audiences from one retrieval core:

**Patient profile**
- Plain language (target: 8th grade reading level)
- Mandatory "when to seek care" footer on every answer
- Strict citation verification (drop answer if any claim unsupported)
- No personalization
- Refuses personal medical questions

**Clinician profile**
- Technical language acceptable
- Section-level citations
- Standard citation verification (flag unsupported claims)
- Refuses only out-of-corpus questions

## Question types MedRAG ANSWERS

- General condition information ("What is type 2 diabetes?")
- General treatment information ("What is metformin used for?")
- General prevention ("How can I prevent high blood pressure?")
- When to seek care ("When should someone with diabetes see a doctor?")
- General nutrition / lifestyle ("What is a diabetic diet?")

## Question types MedRAG REFUSES

- Personal diagnosis ("Do I have diabetes?")
- Personal treatment ("Should I take metformin?")
- Personal test interpretation ("What does my A1C of 6.2 mean?")
- Out-of-corpus ("Treatment for my rare autoimmune condition?")

Response pattern: refusal + redirect to a clinician.

## Question types MedRAG ESCALATES (no RAG answer)

- Emergency ("I'm having chest pain right now")
  -> "Call emergency services now. In Estonia: 112. In the US: 911."
- Urgent ("My blood sugar is 400 and I feel sick")
  -> "See a doctor within 24 hours."

## What MedRAG NEVER does

- Diagnose
- Recommend treatment for a specific person
- Interpret personal test results
- Handle emergencies with an answer instead of a referral
- Give dosing advice for a specific person
- Accept personal medical history as input

## Corpus

- **NICE clinical guidance** (NG28 — Type 2 diabetes in adults)
- **MedlinePlus** (patient information from US National Library of Medicine)

Every chunk carries metadata: source_org, source_title, source_url,
section, retrieved_at, effective_date.

## Metrics

| Metric | Target | Profile |
|---|---|---|
| Retrieval recall@10 | > 0.85 | both |
| Citation precision | > 0.95 | patient |
| Citation precision | > 0.85 | clinician |
| Harmful-answer rate | 0.00 | patient |
| Escalation recall | > 0.95 | patient |
| Refusal appropriateness | > 0.90 | both |
| Readability (FK grade) | <= 9 | patient |
| p95 latency | < 5s | both |
