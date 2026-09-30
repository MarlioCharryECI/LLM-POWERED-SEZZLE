# Prompts

Two parts: the prompts I gave the AI to **build** this (the working prompts, in order), and
the prompts that **ship inside** the system.

---

## Part 1 — Build prompts (in order)

These are the prompts from the build session, edited lightly for brevity. The work was gated
step by step, with a review after each step. The through-line: analyze and decide before
coding, keep it simple, treat the eval as a regression harness, and fix failure *classes*
rather than individual cases.

### 1. Analyze and design first (no code)
> You are acting as a senior Applied AI engineer helping me complete a take-home assignment.
>
> Your job is NOT to blindly generate code. First, analyze the entire repository and design the
> solution as a senior engineer would.
>
> Objectives: (1) understand the requirements; (2) identify what the system actually has to do;
> (3) propose the minimum architecture that fits the problem; (4) avoid overengineering; (5)
> prioritize design decisions, evaluation, and iteration over code volume.
>
> Read PROMPT.md first, then SUBMISSION.md, all policy files, orders.json, and the visible
> evaluation cases. Then produce: an assignment analysis (what must be built vs. optional);
> an architecture proposal (retrieval, order lookup, routing, escalation); a risk analysis
> (failure cases and hallucination risks); a development plan that fits the 2-hour budget; and
> a documentation plan (README, DECISIONS, ITERATION, PROMPTS).
>
> Constraints: prefer simple, explainable approaches; every design choice must have a rationale;
> call out tradeoffs explicitly; if a simpler solution is sufficient, prefer it. Do not generate
> code yet — first produce the analysis and plan.

### 2. Critical design review (stress-test the plan)
> Before we build, stress-test this design as a skeptical senior engineer. For each decision,
> what are its weaknesses, what would a skeptic push back on, and what evidence would
> strengthen it or make me change my mind? Which three decisions are the most consequential and
> worth writing down? Where are the likely failure and hallucination points? Given the 2-hour
> budget, how should I sequence the work to de-risk the important parts first? Be brutally
> honest and keep favoring the simplest sufficient approach.

### 3. Turn the plan into a concrete execution plan
> Now turn this into a concrete execution plan for the repo. For every step: what to build,
> what evidence to collect, what output files to save, and which doc section it supports. I want
> documentation produced alongside development, not reconstructed afterward.
>
> Provide: exact repository structure; exact implementation order; the points where I should
> stop and run evaluations; the artifacts that should exist after the first run and after the
> final run; and draft outlines for README, DECISIONS, ITERATION, PROMPTS. Aim for a clean,
> well-evidenced submission, not just working code.

### 4. Implement, step by step (Step 0 and Step 1)
> The architecture and evaluation strategy are approved. Proceed with implementation.
>
> Constraints: keep it as small as possible; no LangChain, Pinecone, vector DBs, or
> orchestration frameworks; prefer plain Python; prefer clarity over extensibility; optimize for
> correctness and explainability, not feature count.
>
> Follow the execution plan exactly. Stop after each major step and explain what was built, why,
> what evidence to capture, and which doc section it supports. Start with Step 0 (repository
> structure, file layout, data organization), then Step 1 (run_cases.py contract stub). Don't go
> further until those are reviewed.

### 5. Step 2 — policies, tools, tests
> Proceed to Step 2. Implement policies.py, tools.py, tests/test_tools.py.
>
> Requirements: (1) user_id must be injected server-side and never supplied by the model; (2)
> use orders.json.today as the source of truth for all date calculations; (3) precompute
> next_upcoming_installment and other deterministic fields in the tool, not in the LLM; (4) add
> tests covering the v01 expected payment calculation; (5) explain every design choice; (6) tell
> me exactly what evidence to record in devlog.md. Don't implement the LLM yet.

### 6. Step 3 — prompts, llm, agent
> Proceed to Step 3. Implement prompts.py, llm.py, agent.py.
>
> Follow the agreed architecture: full policy context in the prompt; single-pass tool calling;
> structured output {route, answer}. Keep routing model-driven, not keyword-driven. Bind user_id
> server-side so the model can never request another user's data. Explain the system prompt, why
> each routing category exists, and why the tool interface is safe. After implementation, show a
> sample interaction and identify expected weaknesses before the first evaluation run. Build for
> robustness on unseen cases, not for the visible ten.

### 7. Constraint pivot — $0, no paid API
> I don't have an Anthropic API key, and I don't want to spend money on this. Treat a paid API
> as a last resort.
>
> Redesign so that: the LLM interface stays provider-agnostic; Anthropic is no longer required;
> OpenAI is not assumed; the default uses Ollama locally; the whole thing can run at $0.
>
> Evaluate the impact of local models on structured output, tool-calling, route classification,
> policy grounding, hidden-case robustness, and development complexity (gain / lose / risk for
> each). Then compare qwen3, qwen2.5:7b-instruct, llama3.1:8b, gemma3, and mistral-small (RAM,
> speed, JSON compliance, instruction-following, fit for this task) and recommend one for a $0
> local run. Also estimate the total cost of running the visible cases plus a few iteration
> passes on Ollama vs. Anthropic vs. OpenAI. Be brutally practical.

### 8. Implement the Ollama redesign
> The architecture change is approved. Don't spend more time on analysis — implement.
>
> (1) Provider-agnostic LLM layer; (2) qwen2.5:7b-instruct as the default; (3) the router →
> fetch → answer flow; (4) routing stays model-driven; (5) schema-constrained JSON output; (6)
> disable any reasoning/thinking output; (7) keep Anthropic/OpenAI behind the same interface,
> optional; (8) comment the design decisions that back the ADRs. After implementation, review
> the code critically and identify weaknesses before the first eval run, then stop.

