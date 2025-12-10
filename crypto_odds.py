"""
Script to fetch odds for all cryptocurrency related markets on Polymarket.
"""
from py_clob_client.client import ClobClient
import json
import httpx
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
        'bitcoin', 'btc', 'ethereum', 'eth', 'cryptocurrency',
        'solana', 'sol ', 'cardano', 'ada ', 'polygon', 'matic',
        'avalanche', 'avax', 'chainlink', 'link ', 'uniswap', 'uni ',
        'litecoin', 'ltc', 'dogecoin', 'doge', 'xrp', 'ripple',
        'polkadot', 'dot ', 'cosmos', 'atom ', 'algorand', 'algo ',
        'shiba', 'shib', 'tether', 'usdt', 'usdc', 'binance', 'bnb',
        'terra', 'luna', 'stellar', 'xlm', 'monero', 'xmr',
        'eos', 'tezos', 'xtz', 'dash', 'zcash', 'zec',
        'defi', 'web3', 'blockchain'
    ]
    
    if 'data' not in markets:
        return crypto_markets
    
    for market in markets['data']:
        if not isinstance(market, dict):
            continue
            
        # Check various fields for cryptocurrency related content
        # Try all possible field names from Gamma API
        market_text = ' '.join([
            str(market.get('question', '')),
            str(market.get('description', '')),
            str(market.get('slug', '')),
            str(market.get('title', '')),
            str(market.get('name', '')),
            str(market.get('text', '')),
            str(market.get('market', '')),
            str(market.get('condition', '')),
            str(market.get('conditionId', '')),
            str(market.get('condition_id', '')),
        ]).lower()
        
        # Also check outcomes if they exist
        outcomes = market.get('outcomes', [])
        if outcomes:
            for outcome in outcomes:
                if isinstance(outcome, dict):
                    market_text += ' ' + ' '.join([
                        str(outcome.get('title', '')),
                        str(outcome.get('name', '')),
                        str(outcome.get('text', '')),
                        str(outcome.get('outcome', ''))
                    ]).lower()
        
        # Also check tokens if they exist
        tokens = market.get('tokens', [])
        if tokens:
            for token in tokens:
                if isinstance(token, dict):
                    market_text += ' ' + str(token.get('outcome', '')).lower()
        
        # Check if any search term appears in the market text
        if any(term in market_text for term in search_terms):
            crypto_markets.append(market)
    
    return crypto_markets


def get_token_ids_for_condition(client: ClobClient, condition_id: str) -> Dict[str, str]:
    """
    Get token IDs for a condition by fetching from simplified markets.
    
    Args:
        client: ClobClient instance
        condition_id: The condition ID to look up
        
    Returns:
        Dictionary mapping outcome names to token IDs
    """
    token_map = {}
    try:
        simplified = client.get_simplified_markets()
        markets_list = simplified.get('data', [])
        
        for market in markets_list:
            if market.get('condition_id') == condition_id:
                tokens = market.get('tokens', [])
                for token in tokens:
                    if isinstance(token, dict):
                        outcome = token.get('outcome', '')
                        token_id = token.get('token_id')
                        if outcome and token_id:
                            token_map[outcome] = str(token_id)
                break
    except Exception as e:
        print(f"Error getting token IDs: {e}")
    
    return token_map


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
        'market_id': market.get('id') or market.get('_id'),
        'question': market.get('question'),
        'slug': market.get('slug'),
        'end_date': market.get('endDate') or market.get('end_date'),
        'condition_id': market.get('conditionId') or market.get('condition_id'),
        'outcomes': []
    }
    
    # Get outcomes - could be list of strings or list of dicts
    outcomes = market.get('outcomes', [])
    outcome_prices_raw = market.get('outcomePrices', [])
    condition_id = market.get('conditionId') or market.get('condition_id')
    
    if not condition_id:
        print(f"Warning: No condition_id for market {market.get('id')}")
        return market_info
    
    # Parse outcomes if it's a JSON string
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except:
            pass
    
    # Parse outcomePrices if it's a JSON string
    outcome_prices_list = []
    if isinstance(outcome_prices_raw, str):
        try:
            outcome_prices_list = json.loads(outcome_prices_raw)
        except:
            pass
    elif isinstance(outcome_prices_raw, list):
        outcome_prices_list = outcome_prices_raw
    elif isinstance(outcome_prices_raw, dict):
        outcome_prices_list = list(outcome_prices_raw.values())
    
    # Get token IDs for this condition
    token_map = get_token_ids_for_condition(client, condition_id)
    
    # Extract outcome names
    outcome_names = []
    if isinstance(outcomes, list):
        for outcome in outcomes:
            if isinstance(outcome, str):
                outcome_names.append(outcome)
            elif isinstance(outcome, dict):
                outcome_names.append(outcome.get('name', outcome.get('title', 'Unknown')))
    elif isinstance(outcomes, dict):
        outcome_names = list(outcomes.values()) if outcomes else []
    
    # Process each outcome
    for idx, outcome_name in enumerate(outcome_names):
        try:
            # Get price from outcomePrices list (index corresponds to outcome index)
            price = None
            if idx < len(outcome_prices_list):
                try:
                    price = float(outcome_prices_list[idx])
                except (ValueError, TypeError):
                    pass
            
            outcome_info = {
                'outcome': outcome_name,
                'price': price,
                'probability': price if price else None
            }
            
            # Try to get token_id and fetch order book data
            token_id = token_map.get(outcome_name)
            if token_id:
                try:
                    midpoint = client.get_midpoint(token_id)
                    buy_price = client.get_price(token_id, side="BUY")
                    sell_price = client.get_price(token_id, side="SELL")
                    order_book = client.get_order_book(token_id)
                    
                    outcome_info.update({
                        'token_id': token_id,
                        'midpoint_price': midpoint,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'probability': midpoint if midpoint else price,
                        'order_book': {
                            'bids': order_book.bids[:3] if order_book and order_book.bids else [],
                            'asks': order_book.asks[:3] if order_book and order_book.asks else []
                        } if order_book else None
                    })
                except Exception as e:
                    outcome_info['order_book_error'] = str(e)
            
            market_info['outcomes'].append(outcome_info)
            
        except Exception as e:
            print(f"Error processing outcome {outcome_name}: {e}")
            market_info['outcomes'].append({
                'outcome': outcome_name,
                'error': str(e)
            })
    
    return market_info


