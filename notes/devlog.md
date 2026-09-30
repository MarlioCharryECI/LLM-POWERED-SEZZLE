# Dev log (live scratch → source for the 4 deliverable docs)

Frozen clock for all order reasoning: `data/orders.json.today = 2026-07-01`
(NOT the system date). Evidence anchor: golden v01 → next payment for ord_3006
is installment 4, due 2026-07-11, amount 118.36.

## Step 0 — scaffold + data move
- Created layout: agent/, data/(orders.json + policies/), cases/, artifacts/, notes/, tests/.
- Moved the provided kit into the brief's expected paths (`data/`, `cases/`); left the
  original `docs/` kit untouched as provenance.
- Renamed 12 policy files to clean ordered slugs `01..12-*.md`.
- Decision to record (README rename note): matching the brief's canonical layout so
  `run_cases.py` reads `cases/*.jsonl` and `data/orders.json` the way a reviewer expects.

## Step 1 — contract stub
- `run_cases.py` written in final shape (pure I/O); intelligence hidden behind
  `agent.answer_case(question, user_id) -> {route, answer}` (signature frozen).
- Defensive by design: malformed input line skipped with warning; per-case
  exception emits a safe `escalate` fallback (correct support default) so one bad
  case can't abort the hidden-set batch; invalid route coerced to `escalate`.
- Proven: ran over `cases/golden_visible.jsonl` → 10 in / 10 out, valid schema,
  order preserved. (stub returns placeholder escalate; real agent = Step 3.)
- Env note for later steps: interpreter at
  `...\Python313\python.exe`; `anthropic` NOT yet installed and no API key set —
  needed from Step 3.

## Step 2 — policies.py, tools.py, tests
- policies.py: loads all 12 docs, sorted order, wrapped in <policy source="..">
  tags for citeability. Measured size: **12 policies, 8260 chars (~2k tokens)** —
  confirms full-stuffing is viable; this number backs DECISIONS #1 (retrieval) and
  the cost ADR (#3, cacheable prefix).
- tools.py structural guarantees:
  * AUTH: every fn takes user_id first; get_order(user_id, order_id) returns None
    for BOTH foreign and nonexistent ids (indistinguishable → no existence leak).
    Step 3 binds user_id server-side so the model has no arg to pass a foreign id.
  * FROZEN CLOCK: get_today() reads orders.json.today (2026-07-01); never now().
  * PRECOMPUTED (off the LLM): next_upcoming_installment (+days_until_due),
    failed/paused installments, remaining_unpaid_total, refund business-day window,
    reschedule fee/remaining. Model verbalizes facts, does no arithmetic.
- Assumption logged: business-day calc is weekday-only (no holiday calendar) —
  sufficient for the 3–10 day refund window decision.
- EVIDENCE (tests pin the fragile math to golden expectations):
  * v01: ord_3006 next = inst 4, due 2026-07-11, $118.36, 10 days out ✓
  * v10: ord_3014 refund = 3 business days since 06-28, within 10-day window ✓
  * v04: ord_3016 surfaces 1 failed installment (#2) ✓
  * v03: ord_3006 reschedules_used=0 → first free, fee 0, 3 remaining ✓
         ord_3001 used=2 → next fee $5, 1 remaining ✓
  * AUTH: u001 cannot read u002's ord_3006 (None); unknown user → empty, no error ✓
  * All 11 tests pass (`python -m unittest discover -s tests`).
- Supports: DECISIONS #1 & #2, ITERATION (date/auth de-risking), README §Guardrails.

## Failure taxonomy (fill at Checkpoint A)
- (pending first run)
