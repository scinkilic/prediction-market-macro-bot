from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from config import WATCHLIST_KEYWORDS


def _tokenize(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _has_usable_price(market: Dict[str, Any]) -> bool:
    return any(
        market.get(field) is not None
        for field in ("last_price", "yes_bid", "yes_ask")
    )


def filter_relevant_markets(markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    keyword_tokens = {kw.lower() for kw in WATCHLIST_KEYWORDS}

    for market in markets:
        title = market.get("title") or ""
        subtitle = market.get("subtitle") or ""
        text = f"{title} {subtitle}"
        tokens = _tokenize(text)

        if tokens & keyword_tokens and _has_usable_price(market):
            filtered.append(market)

    return filtered
