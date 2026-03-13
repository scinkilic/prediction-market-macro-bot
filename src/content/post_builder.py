from __future__ import annotations

from datetime import datetime
from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def format_price(price) -> str:
    price = _safe_float(price)
    if price is None:
        return "N/A"
    return f"{round(price * 100, 1)}%"


def build_market_snapshot_post(market: dict, captured_at: str) -> str:
    title = market.get("title", "Unknown Market")
    ticker = market.get("ticker", "")

    price = (
        market.get("last_price")
        or market.get("yes_bid")
        or market.get("yes_ask")
    )

    price_str = format_price(price)

    timestamp = datetime.fromisoformat(captured_at).strftime("%b %d %Y %H:%M UTC")

    post = f"""
Current Kalshi snapshot:

{title}

Current market probability: {price_str}

Ticker: {ticker}
As of: {timestamp}
""".strip()

    return post


def build_top_markets_post(markets: list[dict], captured_at: str, limit: int = 5) -> str:
    timestamp = datetime.fromisoformat(captured_at).strftime("%b %d %Y %H:%M UTC")

    lines = []

    for m in markets[:limit]:
        price = (
            m.get("last_price")
            or m.get("yes_bid")
            or m.get("yes_ask")
        )

        price_str = format_price(price)
        title = m.get("title", "Unknown")

        lines.append(f"{price_str} — {title}")

    body = "\n".join(lines)

    post = f"""
Prediction market snapshot:

{body}

As of: {timestamp}
Source: Kalshi
""".strip()

    return post


def build_signal_post(signal: dict, captured_at: str) -> str:
    timestamp = datetime.fromisoformat(captured_at).strftime("%b %d %Y %H:%M UTC")

    title = signal.get("title", "Unknown market")
    previous_price = format_price(signal.get("previous_price"))
    current_price = format_price(signal.get("current_price"))

    raw_change = _safe_float(signal.get("price_change")) or 0.0
    change_points = raw_change * 100.0

    direction = "rose" if raw_change > 0 else "fell"

    post = f"""
Prediction market move:

{title}

Odds {direction} from {previous_price} to {current_price}
Move: {change_points:+.1f} points

As of: {timestamp}
Source: Kalshi
""".strip()

    return post

