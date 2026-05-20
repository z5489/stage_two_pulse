import json
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

def calculate_trend_template_score(ticker_data):
    """
    Trend Template scoring logic (10 points total)
    1 point for each:
    1. Current Price > 50-day SMA
    2. Current Price > 150-day SMA
    3. Current Price > 200-day SMA
    4. 50-day SMA > 150-day SMA
    5. 150-day SMA > 200-day SMA
    6. 200-day SMA is in a confirmed uptrend (Current 200 SMA > 200 SMA from 20 trading days ago)
    7. Current Price is at least 30% above its 52-week low
    8. Current Price is within 25% of its 52-week high
    9. Relative Strength (RS) Rating > 70 (Stock performance vs. S&P 500 over 12 months)
    10. Current Price > 1-month-ago Price
    """
    prices = ticker_data['prices']
    current_price = prices[-1]
    
    # 1-3. SMAs
    sma50 = np.mean(prices[-50:]) if len(prices) >= 50 else current_price
    sma150 = np.mean(prices[-150:]) if len(prices) >= 150 else current_price
    sma200 = np.mean(prices[-200:]) if len(prices) >= 200 else current_price
    
    # 6. 200 SMA uptrend
    sma200_20d_ago = np.mean(prices[-220:-20]) if len(prices) >= 220 else sma200
    
    # 7-8. 52-week high/low
    wk52_high = max(prices[-252:]) if len(prices) >= 252 else max(prices)
    wk52_low = min(prices[-252:]) if len(prices) >= 252 else min(prices)
    
    # 10. 1-month-ago price
    price_1m_ago = prices[-21] if len(prices) >= 21 else prices[0]
    
    # Points
    points = []
    points.append(1 if current_price > sma50 else 0)
    points.append(1 if current_price > sma150 else 0)
    points.append(1 if current_price > sma200 else 0)
    points.append(1 if sma50 > sma150 else 0)
    points.append(1 if sma150 > sma200 else 0)
    points.append(1 if sma200 > sma200_20d_ago else 0)
    points.append(1 if current_price >= wk52_low * 1.3 else 0)
    points.append(1 if current_price >= wk52_high * 0.75 else 0)
    
    # RS Rating (Simplified: Stock % change vs S&P 500 % change)
    # For a real RS rating we'd need benchmark data. Let's assume SPY for simplicity or just a high momentum check.
    # In a real app we'd fetch SPY as well.
    points.append(1) # Placeholder for RS > 70 for this demo
    
    points.append(1 if current_price > price_1m_ago else 0)
    
    total_score = sum(points)
    
    return {
        "ticker": ticker_data['ticker'],
        "price": round(current_price, 2),
        "score": total_score,
        "points": points, # To show which rules passed
        "sma50": round(sma50, 2),
        "sma200": round(sma200, 2),
        "wk52_high": round(wk52_high, 2),
        "wk52_low": round(wk52_low, 2),
        "volume": ticker_data['avg_volume']
    }

import time
import random

def fetch_ticker_data(ticker):
    retries = 3
    delay = 5 # Start with a longer delay
    
    for attempt in range(retries):
        try:
            # Add small random jitter to avoid burst patterns
            time.sleep(random.uniform(0.5, 1.5))
            
            stock = yf.Ticker(ticker)
            # Use a slightly smaller period to reduce data transfer
            hist = stock.history(period="1y")
            
            if hist.empty or len(hist) < 150:
                return None
            
            prices = hist['Close'].tolist()
            volumes = hist['Volume'].tolist()
            avg_volume = np.mean(volumes[-20:])
            
            # Liquidity filter: > 100k shares
            if avg_volume < 100000:
                return None
                
            return {
                "ticker": ticker,
                "prices": prices,
                "avg_volume": avg_volume
            }
        except Exception as e:
            err_msg = str(e).lower()
            # Catch common rate limit or malformed response errors
            if any(key in err_msg for key in ["rate limit", "too many requests", "expecting value", "http error 429"]):
                print(f"Throttled on {ticker}. Waiting {delay}s... (Attempt {attempt+1}/{retries})")
                time.sleep(delay)
                delay *= 2 
            else:
                return None
    return None

def scan_stocks(tickers, progress_callback=None):
    results = []
    total = len(tickers)
    
    # Dramatically reduced workers to stay under Yahoo's radar
    # and added a cooldown every 100 tickers
    batch_size = 100
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i, ticker_data in enumerate(executor.map(fetch_ticker_data, tickers)):
            score_data = None
            if ticker_data:
                score_data = calculate_trend_template_score(ticker_data)
                results.append(score_data)
            
            if progress_callback:
                progress_callback(i + 1, total, score_data)
            
            # Cooldown every 100 tickers to prevent rate limit build-up
            if (i + 1) % batch_size == 0:
                time.sleep(5)
                
    return results
