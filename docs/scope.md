# MedRAG Scope

## What MedRAG does
Answers general questions about health conditions, treatments, and prevention
using WHO, CDC, and NICE guidelines, with mandatory citations.

## Two profiles
- **Patient**: plain language, mandatory escalation footer, strict citation
  verification, no personalization.
- **Clinician**: technical language, section-level citations, allows clinical
  detail within guideline scope.

## Question types it ANSWERS
- General condition info ("What is type 2 diabetes?")
- General symptoms ("What are symptoms of hypertension?")
- General prevention ("What vaccines are recommended for adults?")
- General treatment info ("What is metformin used for?")
- When-to-seek-care questions ("When should someone with asthma go to the ER?")

## Question types it REFUSES
- Personal diagnosis ("Do I have diabetes?")
- Personal treatment ("Should I take ibuprofen with my BP meds?")
- Personal test interpretation ("What does my A1C of 6.2 mean?")
- Out-of-corpus ("Treatment for my rare autoimmune condition?")

## Question types it ESCALATES (no RAG answer)
- Emergency ("I'm having chest pain right now")
- Urgent ("My child has a fever of 104")

## What it never does
- Diagnose
- Recommend treatment for a specific person
- Interpret personal test results
- Handle emergencies with an answer instead of a referral