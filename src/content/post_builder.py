from __future__ import annotations

from datetime import datetime


def format_price(price) -> str:
    if price is None:
        return "N/A"

    try:
        price = float(price)
    except Exception:
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
Market snapshot:

{title}

Current market probability: {price_str}

Ticker: {ticker}
Source: Kalshi
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

Source: Kalshi
As of: {timestamp}
""".strip()

    return post
