from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _safe_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _hours_to_close(close_time: str | None, now: datetime) -> float:
    if not close_time:
        return 999999.0

    try:
        dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
        delta = dt - now
        return max(delta.total_seconds() / 3600.0, 0.0)
    except Exception:
        return 999999.0


def _market_price(market: dict) -> float:
    for field in ("last_price", "yes_bid", "yes_ask"):
        value = market.get(field)
        if value is not None:
            return _safe_float(value)
    return 0.0


def score_market_for_snapshot(market: dict, now: datetime | None = None) -> float:
    """
    Score a market for current-state snapshot content.
    Higher is better.
    """
    now = now or datetime.now(timezone.utc)

    volume = _safe_float(market.get("volume"))
    open_interest = _safe_float(market.get("open_interest"))
    price = _market_price(market)
    hours_to_close = _hours_to_close(market.get("close_time"), now)

    # Favor mid-range nontrivial probabilities slightly more than extreme dead-certainty markets
    middle_band_bonus = 1.0 - abs(price - 0.5) * 2.0
    middle_band_bonus = max(middle_band_bonus, 0.0)

    # Favor nearer-term markets, but don't overreward ultra-close expiring noise
    if hours_to_close <= 24:
        recency_score = 3.0
    elif hours_to_close <= 24 * 7:
        recency_score = 2.0
    elif hours_to_close <= 24 * 30:
        recency_score = 1.0
    else:
        recency_score = 0.25

    score = (
        volume * 0.00001
        + open_interest * 0.00002
        + middle_band_bonus * 2.5
        + recency_score
    )

    return score


def score_signal_for_post(signal: dict, market_lookup: dict[str, dict]) -> float:
    """
    Score a detected move for whether it deserves a post.
    Strongly favor move magnitude first, then use liquidity as a tie-breaker.
    """
    abs_change = _safe_float(signal.get("abs_price_change"))
    market = market_lookup.get(signal.get("ticker", ""), {})
    volume = _safe_float(market.get("volume"))
    open_interest = _safe_float(market.get("open_interest"))

    signal_type = signal.get("signal_type", "price_move")

    threshold_bonus = 0.0
    if signal_type != "price_move":
        threshold_bonus = 3.0

    score = (
        abs_change * 1000.0
        + volume * 0.000002
        + open_interest * 0.000005
        + threshold_bonus
    )
    return score


def select_best_snapshot_market(markets: list[dict]) -> dict | None:
    if not markets:
        return None

    now = datetime.now(timezone.utc)
    ranked = sorted(
        markets,
        key=lambda m: score_market_for_snapshot(m, now),
        reverse=True,
    )
    return ranked[0]


def select_best_signal(signals: list[dict], market_lookup: dict[str, dict]) -> dict | None:
    if not signals:
        return None

    ranked = sorted(
        signals,
        key=lambda s: score_signal_for_post(s, market_lookup),
        reverse=True,
    )
    return ranked[0]


def select_diverse_top_markets(markets: list[dict], limit: int = 5) -> list[dict]:
    """
    Pick a diversified set of markets instead of five near-duplicates.
    Uses one-per-title-prefix / one-per-series bias.
    """
    if not markets:
        return []

    now = datetime.now(timezone.utc)

    ranked = sorted(
        markets,
        key=lambda m: score_market_for_snapshot(m, now),
        reverse=True,
    )

    selected: list[dict] = []
    seen_series: set[str] = set()
    seen_title_roots: set[str] = set()

    for market in ranked:
        series = str(market.get("series_ticker") or "")
        title = str(market.get("title") or "").lower()

        title_root = title[:45]

        # Soft diversity filter
        if series in seen_series:
            continue
        if title_root in seen_title_roots:
            continue

        selected.append(market)
        seen_series.add(series)
        seen_title_roots.add(title_root)

        if len(selected) >= limit:
            break

    # If diversity filter was too strict, backfill
    if len(selected) < limit:
        selected_tickers = {m.get("ticker") for m in selected}
        for market in ranked:
            if market.get("ticker") in selected_tickers:
                continue
            selected.append(market)
            if len(selected) >= limit:
                break

    return selected[:limit]

