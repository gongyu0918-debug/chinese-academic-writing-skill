# Round 6 pre-ANTI-AI evidence

- Candidate commit: `1af482d`
- Writer contexts: two fresh contexts, 12 core prompts each, 24 raw outputs retained under `writers/`
- Deterministic precheck: failed because `writer-b/L01.md` contained 187 characters, below that case's 200-character minimum
- Repair decision: no Prompt change was made for this single short-output occurrence because it did not meet the three-reproduction rule
- Scope change: the user then requested a Prompt-driven ANTI-AI review layer. This directory is retained as the pre-layer writing snapshot and is not claimed as release evidence.

The directory has no manifest or blind-verifier records and therefore cannot pass the strict release checker.
