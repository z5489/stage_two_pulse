import os
import sys
import json
import pandas as pd
from datetime import datetime, timezone
from stock_engine import scan_stocks

DATA_PATH = "antigravity-dashboard/public/results"

def run_job():
    os.makedirs(DATA_PATH, exist_ok=True)
    
    # Allow passing a specific ticker file name as command line argument
    ticker_file = "tickers.json"
    if len(sys.argv) > 1:
        ticker_file = sys.argv[1]
        
    print(f"Reading tickers from {ticker_file}...")
    symbols = []
    if os.path.exists(ticker_file):
        with open(ticker_file, "r") as f:
            symbols = json.load(f)
    else:
        print(f"Error: {ticker_file} not found!")
        return
    
    buffer = []
    
    def handle_step(curr, total, item=None):
        if item:
            buffer.append(item)
        if curr % 20 == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed {curr}/{total}")

    print(f"Initialising market scan for {len(symbols)} tickers...")
    scan_stocks(symbols, progress_callback=handle_step)
    
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output = os.path.join(DATA_PATH, f"trend_template_results_{stamp}.csv")
    
    df = pd.DataFrame(buffer)
    if not df.empty and 'points' in df.columns:
        df['points'] = df['points'].apply(str)
        
    # Robust Append Logic: Load existing results for the day, merge, and deduplicate
    if os.path.exists(output):
        try:
            existing_df = pd.read_csv(output)
            if not df.empty:
                df = pd.concat([existing_df, df], ignore_index=True)
                df = df.drop_duplicates(subset=['ticker'], keep='last')
            else:
                df = existing_df
            print(f"Merged with existing file. Total records in dataset: {len(df)}")
        except Exception as e:
            print(f"Error reading existing CSV {output}: {e}. Keeping current scan results only.")
            
    if not df.empty:
        df.to_csv(output, index=False)
    else:
        print("No records to save.")
    
    # Generate history.json for serverless discovery
    files = [f for f in os.listdir(DATA_PATH) if f.endswith('.csv')]
    dates = sorted([f.split('_')[-1].replace('.csv', '') for f in files], reverse=True)
    with open(os.path.join(DATA_PATH, 'history.json'), 'w') as f:
        json.dump({"dates": dates}, f)
        
    print(f"Sync completed: {output} ({len(df) if not df.empty else 0} total records)")
    print(f"History updated: {len(dates)} dates indexed")

if __name__ == "__main__":
    run_job()

