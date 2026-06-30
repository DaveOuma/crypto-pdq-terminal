# Crypto PDQ Terminal

Buy crypto directly from your terminal using a card. Insert card details, get real-time Binance quotes, and execute trades.

## What it does

- Takes card number, expiry, and CVV (validates with Luhn algorithm)
- Fetches live crypto prices from Binance API
- Executes market orders for BTC or ETH
- Shows transaction IDs and confirmation

## Setup

1. Clone this repo
2. Install dependencies:
3. Create `.env` file with your Binance API keys:
4. Run:

## Security Notes

- Card data never stored or logged
- Input masked during entry
- API keys kept in `.env` (never commit to GitHub)

## Dependencies

- Python 3.8+
- `rich` for terminal UI
- `requests` for API calls
- `python-binance` for Binance SDK

## Disclaimer

For educational purposes only. Not financial advice. Test with small amounts first.

---

- Built with `coffee` and late-night `coding sessions`
