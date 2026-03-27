import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# ================= UI =================
st.markdown("# 📊 AI TRADING DASHBOARD (PRO)")
st.markdown("Hybrid 12-Rule Intraday System")

stocks = ["TATASTEEL.NS","ITC.NS","WIPRO.NS","IDFC.NS","BANKBARODA.NS","ONGC.NS"]

# ================= DATA =================
def get_data(stock, period, interval):
    data = yf.download(stock, period=period, interval=interval)
    return data.dropna()

# ================= 12 RULE ENGINE =================
def analyze(data):
    if data is None or len(data) < 20:
        return 0, {}

    close = data['Close']
    open_ = data['Open']
    high = data['High']
    low = data['Low']
    volume = data['Volume']

    rules = {}

    try:
        rules["Trend"] = close.iloc[-1] > close.mean()
        rules["Momentum"] = close.iloc[-1] > close.iloc[-2]
        rules["Volume"] = volume.iloc[-1] > volume.mean()
        rules["Candle"] = close.iloc[-1] > open_.iloc[-1]
        rules["Breakout"] = close.iloc[-1] > high[:-1].max()
        rules["Breakdown"] = close.iloc[-1] < low[:-1].min()

        mid = (high.iloc[-1] + low.iloc[-1]) / 2
        rules["Buyer"] = close.iloc[-1] > mid

        rules["PrevHigh"] = close.iloc[-1] > high.iloc[-2]
        rules["PrevLow"] = close.iloc[-1] > low.iloc[-2]

        rules["Gap"] = open_.iloc[-1] > close.iloc[-2]

        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        rules["MA"] = ma5.iloc[-1] > ma10.iloc[-1]

    except:
        return 0, {}

    score = sum([1 if v else -1 for v in rules.values()])

    return score, rules

# ================= SIGNAL =================
def predict(score):
    if score >= 6:
        return "STRONG BUY"
    elif score >= 3:
        return "BUY"
    elif score <= -5:
        return "STRONG SELL"
    elif score <= -2:
        return "SELL"
    else:
        return "WAIT"

# ================= SESSION =================
def session_analysis(data):
    step = len(data)//4
    res = {}
    for i in range(4):
        part = data.iloc[i*step:(i+1)*step]
        if len(part) < 2:
            continue
        s = part['Close'].iloc[0]
        e = part['Close'].iloc[-1]
        res[f"S{i+1}"] = (round(s,2), round(e,2), "UP" if e>s else "DOWN")
    return res

# ================= BENCHMARK =================
def calc(df):
    return round(df['High'].max(),2), round(df['Low'].min(),2), round(df['Close'].mean(),2)

# ================= TIMEFRAME =================
tf = st.selectbox("Timeframe",["Today","3D","Weekly","Monthly","Yearly"])

if tf=="Today": period,interval="1d","5m"
elif tf=="3D": period,interval="3d","5m"
elif tf=="Weekly": period,interval="7d","15m"
elif tf=="Monthly": period,interval="1mo","30m"
else: period,interval="1y","1d"

# ================= MAIN =================
rows = []

for s in stocks:
    d = get_data(s,period,interval)
    if d.empty:
        continue

    score, _ = analyze(d)
    signal = predict(score)

    rows.append([s,signal,score])

df = pd.DataFrame(rows,columns=["Stock","Signal","Score"])
st.dataframe(df)

# ================= BEST =================
if not df.empty:
    best = df.sort_values("Score",ascending=False).iloc[0]
    st.success(f"BEST TRADE: {best['Stock']} → {best['Signal']}")

# ================= RULE =================
sel = st.selectbox("Select Stock",stocks)
d = get_data(sel,period,interval)

score, rules = analyze(d)

st.subheader("Rule Breakdown")
for k,v in rules.items():
    st.write(k, "🟢" if v else "🔴")

# ================= SESSION =================
st.subheader("Session Analysis")
today = yf.download(sel,period="1d",interval="5m")
sess = session_analysis(today)

for k,v in sess.items():
    st.write(k, v)

# ================= HISTORY =================
st.subheader("3 Day History")
d3 = yf.download(sel,period="3d",interval="30m")
d3['Date'] = d3.index.date

for dt,g in d3.groupby("Date"):
    s = session_analysis(g)
    st.write(dt, s)

# ================= BENCHMARK =================
st.subheader("Benchmark")

yr = yf.download(sel,period="1y")
w = yr.tail(5)
m = yr.tail(22)

wh,wl,wa = calc(w)
mh,ml,ma = calc(m)
yh,yl,ya = calc(yr)

st.write("Week:",wh,wl,wa)
st.write("Month:",mh,ml,ma)
st.write("52W:",yh,yl,ya)

# ================= FINAL SIGNAL =================
cp = yr['Close'].iloc[-1]

if cp > ma:
    st.success("UP")
else:
    st.error("DOWN")

# ================= CHART =================
fig = go.Figure(data=[go.Candlestick(
    x=d.index,
    open=d['Open'],
    high=d['High'],
    low=d['Low'],
    close=d['Close']
)])

st.plotly_chart(fig, use_container_width=True)
