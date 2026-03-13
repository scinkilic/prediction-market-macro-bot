from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests

from config import (
    BACKOFF_SECONDS,
    BASE_URL,
    DEFAULT_TIMEOUT,
    MARKETS_PER_SERIES_LIMIT,
    MAX_RETRIES,
    MAX_SERIES_TO_TRACK,
    REQUEST_SLEEP_SECONDS,
    SERIES_CATEGORY_ALLOWLIST,
    SERIES_KEYWORD_ALLOWLIST,
)

SERIES_ENDPOINT = f"{BASE_URL}/series"
MARKETS_ENDPOINT = f"{BASE_URL}/markets"
RAW_DATA_DIR = Path("data/raw")


class KalshiClient:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()

    def _get_with_backoff(self, url: str, params: Dict[str, Any]) -> requests.Response:
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)

                if response.status_code == 429:
                    sleep_s = BACKOFF_SECONDS * attempt
                    print(
                        f"Rate limited (429) for {url}. "
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
                    f"Request failed for {url} on attempt {attempt}/{MAX_RETRIES}: {exc}. "
                    f"Sleeping {sleep_s:.1f}s..."
                )
                time.sleep(sleep_s)

        raise RuntimeError(f"Failed request for {url}. Last error: {last_error}")

    def fetch_series_list(self) -> List[Dict[str, Any]]:
        response = self._get_with_backoff(
            SERIES_ENDPOINT,
            {
                "include_volume": "true",
            },
        )
        payload = response.json()
        return payload.get("series", [])

    @staticmethod
    def _series_matches_theme(series: Dict[str, Any]) -> bool:
        category = (series.get("category") or "").strip().lower()
        title = (series.get("title") or "").lower()
        tags = [str(tag).lower() for tag in (series.get("tags") or [])]

        if category in SERIES_CATEGORY_ALLOWLIST:
            return True

        combined = " ".join([title] + tags)
        return any(keyword in combined for keyword in SERIES_KEYWORD_ALLOWLIST)

    def select_target_series(self, series_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        matched = [s for s in series_list if self._series_matches_theme(s)]

        matched.sort(
            key=lambda s: float(s.get("volume_fp") or 0.0),
            reverse=True,
        )

        return matched[:MAX_SERIES_TO_TRACK]

    def fetch_markets_for_series(
        self,
        series_ticker: str,
        status: str = "open",
        limit: int = MARKETS_PER_SERIES_LIMIT,
    ) -> List[Dict[str, Any]]:
        response = self._get_with_backoff(
            MARKETS_ENDPOINT,
            {
                "series_ticker": series_ticker,
                "status": status,
                "limit": limit,
                "mve_filter": "exclude",
            },
        )
        payload = response.json()
        return payload.get("markets", [])

    def fetch_target_markets(self) -> List[Dict[str, Any]]:
        all_series = self.fetch_series_list()
        target_series = self.select_target_series(all_series)

        print(f"Fetched {len(all_series)} total series.")
        print(f"Selected {len(target_series)} target series.\n")

        for s in target_series:
            print(
                {
                    "ticker": s.get("ticker"),
                    "title": s.get("title"),
                    "category": s.get("category"),
                    "volume_fp": s.get("volume_fp"),
                    "tags": s.get("tags"),
                }
            )

        deduped: Dict[str, Dict[str, Any]] = {}

        for series in target_series:
            series_ticker = series.get("ticker")
            if not series_ticker:
                continue

            print(f"\nFetching markets for series {series_ticker}...")
            markets = self.fetch_markets_for_series(series_ticker=series_ticker)

            print(f"Found {len(markets)} markets in series {series_ticker}.")

            for market in markets:
                simplified = self.simplify_market(market)
                simplified["series_ticker"] = series_ticker
                simplified["series_title"] = series.get("title")
                simplified["series_category"] = series.get("category")
                deduped[simplified["ticker"]] = simplified

            time.sleep(REQUEST_SLEEP_SECONDS)

        return list(deduped.values())

    @staticmethod
    def simplify_market(market: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ticker": market.get("ticker"),
            "title": market.get("title"),
            "subtitle": market.get("subtitle"),
            "status": market.get("status"),
            "event_ticker": market.get("event_ticker"),
            "market_type": market.get("market_type"),

            # New fixed-point price fields
            "yes_bid": market.get("yes_bid_dollars"),
            "yes_ask": market.get("yes_ask_dollars"),
            "last_price": market.get("last_price_dollars"),

            # New fixed-point size / volume fields
            "volume": market.get("volume_fp"),
            "open_interest": market.get("open_interest_fp"),

            # Extra useful fields
            "yes_bid_size": market.get("yes_bid_size_fp"),
            "yes_ask_size": market.get("yes_ask_size_fp"),
            "liquidity": market.get("liquidity_dollars"),
            "previous_price": market.get("previous_price_dollars"),
            "notional_value": market.get("notional_value_dollars"),

            "close_time": market.get("close_time"),
            "expiration_time": market.get("expiration_time"),
            "result": market.get("result"),
            "rules_primary": market.get("rules_primary"),
        }

    @staticmethod
    def save_raw_markets(markets: List[Dict[str, Any]]) -> Path:
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = RAW_DATA_DIR / f"kalshi_target_markets_{timestamp}.json"

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(markets, f, indent=2)

        return output_path


def main() -> None:
    client = KalshiClient()
    markets = client.fetch_target_markets()

    print(f"\nFetched {len(markets)} total deduped target markets.\n")

    if not markets:
        print("No markets found.")
        return

    print("First raw simplified market:\n")
    print(json.dumps(markets[0], indent=2))

    path = client.save_raw_markets(markets)
    print(f"\nSaved raw target markets to: {path}")

if __name__ == "__main__":
    main()
