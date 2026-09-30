# Prompts

Two parts: the prompts I gave the AI to **build** this (verbatim, in order), and the prompts
that **ship inside** the system.

---

## Part 1 — Build prompts (verbatim, in order)

These are the actual prompts I sent during the build session, lightly formatted for reading.
The work was gated step by step, with a review after each step. The through-line: analyze and
decide before coding, treat the eval as a regression harness, and fix failure *classes* rather
than individual cases.

### 1. Analyze and design first (no code)
> You are acting as a senior Applied AI engineer helping me complete a take-home assignment.
>
> Your job is NOT to blindly generate code. First, analyze the entire repository and help me
> design the solution as a senior engineer would.
>
> Objectives: (1) Understand the assignment requirements. (2) Identify what is being evaluated.
> (3) Propose the minimum architecture that maximizes evaluation score. (4) Avoid
> overengineering. (5) Prioritize design decisions, evaluation, and iteration over code volume.
>
> When reviewing the repository: read PROMPT.md first, then SUBMISSION.md, then all policy
> files, orders.json, and the visible evaluation cases.
>
> Then produce: Assignment Analysis (what needs to be built / optional / likely graded);
> Architecture Proposal (retrieval, order lookup, routing, escalation); Risk Analysis
> (failure cases and hallucination risks); Development Plan (fits the 2-hour budget);
> Documentation Plan (README, DECISIONS, ITERATION, PROMPTS).
>
> Constraints: prefer simple and explainable approaches; every design choice must have a
> rationale; explicitly call out tradeoffs; if a simpler solution is sufficient, prefer it.
> Do not generate code yet — first produce the analysis and implementation plan.

### 2. Switch to the reviewer's seat
> Now stop thinking like an implementer and think like a Sezzle reviewer. Assume you are
> reviewing 100 submissions and need to rank candidates. I do not want implementation details.
>
> I want to understand: (1) What would distinguish a top 10% submission from an average one?
> (2) What mistakes are most likely to make candidates fail? (3) Which design choices signal
> junior / mid / senior / strong applied AI engineer? (4) Challenge your own architecture — for
> each decision, its weaknesses, what a skeptical reviewer would criticize, and what evidence
> would strengthen it. (5) Which three decisions would make the strongest DECISIONS.md? (6) With
> only 2 hours, where would you spend every 15-minute block to maximize score?
>
> Be brutally honest. Optimize for review score, not technical complexity.

### 3. Reviewer-focused execution plan (docs produced alongside code)
> Now let's optimize the actual repository for reviewer score. Before generating code, create a
> reviewer-focused execution plan. For every implementation step: what to build, what evidence
> to collect, what output files to save, what artifacts to preserve, and which doc section it
> supports. I want documentation produced alongside development, not reconstructed afterward.
>
> Then provide: exact repository structure; exact implementation order; exact points to stop and
> run evaluations; exact artifacts after the first run; exact artifacts after the final run;
> draft outlines for README, DECISIONS, ITERATION, PROMPTS. The goal is to rank as a strong
> candidate, not just complete the assignment.

### 4. Implement, step by step (Step 0 and Step 1)
> The architecture and evaluation strategy are now approved. Proceed with implementation.
>
> Constraints: optimize for reviewer score, not feature count; keep it as small as possible; no
> LangChain, Pinecone, vector DBs, or orchestration frameworks; prefer plain Python; prefer
> clarity over extensibility.
>
> Follow the execution plan exactly. Stop after each major step and explain what was built, why,
> what evidence to capture, and which doc section it supports. Start with Step 0 (repository
> structure, file layout, data organization), then Step 1 (run_cases.py contract stub). Do not
> implement further steps until those are complete and reviewed.

### 5. Step 2 — policies, tools, tests
> Proceed to Step 2. Implement policies.py, tools.py, tests/test_tools.py.
>
> Requirements: (1) user_id must be injected server-side and never supplied by the model. (2)
> Use orders.json.today as the source of truth for all date calculations. (3) Precompute
> next_upcoming_installment and other deterministic fields in the tool, not in the LLM. (4) Add
> tests covering the v01 expected payment calculation. (5) Explain every design choice. (6) Tell
> me exactly what evidence to record in devlog.md. Do not implement the LLM yet.