def fetch_markets_from_gamma_api(limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch markets from Polymarket's Gamma API which includes full market details.
    
    Args:
        limit: Maximum number of markets to fetch
        
    Returns:
        List of market dictionaries with full details
    """
    markets = []
    url = "https://gamma-api.polymarket.com/markets"
    params = {
        'active': 'true',
        'closed': 'false',
        'limit': limit
    }
    
    try:
        with httpx.Client() as client:
            response = client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                markets = data
            elif isinstance(data, dict) and 'data' in data:
                markets = data['data']
            elif isinstance(data, dict) and 'results' in data:
                markets = data['results']
                
    except Exception as e:
        print(f"Error fetching from Gamma API: {e}")
        return []
    
    return markets


def main():
    """
    Main function to fetch and display cryptocurrency market odds.
    """
    # Initialize read-only client (no authentication needed for market data)
    HOST = "https://clob.polymarket.com"
    client = ClobClient(HOST)
    
    print("Fetching markets from Polymarket Gamma API...")
    try:
        # Get markets from Gamma API (has full market details)
        all_markets = fetch_markets_from_gamma_api(limit=2000)
        
        if not all_markets:
            print("ERROR: No markets returned from API")
            return
        
        print(f"Found {len(all_markets)} total markets")
        
        # Debug: Print first 10 markets to see structure
        print("\n" + "="*80)
        print("SAMPLE MARKETS (First 10):")
        print("="*80)
        for i, market in enumerate(all_markets[:10], 1):
            print(f"\nMarket {i}:")
            if isinstance(market, dict):
                # Print key fields
                for key in ['question', 'title', 'description', 'slug', 'id', 'conditionId']:
                    if key in market:
                        value = str(market[key])[:100]
                        print(f"  {key}: {value}")
                # Show available keys
                print(f"  Available keys: {list(market.keys())[:15]}")
            print()
        
        # Normalize the data structure for filtering
        normalized_markets = {'data': all_markets}
        
        # Filter for cryptocurrency related markets
        print("\n" + "="*80)
        print("Filtering for cryptocurrency related markets...")
        print("="*80)
        crypto_markets = filter_crypto_markets(normalized_markets)
        print(f"Found {len(crypto_markets)} cryptocurrency related markets\n")
        
        if not crypto_markets:
            print("No cryptocurrency related markets found.")
            return
        
        # Show first 20 crypto markets found
        print("\nFirst 20 cryptocurrency markets found:")
        for i, market in enumerate(crypto_markets[:20], 1):
            print(f"  {i}. {market.get('question', 'Unknown')}")
        print()
        
        # Get odds for each market (limit to first 20 for faster processing)
        limit = min(20, len(crypto_markets))
        print(f"Processing first {limit} markets for detailed odds...\n")
        results = []
        for i, market in enumerate(crypto_markets[:limit], 1):
            print(f"Processing market {i}/{limit}: {market.get('question', 'Unknown')[:80]}...")
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

