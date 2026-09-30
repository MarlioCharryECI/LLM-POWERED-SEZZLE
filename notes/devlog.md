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

## Failure taxonomy (fill at Checkpoint A)
- (pending first run)
