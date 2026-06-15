from fastapi import APIRouter
import yfinance as yf

router = APIRouter()

@router.get("/api/quote")
async def get_quote(symbol: str):
    """Return latest price for a single ticker symbol."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = getattr(info, 'last_price', None) or getattr(info, 'regularMarketPrice', None)
        if price is None:
            hist = ticker.history(period="1d", interval="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
        return {"symbol": symbol, "price": round(float(price), 8) if price else None}
    except Exception as e:
        return {"symbol": symbol, "price": None, "error": str(e)}
