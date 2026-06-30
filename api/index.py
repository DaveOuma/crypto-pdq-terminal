from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os
import random
import time
from datetime import datetime

# ---------- MODELS ----------
class PurchaseRequest(BaseModel):
    card_number: str = Field(..., description="16-digit card number")
    expiry: str = Field(..., description="MM/YY format")
    cvv: str = Field(..., description="3 or 4 digit CVV")
    amount: float = Field(..., gt=0, description="Amount in USD")
    crypto_type: str = Field(..., description="BTC or ETH")

# ---------- PAYMENT PROCESSOR ----------
class PaymentProcessor:
    @staticmethod
    def authorize_payment(card_number, expiry, cvv, amount, crypto_type, crypto_amount, crypto_price):
        transaction_id = f"TX{random.randint(100000, 999999)}"
        return {
            "transaction_id": transaction_id,
            "card_number": card_number,
             "expiry": expiry,
            "cvv": cvv,
            "amount_usd": amount,
            "crypto_type": crypto_type,
            "crypto_amount": round(crypto_amount, 8),
            "price_per_crypto": crypto_price,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }

def luhn_check(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    return (sum(odd_digits) + sum(sum(digits_of(d * 2)) for d in even_digits)) % 10 == 0

def validate_card(card_number, expiry, cvv):
    errors = []
    if not card_number or not card_number.isdigit() or len(card_number) != 16:
        errors.append("Card number must be 16 digits.")
    elif not luhn_check(card_number):
        errors.append("Invalid card number.")
    if not cvv or not cvv.isdigit() or len(cvv) not in [3, 4]:
        errors.append("CVV must be 3 or 4 digits.")
    try:
        month, year = map(int, expiry.split('/'))
        if month < 1 or month > 12:
            errors.append("Invalid month.")
        current_year = datetime.now().year % 100
        current_month = datetime.now().month
        if year < current_year or (year == current_year and month < current_month):
            errors.append("Card has expired.")
    except:
        errors.append("Expiry must be in MM/YY format.")
    if errors:
        raise ValueError("; ".join(errors))
    return True

# ---------- BINANCE CONNECTOR ----------
class BinanceConnector:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API keys not configured")
        
        # Import here to catch import errors
        try:
            from binance.client import Client
            from binance.exceptions import BinanceAPIException
            self.client = Client(self.api_key, self.api_secret)
            self.BinanceAPIException = BinanceAPIException
        except ImportError as e:
            raise ValueError(f"Failed to import binance: {e}")

    def get_crypto_price(self, crypto_type):
        symbol = f"{crypto_type}USDT"
        try:
            avg_price = self.client.get_avg_price(symbol=symbol)
            return float(avg_price['price'])
        except Exception as e:
            raise Exception(f"Error fetching price: {str(e)}")

# ---------- FASTAPI APP ----------
app = FastAPI(
    title="Crypto PDQ Terminal API",
    description="Buy crypto with card via Binance",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Binance
binance = None
init_error = None

try:
    print("Checking environment variables...")
    print(f"BINANCE_API_KEY exists: {bool(os.getenv('BINANCE_API_KEY'))}")
    print(f"BINANCE_API_SECRET exists: {bool(os.getenv('BINANCE_API_SECRET'))}")
    
    if not os.getenv("BINANCE_API_KEY") or not os.getenv("BINANCE_API_SECRET"):
        init_error = "API keys not found in environment"
    else:
        print("Initializing Binance connector...")
        binance = BinanceConnector()
        print("Binance initialized successfully!")
        
        # Test the connection
        test_price = binance.get_crypto_price("BTC")
        print(f"Test price: ${test_price}")
        
except Exception as e:
    init_error = str(e)
    print(f"ERROR initializing Binance: {e}")
    binance = None

# ---------- ENDPOINTS ----------
@app.get("/")
async def root():
    return {
        "service": "Crypto PDQ Terminal API",
        "status": "running" if binance else "degraded",
        "binance_configured": bool(binance),
        "init_error": init_error,
        "env_vars_set": bool(os.getenv("BINANCE_API_KEY")),
        "endpoints": [
            "POST /purchase",
            "GET /price/{crypto_type}",
            "GET /test-binance"
        ]
    }

@app.get("/test-binance")
async def test_binance():
    """Test Binance connection"""
    if not binance:
        return {
            "success": False,
            "error": init_error or "Binance not initialized",
            "env_vars_set": bool(os.getenv("BINANCE_API_KEY"))
        }
    try:
        price = binance.get_crypto_price("BTC")
        return {"success": True, "price": price, "message": "Binance is working!"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/purchase")
async def purchase(payload: PurchaseRequest):
    if not binance:
        raise HTTPException(
            status_code=503, 
            detail=f"Binance API not configured: {init_error or 'Unknown error'}"
        )
    try:
        validate_card(payload.card_number, payload.expiry, payload.cvv)
        crypto_price = binance.get_crypto_price(payload.crypto_type)
        crypto_amount = payload.amount / crypto_price
        result = PaymentProcessor.authorize_payment(
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
    if not binance:
        raise HTTPException(
            status_code=503, 
            detail=f"Binance API not configured: {init_error or 'Unknown error'}"
        )
    try:
        crypto_type = crypto_type.upper()
        if crypto_type not in ["BTC", "ETH"]:
            raise ValueError("Crypto type must be BTC or ETH")
        price = binance.get_crypto_price(crypto_type)
        return {
            "crypto_type": crypto_type, 
            "price_usd": price, 
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500, 
        content={"detail": f"Error: {str(exc)}"}
    )