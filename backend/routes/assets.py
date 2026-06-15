"""Route POST /api/assets/sync — converts localStorage assets to transactions.json."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter()
DATA_FILE = Path(os.getenv("TRANSACTIONS_FILE", "data/transactions.json"))

TICKER_ALIASES = {
    "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD",
    "BNB": "BNB-USD", "XRP": "XRP-USD", "ADA": "ADA-USD",
    "DOGE": "DOGE-USD", "AVAX": "AVAX-USD", "MATIC": "MATIC-USD",
    "DOT": "DOT-USD", "LINK": "LINK-USD", "LTC": "LTC-USD",
}

class Asset(BaseModel):
    symbol: str
    type: str
    qty: float
    buyPrice: float
    accountIdx: Optional[str] = ""

class SyncPayload(BaseModel):
    assets: list[Asset]

@router.post("/api/assets/sync")
async def sync_assets(payload: SyncPayload):
    if not payload.assets:
        raise HTTPException(status_code=400, detail="Aucun actif fourni.")

    transactions = []
    for a in payload.assets:
        sym = a.symbol.upper()
        ticker = TICKER_ALIASES.get(sym, sym)
        transactions.append({
            "date": "2024-01-01",
            "symbol": ticker,
            "type": "BUY",
            "quantity": a.qty,
            "price": a.buyPrice,
            "fee": 0.0,
            "currency": "USD",
        })

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(transactions, f, indent=2, ensure_ascii=False)

    return {"status": "ok", "synced": len(transactions)}
