# Sezzle Support Agent

An LLM-powered shopper-support assistant that **answers policy questions, looks up a
shopper's own orders, and escalates human-only actions** — grounded in 12 policy docs and a
mock orders dataset. Runs fully local at **$0** on Ollama.

## How it works
Two schema-constrained JSON calls per question:
1. **Route** — the model classifies into `policy | tool | both | escalate` (model-driven).
2. **Answer** — if the route needs account data, we fetch the shopper's orders
   **server-side** (the model never supplies a `user_id`) and the model writes a grounded,
   single-paragraph reply.

All policies are stuffed into context (the corpus is ~2k tokens — no RAG needed). All
date/money math (next payment, refund window, reschedule fees) is computed **deterministically
in the tool**, so the model never does arithmetic. A deterministic post-filter (`guardrails.py`)
overrides any answer that states a spending limit / decline reason or promises a waiver/pause.

## Setup
```bash
# 1. Local model (default, $0):
ollama pull qwen2.5:7b
ollama serve                      # if not already running

# 2. Python deps:
pip install -r requirements.txt   # only needed if using a paid provider; local path is stdlib
```
No API key is needed for the default local path. To use a paid provider instead:
`SEZZLE_PROVIDER=anthropic` (or `openai`) with the matching key — see `.env.example`.

## Run
```bash
# The contract: reads {id, question, user_id} -> writes {id, route, answer}
python run_cases.py cases/golden_visible.jsonl artifacts/answers.jsonl

# Score against the golden cases:
python eval.py cases/golden_visible.jsonl artifacts/answers.jsonl

# Unit tests (tool math + guardrails; no model needed):
python -m unittest discover -s tests
```

## Results
Visible golden set: **8–9/10 pass, 9/10 route-correct** (from a 5/10 first-run baseline — see
`ITERATION.md`). Evidence in `artifacts/`: first vs final answers + scores, red-team
transcripts (`redteam.md`), and latency/cost (`cost_latency.md`).

## Layout
```
run_cases.py   eval.py              # contract + scorer
agent/         agent.py prompts.py llm.py tools.py policies.py guardrails.py
data/          orders.json  policies/*.md
cases/         golden_visible.jsonl
tests/         test_tools.py test_guardrails.py
artifacts/     answers_first/final.jsonl, eval_first/final.txt, redteam.md, cost_latency.md
notes/         devlog.md  (live iteration log)  + probe scripts
```

## Honestly unfinished
- **Routing ceiling:** the 7B mislabels refund-status as `tool` (answer is still correct);
  v03 swings run-to-run due to local-inference variance at `temperature 0`.
- **Guardrail is regex** — defense-in-depth, not a proof; a novel paraphrase could slip.
- **No clarify-branch** for ambiguous references ("my Bloom & Vine order" when there are two).
- **Local latency (~20s p95)** is a dev stand-in; production p95 ≤ 3s relies on a hosted
  small model + prompt caching (design reasoning in `DECISIONS.md` / `cost_latency.md`).
- Prompts I used to build this are in `PROMPTS.md`.
