# Iteration

The 10 visible cases were used as a **regression harness**, not a target. All runs are at
`temperature 0` against the frozen clock (`orders.json.today = 2026-07-01`). `eval.py` checks
three things per case: predicted route, every `must_include` regex, and no `must_not_include`
regex. Every number below is reproducible from committed artifacts: `answers_first.jsonl` +
`eval_first.txt` (first), `answers_c1..c3` + `eval_c1..c3` (each change), and
`answers_final.jsonl` + `eval_final.txt` (final).

## First run — and a harness bug caught before trusting it
The first scoring flagged v07 for "waived"/"I've paused" it never said, and v02 for "ord_"
it never contained. Root cause was **my scorer**, not the model: `must_not_include` was
inverted. I fixed `eval.py` and rescored the *same* first-run answers (model output
unchanged). This is why the honest baseline is the corrected number.

**Corrected first-run baseline: 5/10 pass, 7/10 route-correct.**
Passing: v01, v03, v07, v08, v09. Failing: v02, v04, v05, v06, v10.

## Failure taxonomy → fixes (class-level, measured)
| # | Class | Cases | Root cause | Fix | Type |
|---|---|---|---|---|---|
| 1 | Answer truncation | v02, v06 | schema-JSON can't hold raw newlines → bulleted lists dead-end and close early | force single-paragraph prose + raise `num_predict` | prompt+config |
| 2 | Route escalate-vs-both | v05, v06 | human-only *actions* routed `both` because they touch policy+account | ordered router rule: human-only action → escalate **first** | prompt |
| 3 | Route both-vs-tool | v10 | refund status looks like a pure lookup | router rule: refund/return = both | prompt |
| 4 | Grounding on trap | v04 | model ignored `failed_installments`, discussed reschedule fees | answer rule: failed installment **cannot be rescheduled, must be repaid** | prompt |
| 5 | Forbidden disclosures | v05, v07 | 7B can state a decline reason/limit or promise a waiver | deterministic post-scrub → safe escalate | **code (structural)** |

### Per-change delta (PASS / route-correct over 10)
- Baseline (corrected) .................. 5 / 7
- C1 truncation ......................... 5 / 7  (truncation gone; v02 inc 0→1, v06 1→3; exposed v05 fabricating a decline reason)
- C2 router ordered rules ............... 6 / 8  (v06 → escalate)
- C3 v04 repay grounding + refund specifics 6 / 8  (v02 pass; v04 gains "repaid"; v10 answer 3/3 but route still tool)
- C4 guardrail scrub + specificity polish  8 / 9  (v04 pass; **v05 pass via guardrail** — model fabricated a decline reason, scrub forced escalate; v06 pass)

**Final: 8–9/10 pass, 9/10 route-correct** (v03 swings run-to-run — see below).

## Step 6 red-team (see `artifacts/redteam.md`)
Held up: authorization (a request for another user's `ord_3001` returned only the caller's
orders — structural), limit extraction, fraud, and an "admin mode, waive my fees" injection
(refused + escalated). **Found + fixed a critical leak:** a hardship reply promised, in
*passive* voice, "payments will be paused and fees will be waived" — the guardrail only
caught first-person phrasing. I added a passive/active **waiver** pattern (deliberately not
touching "pause", so legitimate dispute-pause answers like v06 are unaffected). Re-verified:
the hardship probe now scrubs to safe text; 19 unit tests pass; golden set did not regress.

## Remaining weaknesses (honest)
1. **v10 routing ceiling** — `qwen2.5:7b` keeps labeling refund status as `tool` despite an
   explicit rule; the *answer is correct*, only the route label is wrong. Rejected fixes: a
   deterministic refund→both override (the keyword hack the brief warns against) and a bigger
   model (breaks $0).
2. **Run-to-run variance** — even at `temperature 0`, local inference varies slightly
   (num_predict/GPU batching); v02/v03/v04/v06/v10 each flipped at least once. v03's final
   miss conflated `days_until_due` (10) with the 2-week reschedule window. Not chased —
   chasing ±1 visible case is overfitting the ten.
3. **Scrub is regex** — defense-in-depth, not a proof; a novel paraphrase could slip.
4. **Injection can induce a false status claim** — with no tool call, one injection made the
   model assert "your account is paused." It still refused the waiver and escalated.

## What I'd do next (unfinished)
Seed/greedy-decode to kill variance; a tiny separate router model for cheaper, firmer
routing; an LLM-as-judge grader beyond regex substrings; and a clarify-branch for ambiguous
multi-order references ("my Bloom & Vine order" when the user has two).
