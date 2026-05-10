import os
import io
import json
import time
import threading
import pandas as pd
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from stock_engine import scan_stocks

app = Flask(__name__)
CORS(app)

DATA_PATH = "results"
os.makedirs(DATA_PATH, exist_ok=True)

state = {
    "data": [],
    "progress": 0,
    "total": 0,
    "status": "idle"
}

def resolve_target_date():
    now = datetime.now(timezone.utc)
    if now.weekday() < 5 and now.hour >= 22:
        return now.strftime("%Y-%m-%d")
    
    offset = {0: 3, 6: 2}.get(now.weekday(), 1)
    return (now - timedelta(days=offset)).strftime("%Y-%m-%d")

def get_archive_path(date_str):
    return os.path.join(DATA_PATH, f"trend_template_results_{date_str}.csv")

def execute_market_scan():
    global state
    tickers = []
    if os.path.exists("tickers.json"):
        with open("tickers.json", "r") as f:
            tickers = json.load(f)
    
    state.update({"status": "scanning", "progress": 0, "total": len(tickers), "data": []})
    
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = get_archive_path(stamp)
    if os.path.exists(path):
        os.remove(path)
    
    def on_step(curr, total, item=None):
        state["progress"] = curr
        if item:
            state["data"].append(item)
            df = pd.DataFrame([item])
            if 'points' in df.columns:
                df['points'] = df['points'].apply(str)
            df.to_csv(path, mode='a', index=False, header=not os.path.exists(path))
        
    scan_stocks(tickers, progress_callback=on_step)
    state["status"] = "complete"

@app.route('/api/scan', methods=['POST'])
def start_scan():
    if state["status"] == "scanning":
        return jsonify({"error": "Active scan in progress"}), 400
    threading.Thread(target=execute_market_scan).start()
    return jsonify({"status": "initiated"})

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(state)

@app.route('/api/load_csv', methods=['POST'])
@app.route('/api/load_trend_template', methods=['GET', 'POST'])
def load_archive():
    global state
    # Handle both POST JSON and GET query parameters
    date_val = None
    if request.is_json:
        date_val = request.json.get('date')
    if not date_val:
        date_val = request.args.get('date')
    if not date_val:
        date_val = resolve_target_date()
        
    path = get_archive_path(date_val)
    
    if not os.path.exists(path):
        return jsonify({
            "error": "Archive not found",
            "date": date_val,
            "is_future": date_val == datetime.now(timezone.utc).strftime("%Y-%m-%d")
        }), 404
    
    try:
        df = pd.read_csv(path)
        if 'points' in df.columns:
            import ast
            df['points'] = df['points'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
            
        state.update({
            "data": df.to_dict(orient='records'),
            "status": "complete",
            "progress": len(df),
            "total": len(df)
        })
        return jsonify({"status": "loaded", "data": state["data"], "date": date_val, "count": len(df)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def list_history():
    files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv")]
    dates = sorted([f.split('_')[-1].split('.')[0] for f in files], reverse=True)
    return jsonify({"dates": dates})

@app.route('/api/current_config', methods=['GET'])
def fetch_config():
    now = datetime.now(timezone.utc)
    return jsonify({
        "target_date": resolve_target_date(),
        "today": now.strftime("%Y-%m-%d"),
        "gmt_hour": now.hour
    })

@app.route('/api/export', methods=['GET'])
def download_excel():
    if not state["data"]:
        return jsonify({"error": "Empty dataset"}), 400
    
    df = pd.DataFrame(state["data"])
    if 'points' in df.columns:
        df['points'] = df['points'].apply(str)
        
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Analysis')
    buf.seek(0)
    
    return send_file(buf, as_attachment=True, download_name=f"export_{int(time.time())}.xlsx")

if __name__ == '__main__':
    app.run(port=5000)
