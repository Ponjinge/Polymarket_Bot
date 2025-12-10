# Polymarket Bot

A Python bot to fetch and analyze odds for cryptocurrency related markets on Polymarket.

## Features

- Fetches all current markets from Polymarket
- Filters for markets related to cryptocurrencies (BTC, ETH, SOL, and many others)
- Retrieves odds, prices, and order book data for each market
- Exports results to JSON format

## Installation

1. Activate the virtual environment:
```bash
source .venv/bin/activate
```

2. Install the required dependencies (if not already installed):
```bash
pip install -r requirements.txt
```

## Usage

Run the script to fetch cryptocurrency market odds:

```bash
python crypto_odds.py
```

The script will:
1. Connect to Polymarket's CLOB API (read-only, no authentication needed)
2. Fetch all available markets
3. Filter for cryptocurrency related markets
4. Get current odds/prices for each outcome
5. Display results in the terminal
6. Save results to `crypto_odds.json`

## Output

The script displays:
- Market question/title
- Market ID and end date
- For each outcome:
  - Current probability (midpoint price)
  - Buy and sell prices
  - Top bids and asks from the order book

Results are also saved to `crypto_odds.json` for further analysis.

## Notes

- This script uses read-only access, so no API credentials are required
- The script searches for markets containing: Bitcoin (BTC), Ethereum (ETH), Solana (SOL), Cardano (ADA), Polygon (MATIC), Avalanche (AVAX), Chainlink (LINK), Uniswap (UNI), Litecoin (LTC), Dogecoin (DOGE), XRP, Polkadot (DOT), Cosmos (ATOM), Algorand (ALGO), and other crypto-related terms
- All prices are in dollars from 0.00 to 1.00 (representing probability)
