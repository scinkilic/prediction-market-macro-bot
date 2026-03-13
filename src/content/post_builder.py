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

def build_top_movers_post(signals: list[dict], captured_at: str, limit: int = 5) -> str:
    timestamp = datetime.fromisoformat(captured_at).strftime("%b %d %Y %H:%M UTC")

    if not signals:
        return f"""
Top prediction market movers:

No meaningful movers detected.

As of: {timestamp}
Source: Kalshi
""".strip()

    lines = []

    for signal in signals[:limit]:
        title = signal.get("title", "Unknown market")
        previous_price = format_price(signal.get("previous_price"))
        current_price = format_price(signal.get("current_price"))

        raw_change = _safe_float(signal.get("price_change")) or 0.0
        change_points = raw_change * 100.0

        lines.append(
            f"{title}\n"
            f"{previous_price} → {current_price} ({change_points:+.1f} pts)"
        )

    body = "\n\n".join(lines)

    post = f"""
Top prediction market movers:

{body}

As of: {timestamp}
Source: Kalshi
""".strip()

    return post

def build_bucket_snapshot_post(
    markets: list[dict],
    captured_at: str,
    bucket_name: str,
    limit: int = 5,
) -> str:
    timestamp = datetime.fromisoformat(captured_at).strftime("%b %d %Y %H:%M UTC")

    if not markets:
        return f"""
{bucket_name.title()} prediction market snapshot:

No relevant markets found.

As of: {timestamp}
Source: Kalshi
""".strip()

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
{bucket_name.title()} prediction market snapshot:

{body}

As of: {timestamp}
Source: Kalshi
""".strip()

    return post

def build_daily_brief_post(
    macro_markets: list[dict],
    political_markets: list[dict],
    signals: list[dict],
    captured_at: str,
) -> str:
    timestamp = datetime.fromisoformat(captured_at).strftime("%b %d %Y %H:%M UTC")

    lines = ["Prediction market update:", ""]

    # Macro summary
    if macro_markets:
        top_macro = macro_markets[0]
        macro_price = (
            top_macro.get("last_price")
            or top_macro.get("yes_bid")
            or top_macro.get("yes_ask")
        )
        lines.append(
            f"{top_macro.get('title', 'Top macro market')} is currently at {format_price(macro_price)}."
        )
        lines.append("")

    # Political summary
    if political_markets:
        top_political = political_markets[0]
        political_price = (
            top_political.get("last_price")
            or top_political.get("yes_bid")
            or top_political.get("yes_ask")
        )

        lines.append(
            f"{top_political.get('title', 'Top political market')} is currently at {format_price(political_price)}."
        )

        if len(political_markets) > 1:
            second = political_markets[1]
            second_price = (
                second.get("last_price")
                or second.get("yes_bid")
                or second.get("yes_ask")
            )
            lines.append(
                f"{second.get('title', 'Second political market')} is at {format_price(second_price)}."
            )
        lines.append("")

    # Signal summary
    if signals:
        top_signal = signals[0]
        prev_price = format_price(top_signal.get("previous_price"))
        curr_price = format_price(top_signal.get("current_price"))
        raw_change = _safe_float(top_signal.get("price_change")) or 0.0
        change_points = raw_change * 100.0

        direction = "rose" if raw_change > 0 else "fell"

        lines.append(
            f"Biggest recent move: {top_signal.get('title', 'Unknown market')} {direction} from {prev_price} to {curr_price} ({change_points:+.1f} pts)."
        )
        lines.append("")
    else:
        lines.append("No major short-term market moves were detected in the latest snapshot.")
        lines.append("")

    lines.append(f"As of: {timestamp}")
    lines.append("Source: Kalshi")

    return "\n".join(lines).strip()

