from __future__ import annotations

from datetime import datetime, timezone

from data_sources.kalshi_client import KalshiClient
from storage.db import init_db, insert_market_snapshots


def main() -> None:
    init_db()

    client = KalshiClient()
    markets = client.fetch_markets(limit=25, max_pages=2)
    simplified = [client.simplify_market(m) for m in markets]

    captured_at = datetime.now(timezone.utc).isoformat()
    inserted = insert_market_snapshots(captured_at, simplified)

    print(f"\nCaptured snapshot time: {captured_at}")
    print(f"Inserted {inserted} market snapshots into SQLite database.")


if __name__ == "__main__":
    main()
