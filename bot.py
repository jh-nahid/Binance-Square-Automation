import os
import re
import random
import requests
from google import genai

BINANCE_SQUARE_KEY = os.getenv("BINANCE_SQUARE_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

SQUARE_API_URL = "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add"

# Dynamic Content Pillars available for autonomous routing
CONTENT_PILLARS = [
    {
        "type": "official_news",
        "focus": "Official Binance announcements, new token listings, Launchpool/Megadrop farming, product updates, and ecosystem releases.",
        "tags": ["#BinanceNews", "#BinanceSquare"]
    },
    {
        "type": "trending_debate",
        "focus": "Viral crypto community debates: meme coins vs utility tokens, CEX transparency vs self-custody, airdrop meta, or AI agent tokens.",
        "tags": ["#CryptoDiscussion", "#BinanceSquare"]
    },
    {
        "type": "macro_events",
        "focus": "Institutional ETF inflows, Bitcoin dominance shifts, global macroeconomic events (Fed rates, liquidity cycles), and token unlocks.",
        "tags": ["#Bitcoin", "#CryptoMarket"]
    },
    {
        "type": "market_breakouts",
        "focus": "Top 24h market gainers, volume surges, technical breakout levels, and order book buy-walls.",
        "tags": ["#Altcoins", "#TradingSignals"]
    },
    {
        "type": "defi_onchain",
        "focus": "Decentralized finance volume shifts, Layer-2 ecosystem competition, DEX liquidity depth, and on-chain protocol yields.",
        "tags": ["#DeFi", "#Web3"]
    },
    {
        "type": "security_safety",
        "focus": "Practical crypto security, phishing/scam prevention, risk-reward management, leverage warnings, and capital preservation.",
        "tags": ["#CryptoSafety", "#BinanceSquare"]
    }
]

def fetch_market_and_news():
    """Gather live market data and Binance announcements simultaneously."""
    data_packet = {
        "lead_coins": ["BTC", "BNB"],
        "movers_summary": "$BTC, $BNB holding steady",
        "official_news": [],
        "has_news": False
    }

    # 1. Fetch 24h gainers
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=8)
        data = res.json()
        usdt_pairs = [
            d for d in data 
            if d.get("symbol", "").endswith("USDT") and float(d.get("quoteVolume", 0)) > 3000000
        ]
        top = sorted(usdt_pairs, key=lambda x: float(x.get("priceChangePercent", 0)), reverse=True)
        data_packet["lead_coins"] = [t["symbol"].replace("USDT", "") for t in top[:2]]
        data_packet["movers_summary"] = ", ".join(
            [f"{t['symbol'].replace('USDT','')}: {t['priceChangePercent']}%" for t in top[:5]]
        )
    except Exception as e:
        print(f"Ticker warning: {e}")

    # 2. Fetch latest official Binance announcements
    try:
        news_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageSize=6&pageNo=1"
        n_res = requests.get(news_url, timeout=8)
        catalogs = n_res.json().get("data", {}).get("catalogs", [])
        titles = []
        for cat in catalogs:
            for item in cat.get("articles", [])[:2]:
                titles.append(item.get("title", ""))
        if titles:
            data_packet["official_news"] = titles[:4]
            data_packet["has_news"] = True
    except Exception as e:
        print(f"News warning: {e}")

    return data_packet

def select_best_pillar(intel):
    """Dynamically prioritize news/events if available, otherwise rotate through analysis & discussions."""
    if intel["has_news"] and random.random() < 0.45:
        # Prioritize news/event slot when fresh announcements exist
        return CONTENT_PILLARS[0]
    
    # Otherwise, select freely from discussions, market trends, DeFi, or macro
    other_pillars = CONTENT_PILLARS[1:]
    return random.choice(other_pillars)

def generate_autonomous_post(intel, pillar):
    """Generate high-engagement post using Gemini with dynamic context."""
    if not GEMINI_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    
    client = genai.Client(api_key=GEMINI_KEY)
    
    coin1 = intel["lead_coins"][0]
    coin2 = intel["lead_coins"][1]
    news_text = " | ".join(intel["official_news"]) if intel["official_news"] else "No major platform announcements right now."

    prompt = f"""You are a top creator on Binance Square. You have complete creative freedom to write high-engagement Web3 content.

SELECTED TOPIC PILLAR: {pillar['type'].upper()}
EDITORIAL FOCUS: {pillar['focus']}

AVAILABLE REAL-TIME CONTEXT:
- Official Binance Updates / Events: {news_text}
- Live 24H Top Movers: {intel['movers_summary']}
- Primary Reference Tickers: ${coin1}, ${coin2}

CORE WRITING GUIDELINES:
1. Hook readers immediately with a bold, curiosity-inducing opening sentence.
2. Deliver unique insight, analysis, or news value based on the selected focus.
3. CASHTAG RULE (MANDATORY): You may prefix AT MOST TWO tokens with '$' (e.g. ${coin1} and ${coin2}). Mention any other tokens strictly as plain text (e.g., write Solana or Cake, NEVER $SOL or $CAKE).
4. HASHTAG RULE (MANDATORY): End the post with EXACTLY two hashtags: {' '.join(pillar['tags'])}.
5. End with an engaging open-ended question to maximize comment activity.
6. Target word count: 110 to 140 words. Output raw post text only, no headings, markdown fences, or preamble."""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text.strip()

def validate_and_sanitize(raw_text, pillar_tags):
    """Guarantee strict compliance with Binance Square constraints."""
    text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    text = re.sub(r"^```[a-zA-Z]*\n|```$", "", text).strip()
    
    # 1. Enforce max 2 cashtags
    cashtags = re.findall(r"\$[A-Za-z0-9]+", text)
    if len(cashtags) > 2:
        for extra in cashtags[2:]:
            text = text.replace(extra, extra[1:])
            
    # 2. Enforce exactly the 2 assigned pillar hashtags
    text = re.sub(r"#[A-Za-z0-9_]+", "", text).strip()
    text = f"{text}\n\n{' '.join(pillar_tags)}"
    
    # 3. Guard length limit
    if len(text) > 850:
        text = text[:850] + "..."
        
    return text

def post_to_binance_square(content):
    if not BINANCE_SQUARE_KEY:
        raise ValueError("BINANCE_SQUARE_API_KEY is not set.")
        
    headers = {
        "X-Square-OpenAPI-Key": BINANCE_SQUARE_KEY,
        "Content-Type": "application/json",
        "clienttype": "binanceSkill"
    }
    res = requests.post(SQUARE_API_URL, headers=headers, json={"bodyTextOnly": content}, timeout=15)
    print(f"Status: {res.status_code}, Body: {res.text}")

if __name__ == "__main__":
    print("[1/4] Gathering real-time market data & news...")
    intel = fetch_market_and_news()
    
    print("[2/4] Selecting optimal topic pillar...")
    pillar = select_best_pillar(intel)
    print(f"--> Chosen Pillar: {pillar['type'].upper()} ({pillar['focus'][:45]}...)")
    
    print("[3/4] Generating SEO-optimized post...")
    raw = generate_autonomous_post(intel, pillar)
    final_post = validate_and_sanitize(raw, pillar["tags"])
    
    print("--- Final Validated Post ---")
    print(final_post)
    print("----------------------------")
    
    print("[4/4] Submitting to Binance Square...")
    post_to_binance_square(final_post)
