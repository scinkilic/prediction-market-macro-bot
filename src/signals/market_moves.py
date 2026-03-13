from __future__ import annotations

from typing import Dict, List, Any


def detect_large_price_moves(
    markets: List[Dict[str, Any]],
    threshold: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Detect markets where bid/ask spread suggests a large probability move.
    """

    signals = []

    for market in markets:
        yes_bid = market.get("yes_bid")
        yes_ask = market.get("yes_ask")

        if yes_bid is None or yes_ask is None:
            continue

        spread = abs(yes_ask - yes_bid)

        if spread >= threshold:
            signals.append(
                {
                    "ticker": market.get("ticker"),
                    "title": market.get("title"),
                    "yes_bid": yes_bid,
                    "yes_ask": yes_ask,
                    "spread": spread,
                }
            )

    return signals
