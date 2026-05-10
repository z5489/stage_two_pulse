import yfinance as yf
import numpy as np
from stock_engine import calculate_minervini_score, fetch_ticker_data

def debug_ticker(ticker):
    print(f"--- Debugging {ticker} ---")
    try:
        stock = yf.Ticker(ticker)
        print(f"Ticker object created for {ticker}")
        
        hist = stock.history(period="14mo")
        print(f"History fetch result: {len(hist)} rows")
        
        if hist.empty:
            print("ERROR: History is empty.")
            return
            
        if len(hist) < 200:
            print(f"ERROR: Not enough data ({len(hist)} < 200 days).")
            return
            
        prices = hist['Close'].tolist()
        volumes = hist['Volume'].tolist()
        avg_volume = np.mean(volumes[-20:])
        print(f"Current Price: {prices[-1]}")
        print(f"Avg Volume (20d): {avg_volume}")
        
        if avg_volume < 100000:
            print(f"FILTERED: Avg volume {avg_volume} < 100,000")
            return
            
        ticker_data = {
            "ticker": ticker,
            "prices": prices,
            "avg_volume": avg_volume
        }
        
        score_data = calculate_minervini_score(ticker_data)
        print(f"Score: {score_data['score']}/10")
        print(f"Points detail: {score_data['points']}")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    debug_ticker("FSLR")
