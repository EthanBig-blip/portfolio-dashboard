"""
Market data layer — uses the unified fetcher (CoinGecko + Yahoo direct HTTP).
No yfinance dependency for live/history data.
"""
from datetime import datetime, timedelta
from . import cache
from .fetcher import get_series, get_price  # noqa: F401

BENCHMARKS = {
    "sp500":     {"name": "S&P 500",    "symbol": "^GSPC", "color": "#5591c7", "icon": "🇺🇸"},
    "nasdaq100": {"name": "Nasdaq 100", "symbol": "^NDX",  "color": "#9b72cf", "icon": "💻"},
    "msci":      {"name": "MSCI World", "symbol": "URTH",  "color": "#e8af34", "icon": "🌍"},
    "cac40":     {"name": "CAC 40",     "symbol": "^FCHI", "color": "#e06c75", "icon": "🇫🇷"},
}

LIVRET_A_RATE = 0.025


def fetch_series(ticker: str, period: str = "1y", interval: str = "1d") -> list[dict]:
    return get_series(ticker, period)


def fetch_livret_a(days: int = 365) -> list[dict]:
    base = 100.0
    result = []
    daily_rate = LIVRET_A_RATE / 365
    for i in range(days, -1, -1):
        d = (datetime.now() - timedelta(days=i)).date()
        result.append({"date": str(d), "close": round(base, 4)})
        base *= (1 + daily_rate)
    return result


def get_benchmark_data(bench_id: str, period: str = "1y") -> dict:
    if bench_id == "livreta":
        series = fetch_livret_a(365)
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


def get_all_benchmarks(period: str = "1y") -> list[dict]:
    ids = list(BENCHMARKS.keys()) + ["livreta"]
    return [get_benchmark_data(bid, period) for bid in ids]
