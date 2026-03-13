from __future__ import annotations

from datetime import datetime, timezone

from content.post_builder import (
    build_market_snapshot_post,
    build_top_markets_post,
)
from data_sources.kalshi_client import KalshiClient
from signals.snapshot_compare import build_all_changes, compare_snapshots
from storage.db import (
    get_distinct_capture_times,
    get_snapshots_for_capture_time,
    init_db,
    insert_market_snapshots,
)


def main() -> None:
    init_db()

    client = KalshiClient()
    target_markets = client.fetch_target_markets()

    if not target_markets:
        print("\nNo target markets found from selected series.")
        return

    priced_markets = [
        market
        for market in target_markets
        if any(market.get(field) is not None for field in ("last_price", "yes_bid", "yes_ask"))
    ]

    print(f"\nFetched {len(target_markets)} target markets total.")
    print(f"Usable priced markets: {len(priced_markets)}")

    captured_at = datetime.now(timezone.utc).isoformat()
    inserted = insert_market_snapshots(captured_at, priced_markets)

    print(f"\nCaptured snapshot time: {captured_at}")
    print(f"Inserted {inserted} target market snapshots into SQLite database.")

    # ------------------------------------------------
    # Example generated single-market post
    # ------------------------------------------------
    if priced_markets:
        example_market = priced_markets[0]

        single_post = build_market_snapshot_post(
            example_market,
            captured_at,
        )

        print("\nExample generated single-market post:\n")
        print(single_post)

        # Sort markets by highest current probability for a cleaner leaderboard
        def sort_price(market: dict) -> float:
            for field in ("last_price", "yes_bid", "yes_ask"):
                value = market.get(field)
                if value is not None:
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        return 0.0
            return 0.0

        ranked_markets = sorted(
            priced_markets,
            key=sort_price,
            reverse=True,
        )

        top_post = build_top_markets_post(
            ranked_markets,
            captured_at,
            limit=5,
        )

        print("\nExample generated top-markets post:\n")
        print(top_post)

    capture_times = get_distinct_capture_times(limit=2)
    if len(capture_times) < 2:
        print("\nNot enough snapshots yet to compare.")
        return

    current_capture = capture_times[0]
    previous_capture = capture_times[1]

    current_rows = get_snapshots_for_capture_time(current_capture)
    previous_rows = get_snapshots_for_capture_time(previous_capture)

    all_changes = build_all_changes(
        previous_rows=previous_rows,
        current_rows=current_rows,
    )

    signals = compare_snapshots(
        previous_rows=previous_rows,
        current_rows=current_rows,
        min_price_change=0.01,
    )

    print(f"\nCompared snapshots:")
    print(f"Previous: {previous_capture}")
    print(f"Current:  {current_capture}")
    print(f"Shared priced markets: {len(all_changes)}")
    print(f"Detected {len(signals)} signals.\n")

    print("Top 15 raw changes:")
    for change in all_changes[:15]:
        print(
            f"{change['signal_type']} | "
            f"{change['ticker']} | "
            f"{change['previous_price']} -> {change['current_price']} "
            f"({change['price_change']:+.6f})"
        )

    if signals:
        print("\nSignals over threshold:")
        for signal in signals[:10]:
            print(
                f"{signal['signal_type']} | "
                f"{signal['ticker']} | "
                f"{signal['previous_price']} -> {signal['current_price']} "
                f"({signal['price_change']:+.6f})"
            )


if __name__ == "__main__":
    main()
