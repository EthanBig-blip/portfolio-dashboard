from fastapi import APIRouter
from ..fetcher import get_price

router = APIRouter()

@router.get("/api/quote")
async def get_quote(symbol: str):
    """Return latest price for a single ticker symbol."""
    price = get_price(symbol)
    return {"symbol": symbol, "price": price}
