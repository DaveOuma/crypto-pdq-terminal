import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

class BinanceConnector:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API keys not configured")
        
        self.client = Client(self.api_key, self.api_secret)

    def get_crypto_price(self, crypto_type):
        """Get current price from Binance."""
        symbol = f"{crypto_type}USDT"
        try:
            avg_price = self.client.get_avg_price(symbol=symbol)
            return float(avg_price['price'])
        except BinanceAPIException as e:
            raise Exception(f"Binance API error: {e.message}")
        except Exception as e:
            raise Exception(f"Error fetching price: {str(e)}")

    def get_balance(self, asset="USDT"):
        """Get balance for a specific asset."""
        try:
            balance = self.client.get_asset_balance(asset=asset)
            return {
                "asset": asset,
                "free": float(balance['free']),
                "locked": float(balance['locked']),
                "total": float(balance['free']) + float(balance['locked'])
            }
        except Exception as e:
            raise Exception(f"Error fetching balance: {str(e)}")

    def get_recent_orders(self, symbol="BTCUSDT", limit=5):
        """Get recent orders."""
        try:
            orders = self.client.get_my_trades(symbol=symbol, limit=limit)
            return [
                {
                    "order_id": order['orderId'],
                    "price": float(order['price']),
                    "qty": float(order['qty']),
                    "quote_qty": float(order['quoteQty']),
                    "time": order['time']
                }
                for order in orders
            ]
        except Exception as e:
            raise Exception(f"Error fetching orders: {str(e)}")
