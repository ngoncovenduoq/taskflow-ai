"""Summarize LangChain token usage and estimate OpenRouter model costs.

Pricing is public catalog pricing, not the definitive billed generation cost.
"""

import re
from decimal import Decimal
from functools import lru_cache
from urllib.parse import quote


_MODEL_SLUG = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.:/-]+")


@lru_cache(maxsize=32)
def get_model_pricing(model: str):
    """Return (input_price, output_price) in USD/token, or None.

    Public pricing is fetched only once per model per Python process.
    A price lookup failure must never break a user chat request.
    """
    if not _MODEL_SLUG.fullmatch(model):
        return None

    try:
        import requests

        url = (
            "https://openrouter.ai/api/v1/model/"
            + quote(model, safe="/")
        )
        response = requests.get(url, timeout=4)
        response.raise_for_status()
        data = response.json().get("data", {})
        pricing = data.get("pricing", {})

        input_rate = Decimal(str(pricing["prompt"]))
        output_rate = Decimal(str(pricing["completion"]))

        if input_rate < 0 or output_rate < 0:
            return None

        return input_rate, output_rate
    except Exception:
        # Missing/changed catalog data, network errors, etc.
        return None


def summarize_usage(usage_metadata: dict, pricing_lookup=None) -> dict:
    """Create a JSON-ready per-model usage report.

    In tests, pricing_lookup can be supplied to avoid all network traffic.
    """
    lookup = pricing_lookup or get_model_pricing
    usage_metadata = usage_metadata or {}

    model_rows = []
    all_prices_available = bool(usage_metadata)
    estimated_total = Decimal("0")
    input_total = 0
    output_total = 0
    tokens_total = 0
    reasoning_total = 0

    for model, usage in sorted(usage_metadata.items()):
        usage = usage or {}
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        total_tokens = int(
            usage.get("total_tokens") or input_tokens + output_tokens
        )
        reasoning_tokens = int(
            (usage.get("output_token_details") or {}).get("reasoning") or 0
        )

        input_total += input_tokens
        output_total += output_tokens
        tokens_total += total_tokens
        reasoning_total += reasoning_tokens

        rates = lookup(model)
        estimated_cost = None
        if rates is None:
            all_prices_available = False
        else:
            input_rate, output_rate = map(Decimal, map(str, rates))
            estimated_cost = (
                input_rate * input_tokens + output_rate * output_tokens
            )
            estimated_total += estimated_cost

        model_rows.append({
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": (
                float(estimated_cost) if estimated_cost is not None else None
            ),
        })

    return {
        "usage_available": bool(usage_metadata),
        "input_tokens": input_total,
        "output_tokens": output_total,
        "reasoning_tokens": reasoning_total,
        "total_tokens": tokens_total,
        "estimated_cost_usd": (
            float(estimated_total) if all_prices_available else None
        ),
        "cost_is_estimate": True,
        "by_model": model_rows,
    }
