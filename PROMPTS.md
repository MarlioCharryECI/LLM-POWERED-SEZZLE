# Prompts

Two parts: the prompts I used to **build** this (directing the AI tool), and the prompts that
**ship inside** the system.

---

## Part 1 — Build / scaffolding prompts (how I directed the AI)

I used an AI coding assistant throughout, gated step-by-step with review after each step. The
prompts, in order (paraphrased to their intent):

1. **Analyze, don't code.** "Analyze the whole repo as a senior engineer. Read PROMPT.md,
   SUBMISSION.md, all policies, orders.json, the golden cases. Produce: assignment analysis,
   architecture proposal (retrieval / order lookup / routing / escalation), risk analysis, a
   2-hour plan, and a documentation plan. Prefer the simplest sufficient approach; every
   choice needs a rationale and a tradeoff."
2. **Think like a reviewer.** "Rank 100 submissions. What separates top 10%? What fails
   people? What signals junior vs senior? Challenge my own architecture — weaknesses, what a
   skeptic would criticize, what evidence would strengthen each decision."
3. **Reviewer-focused execution plan.** "Produce exact repo structure, implementation order,
   stop-and-eval points, first-run vs final-run artifacts, and doc outlines — documentation
   produced *alongside* development, not reconstructed."
4. **Implement step-by-step** (each its own prompt, with a review gate):
   Step 0 scaffold + data layout · Step 1 `run_cases.py` contract stub · Step 2 `policies.py`
   + `tools.py` + tests (auth server-side, frozen clock, precomputed derivations) · Step 3
   prompts + llm + agent.
5. **Constraint pivot — $0.** "I have no API key and won't pay. Make the LLM layer
   provider-agnostic, default to local Ollama, keep Anthropic/OpenAI optional. Evaluate the
   impact of local models on structured output / tool use / routing / grounding / robustness,
   compare candidate models, and pick one for $0." → chose `qwen2.5:7b`, and (approved) swapped
   native tool-calling for a **router→fetch→answer** schema-JSON flow.
6. **Checkpoint A + diagnose.** "Build `eval.py`, run the first pass, save artifacts, and
   diagnose failures as a taxonomy — classes, not cases."
7. **Fix by class, measure each change.** "Fix failure classes in priority order; record a
   before/after delta per change; avoid case-specific hacks; optimize for hidden-case
   robustness."
8. **Lightweight red-team + latency**, then **write README / DECISIONS / ITERATION / PROMPTS.**

What I kept vs. rewrote: I accepted scaffolding/boilerplate (I/O harness, test skeletons) but
drove every design decision, the routing taxonomy, the guardrail scope, and all diagnosis
myself. The AI found one bug I told it to look for (inverted scorer) and one I surfaced via
red-team (passive-voice waiver leak).

---

## Part 2 — In-system prompts (shipped)

Source of truth: `agent/prompts.py`. The full policy corpus is injected into both system
prompts (`_BASE`). Below are the task sections and schemas verbatim.

### Router call — schema
```json
{"type":"object","properties":{"route":{"type":"string",
  "enum":["policy","tool","both","escalate"]}},"required":["route"]}
```
### Router task (verbatim `_ROUTER_TASK` + decision rules)
> Choose the ONE route this question requires:
> - **policy** — general question answerable from policies alone, no shopper-specific orders.
> - **tool** — a pure lookup of this shopper's own account data, no policy rule needed.
> - **both** — a policy rule must be APPLIED to this shopper's specific order state.
> - **escalate** — the requested ACTION is human-only (fraud/unrecognized order; hardship;
>   filing a dispute; a specific spending limit or decline reason; credit-bureau correction;
>   any ad-hoc fee waiver).
>
> Decision rules — apply IN ORDER, stop at the first match:
> 1. Human-only action to DO/DISCLOSE → **escalate** (even if you also explain policy, even if
>    it's their own order).
> 2. Else needs BOTH a policy rule AND order state → **both** (includes refund/return status
>    and reschedule/failed-payment eligibility).
> 3. Else needs only stored data → **tool**. 4. Else → **policy**.

### Answer call — schema
```json
{"type":"object","properties":{"answer":{"type":"string"}},"required":["answer"]}
```
### Answer task (key rules, verbatim from `_ANSWER_TASK`)
> **Grounding:** rules ONLY from the policies; account facts ONLY from the provided account
> data; never invent a date/amount/limit/fee. Use the pre-computed fields as given (don't do
> your own date/money math); treat `as_of` as today. Quote the specific figures the shopper
> needs. If a fact is missing, say so and escalate.
>
> **Route-specific:** *policy* — no order ids/specifics. *tool* — from the data. *both* — apply
> the rule to this order; **a failed installment CANNOT be rescheduled and must be REPAID**;
> refunds apply to remaining unpaid installments first, then 3–10 business days. *escalate* —
> warm handoff to a human; fraud → advise password/2FA, don't read back details; hardship →
> empathetic, promise nothing; disputes → state 90-day filing / 15-day merchant / installments
> pause; limits → never state a number or invent a decline reason.
>
> **Format:** ONE flowing paragraph of plain prose — no lists/markdown/line breaks (they break
> the JSON string and truncate the reply).

### Tool description (note: NO `user_id` parameter — auth is server-side)
> `get_my_orders` — Look up the CURRENT authenticated shopper's own orders and installment
> schedules… Returns pre-computed facts (next installment, days-until-due, failed/paused
> installments, remaining balance, refund window, reschedule fees). **You cannot look up
> anyone else's account.**

### Guardrail override copy (deterministic, `agent/guardrails.py`)
- Limit/decline disclosure → *"I'm not able to share the exact reason an individual order was
  declined or your precise spending limit — that needs a human agent, and I'm connecting you
  with one now…"*
- Waiver/pause promise → *"I'm really sorry you're dealing with this. I'm not able to change
  your payments or fees myself, but I'm connecting you with a human support specialist…"*