### 6. Step 3 — prompts, llm, agent
> Proceed to Step 3. Implement prompts.py, llm.py, agent.py.
>
> Follow the agreed architecture: full policy context in prompt; single-pass tool calling;
> structured output {route, answer}. Keep routing model-driven, not keyword-driven. Bind user_id
> server-side so the model can never request another user's data. Explain the system prompt, why
> each routing category exists, and why the tool interface is safe. After implementation: show a
> sample interaction and identify expected weaknesses before the first evaluation run. Do not
> optimize for the visible cases — optimize for hidden-case robustness.

### 7. Constraint pivot — $0, no paid API
> I do not have an Anthropic API key, and I do not intend to spend money on this take-home. Treat
> a paid API as a last resort.
>
> Redesign so that: the LLM interface stays provider-agnostic; Anthropic is no longer required;
> OpenAI is not assumed; the default uses Ollama locally; the solution can be completed at $0.
>
> Evaluate the impact of local models on: structured output reliability, tool-calling
> reliability, route-classification quality, policy-grounding quality, hidden-case robustness,
> development complexity (gain / lose / risks for each). Then compare qwen3, qwen2.5:7b-instruct,
> llama3.1:8b, gemma3, mistral-small (RAM, speed, JSON compliance, instruction-following,
> suitability). Then answer: if optimizing to pass this take-home at $0, which model and why?
> Also estimate total cost with Ollama, Anthropic, and OpenAI for the visible cases plus a few
> iteration passes. Be brutally practical and cost-conscious.

### 8. Implement the Ollama redesign
> The architecture change is approved. Do not spend more time on analysis. Proceed with
> implementation.
>
> (1) Implement the Ollama-based provider-agnostic LLM layer. (2) Use qwen2.5:7b-instruct as the
> default. (3) Implement the router → fetch → answer flow. (4) Keep routing model-driven. (5) Use
> schema-constrained JSON output. (6) Disable any reasoning/thinking output. (7) Keep
> Anthropic/OpenAI behind the same interface, optional. (8) Comment the design decisions that
> support the ADRs. After implementation, review the code as a Sezzle reviewer and identify
> weaknesses before Checkpoint A, then stop.

### 9. Step 4 — first eval run + diagnosis
> Ollama is installed and qwen2.5:7b is responding correctly. Proceed with Step 4.

### 10. Step 5 — fix failure classes, measure each change
> Proceed to Step 5. Goals: fix failure classes, not individual cases; preserve the iteration
> evidence; capture the impact of every meaningful change (hypothesis, why it should help the
> class, before/after delta, update devlog.md). Priorities: (1) answer truncation, (2) escalate
> vs both routing, (3) both vs tool routing, (4) v04 failed-installment grounding, (5)
> defense-in-depth guardrails. Avoid case-specific hacks; optimize for hidden-case robustness.
> After the fixes: run evaluation again, produce the final taxonomy, compare first vs final, and
> identify remaining weaknesses honestly. Then stop and prepare the documentation inputs.

### 11. Step 6 — lightweight red-team + latency (max 15 min)
> Proceed with a lightweight Step 6. Maximum 15 minutes. Red-team the final system, generate
> documentation evidence, measure latency and runtime characteristics, and produce artifacts
> useful for README, DECISIONS, and ITERATION. Do not modify the agent unless a critical issue is
> discovered. After Step 6, stop implementation and move directly to README, DECISIONS,
> ITERATION, PROMPTS. Prioritize professionalism, clarity, and reviewer experience.

### 12. Full repository review (reviewer hat)
> Act as a senior Sezzle reviewer evaluating whether this candidate should advance. Assess
> engineering judgment, professionalism, communication quality, and overall signal — not
> features. Review: repository professionalism; documentation quality (weak wording, vague
> explanations, AI-generated-sounding text, missing evidence); reviewer perception (junior / mid
> / senior / strong applied AI signals, present vs missing); story coherence; evidence quality;
> candidate ranking out of 100; and high-impact improvements only (< 30 min, presentation and
> credibility, no new features). Be brutally honest.

### 13. Apply the polish
> Yes, do it, make everything clean — remember the objective was [the recruiter brief: a ~2-hour
> take-home that mirrors the Applied AI team's work; graded on design decisions and one round of
> visible iteration, with the build prompts included].

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
