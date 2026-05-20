import os
import sys
import pandas as pd
from datetime import datetime, timezone

DATA_PATH = "antigravity-dashboard/public/results"

def export_to_excel(date_str=None):
    if not date_str:
        # Default to today
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    csv_file = os.path.join(DATA_PATH, f"trend_template_results_{date_str}.csv")
    excel_file = os.path.join(DATA_PATH, f"trend_template_results_{date_str}.xlsx")
    
    if not os.path.exists(csv_file):
        # Look for the latest CSV in DATA_PATH if specified/today's doesn't exist
        files = [f for f in os.listdir(DATA_PATH) if f.startswith("trend_template_results_") and f.endswith(".csv")]
        if not files:
            print(f"Error: No CSV results found in {DATA_PATH}!")
            return
        
        # Sort to get the latest
        files.sort()
        csv_file = os.path.join(DATA_PATH, files[-1])
        date_str = files[-1].split("_")[-1].replace(".csv", "")
        excel_file = os.path.join(DATA_PATH, f"trend_template_results_{date_str}.xlsx")
        
    print(f"Reading CSV from {csv_file}...")
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            print("CSV is empty. Nothing to export.")
            return
            
        print(f"Exporting {len(df)} records to Excel: {excel_file}...")
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Analysis')
        print(f"Success! Created {excel_file}")
    except Exception as e:
        print(f"Error exporting to Excel: {e}")

if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    export_to_excel(target_date)
