import os
import requests
from groq import Groq

BINANCE_SQUARE_KEY = os.getenv("BINANCE_SQUARE_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

SQUARE_API_URL = "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add"

def get_market_trends():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        data = res.json()
        usdt_pairs = [
            d for d in data 
            if d.get("symbol", "").endswith("USDT") and float(d.get("quoteVolume", 0)) > 5000000
        ]
        top_gainers = sorted(usdt_pairs, key=lambda x: float(x.get("priceChangePercent", 0)), reverse=True)[:5]
        summary = []
        for c in top_gainers:
            sym = c["symbol"].replace("USDT", "")
            summary.append(f"${sym}: {c.get("priceChangePercent")}%")
        return ", ".join(summary)
    except Exception as e:
        return "$BTC, $ETH, $SOL momentum"

def generate_seo_post(trends_data):
    if not GROQ_KEY:
        raise ValueError("GROQ_API_KEY is not set.")
    client = Groq(api_key=GROQ_KEY)
    prompt = f"""You are an expert crypto analyst for Binance Square.
Trending movers: {trends_data}

Write a high-engagement, concise (120-180 words) Binance Square post.
1. Hook reader on market momentum.
2. Embed tickers ($BTC, $BNB, top movers).
3. Add 3-5 tags at the end (#BinanceSquare #Crypto).
4. Return ONLY raw post text."""
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return res.choices[0].message.content.strip()

def post_to_binance_square(content):
    if not BINANCE_SQUARE_KEY:
        raise ValueError("BINANCE_SQUARE_API_KEY is not set.")
    hdrs = {
        "X-Square-OpenAPI-Key": BINANCE_SQUARE_KEY,
        "Content-Type": "application/json",
        "clienttype": "binanceSkill"
    }
    r = requests.post(SQUARE_API_URL, headers=hdrs, json={"bodyTextOnly": content}, timeout=15)
    print(f"Status: {r.status_code}, Body: {r.text}")

if __name__ == "__main__":
    t = get_market_trends()
    p = generate_seo_post(t)
    print(p)
    post_to_binance_square(p)
