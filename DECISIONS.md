# Decision Records

Three decisions I'd most want to defend. Format: decision · options · why · what would change my mind.

## ADR 1 — Retrieval: put the whole policy corpus in the prompt (no RAG)
**Decision:** Load all 12 policy docs (~2k tokens total, measured 8,260 chars) into the
system prompt every call; no chunking, embeddings, or vector store.
**Options considered:** (a) full-context stuffing; (b) BM25 keyword top-k; (c) embedding
retrieval.
**Why:** at ~2k tokens retrieval recall is a solved problem — stuffing is 100% recall,
zero infra, lower latency. Top-k actively *hurts* here: the "I missed a payment, can I
reschedule?" case needs the rescheduling **and** failed-payment docs simultaneously,
exactly where top-k silently drops one. The corpus is also a stable, cacheable prefix.
**What would change my mind:** corpus growth past the context/cost budget (order ~50–100
docs / tens of thousands of tokens). Then: BM25 first (cheap, explainable), embeddings only
if lexical recall proves insufficient.

## ADR 2 — Guardrails: structural where the stakes are high, advisory where cheap
**Decision:** Enforce authorization and the "never invent a limit / never promise a
waiver" rules in **code**; leave tone and phrasing to the prompt.
**Options considered:** (a) all guardrails in the prompt; (b) all in code; (c) split by stakes.
**Why:** the model's order tool exposes **no `user_id`** — it's bound server-side, so the
model *cannot* fetch another shopper's data (red-team confirmed: a request for a foreign
order returned only the caller's orders). A deterministic post-filter overrides invented
decline reasons / limit figures / waiver promises to a safe escalate. These are the
"critical fail" behaviors, so they must be *prevented*, not *requested*. Tone is low-stakes
→ prompt is fine.
**What would change my mind:** red-team showing the scrub is routinely bypassed by paraphrase
(it's regex — brittle by nature), or that it over-fires on benign answers. Then move
classification of sensitive intents to a small dedicated model/classifier.

## ADR 3 — Loop shape + model: local $0 `qwen2.5:7b` via router→fetch→answer (schema-JSON)
**Decision:** Two schema-constrained JSON calls (route, then answer), with a deterministic
order-fetch in between — not native tool-calling, not an agentic loop. Default model is
local `qwen2.5:7b` on Ollama ($0).
**Options considered:** (a) native function-calling on a paid model; (b) agentic ReAct loop;
(c) router→fetch→answer on a local model.
**Why:** native tool-calling is the least reliable thing a 7B does; schema-constrained JSON
is far more robust and *structurally* removes thinking/`<think>` leakage. Routing gates the
second call, so ~half of traffic (policy/escalate) is a single call. **Meeting the prod
budget (100k/day, ~$50/day, p95 ≤ 3s):** local p95 is ~20s (a 6 GB laptop 7B is the dev
stand-in, not prod) — but the *design* meets it on a hosted small model: cacheable ~2k policy
prefix, ~1.5 calls/q, and all date/money math is deterministic (no extra calls). See
`artifacts/cost_latency.md`.
**What would change my mind:** measured routing accuracy on a hosted small model being too low
(then fold router into the answer call and infer route post-hoc), or the extra call breaking
p95 (then single-call with structured output + deterministic order pre-fetch).
