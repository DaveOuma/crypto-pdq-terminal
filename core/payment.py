import random
import time
from datetime import datetime

class PaymentProcessor:
    @staticmethod
    def authorize_payment(card_number, expiry, cvv, amount, crypto_type, crypto_amount, crypto_price):
        """Authorize payment and return transaction payload."""
        time.sleep(1)  # Simulate processing delay
        
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
    """Validate card number using Luhn algorithm."""
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    
    return (sum(odd_digits) + sum(sum(digits_of(d * 2)) for d in even_digits)) % 10 == 0


def validate_card(card_number, expiry, cvv):
    """Validate card details."""
    errors = []
    
    # Card number
    if not card_number or not card_number.isdigit() or len(card_number) != 16:
        errors.append("Card number must be 16 digits.")
    elif not luhn_check(card_number):
        errors.append("Invalid card number.")
    
    # CVV
    if not cvv or not cvv.isdigit() or len(cvv) not in [3, 4]:
        errors.append("CVV must be 3 or 4 digits.")
    
    # Expiry
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
