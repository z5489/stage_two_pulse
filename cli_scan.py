import os
import json
import pandas as pd
from datetime import datetime, timezone
from stock_engine import scan_stocks

def run_job():
    os.makedirs("antigravity-dashboard/public/results", exist_ok=True)
    
    symbols = []
    if os.path.exists("tickers.json"):
        with open("tickers.json", "r") as f:
            symbols = json.load(f)
    
    buffer = []
    
    def handle_step(curr, total, item=None):
        if item:
            buffer.append(item)
            if curr % 20 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed {curr}/{total}")

    print(f"Initialising market scan for {len(symbols)} tickers...")
    scan_stocks(symbols, progress_callback=handle_step)
    
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output = os.path.join("antigravity-dashboard/public/results", f"trend_template_results_{stamp}.csv")
    
    df = pd.DataFrame(buffer)
    if 'points' in df.columns:
        df['points'] = df['points'].apply(str)
    
    df.to_csv(output, index=False)
    
    # Generate history.json for serverless discovery
    files = [f for f in os.listdir(DATA_PATH) if f.endswith('.csv')]
    dates = sorted([f.split('_')[-1].replace('.csv', '') for f in files], reverse=True)
    with open(os.path.join(DATA_PATH, 'history.json'), 'w') as f:
        json.dump({"dates": dates}, f)
        
    print(f"Sync completed: {output} ({len(buffer)} records)")
    print(f"History updated: {len(dates)} dates indexed")

if __name__ == "__main__":
    run_job()
