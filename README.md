# Antigravity Stock Scanner

A full-stack application for scanning stocks using the Minervini Trend Template criteria.

## Project Structure
- `/antigravity-dashboard`: React frontend (Vite).
- `server.py`: Flask API server.
- `stock_engine.py`: Core logic for fetching data and scoring stocks.
- `tickers.json`: List of symbols to scan.

## Quick Start

### 1. Setup Backend
Create and activate a virtual environment:
```bash
# Create venv
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the server:
```bash
python server.py
```
The API will run at `http://127.0.0.1:5000`.

### 2. Setup Frontend
Navigate to the dashboard directory:
```bash
cd antigravity-dashboard
npm install
npm run dev
```
The UI will run at `http://localhost:5173`.

## Scan Configuration
Modify `tickers.json` to change the list of stocks being scanned. The engine uses `yfinance` to fetch 14 months of historical data for each ticker to calculate 50, 150, and 200-day SMAs.

## Results
Scanned results are saved to date-stamped files in the `results/` directory.
