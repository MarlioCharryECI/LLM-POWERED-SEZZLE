"""Agent orchestration.

STEP 1 STUB: returns a fixed placeholder so the run_cases.py contract can be
proven end-to-end before any LLM or tools exist. The real single-pass,
tool-enabled implementation lands in Step 3 and replaces the body of
`answer_case` only — the function signature and return shape are frozen here so
`run_cases.py` never has to change.
"""


def answer_case(question: str, user_id: str) -> dict:
    """Answer one support question.

    Args:
        question: the shopper's message.
        user_id:  the authenticated shopper id (injected by the harness; the
                  model never supplies this — this is where order-lookup
                  authorization is structurally enforced later).

    Returns:
        {"route": one of "policy"|"tool"|"both"|"escalate", "answer": str}
    """
    return {
        "route": "escalate",
        "answer": "[stub] agent not implemented yet",
    }
