from __future__ import annotations

from typing import Any, Dict, List


def _index_by_ticker(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        ticker = row.get("ticker")
        if ticker:
            indexed[ticker] = row
    return indexed


def _safe_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _effective_price(row: Dict[str, Any]) -> float | None:
    last_price = _safe_number(row.get("last_price"))
    if last_price is not None:
        return last_price

    yes_bid = _safe_number(row.get("yes_bid"))
    yes_ask = _safe_number(row.get("yes_ask"))

    if yes_bid is not None and yes_ask is not None:
        return (yes_bid + yes_ask) / 2.0
    if yes_bid is not None:
        return yes_bid
    if yes_ask is not None:
        return yes_ask

    return None


def build_all_changes(
    previous_rows: List[Dict[str, Any]],
    current_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    previous_by_ticker = _index_by_ticker(previous_rows)
    current_by_ticker = _index_by_ticker(current_rows)

    all_changes: List[Dict[str, Any]] = []
    shared_tickers = set(previous_by_ticker.keys()) & set(current_by_ticker.keys())

    for ticker in shared_tickers:
        prev_row = previous_by_ticker[ticker]
        curr_row = current_by_ticker[ticker]

        prev_price = _effective_price(prev_row)
        curr_price = _effective_price(curr_row)

        if prev_price is None or curr_price is None:
            continue

        price_change = curr_price - prev_price
        abs_change = abs(price_change)

        signal_type = "price_move"
        if prev_price < 0.50 <= curr_price:
            signal_type = "crossed_above_50"
        elif prev_price > 0.50 >= curr_price:
            signal_type = "crossed_below_50"
        elif prev_price < 0.25 <= curr_price:
            signal_type = "crossed_above_25"
        elif prev_price > 0.75 >= curr_price:
            signal_type = "crossed_below_75"

        all_changes.append(
            {
                "signal_type": signal_type,
                "ticker": ticker,
                "title": curr_row.get("title"),
                "previous_price": prev_price,
                "current_price": curr_price,
                "price_change": price_change,
                "abs_price_change": abs_change,
                "previous_capture": prev_row.get("captured_at"),
                "current_capture": curr_row.get("captured_at"),
            }
        )

    all_changes.sort(key=lambda x: x["abs_price_change"], reverse=True)
    return all_changes


def compare_snapshots(
    previous_rows: List[Dict[str, Any]],
    current_rows: List[Dict[str, Any]],
    min_price_change: float = 0.01,
) -> List[Dict[str, Any]]:
    all_changes = build_all_changes(previous_rows, current_rows)
    return [x for x in all_changes if x["abs_price_change"] >= min_price_change]
