"""Unit tests pinning the deterministic tool math and the auth boundary.

These exist because this is exactly the logic we deliberately moved OUT of the
LLM: if it's wrong, the model will repeat it confidently. So we pin it to the
golden expectations. Run: python -m pytest tests/ -q
(or: python -m unittest discover -s tests)
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools import get_orders, get_order, get_today  # noqa: E402


class TestFrozenClock(unittest.TestCase):
    def test_today_is_frozen_dataset_value(self):
        # Must be the dataset's date, NOT the wall clock.
        self.assertEqual(get_today().isoformat(), "2026-07-01")


class TestV01NextPayment(unittest.TestCase):
    """Golden v01: u002 Nordic Kicks -> next payment 2026-07-11, $118.36."""

    def test_next_upcoming_matches_golden(self):
        order = get_order("u002", "ord_3006")
        self.assertIsNotNone(order)
        nxt = order["next_upcoming_installment"]
        self.assertEqual(nxt["due_date"], "2026-07-11")
        self.assertEqual(nxt["amount"], 118.36)
        self.assertEqual(nxt["installment"], 4)
        # 2026-07-01 -> 2026-07-11 is 10 days out (well over the 24h reschedule rule).
        self.assertEqual(nxt["days_until_due"], 10)


class TestV04FailedInstallment(unittest.TestCase):
    """Golden v04: u006 Circuit City Lights (ord_3016) has a FAILED installment
    that policy says must be repaid, not rescheduled. The tool must surface it."""

    def test_failed_installment_surfaced(self):
        order = get_order("u006", "ord_3016")
        self.assertIsNotNone(order)
        self.assertEqual(order["status"], "payment_failed")
        self.assertEqual(len(order["failed_installments"]), 1)
        self.assertEqual(order["failed_installments"][0]["installment"], 2)


class TestV10RefundWindow(unittest.TestCase):
    """Golden v10: u005 ord_3014 refund issued 2026-06-28, still processing.
    As of 2026-07-01 that's 3 business days -> inside the 3-10 day window."""

    def test_refund_business_days_and_window(self):
        order = get_order("u005", "ord_3014")
        self.assertIsNotNone(order)
        refund = order["refund"]
        self.assertEqual(refund["status"], "processing")
        self.assertEqual(refund["business_days_since_issued"], 3)
        self.assertTrue(refund["within_standard_window"])
        # Refund applies to remaining unpaid installments first — but ord_3014 is
        # fully paid, so any refund is cash back to the shopper.
        self.assertEqual(order["remaining_unpaid_count"], 0)


class TestRescheduleDerivation(unittest.TestCase):
    """Golden v03: u002 ord_3006 has reschedules_used=0 -> first is free."""

    def test_first_reschedule_free(self):
        order = get_order("u002", "ord_3006")
        self.assertTrue(order["next_reschedule_free"])
        self.assertEqual(order["next_reschedule_fee"], 0)
        self.assertEqual(order["reschedules_remaining"], 3)

    def test_exhausted_reschedules_charge_fee(self):
        # ord_3001 has reschedules_used=2 -> next one costs $5, 1 remaining.
        order = get_order("u001", "ord_3001")
        self.assertFalse(order["next_reschedule_free"])
        self.assertEqual(order["next_reschedule_fee"], 5)
        self.assertEqual(order["reschedules_remaining"], 1)


class TestAuthorizationBoundary(unittest.TestCase):
    """The structural guardrail: a user can never see another user's order."""

    def test_foreign_order_returns_none(self):
        # ord_3006 belongs to u002; u001 must not be able to read it.
        self.assertIsNone(get_order("u001", "ord_3006"))

    def test_nonexistent_order_returns_none(self):
        self.assertIsNone(get_order("u002", "ord_9999"))

    def test_foreign_and_missing_are_indistinguishable(self):
        # Both return None: we never leak that ord_3006 exists for someone else.
        self.assertEqual(
            get_order("u001", "ord_3006"),
            get_order("u001", "ord_0000"),
        )

    def test_unknown_user_is_empty_not_error(self):
        result = get_orders("u999")
        self.assertFalse(result["found"])
        self.assertEqual(result["orders"], [])

    def test_get_orders_only_returns_owned_rows(self):
        result = get_orders("u002")
        self.assertTrue(all(o["order_id"] in {"ord_3005", "ord_3006"}
                            for o in result["orders"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
