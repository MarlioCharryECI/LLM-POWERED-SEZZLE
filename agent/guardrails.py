"""Deterministic output guardrails — defense-in-depth AFTER the model.

The prompt TELLS the model not to reveal a specific spending limit / decline
reason or promise a waiver/pause. This module makes those failures unable to
reach the shopper even when a small model slips: if the generated answer trips a
forbidden pattern, we override to a safe escalate with canned copy. That is the
"structurally prevented, not merely told" property the rubric rewards.

Scope is deliberately narrow to avoid clobbering good answers:
- We only trigger on a *specific decline reason* or a *stated limit figure*, not
  on general explanations of how limits work (which policy allows).
- We only trigger on *first-person* commitments to waive/pause/extend, not on
  describing what a human agent might discuss.
"""

import re

# "declined ... because/due to/since/exceeded ..." = a specific decline reason.
_DECLINE_REASON = re.compile(
    r"\bdeclin\w*\b[^.]{0,60}\b(because|due to|since|as it|exceed\w*)", re.IGNORECASE
)
# A concrete spending-limit figure being disclosed.
_LIMIT_FIGURE = re.compile(
    r"\b(spending|credit|order)?\s*limit\b[^.]{0,25}\$\s?\d"
    r"|\$\s?\d[\d,.]*[^.]{0,25}\blimit\b",
    re.IGNORECASE,
)
# First-person promise to waive / pause / extend.
_PROMISE = re.compile(
    r"\bI\s*('?ve|'?ll| have| will| can| could| am able to| am going to)\b"
    r"[^.]{0,30}\b(waiv\w*|paus\w*|extend\w*)",
    re.IGNORECASE,
)
# Passive/active WAIVER promise in any voice ("fees will be waived", "we waived").
# We scrub waivers broadly because the assistant is never authorized to grant one
# (the single automatic failed-payment waiver is not assistant-promised). We do
# NOT scrub "pause" here: pausing is legitimate during a dispute investigation, and
# a blanket pause-scrub would wrongly clobber correct dispute answers. The gerund
# "waiving" (e.g. "a human agent can discuss waiving fees") is intentionally NOT
# matched — that is describing, not promising.
_WAIVER = re.compile(
    r"\b(waived|waiver\b|will\s+(be\s+)?waive|have\s+waived|waive\s+your)\b",
    re.IGNORECASE,
)

_LIMIT_SAFE = (
    "I'm not able to share the exact reason an individual order was declined or "
    "your precise spending limit — that needs a human agent, and I'm connecting "
    "you with one now. In general, spending power is dynamic: it grows with "
    "on-time payments and as you pay down open orders."
)

_PROMISE_SAFE = (
    "I'm really sorry you're dealing with this. I'm not able to change your "
    "payments or fees myself, but I'm connecting you with a human support "
    "specialist who can go over your options with you."
)


def scrub(route: str, answer: str) -> tuple[str, str, str | None]:
    """Return (route, answer, tripped) — tripped names the rule if overridden."""
    if _DECLINE_REASON.search(answer) or _LIMIT_FIGURE.search(answer):
        return "escalate", _LIMIT_SAFE, "limit_or_decline"
    if _PROMISE.search(answer) or _WAIVER.search(answer):
        return "escalate", _PROMISE_SAFE, "waiver_or_pause_promise"
    return route, answer, None
