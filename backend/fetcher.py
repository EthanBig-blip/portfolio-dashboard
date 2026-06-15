"""
Unified market data fetcher.
  - Crypto  → CoinGecko (gratuit, sans clé)
  - Actions / Indices → yfinance avec session curl_cffi (bypass cookies Yahoo 2024)
  - Fallback synthétique si tout échoue
"""
import json
import urllib.request
from datetime import datetime, timedelta, date
from . import cache

CACHE_TTL = 300

COINGECKO_IDS = {
    "BTC-USD": "bitcoin",      "ETH-USD": "ethereum",     "SOL-USD": "solana",
    "BNB-USD": "binancecoin",  "XRP-USD": "ripple",       "ADA-USD": "cardano",
    "DOGE-USD": "dogecoin",    "AVAX-USD": "avalanche-2", "MATIC-USD": "matic-network",
    "DOT-USD": "polkadot",     "LINK-USD": "chainlink",   "LTC-USD": "litecoin",
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "BNB": "binancecoin", "XRP": "ripple", "ADA": "cardano",
    "DOGE": "dogecoin", "AVAX": "avalanche-2",
}

PERIOD_TO_DAYS = {
    "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
    "1y": 365, "2y": 730, "5y": 1825, "max": 1825,
}

CG_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Session curl_cffi réutilisée (imite Chrome, gère les cookies Yahoo)
_yf_session = None

def _get_yf_session():
    global _yf_session
    if _yf_session is None:
        try:
            from curl_cffi import requests as cffi_requests
            _yf_session = cffi_requests.Session(impersonate="chrome")
            print("[fetcher] curl_cffi session ready")
        except ImportError:
            print("[fetcher] curl_cffi not installed, using default yfinance session")
    return _yf_session


def _is_crypto(symbol: str) -> bool:
    return symbol.upper() in COINGECKO_IDS


def _cg_get(url: str, timeout: int = 8):
    try:
        req = urllib.request.Request(url, headers=CG_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[fetcher] CoinGecko error: {e}")
        return None


# ─── PRIX ACTUEL ───────────────────────────────────────────

def get_price(symbol: str) -> float | None:
    key = f"price:{symbol}"
    cached = cache.get(key, CACHE_TTL)
    if cached is not None:
        return cached

    price = None

    if _is_crypto(symbol):
        cg_id = COINGECKO_IDS[symbol.upper()]
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
        data = _cg_get(url)
        if data and cg_id in data:
            price = data[cg_id]["usd"]
    else:
        try:
            import yfinance as yf
            sess = _get_yf_session()
            t = yf.Ticker(symbol, session=sess) if sess else yf.Ticker(symbol)
            price = t.fast_info["lastPrice"]
        except Exception as e:
            print(f"[fetcher] yfinance price error for {symbol}: {e}")

    if price is not None:
        cache.set(key, float(price))
    return float(price) if price is not None else None


# ─── SÉRIE HISTORIQUE ────────────────────────────────────────

def get_series(symbol: str, period: str = "1y") -> list[dict]:
    key = f"series:{symbol}:{period}"
    cached = cache.get(key, CACHE_TTL)
    if cached:
        return cached

    days = PERIOD_TO_DAYS.get(period, 365)
    data = None

    if _is_crypto(symbol):
        cg_id = COINGECKO_IDS[symbol.upper()]
        url = (
            f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
            f"?vs_currency=usd&days={days}&interval=daily"
        )
        raw = _cg_get(url)
        if raw and "prices" in raw and raw["prices"]:
            data = [
                {
                    "date": str(datetime.utcfromtimestamp(p[0] / 1000).date()),
                    "close": round(p[1], 4)
                }
                for p in raw["prices"]
            ]
    else:
        try:
            import yfinance as yf
            import pandas as pd
            sess = _get_yf_session()
            end = datetime.now()
            start = end - timedelta(days=days)
            df = yf.download(
                symbol,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                interval="1d",
                progress=False,
                auto_adjust=True,
                threads=False,
                session=sess,
            )
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                col = next((c for c in df.columns if str(c).lower() == "close"), None)
                if col:
                    df = df[[col]].dropna()
                    data = [
                        {"date": str(ts.date()), "close": round(float(v), 4)}
                        for ts, v in df[col].items()
                    ]
        except Exception as e:
            print(f"[fetcher] yfinance history error for {symbol}: {e}")

    # Fallback synthétique
    if not data:
        price = get_price(symbol)
        if price:
            today = date.today()
            step = max(1, days // 200)
            data = [
                {"date": str(today - timedelta(days=days - i)), "close": round(price, 4)}
                for i in range(0, days + 1, step)
            ]
            print(f"[fetcher] Synthetic fallback for {symbol}")

    if data:
        cache.set(key, data)
    return data or []
