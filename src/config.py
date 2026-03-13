SERIES_CATEGORY_ALLOWLIST = {
    "economics",
    "politics",
    "world",
    "technology",
    "climate",
}

SERIES_KEYWORD_ALLOWLIST = {
    "fed",
    "fomc",
    "rate",
    "rates",
    "cpi",
    "inflation",
    "gdp",
    "jobs",
    "jobless",
    "recession",
    "election",
    "president",
    "congress",
    "trump",
    "biden",
    "china",
    "russia",
    "ukraine",
    "israel",
    "iran",
    "oil",
    "tariff",
    "war",
}

MAX_SERIES_TO_TRACK = 12
MARKETS_PER_SERIES_LIMIT = 100
REQUEST_SLEEP_SECONDS = 1.25
MAX_RETRIES = 5
BACKOFF_SECONDS = 3.0
DEFAULT_TIMEOUT = 10
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
