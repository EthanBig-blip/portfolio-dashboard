"""Portfolio calculations: PnL, ROAI, performance metrics."""
import json, os
from pathlib import Path

# Chemin absolu : toujours relatif à la racine du projet, peu importe d'où uvicorn est lancé
_PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = Path(os.getenv("TRANSACTIONS_FILE", str(_PROJECT_ROOT / "data" / "transactions.json")))


def load_transactions() -> list[dict]:
    if not DATA_FILE.exists():
        print(f"[portfolio] WARN: {DATA_FILE} not found, using demo data")
        return _demo_transactions()
    with open(DATA_FILE) as f:
        data = json.load(f)
    print(f"[portfolio] Loaded {len(data)} transactions from {DATA_FILE}")
    return data


def _demo_transactions() -> list[dict]:
    return [
        {"date": "2023-01-10", "symbol": "BTC-USD",  "type": "BUY",  "quantity": 0.1,  "price": 17200, "fee": 3.44,  "currency": "USD"},
        {"date": "2023-03-15", "symbol": "ETH-USD",  "type": "BUY",  "quantity": 1.5,  "price": 1680,  "fee": 2.52,  "currency": "USD"},
        {"date": "2023-06-01", "symbol": "BTC-USD",  "type": "BUY",  "quantity": 0.05, "price": 27000, "fee": 1.35,  "currency": "USD"},
        {"date": "2023-09-20", "symbol": "BTC-USD",  "type": "SELL", "quantity": 0.03, "price": 26800, "fee": 0.80,  "currency": "USD"},
        {"date": "2024-01-05", "symbol": "SOL-USD",  "type": "BUY",  "quantity": 10,   "price": 102,   "fee": 1.02,  "currency": "USD"},
        {"date": "2024-03-10", "symbol": "BTC-USD",  "type": "BUY",  "quantity": 0.02, "price": 68000, "fee": 1.36,  "currency": "USD"},
        {"date": "2024-07-01", "symbol": "ETH-USD",  "type": "BUY",  "quantity": 0.5,  "price": 3200,  "fee": 1.60,  "currency": "USD"},
        {"date": "2025-01-15", "symbol": "BTC-USD",  "type": "BUY",  "quantity": 0.01, "price": 98000, "fee": 0.98,  "currency": "USD"},
    ]


def compute_invested_capital(transactions: list[dict]) -> float:
    total = 0.0
    for t in transactions:
        if t["type"] in ("BUY", "DEPOSIT"):
            total += t["quantity"] * t["price"] + t.get("fee", 0)
        elif t["type"] in ("SELL", "WITHDRAW"):
            total -= t["quantity"] * t["price"] - t.get("fee", 0)
    return round(total, 2)


def compute_holdings(transactions: list[dict]) -> dict[str, float]:
    holdings: dict[str, float] = {}
    for t in transactions:
        sym = t["symbol"]
        if t["type"] == "BUY":
            holdings[sym] = holdings.get(sym, 0) + t["quantity"]
        elif t["type"] == "SELL":
            holdings[sym] = holdings.get(sym, 0) - t["quantity"]
    return {k: v for k, v in holdings.items() if v > 0.000001}


def compute_performance(portfolio_series: list[dict]) -> dict:
    if not portfolio_series:
        return {}
    values = [d["value"] for d in portfolio_series]
    last = values[-1]
    def perf_from(idx):
        start = values[max(0, idx)]
        return {"abs": round(last - start, 2), "pct": round((last - start) / start, 6) if start else 0}
    n = len(values)
    return {
        "current_value": round(last, 2),
        "today":    perf_from(n - 2),
        "wtd":      perf_from(n - 8),
        "mtd":      perf_from(n - 31),
        "ytd":      perf_from(n - 181),
        "one_year": perf_from(n - 366),
        "max":      perf_from(0),
    }
