"""Agent orchestration — router -> fetch -> answer.

Flow (flat and auditable):
  1. ROUTER  : model classifies the question into one of four routes (model-driven).
  2. FETCH   : if route needs account data (tool|both), we call get_orders for the
               BOUND user_id ourselves. The model never supplies a user_id, so it
               cannot reach another shopper's data. For policy|escalate we fetch
               nothing, so order data cannot leak on those routes.
  3. ANSWER  : model writes the grounded, shopper-facing reply.

Every LLM call is schema-constrained JSON; any transport/parse failure degrades
to a safe escalate, because "hand to a human" is the correct support default when
the pipeline can't answer. This is evidence-generating over clever: deterministic
control flow, easy to diagnose at Checkpoint A.
"""

import time

from agent import prompts
from agent.llm import chat_json
from agent.tools import get_orders

VALID_ROUTES = {"policy", "tool", "both", "escalate"}
_NEEDS_ORDERS = {"tool", "both"}

_ESCALATE_FALLBACK = {
    "route": "escalate",
    "answer": (
        "I'm sorry, I'm having trouble with that right now — let me connect you "
        "with a human support agent who can help."
    ),
}


def _route(question: str, meta: dict) -> str:
    t0 = time.perf_counter()
    obj = chat_json(prompts.build_router_system(), question, prompts.ROUTE_SCHEMA)
    meta["router_ms"] = round((time.perf_counter() - t0) * 1000)
    route = obj.get("route")
    return route if route in VALID_ROUTES else "escalate"


def _answer(question: str, route: str, orders, meta: dict) -> str:
    user = prompts.build_answer_user(question, route, orders)
    t0 = time.perf_counter()
    obj = chat_json(prompts.build_answer_system(), user, prompts.ANSWER_SCHEMA)
    meta["answer_ms"] = round((time.perf_counter() - t0) * 1000)
    answer = obj.get("answer", "")
    return answer if isinstance(answer, str) and answer.strip() else ""


def answer_case(question: str, user_id: str, return_meta: bool = False) -> dict:
    """Answer one support question for the authenticated `user_id`.

    `user_id` is the authorization boundary: captured here, passed to get_orders
    by us. The model has no channel to request a different shopper's data.
    """
    meta = {"tool_called": False, "route": None}
    try:
        route = _route(question, meta)
        meta["route"] = route

        orders = None
        if route in _NEEDS_ORDERS:
            orders = get_orders(user_id)   # server-side, bound user_id
            meta["tool_called"] = True

        answer = _answer(question, route, orders, meta)
        if not answer:
            result = dict(_ESCALATE_FALLBACK)
        else:
            result = {"route": route, "answer": answer}
    except Exception as e:  # never let one case break the batch
        meta["error"] = repr(e)
        result = dict(_ESCALATE_FALLBACK)

    if return_meta:
        return {**result, "_meta": meta}
    return result
