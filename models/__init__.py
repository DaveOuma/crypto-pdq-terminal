from pydantic import BaseModel, Field
from typing import Optional

class PurchaseRequest(BaseModel):
    card_number: str = Field(..., description="16-digit card number")
    expiry: str = Field(..., description="MM/YY format")
    cvv: str = Field(..., description="3 or 4 digit CVV")
    amount: float = Field(..., gt=0, description="Amount in USD")
    crypto_type: str = Field(..., description="BTC or ETH")

class BalanceRequest(BaseModel):
    asset: Optional[str] = Field("USDT", description="Asset to check balance for")

class PriceRequest(BaseModel):
    crypto_type: str = Field(..., description="BTC or ETH")