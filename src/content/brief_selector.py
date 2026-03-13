from __future__ import annotations


def _safe_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def score_market_for_brief(market: dict) -> float:
    """
    Score markets for inclusion in the daily brief.

    Strongly prefer:
    - interpretable probabilities (roughly 10% to 90%)
    - especially probabilities closer to the middle
    - liquidity only as a light tie-breaker
    """
    price = (
        market.get("last_price")
        or market.get("yes_bid")
        or market.get("yes_ask")
    )
    price = _safe_float(price)

    volume = _safe_float(market.get("volume"))
    open_interest = _safe_float(market.get("open_interest"))

    # Very strong penalty for trivial/extreme contracts
    if price <= 0.03 or price >= 0.97:
        extreme_penalty = -20.0
    elif price <= 0.08 or price >= 0.92:
        extreme_penalty = -10.0
    else:
        extreme_penalty = 0.0

    # Reward being close to the center
    # 0.50 gets the best score, tails get much lower
    distance_from_50 = abs(price - 0.5)
    center_score = (1 - distance_from_50) * 20.0

    # Liquidity only as a light tie-breaker
    liquidity_score = volume * 0.0000005 + open_interest * 0.000001

    return center_score + liquidity_score + extreme_penalty


def select_best_brief_market(markets: list[dict]) -> dict | None:
    if not markets:
        return None

    scored = [(score_market_for_brief(m), m) for m in markets]
    scored.sort(reverse=True, key=lambda x: x[0])

    return scored[0][1]

