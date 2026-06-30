from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from core.payment import PaymentProcessor, validate_card
from core.binance_client import BinanceConnector
from models import PurchaseRequest, BalanceRequest, PriceRequest

app = FastAPI(
    title="Crypto PDQ Terminal API",
    description="Buy crypto with card via Binance",
    version="1.0.0"
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize connectors
try:
    binance = BinanceConnector()
    processor = PaymentProcessor()
except ValueError as e:
    binance = None
    processor = None
    print(f"ERROR: {e}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Crypto PDQ Terminal API",
        "status": "running" if binance else "degraded (Binance not configured)",
        "endpoints": [
            "POST /purchase",
            "GET /price/{crypto_type}",
            "GET /balance/{asset}",
            "GET /orders/{symbol}"
        ]
    }


@app.post("/purchase", status_code=status.HTTP_200_OK)
async def purchase(payload: PurchaseRequest):
    """
    Purchase crypto using card details.
    
    - Validates card (Luhn algorithm)
    - Fetches real-time Binance price
    - Simulates payment authorization
    - Returns transaction details
    """
    if not binance:
        raise HTTPException(
            status_code=503,
            detail="Binance API not configured. Set BINANCE_API_KEY and BINANCE_API_SECRET."
        )
    
    try:
        # Validate card
        validate_card(
            payload.card_number,
            payload.expiry,
            payload.cvv
        )
        
        # Fetch real crypto price
        crypto_price = binance.get_crypto_price(payload.crypto_type)
        
        # Calculate crypto amount
        crypto_amount = payload.amount / crypto_price
        
        # Process payment (card_number, expiry, cvv, amount, crypto_type, crypto_amount, crypto_price)
        card_number = payload.card_number
        result = processor.authorize_payment(
            payload.card_number,
            payload.expiry,
            payload.cvv,
            payload.amount,
            payload.crypto_type,
            crypto_amount,
            crypto_price
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/price/{crypto_type}")
async def get_price(crypto_type: str):
    """
    Get current price for a cryptocurrency from Binance.
    """
    if not binance:
        raise HTTPException(
            status_code=503,
            detail="Binance API not configured."
        )
    
    try:
        crypto_type = crypto_type.upper()
        if crypto_type not in ["BTC", "ETH"]:
            raise ValueError("Crypto type must be BTC or ETH")
        
        price = binance.get_crypto_price(crypto_type)
        return {
            "crypto_type": crypto_type,
            "price_usd": price,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/balance/{asset}")
async def get_balance(asset: str = "USDT"):
    """
    Get balance for a specific asset in Binance account.
    """
    if not binance:
        raise HTTPException(
            status_code=503,
            detail="Binance API not configured."
        )
    
    try:
        asset = asset.upper()
        balance = binance.get_balance(asset)
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/{symbol}")
async def get_orders(symbol: str = "BTCUSDT", limit: int = 5):
    """
    Get recent orders from Binance.
    """
    if not binance:
        raise HTTPException(
            status_code=503,
            detail="Binance API not configured."
        )
    
    try:
        symbol = symbol.upper()
        orders = binance.get_recent_orders(symbol, limit)
        return {"symbol": symbol, "orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )
