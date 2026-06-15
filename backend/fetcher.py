"""
Unified market data fetcher — no yfinance dependency for live/history data.
Sources (in order of priority):
  1. CoinGecko (crypto) — free, no key
  2. Direct Yahoo Finance v8 JSON (actions/indices) — raw HTTP, no yfinance
  3. Synthetic flat series from last known price (last resort)
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, date
from . import cache

CACHE_TTL = 300

# CoinGecko IDs for common crypto tickers
COINGECKO_IDS = {
    "BTC-USD": "bitcoin", "ETH-USD": "ethereum", "SOL-USD": "solana",
    "BNB-USD": "binancecoin", "XRP-USD": "ripple", "ADA-USD": "cardano",
    "DOGE-USD": "dogecoin", "AVAX-USD": "avalanche-2", "MATIC-USD": "matic-network",
    "DOT-USD": "polkadot", "LINK-USD": "chainlink", "LTC-USD": "litecoin",
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
}

PERIOD_TO_DAYS = {
    "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
    "1y": 365, "2y": 730, "5y": 1825, "max": 1825,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


def _get(url: str, timeout: int = 8) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[fetcher] HTTP error {url[:60]}: {e}")
        return None


# ─── PRIX ACTUEL ────────────────────────────────────────────────

def get_price(symbol: str) -> float | None:
    key = f"price:{symbol}"
    cached = cache.get(key, CACHE_TTL)
    if cached is not None:
        return cached

    price = None

    # 1. CoinGecko pour les cryptos
    cg_id = COINGECKO_IDS.get(symbol.upper())
    if cg_id:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
        data = _get(url)
        if data and cg_id in data:
            price = data[cg_id]["usd"]

    # 2. Yahoo Finance v8 direct HTTP
    if price is None:
        ticker = symbol.replace("-USD", "-USD")  # keep as-is
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval=1d&range=1d"
        data = _get(url)
        try:
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        except Exception:
            pass

    if price is not None:
        cache.set(key, float(price))
    return float(price) if price is not None else None


# ─── SÉRIE HISTORIQUE ────────────────────────────────────────────

def get_series(symbol: str, period: str = "1y") -> list[dict]:
    key = f"series:{symbol}:{period}"
    cached = cache.get(key, CACHE_TTL)
    if cached:
        return cached

    days = PERIOD_TO_DAYS.get(period, 365)
    data = None

    # 1. CoinGecko market_chart pour les cryptos
    cg_id = COINGECKO_IDS.get(symbol.upper())
    if cg_id:
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
        raw = _get(url)
        if raw and "prices" in raw and raw["prices"]:
            data = [
                {
                    "date": str(datetime.utcfromtimestamp(p[0] / 1000).date()),
                    "close": round(p[1], 4)
                }
                for p in raw["prices"]
            ]

    # 2. Yahoo Finance v8 direct HTTP
    if not data:
        end = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=days)).timestamp())
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
            f"?interval=1d&period1={start}&period2={end}"
        )
        raw = _get(url)
        try:
            result = raw["chart"]["result"][0]
            timestamps = result["timestamp"]
            closes = result["indicators"]["quote"][0]["close"]
            data = [
                {
                    "date": str(datetime.utcfromtimestamp(ts).date()),
                    "close": round(float(c), 4)
                }
                for ts, c in zip(timestamps, closes) if c is not None
            ]
        except Exception:
            pass

    # 3. Fallback synthétique depuis prix actuel
    if not data:
        price = get_price(symbol)
        if price:
            today = date.today()
            data = [
                {"date": str(today - timedelta(days=days - i)), "close": round(price, 4)}
                for i in range(0, days + 1, max(1, days // 200))
            ]
            print(f"[fetcher] Synthetic fallback for {symbol}")

    if data:
        cache.set(key, data)
    return data or []
