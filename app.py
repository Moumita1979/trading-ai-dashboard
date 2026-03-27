import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 AI Trading Dashboard (PRO)")

stocks = ["TATASTEEL.NS", "ITC.NS", "WIPRO.NS", "ONGC.NS"]

def get_data(stock):
    return yf.download(stock, period="1d", interval="5m").dropna()

def _to_bool(val):
    try:
        return bool(val)
    except Exception:
        if hasattr(val, "iloc"):
            return bool(val.iloc[-1])
        if hasattr(val, "__len__") and len(val) > 0:
            return bool(val[-1])
        return False

def analyze(data):
    if data is None or len(data) < 10:
        return 0, {}

    close = data["Close"]
    open_ = data["Open"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    rules = {}
    try:
        rules["Trend"] = _to_bool(close.iloc[-1] > close.mean())
        rules["Momentum"] = _to_bool(close.iloc[-1] > close.iloc[-2])
        rules["Volume"] = _to_bool(volume.iloc[-1] > volume.mean())
        rules["Candle"] = _to_bool(close.iloc[-1] > open_.iloc[-1])
        rules["Breakout"] = _to_bool(close.iloc[-1] > high[:-1].max())
        rules["Buyer"] = _to_bool(close.iloc[-1] > (high.iloc[-1] + low.iloc[-1]) / 2)
    except Exception:
        return 0, {}

    score = sum([1 if v else -1 for v in rules.values()])
    return score, rules

def signal(score):
    if score >= 3:
        return "BUY"
    elif score <= -3:
        return "SELL"
    else:
        return "WAIT"

# MAIN
results = []
for s in stocks:
    d = get_data(s)
    sc, rules = analyze(d)
    sig = signal(sc)
    results.append([s, sig, sc])

df = pd.DataFrame(results, columns=["Stock", "Signal", "Score"])
st.dataframe(df)

if not df.empty:
    best = df.sort_values("Score", ascending=False).iloc[0]
    st.success(f"Best Trade: {best['Stock']} → {best['Signal']}")