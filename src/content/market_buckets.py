from __future__ import annotations


MACRO_KEYWORDS = {
    "fed",
    "rate",
    "rates",
    "cut",
    "cuts",
    "hike",
    "hikes",
    "inflation",
    "cpi",
    "gdp",
    "recession",
    "jobs",
    "unemployment",
    "payrolls",
}

POLITICAL_KEYWORDS = {
    "president",
    "presidential",
    "nominee",
    "primary",
    "election",
    "congress",
    "shutdown",
    "trump",
    "biden",
    "newsom",
    "impeach",
    "impeachment",
    "democratic",
    "republican",
    "mayor",
}


def classify_market_bucket(market: dict) -> str:
    title = str(market.get("title") or "").lower()
    series_title = str(market.get("series_title") or "").lower()
    category = str(market.get("series_category") or "").lower()

    text = f"{title} {series_title} {category}"

    if any(keyword in text for keyword in MACRO_KEYWORDS):
        return "macro"

    if any(keyword in text for keyword in POLITICAL_KEYWORDS):
        return "political"

    if "economics" in category:
        return "macro"

    if "politics" in category:
        return "political"

    return "other"


def split_markets_by_bucket(markets: list[dict]) -> dict[str, list[dict]]:
    buckets = {
        "macro": [],
        "political": [],
        "other": [],
    }

    for market in markets:
        bucket = classify_market_bucket(market)
        buckets[bucket].append(market)

    return buckets

