"""Score answers.jsonl against the golden cases.

    python eval.py <golden.jsonl> <answers.jsonl> [report.txt]

For each case we check three things the graders check:
  - route      : predicted route == expected_route
  - must_include: every regex matches the answer (case-insensitive)
  - must_not_include: no regex matches the answer

A case PASSES only if all three hold. We print a per-case table plus the failing
answers (for diagnosis) and a summary. If report.txt is given, the same output is
written there — that file becomes the eval_first / eval_final artifact.
"""

import json
import re
import sys


def _load_jsonl(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _check(patterns, text, want_match):
    """Return list of (pattern, ok) where ok means match-status == want_match."""
    results = []
    for p in patterns:
        found = re.search(p, text, re.IGNORECASE) is not None
        results.append((p, found == want_match))
    return results


def score(golden_path, answers_path):
    golden = _load_jsonl(golden_path)
    answers = {a["id"]: a for a in _load_jsonl(answers_path)}

    lines = []
    passed = 0
    route_hits = 0
    for case in golden:
        cid = case["id"]
        ans = answers.get(cid, {})
        answer_text = ans.get("answer", "")
        got_route = ans.get("route", "<missing>")
        exp_route = case["expected_route"]

        route_ok = got_route == exp_route
        # includes: ok == pattern IS present; excludes: ok == pattern is ABSENT.
        inc = _check(case.get("must_include", []), answer_text, want_match=True)
        exc = _check(case.get("must_not_include", []), answer_text, want_match=False)
        inc_ok = all(ok for _, ok in inc)
        exc_ok = all(ok for _, ok in exc)
        case_pass = route_ok and inc_ok and exc_ok

        passed += case_pass
        route_hits += route_ok

        inc_n = sum(ok for _, ok in inc)
        exc_n = sum(ok for _, ok in exc)
        lines.append(
            f"{cid}  {'PASS' if case_pass else 'FAIL'}  "
            f"route {exp_route:>8}->{got_route:<8} {'ok' if route_ok else 'XX'}  "
            f"inc {inc_n}/{len(inc)}  exc {exc_n}/{len(exc)}"
        )
        if not case_pass:
            if not route_ok:
                lines.append(f"      route miss: wanted {exp_route}, got {got_route}")
            for p, ok in inc:
                if not ok:
                    lines.append(f"      missing include: /{p}/")
            for p, ok in exc:
                if not ok:
                    lines.append(f"      leaked exclude:  /{p}/")
            lines.append(f"      answer: {answer_text}")

    n = len(golden)
    lines.append("")
    lines.append(f"PASS {passed}/{n}   route-correct {route_hits}/{n}")
    return "\n".join(lines)


def main(argv):
    if len(argv) < 3:
        print("usage: python eval.py <golden.jsonl> <answers.jsonl> [report.txt]",
              file=sys.stderr)
        return 2
    report = score(argv[1], argv[2])
    print(report)
    if len(argv) >= 4:
        with open(argv[3], "w", encoding="utf-8") as f:
            f.write(report + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