### 9. Step 4 — first eval run + diagnosis
> Ollama is installed and qwen2.5:7b is responding correctly. Proceed with Step 4.

### 10. Step 5 — fix failure classes, measure each change
> Proceed to Step 5. Goals: fix failure classes, not individual cases; preserve the iteration
> evidence; capture the impact of every meaningful change (hypothesis, why it should help the
> class, before/after delta, update devlog.md). Priorities: (1) answer truncation; (2) escalate
> vs both routing; (3) both vs tool routing; (4) the v04 failed-installment grounding; (5)
> defense-in-depth guardrails. Avoid case-specific hacks; build for robustness on unseen cases.
> After the fixes: run the eval again, produce the final taxonomy, compare first vs final, and
> identify remaining weaknesses honestly. Then stop and prepare the documentation inputs.

### 11. Step 6 — lightweight red-team + latency (max 15 min)
> Proceed with a lightweight Step 6, max 15 minutes. Red-team the final system, generate
> documentation evidence, and measure latency and runtime characteristics, producing artifacts
> useful for README, DECISIONS, and ITERATION. Don't modify the agent unless a critical issue is
> discovered. After Step 6, stop implementation and write README, DECISIONS, ITERATION, PROMPTS.
> Prioritize professionalism and clarity.

### 12. Final quality review of the repository
> Do a thorough, critical review of the finished repository, as a demanding senior engineer
> would before it ships — focus on engineering judgment, professionalism, and communication, not
> features. Cover: repository hygiene (naming, dead code, stray or committed files, duplication,
> structure); documentation quality (weak or vague wording, AI-sounding text, unsupported
> claims, missing evidence); whether the repo tells a coherent story (what was built, why, what
> failed, what changed, why); and evidence quality. Then list only high-impact, low-effort fixes
> (< 30 min) to presentation, clarity, and credibility — no new features, no re-architecting. Be
> brutally honest; if something looks rushed, duplicated, or unprofessional, say so.

### 13. Apply the polish
> Yes — apply those fixes and make the repo clean and submission-ready.

Note on division of labor: I accepted scaffolding and boilerplate from the AI (the I/O harness,
test skeletons) but drove the design decisions, the routing taxonomy, the guardrail scope, and
the diagnosis myself. The AI found one bug I asked it to look for (the inverted scorer) and one
I surfaced through the red-team (the passive-voice waiver leak).

---

## Part 2 — In-system prompts (shipped)

Source of truth: `agent/prompts.py`. The full policy corpus is injected into both system
prompts (`_BASE`). Below are the task sections and schemas, verbatim.

### Router call — schema
```json
{"type":"object","properties":{"route":{"type":"string",
  "enum":["policy","tool","both","escalate"]}},"required":["route"]}
```
### Router task (`_ROUTER_TASK` + decision rules)
> Choose the ONE route this question requires:
> - **policy**: general question answerable from policies alone, no shopper-specific orders.
> - **tool**: a pure lookup of this shopper's own account data, no policy rule needed.
> - **both**: a policy rule must be APPLIED to this shopper's specific order state.
> - **escalate**: the requested ACTION is human-only (fraud/unrecognized order; hardship;
>   filing a dispute; a specific spending limit or decline reason; credit-bureau correction;
>   any ad-hoc fee waiver).
>
> Decision rules, applied in order, stop at the first match:
> 1. Human-only action to DO/DISCLOSE → **escalate** (even if you also explain policy, even if
>    it's their own order).
> 2. Else needs BOTH a policy rule AND order state → **both** (includes refund/return status
>    and reschedule/failed-payment eligibility).
> 3. Else needs only stored data → **tool**. 4. Else → **policy**.

### Answer call — schema
```json
{"type":"object","properties":{"answer":{"type":"string"}},"required":["answer"]}
```
### Answer task (key rules, from `_ANSWER_TASK`)
> **Grounding:** rules ONLY from the policies; account facts ONLY from the provided account
> data; never invent a date, amount, limit, or fee. Use the precomputed fields as given, do not
> do your own date or money math, and treat `as_of` as today. Quote the specific figures the
> shopper needs. If a fact is missing, say so and escalate.
>
> **Route-specific:** *policy* uses no order ids or specifics. *tool* answers from the data.
> *both* applies the rule to this order; a failed installment CANNOT be rescheduled and must be
> REPAID; refunds apply to remaining unpaid installments first, then 3–10 business days.
> *escalate* is a warm handoff to a human: fraud advises password/2FA and reads back no details;
> hardship is empathetic and promises nothing; disputes state the 90-day filing window, the
> 15-day merchant wait, and that installments pause; limits never state a number or invent a
> decline reason.
>
> **Format:** one flowing paragraph of plain prose, with no lists, markdown, or line breaks,
> because those break the JSON string and truncate the reply.

### Tool description (note: no `user_id` parameter; auth is server-side)
> `get_my_orders`: look up the CURRENT authenticated shopper's own orders and installment
> schedules. Returns precomputed facts (next installment, days-until-due, failed/paused
> installments, remaining balance, refund window, reschedule fees). You cannot look up anyone
> else's account.

### Guardrail override copy (deterministic, `agent/guardrails.py`)
- Limit/decline disclosure → *"I'm not able to share the exact reason an individual order was
  declined or your precise spending limit. That needs a human agent, and I'm connecting you with
  one now…"*
- Waiver/pause promise → *"I'm really sorry you're dealing with this. I'm not able to change your
  payments or fees myself, but I'm connecting you with a human support specialist…"*
