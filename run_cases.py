"""The one contract.

    python run_cases.py <cases.jsonl> <answers.jsonl>

Reads a JSONL of {id, question, user_id} and writes a JSONL of
{id, route, answer}. This is the interface the hidden test set runs against, so
it is kept deliberately small and defensive:

- one input line -> exactly one output line, order preserved;
- a malformed or failing case never aborts the batch — it emits a safe
  `escalate` fallback, because in a support setting "hand to a human" is the
  correct behavior when the pipeline cannot answer.

All intelligence lives behind `agent.answer_case`; this file is pure I/O.
"""

import json
import sys

from agent.agent import answer_case

VALID_ROUTES = {"policy", "tool", "both", "escalate"}


def _read_cases(path):
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[warn] skipping malformed line {line_no}: {e}", file=sys.stderr)


def _normalize(result, case_id):
    """Coerce whatever the agent returned into a valid contract record."""
    route = result.get("route")
    answer = result.get("answer", "")
    if route not in VALID_ROUTES:
        route = "escalate"
    return {"id": case_id, "route": route, "answer": answer}


def run(cases_path, answers_path):
    n = 0
    with open(answers_path, "w", encoding="utf-8") as out:
        for case in _read_cases(cases_path):
            case_id = case.get("id")
            question = case.get("question", "")
            user_id = case.get("user_id", "")
            try:
                result = answer_case(question, user_id)
            except Exception as e:  # never let one case kill the batch
                print(f"[warn] case {case_id} failed: {e}", file=sys.stderr)
                result = {
                    "route": "escalate",
                    "answer": "Something went wrong on our side — connecting you to a human agent.",
                }
            record = _normalize(result, case_id)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            n += 1
    print(f"[ok] wrote {n} answers to {answers_path}", file=sys.stderr)


def main(argv):
    if len(argv) != 3:
        print("usage: python run_cases.py <cases.jsonl> <answers.jsonl>", file=sys.stderr)
        return 2
    run(argv[1], argv[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
