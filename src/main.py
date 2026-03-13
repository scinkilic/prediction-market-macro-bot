from __future__ import annotations

from datetime import datetime, timezone

from content.market_buckets import split_markets_by_bucket

from content.brief_selector import select_best_brief_market

from content.event_deduper import select_best_market_per_event

from content.content_selector import (
    select_best_signal,
    select_best_snapshot_market,
    select_diverse_top_markets,
)
from content.post_builder import (
    build_bucket_snapshot_post,
    build_daily_brief_post,
    build_market_snapshot_post,
    build_signal_post,
    build_top_markets_post,
    build_top_movers_post,
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

    market_lookup = {m.get("ticker"): m for m in priced_markets if m.get("ticker")}

    # Best current-state market
    best_snapshot_market = select_best_snapshot_market(priced_markets)
    if best_snapshot_market:
        single_post = build_market_snapshot_post(best_snapshot_market, captured_at)
        print("\nBest single-market post:\n")
        print(single_post)

    # Best diversified top snapshot
    diverse_top_markets = select_diverse_top_markets(priced_markets, limit=5)
    if diverse_top_markets:
        top_post = build_top_markets_post(diverse_top_markets, captured_at, limit=5)
        print("\nBest diversified top-markets post:\n")
        print(top_post)

    # Bucketed snapshot posts
    buckets = split_markets_by_bucket(priced_markets)

    macro_candidates = select_best_market_per_event(buckets["macro"])

    # Political markets should NOT be deduplicated by event
    political_candidates = buckets["political"]

    macro_markets = select_diverse_top_markets(macro_candidates, limit=5)
    political_markets = select_diverse_top_markets(political_candidates, limit=5)

    if macro_markets:
        macro_post = build_bucket_snapshot_post(
            macro_markets,
            captured_at,
            bucket_name="macro",
            limit=5,
        )
        print("\nMacro snapshot post:\n")
        print(macro_post)

    if political_markets:
        political_post = build_bucket_snapshot_post(
            political_markets,
            captured_at,
            bucket_name="political",
            limit=5,
        )
        print("\nPolitical snapshot post:\n")
        print(political_post)


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
        min_price_change=0.009,
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

    best_macro_brief = select_best_brief_market(buckets["macro"])
    best_political_brief = select_best_brief_market(buckets["political"])


    daily_brief = build_daily_brief_post(
        macro_markets=[best_macro_brief] if best_macro_brief else [],
        political_markets=[best_political_brief] if best_political_brief else [],
        signals=signals,
        captured_at=captured_at,
    )

    print("\nDaily brief post:\n")
    print(daily_brief)


    if signals:
        print("\nSignals over threshold:")
        for signal in signals[:10]:
            print(
                f"{signal['signal_type']} | "
                f"{signal['ticker']} | "
                f"{signal['previous_price']} -> {signal['current_price']} "
                f"({signal['price_change']:+.6f})"
            )

        best_signal = select_best_signal(signals, market_lookup)
        if best_signal:
            signal_post = build_signal_post(best_signal, captured_at)
            print("\nBest signal post:\n")
            print(signal_post)

        top_movers_post = build_top_movers_post(signals, captured_at, limit=5)
        print("\nTop movers post:\n")
        print(top_movers_post)


if __name__ == "__main__":
    main()

