from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
MARKETS_ENDPOINT = f"{BASE_URL}/markets"
DEFAULT_TIMEOUT = 10
RAW_DATA_DIR = Path("data/raw")

# Keep this conservative, especially while your trading bot is also running
DEFAULT_PAGE_LIMIT = 50
MAX_PAGES = 3
REQUEST_SLEEP_SECONDS = 1.5
MAX_RETRIES = 5
BACKOFF_SECONDS = 3.0


class KalshiClient:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()

    def _get_with_backoff(self, params: Dict[str, Any]) -> requests.Response:
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    MARKETS_ENDPOINT,
                    params=params,
                    timeout=self.timeout,
                )

                if response.status_code == 429:
                    sleep_s = BACKOFF_SECONDS * attempt
                    print(
                        f"Rate limited by Kalshi (429). "
                        f"Sleeping {sleep_s:.1f}s before retry {attempt}/{MAX_RETRIES}..."
                    )
                    time.sleep(sleep_s)
                    continue

                response.raise_for_status()
                return response

            except requests.RequestException as exc:
                last_error = exc
                sleep_s = BACKOFF_SECONDS * attempt
                print(
                    f"Request failed on attempt {attempt}/{MAX_RETRIES}: {exc}. "
                    f"Sleeping {sleep_s:.1f}s..."
                )
                time.sleep(sleep_s)

        raise RuntimeError(f"Failed to fetch markets after retries. Last error: {last_error}")

    def fetch_markets(
        self,
        limit: int = DEFAULT_PAGE_LIMIT,
        status: Optional[str] = "open",
        event_ticker: Optional[str] = None,
        max_pages: int = MAX_PAGES,
    ) -> List[Dict[str, Any]]:
        all_markets: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        page_count = 0

        while True:
            page_count += 1
            if page_count > max_pages:
                print(f"Reached max_pages={max_pages}, stopping pagination.")
                break

            params: Dict[str, Any] = {"limit": limit}
            if cursor:
                params["cursor"] = cursor
            if status:
                params["status"] = status
            if event_ticker:
                params["event_ticker"] = event_ticker

            print(f"Fetching page {page_count} with params={params}")
            response = self._get_with_backoff(params)
            payload = response.json()

            markets = payload.get("markets", [])
            all_markets.extend(markets)

            print(
                f"Fetched {len(markets)} markets on page {page_count}. "
                f"Running total: {len(all_markets)}"
            )

            cursor = payload.get("cursor")
            if not cursor:
                print("No further cursor returned. Pagination complete.")
                break

            time.sleep(REQUEST_SLEEP_SECONDS)

        return all_markets

    @staticmethod
    def simplify_market(market: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ticker": market.get("ticker"),
            "title": market.get("title"),
            "subtitle": market.get("subtitle"),
            "status": market.get("status"),
            "event_ticker": market.get("event_ticker"),
            "market_type": market.get("market_type"),
            "yes_bid": market.get("yes_bid"),
            "yes_ask": market.get("yes_ask"),
            "last_price": market.get("last_price"),
            "volume": market.get("volume"),
            "open_interest": market.get("open_interest"),
            "close_time": market.get("close_time"),
            "expiration_time": market.get("expiration_time"),
            "result": market.get("result"),
            "rules_primary": market.get("rules_primary"),
        }

    @staticmethod
    def save_raw_markets(markets: List[Dict[str, Any]]) -> Path:
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = RAW_DATA_DIR / f"kalshi_markets_{timestamp}.json"

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(markets, f, indent=2)

        return output_path


def main() -> None:
    client = KalshiClient()

    # Keep this small while your trading bot is live
    markets = client.fetch_markets(limit=25, max_pages=2)

    print(f"\nFetched {len(markets)} total markets.")

    simplified = [client.simplify_market(m) for m in markets[:10]]
    print("\nFirst 10 simplified markets:\n")
    print(json.dumps(simplified, indent=2))

    output_path = client.save_raw_markets(markets)
    print(f"\nSaved raw markets to: {output_path}")


if __name__ == "__main__":
    main()
