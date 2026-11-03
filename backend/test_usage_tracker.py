"""Run with: python -m unittest test_usage_tracker.py -v (offline tests)."""

import unittest
from decimal import Decimal

from usage_tracker import summarize_usage


SAMPLE_USAGE = {
    "openai/gpt-oss-20b": {
        "input_tokens": 400,
        "output_tokens": 50,
        "total_tokens": 450,
        "output_token_details": {"reasoning": 30},
    },
    "openai/gpt-oss-120b": {
        "input_tokens": 1000,
        "output_tokens": 200,
        "total_tokens": 1200,
    },
}

SAMPLE_PRICING = {
    "openai/gpt-oss-20b": (
        Decimal("0.000000018"), Decimal("0.00000009")
    ),
    "openai/gpt-oss-120b": (
        Decimal("0.00000015"), Decimal("0.0000006")
    ),
}


class UsageTrackerTests(unittest.TestCase):
    def test_totals_and_cost(self):
        result = summarize_usage(
            SAMPLE_USAGE,
            pricing_lookup=SAMPLE_PRICING.get,
        )
        self.assertEqual(result["input_tokens"], 1400)
        self.assertEqual(result["output_tokens"], 250)
        self.assertEqual(result["total_tokens"], 1650)
        self.assertEqual(result["reasoning_tokens"], 30)
        self.assertEqual(len(result["by_model"]), 2)
        self.assertAlmostEqual(result["estimated_cost_usd"], 0.0002817)

    def test_missing_price_is_not_reported_as_zero_cost(self):
        result = summarize_usage(
            SAMPLE_USAGE,
            pricing_lookup=lambda model: None,
        )
        self.assertEqual(result["total_tokens"], 1650)
        self.assertIsNone(result["estimated_cost_usd"])

    def test_empty_usage_means_unknown_not_free(self):
        result = summarize_usage({}, pricing_lookup=SAMPLE_PRICING.get)
        self.assertFalse(result["usage_available"])
        self.assertIsNone(result["estimated_cost_usd"])


if __name__ == "__main__":
    unittest.main()
