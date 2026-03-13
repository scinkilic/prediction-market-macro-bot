from __future__ import annotations


def _safe_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def score_market_interest(market: dict) -> float:
    """
    Score how interesting a market is.

    We favor:
    - probabilities near 50%
    - higher volume
    - higher open interest
    """

    price = (
        market.get("last_price")
        or market.get("yes_bid")
        or market.get("yes_ask")
    )

    price = _safe_float(price)

    volume = _safe_float(market.get("volume"))
    open_interest = _safe_float(market.get("open_interest"))

    distance_from_50 = abs(price - 0.5)

    score = (
        (1 - distance_from_50) * 10
        + volume * 0.000002
        + open_interest * 0.000005
    )

    return score


def select_best_market_per_event(markets: list[dict]) -> list[dict]:
    """
    For each event_ticker keep only the most interesting contract.
    """

    best_by_event = {}

    for market in markets:

        event = market.get("event_ticker")

        if not event:
            continue

        score = score_market_interest(market)

        if event not in best_by_event:
            best_by_event[event] = (score, market)
            continue

        if score > best_by_event[event][0]:
            best_by_event[event] = (score, market)

    return [m for _, m in best_by_event.values()]

