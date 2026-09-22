
## Known retrieval gaps (Day 4)

- "first line treatment for T2DM" fails to surface NICE "Initial medicines"
  chapter — the correct chunk exists (chunk 55-ish) but ranks below top-5.
  Possible fixes: query expansion, HyDE, section-aware boosting.

- Verifier false positive: LLM added outside knowledge
  ("metformin is first line") and cited [4] because "metformin" appeared
  in the chunk. The keyword-overlap verifier can't detect this. Needs
  NLI-based verification or LLM-as-judge.

## Known retrieval gaps (Day 4)

- "first line treatment for T2DM" fails to surface NICE "Initial medicines"
  chapter — the correct chunk exists but ranks below top-5.
  Possible fixes: query expansion, HyDE, section-aware boosting.

- Verifier false positive: LLM added outside knowledge
  ("metformin is first line") and cited [4] because "metformin" appeared
  in the chunk. Keyword-overlap verifier can't detect this. Needs
  NLI-based verification or LLM-as-judge.
