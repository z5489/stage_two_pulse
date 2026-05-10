import yfinance as yf
ticker = "FSLR"
stock = yf.Ticker(ticker)
hist = stock.history(period="14mo")
print(f"Ticker: {ticker}")
print(f"History length: {len(hist)}")
if not hist.empty:
    print(f"Last close: {hist['Close'].iloc[-1]}")
    print(f"Volume: {hist['Volume'].iloc[-1]}")
else:
    print("History is empty")
