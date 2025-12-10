"""
Script to fetch odds for all cryptocurrency related markets on Polymarket.
"""
from py_clob_client.client import ClobClient
import json
from typing import List, Dict, Any


def filter_crypto_markets(markets: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter markets to only include those related to cryptocurrencies.
    
    Args:
        markets: Dictionary containing market data from get_simplified_markets()
        
    Returns:
        List of markets that contain crypto-related terms in their title or description
    """
    crypto_markets = []
    search_terms = [
        'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency',
        'solana', 'sol', 'cardano', 'ada', 'polygon', 'matic',
        'avalanche', 'avax', 'chainlink', 'link', 'uniswap', 'uni',
        'litecoin', 'ltc', 'dogecoin', 'doge', 'xrp', 'ripple',
        'polkadot', 'dot', 'cosmos', 'atom', 'algorand', 'algo',
        'price', 'usd', 'market cap', 'trading', 'exchange'
    ]
    
    if 'data' not in markets:
        return crypto_markets
    
    for market in markets['data']:
        # Check various fields for cryptocurrency related content
        market_text = ' '.join([
            market.get('question', ''),
            market.get('description', ''),
            market.get('slug', ''),
            market.get('title', '')
        ]).lower()
        
        # Check if any search term appears in the market text
        if any(term in market_text for term in search_terms):
            crypto_markets.append(market)
    
    return crypto_markets


def get_market_odds(client: ClobClient, market: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get odds/prices for a specific market.
    
    Args:
        client: ClobClient instance
        market: Market dictionary containing market information
        
    Returns:
        Dictionary with market info and odds
    """
    market_info = {
        'market_id': market.get('id'),
        'question': market.get('question'),
        'slug': market.get('slug'),
        'end_date': market.get('end_date'),
        'outcomes': []
    }
    
    # Get token IDs for each outcome
    outcomes = market.get('outcomes', [])
    
    for outcome in outcomes:
        token_id = outcome.get('token_id')
        if not token_id:
            continue
            
        try:
            # Get midpoint price (current odds)
            midpoint = client.get_midpoint(token_id)
            
            # Get buy and sell prices
            buy_price = client.get_price(token_id, side="BUY")
            sell_price = client.get_price(token_id, side="SELL")
            
            # Get order book for more detailed information
            order_book = client.get_order_book(token_id)
            
            outcome_info = {
                'outcome': outcome.get('title', outcome.get('name', 'Unknown')),
                'token_id': token_id,
                'midpoint_price': midpoint,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'probability': midpoint if midpoint else None,  # Midpoint is the implied probability
                'order_book': {
                    'bids': order_book.bids[:3] if order_book.bids else [],  # Top 3 bids
                    'asks': order_book.asks[:3] if order_book.asks else []   # Top 3 asks
                } if order_book else None
            }
            
            market_info['outcomes'].append(outcome_info)
            
        except Exception as e:
            print(f"Error getting odds for token {token_id}: {e}")
            outcome_info = {
                'outcome': outcome.get('title', outcome.get('name', 'Unknown')),
                'token_id': token_id,
                'error': str(e)
            }
            market_info['outcomes'].append(outcome_info)
    
    return market_info


def main():
    """
    Main function to fetch and display cryptocurrency market odds.
    """
    # Initialize read-only client (no authentication needed for market data)
    HOST = "https://clob.polymarket.com"
    client = ClobClient(HOST)
    
    print("Fetching all markets from Polymarket...")
    try:
        # Get all markets
        all_markets = client.get_simplified_markets()
        print(f"Found {len(all_markets.get('data', []))} total markets")
        
        # Filter for cryptocurrency related markets
        print("\nFiltering for cryptocurrency related markets...")
        crypto_markets = filter_crypto_markets(all_markets)
        print(f"Found {len(crypto_markets)} cryptocurrency related markets\n")
        
        if not crypto_markets:
            print("No cryptocurrency related markets found.")
            return
        
        # Get odds for each market
        results = []
        for i, market in enumerate(crypto_markets, 1):
            print(f"Processing market {i}/{len(crypto_markets)}: {market.get('question', 'Unknown')[:80]}...")
            market_odds = get_market_odds(client, market)
            results.append(market_odds)
        
        # Display results
        print("\n" + "="*80)
        print("CRYPTOCURRENCY MARKET ODDS")
        print("="*80 + "\n")
        
        for result in results:
            print(f"Market: {result['question']}")
            print(f"Market ID: {result['market_id']}")
            print(f"End Date: {result.get('end_date', 'N/A')}")
            print("\nOutcomes:")
            
            for outcome in result['outcomes']:
                if 'error' in outcome:
                    print(f"  - {outcome['outcome']}: Error - {outcome['error']}")
                else:
                    prob = outcome.get('probability')
                    prob_pct = f"{prob * 100:.2f}%" if prob else "N/A"
                    print(f"  - {outcome['outcome']}:")
                    print(f"    Probability: {prob_pct}")
                    print(f"    Midpoint Price: ${outcome.get('midpoint_price', 'N/A')}")
                    print(f"    Buy Price: ${outcome.get('buy_price', 'N/A')}")
                    print(f"    Sell Price: ${outcome.get('sell_price', 'N/A')}")
            
            print("\n" + "-"*80 + "\n")
        
        # Save results to JSON file
        output_file = 'crypto_odds.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"Error fetching markets: {e}")
        raise


if __name__ == "__main__":
    main()

