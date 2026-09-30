# Sezzle Support Agent

An LLM-powered shopper-support assistant. It answers policy questions, looks up a shopper's
own orders, and escalates human-only actions, grounded in 12 policy docs and a mock orders
dataset. It runs fully local at **$0** on Ollama.

## How it works
Two schema-constrained JSON calls per question:
1. **Route.** The model classifies the question into `policy | tool | both | escalate`. This
   is model-driven; there is no keyword routing.
2. **Answer.** If the route needs account data, the harness fetches the shopper's orders
   server-side and the model writes a grounded, single-paragraph reply.

Three design choices do most of the work:
- **Policies are stuffed into context.** The corpus is ~2k tokens, so retrieval is
  unnecessary and full-context grounding has perfect recall.
- **All date and money math lives in the tool**, not the model. Next-payment, refund window,
  and reschedule fees are precomputed against the frozen dataset clock, so the model never
  does arithmetic.
- **Authorization is structural.** The order tool takes no `user_id` argument; the harness
  binds it to the authenticated shopper. The model has no way to request another account.

A deterministic post-filter (`agent/guardrails.py`) is the last line of defense: if an answer
states a spending limit or decline reason, or promises a waiver or pause, it is overridden
with a safe escalate.

## Setup
```bash
# 1. Local model (default, $0):
ollama pull qwen2.5:7b
ollama serve                      # if not already running

# 2. Python deps (only needed for a paid provider; the local path is stdlib-only):
pip install -r requirements.txt
```
No API key is needed for the default local path. To use a paid provider instead, set
`SEZZLE_PROVIDER=anthropic` (or `openai`) with the matching key. See `.env.example`.

## Run
```bash
# The contract: reads {id, question, user_id} and writes {id, route, answer}
python run_cases.py cases/golden_visible.jsonl artifacts/answers.jsonl

# Score against the golden cases:
python eval.py cases/golden_visible.jsonl artifacts/answers.jsonl

# Unit tests for the tool math and guardrails (no model needed):
python -m unittest discover -s tests
```

## Results
Visible golden set: **9/10 pass, 9/10 route-correct**, up from a 5/10 first-run baseline. The
score is 8/10 on some runs because local inference varies slightly even at temperature 0;
`ITERATION.md` documents this. The full first-to-final story, with per-change scores, is
reproducible from `artifacts/`.

The strongest single piece of evidence is in `artifacts/redteam.md`: when a shopper asks for
another user's order (`ord_3001`, which belongs to a different account), the agent returns
only the caller's own orders. Authorization holds because of code, not a prompt instruction.

## Layout
```
run_cases.py  eval.py           contract + scorer
agent/        agent.py prompts.py llm.py tools.py policies.py guardrails.py
data/         orders.json, policies/*.md
cases/        golden_visible.jsonl
tests/        test_tools.py, test_guardrails.py
artifacts/    answers_first/final.jsonl, eval_first/final.txt,
              answers_c1..c3 + eval_c1..c3 (per-change iteration evidence),
              redteam.md, cost_latency.md
notes/        devlog.md (raw working log), probe scripts
docs/         PROMPT.md, SUBMISSION.md (the original brief)
```
`notes/devlog.md` is my unedited working log. The distilled version is `ITERATION.md`; the log
is included only for readers who want to see the raw reasoning as it happened.

## Honestly unfinished
- **Routing ceiling.** The 7B sometimes labels a refund-status question as `tool` instead of
  `both`. The answer content is still correct; only the route label is wrong.
- **Run-to-run variance.** Even at temperature 0, local inference varies enough to swing one
  case between runs. I chose not to chase it, since that would mean overfitting the ten
  visible cases.
- **The guardrail is regex.** It is defense-in-depth, not a proof, and a novel paraphrase
  could slip past it.
- **No clarify branch** for ambiguous references such as "my Bloom & Vine order" when the
  shopper has two.
- **Local latency (~20s p95)** is a development stand-in. The production target of p95 ≤ 3s
  relies on a hosted small model plus prompt caching; the reasoning is in `cost_latency.md`.

The prompts I used to build this are in `PROMPTS.md`.
