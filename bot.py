import os
import requests
from openai import OpenAI

BINANCE_SQUARE_KEY = os.getenv("BINANCE_SQUARE_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

SQUARE_API_URL = "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add"

def get_market_trends():
    """Fetch live 24hr market data from public Binance Spot API to find top movers."""
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        data = res.json()
        
        # Filter for major USDT pairs with minimum volume
        usdt_pairs = [
            d for d in data 
            if d.get('symbol', '').endswith('USDT') and float(d.get('quoteVolume', 0)) > 5000000
        ]
        top_gainers = sorted(usdt_pairs, key=lambda x: float(x.get('priceChangePercent', 0)), reverse=True)[:5]
        
        trends_summary = []
        for coin in top_gainers:
            symbol = coin['symbol'].replace('USDT', '')
            change = coin['priceChangePercent']
            price = coin['lastPrice']
            trends_summary.append(f"${symbol}: Price {price}, 24h Change: {change}%")
            
        return "\n".join(trends_summary)
    except Exception as e:
        print(f"Error fetching Binance market data: {e}")
        return "$BTC: Current market leader, $ETH: Smart contract leader, $BNB: Exchange ecosystem token"

def generate_seo_post(trend_data):
    """Use LLM to create an SEO-optimized Binance Square post."""
    client = OpenAI(api_key=OPENAI_KEY)
    
    prompt = f"""
    You are an expert crypto market analyst writing for Binance Square.
    Current trending Binance movers and market data:
    {trend_data}

    Write a high-engagement, concise (120-180 words) Binance Square post analyzing today's momentum.
    Rules:
    1. Hook the reader with a catchy first sentence on market momentum or notable token surge.
    2. Naturally embed cashtags (e.g. $BTC, $BNB, and the top mover tags) so Binance Square links them automatically.
    3. Include 3-5 relevant SEO tags at the end (e.g. #BinanceSquare #CryptoMarket #TradingTips #Altcoins).
    4. Provide clear market sentiment and ask a question at the end to drive community comments.
    5. Return ONLY the raw post text.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def post_to_binance_square(content):
    """Publish the content directly to Binance Square OpenAPI."""
    if not BINANCE_SQUARE_KEY:
        print("Error: BINANCE_SQUARE_API_KEY is not set.")
        return

    headers = {
        "X-Square-OpenAPI-Key": BINANCE_SQUARE_KEY,
        "Content-Type": "application/json",
        "clienttype": "binanceSkill"
    }
    payload = {
        "bodyTextOnly": content
    }
    
    response = requests.post(SQUARE_API_URL, headers=headers, json=payload, timeout=15)
    try:
        result = response.json()
        if response.status_code == 200 and result.get("code") in ["000000", "2000002"]:
            print("Successfully published to Binance Square!")
            print(f"Post ID: {result.get('data', {}).get('id')}")
        else:
            print(f"Failed to post. Status: {response.status_code}, Response: {result}")
    except Exception:
        print(f"Server response ({response.status_code}): {response.text}")

if __name__ == "__main__":
    market_context = get_market_trends()
    post_text = generate_seo_post(market_context)
    print(f"--- Generated Post ---\n{post_text}\n----------------------")
    post_to_binance_square(post_text)
