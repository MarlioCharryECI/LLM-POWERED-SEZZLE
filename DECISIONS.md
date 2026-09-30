# Decision Records

Three decisions I would most want to defend. Each gives the decision, the options I weighed,
why I chose this one, and what evidence would change my mind.

## ADR 1 — Retrieval: put the whole policy corpus in the prompt, no RAG

**Decision.** Load all 12 policy docs (about 2k tokens, measured at 8,260 chars) into the
system prompt on every call. No chunking, embeddings, or vector store.

**Options.** (a) Full-context stuffing. (b) BM25 keyword top-k. (c) Embedding retrieval.

**Why.** At this corpus size retrieval recall is already a solved problem, so stuffing gives
100% recall with zero infrastructure and lower latency. Top-k retrieval would actively hurt:
the "I missed a payment, can I reschedule?" case needs the rescheduling and failed-payment
docs at the same time, which is exactly where top-k drops one. The corpus is also a stable
prefix, so it caches cleanly.

**What would change my mind.** Corpus growth past the context and cost budget, on the order of
50 to 100 docs. At that point I would add BM25 first because it is cheap and explainable, and
reach for embeddings only if lexical recall proved insufficient.

## ADR 2 — Guardrails: structural where the stakes are high, advisory where cheap

**Decision.** Enforce authorization and the "never state a limit, never promise a waiver"
rules in code. Leave tone and phrasing to the prompt.

**Options.** (a) All guardrails in the prompt. (b) All in code. (c) Split by stakes.

**Why.** The order tool exposes no `user_id`, so the model cannot fetch another shopper's
data. The red-team confirms this: a request for a foreign order returns only the caller's
orders. A deterministic post-filter overrides invented decline reasons, limit figures, and
waiver promises with a safe escalate. These are the critical-fail behaviors, so they must be
prevented, not requested. Tone is low-stakes, so the prompt handles it.

**What would change my mind.** A red-team showing the scrub is routinely bypassed by
paraphrase, since it is regex and therefore brittle, or that it over-fires on benign answers.
Either would push me to classify sensitive intents with a small dedicated model instead.

## ADR 3 — Loop shape and model: local `qwen2.5:7b` via router, fetch, answer

**Decision.** Two schema-constrained JSON calls, route then answer, with a deterministic order
fetch in between. Not native tool-calling, not an agentic loop. The default model is local
`qwen2.5:7b` on Ollama, which costs nothing to run.

**Options.** (a) Native function-calling on a paid model. (b) An agentic ReAct loop. (c)
Router, fetch, answer on a local model.

**Why.** Small models emit malformed tool calls far more often than they emit malformed JSON
under a grammar, so schema-constrained output is the more reliable contract, and it also
removes `<think>` leakage. Routing gates the second call, so about half of traffic
(policy and escalate) is a single call. On the production budget of 100k/day, roughly $50/day,
and p95 ≤ 3s: local p95 is about 20s, which is why the laptop 7B is a development stand-in
rather than the production answer. The design still meets the budget on a hosted small model,
for the reasons quantified in `artifacts/cost_latency.md`.

**What would change my mind.** Measured routing accuracy on a hosted small model being too
low, which would push me to fold routing into the answer call and infer the route afterward;
or the extra call breaking p95, which would push me to a single call with structured output
and a deterministic order pre-fetch.
