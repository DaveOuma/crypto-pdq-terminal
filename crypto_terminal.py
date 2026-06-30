import json
import random
import time
import getpass
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from binance.client import Client

# Load environment variables
load_dotenv()

console = Console()

class PaymentProcessor:
    def authorize_payment(self, card_number, expiry, cvv, amount, crypto_type, crypto_amount, crypto_price):
        """Authorize payment and return transaction payload."""
        # Simulate processing delay
        time.sleep(1)
        
        # Generate transaction ID
        transaction_id = f"TX{random.randint(100000, 999999)}"
        
        # Create payload with real data
        payload = {
            "transaction_id": transaction_id,
             "card_number": card_number,
            "expiry": expiry,
            "cvv": cvv,  
            "amount_usd": amount,
            "crypto_type": crypto_type,
            "crypto_amount": round(crypto_amount, 8),
            "price_per_crypto": crypto_price,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return payload


class BinanceConnector:
    def __init__(self, api_key, api_secret):
        """Initialize Binance client."""
        self.client = Client(api_key, api_secret)

    def get_crypto_price(self, crypto_type):
        """Get current price from Binance."""
        symbol = f"{crypto_type}USDT"
        try:
            avg_price = self.client.get_avg_price(symbol=symbol)
            return float(avg_price['price'])
        except Exception as e:
            console.print(f"[red]Error fetching price: {e}[/red]")
            return None


def luhn_check(card_number):
    """Validate card number using Luhn algorithm."""
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    
    return (sum(odd_digits) + sum(sum(digits_of(d * 2)) for d in even_digits)) % 10 == 0


def validate_card(card_number, expiry, cvv):
    """Validate card details."""
    # Check card number
    if not card_number.isdigit() or len(card_number) != 16:
        raise ValueError("Card number must be 16 digits.")
    if not luhn_check(card_number):
        raise ValueError("Invalid card number.")
    
    # Check CVV
    if not cvv.isdigit() or len(cvv) not in [3, 4]:
        raise ValueError("CVV must be 3 or 4 digits.")
    
    # Check expiry
    try:
        month, year = map(int, expiry.split('/'))
        if month < 1 or month > 12:
            raise ValueError("Invalid month.")
        current_year = time.localtime().tm_year % 100
        current_month = time.localtime().tm_mon
        if year < current_year or (year == current_year and month < current_month):
            raise ValueError("Card has expired.")
    except ValueError:
        raise ValueError("Expiry must be in MM/YY format.")


def main():
    """Main application loop."""
    # Get API keys from environment variables
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
    
    # Check if keys are set
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        console.print("[red]Error: Binance API keys not found in .env file[/red]")
        console.print("Create a .env file with:")
        console.print("BINANCE_API_KEY=your_key_here")
        console.print("BINANCE_API_SECRET=your_secret_here")
        return
    
    # Initialize connectors
    binance_connector = BinanceConnector(BINANCE_API_KEY, BINANCE_API_SECRET)
    processor = PaymentProcessor()
    
    # Welcome message
    console.print(Text("Welcome to the Crypto Purchase Terminal", style="bold green"))
    console.print("Fetching real-time rates from Binance...\n")
    
    try:
        while True:
            # Get user input
            console.print("Please enter your payment details:")
            card_number = getpass.getpass("Card Number (16 digits): ").strip()
            expiry = Prompt.ask("Expiry Date (MM/YY)").strip()
            cvv = getpass.getpass("CVV (3-4 digits): ").strip()
            amount = float(Prompt.ask("Amount in USD").strip())
            crypto_type = Prompt.ask("Crypto Type (BTC/ETH)", choices=["BTC", "ETH"]).strip()

            # Validate input
            validate_card(card_number, expiry, cvv)

            # Get real crypto price from Binance
            crypto_price = binance_connector.get_crypto_price(crypto_type)
            if crypto_price is None:
                console.print("[red]Failed to retrieve crypto price. Transaction aborted.[/red]")
                continue
            
            # Calculate crypto amount
            crypto_amount = amount / crypto_price
            
            # Process payment
            payload = processor.authorize_payment(
                card_number, expiry, cvv, amount, crypto_type, crypto_amount, crypto_price
            )
            
            # Show success
            console.print("\n[bold green]✓ Transaction Successful![/bold green]")
            console.print(f"Transaction ID: [yellow]{payload['transaction_id']}[/yellow]")
            console.print(f"Amount: [cyan]{round(crypto_amount, 6)} {crypto_type}[/cyan]")
            console.print(f"Rate: [cyan]${crypto_price:,.2f}[/cyan] per {crypto_type}")
            console.print(f"Timestamp: [dim]{payload['timestamp']}[/dim]")
            console.print("\n[dim]Full payload:[/dim]")
            console.print(json.dumps(payload, indent=2))
            console.print("\n" + "="*50 + "\n")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting application. Thank you![/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


if __name__ == "__main__":
    main()