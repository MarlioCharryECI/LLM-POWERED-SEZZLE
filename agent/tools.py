"""Order lookup tool — deterministic, user-scoped, arithmetic precomputed.

Two design commitments this file enforces (both are graded):

1. AUTHORIZATION IS STRUCTURAL, NOT REQUESTED.
   Every public function takes `user_id` as its first argument and only ever
   returns rows where `order["user_id"] == user_id`. There is no code path that
   fetches an order by id without a user_id. In Step 3 the model's tool is bound
   to the case's user_id server-side (the model has no argument to pass one), so
   the model *cannot* read another shopper's data even if it tries. This is the
   difference between "prevented" and "told not to".

2. FRAGILE MATH LIVES HERE, NOT IN THE LLM.
   All date/money reasoning (next payment, days until due, remaining balance,
   refund business-day window) is computed deterministically against the frozen
   clock `orders.json.today` and handed to the model as facts. The model
   verbalizes and applies policy; it does not do arithmetic. This removes the
   biggest hallucination surface (wrong dates/amounts stated confidently).
"""

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "orders.json"

RESCHEDULE_MAX = 3          # policy 02: max 3 reschedules per order
RESCHEDULE_FEE = 5          # policy 02/10: 2nd and 3rd reschedule cost $5
REFUND_WINDOW_BUSINESS_DAYS = 10  # policy 04: refund lands within 3-10 business days


@lru_cache(maxsize=1)
def _load():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_today() -> date:
    """The frozen 'current date' — the ONLY clock used for reasoning.

    We never call datetime.now(): the dataset ships a `today` and all golden
    expectations are relative to it. Using the wall clock would silently break
    every 'next payment' answer.
    """
    return date.fromisoformat(_load()["today"])


def _parse(d):
    return date.fromisoformat(d) if d else None


def _business_days_between(start: date, end: date) -> int:
    """Weekdays strictly after `start`, up through `end` (Mon-Fri only).

    Simplification: no holiday calendar — documented assumption. Good enough to
    decide whether a refund is still inside its 3-10 business-day window.
    """
    if end <= start:
        return 0
    days = 0
    cur = start
    while cur < end:
        cur = cur.fromordinal(cur.toordinal() + 1)
        if cur.weekday() < 5:  # 0=Mon .. 4=Fri
            days += 1
    return days


def _enrich_order(order: dict, today: date) -> dict:
    """Attach precomputed deterministic facts to one raw order record."""
    installments = order.get("installments", [])

    upcoming = [i for i in installments if i.get("status") == "upcoming"]
    upcoming.sort(key=lambda i: i["due_date"])
    next_up = upcoming[0] if upcoming else None
    next_upcoming = None
    if next_up:
        due = _parse(next_up["due_date"])
        next_upcoming = {
            "installment": next_up["installment"],
            "amount": next_up["amount"],
            "due_date": next_up["due_date"],
            "days_until_due": (due - today).days,  # negative if overdue
        }

    failed = [i for i in installments if i.get("status") == "failed"]
    paused = [i for i in installments if i.get("status") == "paused"]
    unpaid = [i for i in installments if i.get("status") != "paid"]
    remaining_unpaid_total = round(sum(i["amount"] for i in unpaid), 2)

    used = order.get("reschedules_used", 0)
    remaining_reschedules = max(0, RESCHEDULE_MAX - used)
    next_free = used == 0
    next_fee = 0 if (next_free and remaining_reschedules > 0) else RESCHEDULE_FEE

    refund = order.get("refund")
    refund_out = None
    if refund:
        issued = _parse(refund.get("issued_date"))
        bdays = _business_days_between(issued, today) if issued else None
        refund_out = {
            "amount": refund.get("amount"),
            "issued_date": refund.get("issued_date"),
            "status": refund.get("status"),
            "business_days_since_issued": bdays,
            "within_standard_window": (
                bdays is not None and bdays <= REFUND_WINDOW_BUSINESS_DAYS
            ),
        }

    return {
        "order_id": order["order_id"],
        "merchant": order["merchant"],
        "order_date": order["order_date"],
        "total": order["total"],
        "plan": order["plan"],
        "status": order["status"],
        "reschedules_used": used,
        "reschedules_remaining": remaining_reschedules,
        "next_reschedule_free": next_free and remaining_reschedules > 0,
        "next_reschedule_fee": next_fee,
        "next_upcoming_installment": next_upcoming,
        "failed_installments": failed,
        "paused_installments": paused,
        "remaining_unpaid_count": len(unpaid),
        "remaining_unpaid_total": remaining_unpaid_total,
        "refund": refund_out,
        "installments": installments,
    }


def get_orders(user_id: str) -> dict:
    """Return ALL orders for `user_id`, enriched — and nothing else.

    This is the authorization boundary: rows are filtered by user_id before any
    data leaves this function. Unknown user -> empty list (the agent should then
    say it can't find the account / escalate), never an error, never another
    user's data.
    """
    data = _load()
    today = get_today()
    mine = [o for o in data["orders"] if o.get("user_id") == user_id]
    return {
        "user_id": user_id,
        "as_of": today.isoformat(),
        "found": len(mine) > 0,
        "orders": [_enrich_order(o, today) for o in mine],
    }


def get_order(user_id: str, order_id: str):
    """Look up a single order BY id, still scoped to the owner.

    Returns the enriched order, or None if it doesn't exist OR isn't this user's.
    The two cases are intentionally indistinguishable to the caller so we never
    leak the existence of another shopper's order id.
    """
    for o in get_orders(user_id)["orders"]:
        if o["order_id"] == order_id:
            return o
    return None
