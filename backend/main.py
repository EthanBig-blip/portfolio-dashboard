"""
FastAPI application — Portfolio Dashboard backend.
Market data via CoinGecko + direct Yahoo HTTP (no yfinance for history).
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from .fetcher import get_price
from .market import get_all_benchmarks, get_benchmark_data, fetch_series
from .portfolio import load_transactions, compute_holdings, compute_invested_capital, compute_performance
from . import cache
from .routes.quote import router as quote_router
from .routes.assets import router as assets_router

app = FastAPI(title="Portfolio Dashboard", version="2.0.0")

FRONTEND = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")

app.include_router(quote_router)
app.include_router(assets_router)


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(FRONTEND / "index.html"))


@app.get("/portefeuille", include_in_schema=False)
async def portefeuille_page():
    return FileResponse(str(FRONTEND / "portefeuille.html"))


@app.get("/api/health")
async def health():
    return {"status": "OK"}


@app.get("/api/portfolio/summary")
async def portfolio_summary():
    txs = load_transactions()
    holdings = compute_holdings(txs)
    invested = compute_invested_capital(txs)
    total_value = 0.0
    positions = []
    for symbol, qty in holdings.items():
        price = get_price(symbol) or 0.0
        value = qty * price
        total_value += value
        positions.append({
            "symbol": symbol,
            "quantity": round(qty, 8),
            "current_price": round(price, 2),
            "value": round(value, 2)
        })
    pnl = total_value - invested
    pnl_pct = pnl / invested if invested else 0
    return {
        "total_value": round(total_value, 2),
        "invested": round(invested, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 6),
        "positions": sorted(positions, key=lambda x: x["value"], reverse=True),
    }


@app.get("/api/portfolio/history")
async def portfolio_history(period: str = "1y"):
    txs = load_transactions()
    symbols = list(set(t["symbol"] for t in txs if t["type"] in ("BUY", "SELL")))
    histories: dict = {}
    for sym in symbols:
        histories[sym] = fetch_series(sym, period=period)
    if not histories:
        return {"series": [], "invested": [], "performance": {}}
    all_dates = sorted(set(d["date"] for s in histories.values() for d in s))
    price_by_date = {sym: {d["date"]: d["close"] for d in series} for sym, series in histories.items()}
    sorted_txs = sorted(txs, key=lambda x: x["date"])
    holdings: dict = {}
    invested = 0.0
    series_value = []
    series_invested = []
    tx_idx = 0
    for date_str in all_dates:
        while tx_idx < len(sorted_txs) and sorted_txs[tx_idx]["date"] <= date_str:
            t = sorted_txs[tx_idx]
            sym = t["symbol"]
            if t["type"] == "BUY":
                holdings[sym] = holdings.get(sym, 0) + t["quantity"]
                invested += t["quantity"] * t["price"] + t.get("fee", 0)
            elif t["type"] == "SELL":
                holdings[sym] = holdings.get(sym, 0) - t["quantity"]
                invested -= t["quantity"] * t["price"] - t.get("fee", 0)
            tx_idx += 1
        total = sum(
            qty * price_by_date[sym].get(date_str, 0)
            for sym, qty in holdings.items() if qty > 0
        )
        if total > 0:
            series_value.append({"date": date_str, "value": round(total, 2)})
            series_invested.append({"date": date_str, "value": round(invested, 2)})
    return {
        "series": series_value,
        "invested": series_invested,
        "performance": compute_performance(series_value)
    }


@app.get("/api/benchmarks")
async def benchmarks(period: str = "1y"):
    return {"benchmarks": get_all_benchmarks(period)}


@app.get("/api/benchmarks/{bench_id}")
async def benchmark_detail(bench_id: str, period: str = "1y"):
    data = get_benchmark_data(bench_id, period)
    if not data:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return data


@app.get("/api/transactions")
async def transactions():
    return {"transactions": load_transactions()}


@app.post("/api/cache/clear")
async def clear_cache():
    cache.clear()
    return {"status": "cleared"}
