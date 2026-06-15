"""Live market data via yfinance + Livret A taux fixe."""
import os
import yfinance as yf
from datetime import datetime, timedelta, date
from . import cache

CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

BENCHMARKS = {
    "sp500":     {"name": "S&P 500",   "symbol": "^GSPC", "color": "#5591c7", "icon": "🇺🇸"},
    "nasdaq100": {"name": "Nasdaq 100", "symbol": "^NDX",  "color": "#9b72cf", "icon": "💻"},
    "msci":      {"name": "MSCI World", "symbol": "URTH",  "color": "#e8af34", "icon": "🌍"},
    "cac40":     {"name": "CAC 40",     "symbol": "^FCHI", "color": "#e06c75", "icon": "🇫🇷"},
}

LIVRET_A_RATE = 0.025

PERIOD_TO_DAYS = {
    "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
    "1y": 365, "2y": 730, "5y": 1825, "max": 3650,
}


def _days_from_period(period: str) -> int:
    return PERIOD_TO_DAYS.get(period, 730)


def fetch_series(ticker: str, period: str = "2y", interval: str = "1d") -> list[dict]:
    key = f"series:{ticker}:{period}:{interval}"
    cached = cache.get(key, CACHE_TTL)
    if cached:
        return cached

    # --- Try yf.download() first (more reliable than .history()) ---
    try:
        import pandas as pd
        days = _days_from_period(period)
        end = datetime.now()
        start = end - timedelta(days=days)
        df = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval=interval,
            progress=False,
            auto_adjust=True,
            threads=False,
        )
        if df is not None and not df.empty:
            # Handle MultiIndex columns (yfinance >= 0.2.x)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            close_col = next((c for c in df.columns if str(c).lower() == "close"), None)
            if close_col:
                df = df[[close_col]].dropna()
                data = [
                    {"date": str(ts.date()), "close": round(float(row[close_col]), 4)}
                    for ts, row in df.iterrows()
                ]
                if data:
                    cache.set(key, data)
                    return data
    except Exception as e:
        print(f"[market] download() failed for {ticker}: {e}")

    # --- Fallback: .history() ---
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval, auto_adjust=True)
        if not hist.empty:
            data = [
                {"date": str(ts.date()), "close": round(float(row["Close"]), 4)}
                for ts, row in hist.iterrows()
            ]
            cache.set(key, data)
            return data
    except Exception as e:
        print(f"[market] history() failed for {ticker}: {e}")

    # --- Last resort: build synthetic series from fast_info ---
    try:
        t = yf.Ticker(ticker)
        last_price = t.fast_info["lastPrice"]
        if last_price:
            days = _days_from_period(period)
            today = date.today()
            data = [
                {
                    "date": str(today - timedelta(days=days - i)),
                    "close": round(float(last_price), 4)
                }
                for i in range(0, days + 1, max(1, days // 365))
            ]
            print(f"[market] Using fast_info fallback for {ticker}")
            return data
    except Exception as e:
        print(f"[market] fast_info fallback failed for {ticker}: {e}")

    return []


def fetch_livret_a(days: int = 730) -> list[dict]:
    base = 100.0
    result = []
    daily_rate = LIVRET_A_RATE / 365
    for i in range(days, -1, -1):
        d = (datetime.now() - timedelta(days=i)).date()
        result.append({"date": str(d), "close": round(base, 4)})
        base *= (1 + daily_rate)
    return result


def get_benchmark_data(bench_id: str, period: str = "2y") -> dict:
    if bench_id == "livreta":
        series = fetch_livret_a(730)
        return {
            "id": "livreta", "name": "Livret A", "symbol": "LIVRET-A",
            "color": "#98c379", "icon": "🏦", "rate": LIVRET_A_RATE,
            "change_pct": LIVRET_A_RATE, "market_condition": "neutral",
            "series": series,
        }
    if bench_id not in BENCHMARKS:
        return {}
    meta = BENCHMARKS[bench_id]
    series = fetch_series(meta["symbol"], period=period)
    if not series:
        return {**meta, "id": bench_id, "error": "no data", "series": []}
    last = series[-1]["close"]
    first = series[0]["close"]
    high_52w = max(d["close"] for d in series[-252:]) if len(series) >= 252 else last
    vs_high = (last - high_52w) / high_52w if high_52w else 0
    condition = "bull" if vs_high > -0.05 else ("bear" if vs_high < -0.20 else "neutral")
    return {
        "id": bench_id, **meta,
        "last": round(last, 2),
        "change_pct": round((last - first) / first, 6),
        "change_abs": round(last - first, 2),
        "vs_52w_high": round(vs_high, 4),
        "market_condition": condition,
        "series": series,
    }


def get_all_benchmarks(period: str = "2y") -> list[dict]:
    ids = list(BENCHMARKS.keys()) + ["livreta"]
    return [get_benchmark_data(bid, period) for bid in ids]
