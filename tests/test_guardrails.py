"""Pin the deterministic output guardrail: it must catch the dangerous patterns
and must NOT clobber legitimate answers. This is the structural half of "grounding
that's prevented, not merely requested"."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.guardrails import scrub  # noqa: E402


class TestGuardrailTrips(unittest.TestCase):
    """Dangerous outputs must be overridden to a safe escalate."""

    def test_fabricated_decline_reason(self):
        a = "Your order was declined yesterday because the amount exceeded your limit."
        route, _, tripped = scrub("both", a)
        self.assertEqual(route, "escalate")
        self.assertEqual(tripped, "limit_or_decline")

    def test_stated_limit_figure(self):
        route, _, tripped = scrub("both", "Your spending limit is $500 right now.")
        self.assertEqual(route, "escalate")
        self.assertEqual(tripped, "limit_or_decline")

    def test_waiver_or_pause_promise(self):
        route, _, tripped = scrub(
            "escalate", "Sure, I have paused your installments and waived the fee."
        )
        self.assertEqual(route, "escalate")
        self.assertEqual(tripped, "waiver_or_pause_promise")

    def test_passive_waiver_promise(self):
        # Step 6 red-team finding: passive voice must also be caught.
        route, _, tripped = scrub(
            "escalate", "Your payments will be paused and any fees will be waived."
        )
        self.assertEqual(route, "escalate")
        self.assertEqual(tripped, "waiver_or_pause_promise")


class TestGuardrailLeavesGoodAnswersAlone(unittest.TestCase):
    """No false positives on answers policy explicitly allows."""

    def _untouched(self, route, answer):
        r, a, tripped = scrub(route, answer)
        self.assertIsNone(tripped)
        self.assertEqual((r, a), (route, answer))

    def test_general_limit_explanation(self):
        self._untouched("escalate",
                        "Spending power is dynamic and grows with on-time payments.")

    def test_describing_human_agent_actions(self):
        self._untouched("escalate",
                        "A human agent can discuss pausing installments or waiving fees.")

    def test_reschedule_fee_mention(self):
        self._untouched("both",
                        "Your first reschedule is free; later ones cost $5.")

    def test_refund_amount_mention(self):
        self._untouched("both",
                        "Your refund of $185.19 applies to remaining installments first.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
