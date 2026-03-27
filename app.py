import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# ===================== DARK THEME =====================
st.markdown("""
<style>
body {background-color:#0e1117;color:white;}
.block-container {padding-top:1rem;}
</style>
""", unsafe_allow_html=True)

# ===================== STOCK LIST =====================
stocks = ["TATASTEEL.NS","ITC.NS","WIPRO.NS","IDFC.NS","BANKBARODA.NS","ONGC.NS"]

# ===================== DATA =====================
def get_data(stock, period, interval):
    return yf.download(stock, period=period, interval=interval)

# ===================== 12 RULE ENGINE =====================
def analyze(data):
    score = 0
    rules = {}

    if len(data) < 20:
        return 0, {}

    close = data['Close']
    open_ = data['Open']
    high = data['High']
    low = data['Low']
    volume = data['Volume']

    trend = close.iloc[-1] > close.mean()
    momentum = close.iloc[-1] > close.iloc[-2]
    vol = volume.iloc[-1] > volume.mean()
    candle = close.iloc[-1] > open_.iloc[-1]
    breakout = close.iloc[-1] > high[:-1].max()
    breakdown = close.iloc[-1] < low[:-1].min()
    volat = (high.iloc[-1]-low.iloc[-1]) > (high.mean()-low.mean())
    mid = (high.iloc[-1]+low.iloc[-1])/2
    buyer = close.iloc[-1] > mid
    prev_high = close.iloc[-1] > high.iloc[-2]
    prev_low = close.iloc[-1] > low.iloc[-2]
    gap = open_.iloc[-1] > close.iloc[-2]

    ma5 = close.rolling(5).mean()
    ma10 = close.rolling(10).mean()
    ma_cross = ma5.iloc[-1] > ma10.iloc[-1]

    rules = {
        "Trend": trend,
        "Momentum": momentum,
        "Volume": vol,
        "Candle": candle,
        "Breakout": breakout,
        "Breakdown": breakdown,
        "Volatility": volat,
        "Buyer": buyer,
        "PrevHigh": prev_high,
        "PrevLow": prev_low,
        "GapUp": gap,
        "MA Cross": ma_cross
    }

    for k, v in rules.items():
        if v:
            score += 1
        else:
            score -= 1

    return score, rules

# ===================== SIGNAL =====================
def predict(score):
    if score >= 7:
        return "🔥 STRONG BUY"
    elif score >= 4:
        return "🟢 BUY"
    elif score <= -5:
        return "🔻 STRONG SELL"
    elif score <= -2:
        return "🔴 SELL"
    else:
        return "⚠️ WAIT"

def confidence(score):
    return min(100, abs(score)*10)

# ===================== SESSION =====================
def session_analysis(data):
    step = len(data)//4
    result = {}
    for i in range(4):
        df = data.iloc[i*step:(i+1)*step]
        if len(df) < 2: continue
        s = df['Close'].iloc[0]
        e = df['Close'].iloc[-1]
        d = "UP" if e > s else "DOWN"
        result[f"S{i+1}"] = (round(s,2), round(e,2), d)
    return result

# ===================== BENCHMARK =====================
def calc(df):
    return round(df['High'].max(),2), round(df['Low'].min(),2), round(df['Close'].mean(),2)

# ===================== HEADER =====================
st.markdown("# 📊 AI TRADING TERMINAL")
st.markdown("### ⚡ Hybrid Intraday Signal Engine")

# ===================== TIMEFRAME =====================
tf = st.selectbox("Timeframe",["Today","3 Days","Weekly","Monthly","Yearly"])

if tf=="Today": period,interval="1d","5m"
elif tf=="3 Days": period,interval="3d","5m"
elif tf=="Weekly": period,interval="7d","15m"
elif tf=="Monthly": period,interval="1mo","30m"
else: period,interval="1y","1d"

# ===================== MAIN =====================
rows=[]

for s in stocks:
    d = get_data(s,period,interval)
    if d.empty: continue

    sc, rules = analyze(d)
    sig = predict(sc)
    conf = confidence(sc)

    rows.append([s,sig,sc,conf])

df = pd.DataFrame(rows,columns=["Stock","Signal","Score","Confidence"])

# ===================== BEST TRADE CARD =====================
best = df.sort_values("Score",ascending=False).iloc[0]

color = "#00ff99" if "BUY" in best['Signal'] else "#ff4d4d"

st.markdown(f"""
<div style='background:#1c1f26;padding:20px;border-radius:12px;
border-left:6px solid {color};margin-bottom:15px;'>
<h2>🔥 BEST TRADE: {best['Stock']}</h2>
<h3>{best['Signal']}</h3>
<h4>Confidence: {best['Confidence']}%</h4>
</div>
""", unsafe_allow_html=True)

# ===================== TABLE =====================
def color_signal(val):
    if "BUY" in val:
        return "background-color:#003300;color:#00ff00"
    elif "SELL" in val:
        return "background-color:#330000;color:#ff4d4d"
    else:
        return "background-color:#333300;color:#ffff66"

st.dataframe(df.style.applymap(color_signal,subset=["Signal"]), use_container_width=True)

st.markdown("---")

# ===================== RULE BREAKDOWN =====================
st.markdown("## 🧠 RULE ENGINE")

sel = st.selectbox("Select Stock",stocks)
d = get_data(sel,period,interval)
sc, rules = analyze(d)

cols = st.columns(4)
i = 0
for k,v in rules.items():
    cols[i%4].markdown(f"{k}: {'🟢' if v else '🔴'}")
    i+=1

st.markdown("---")

# ===================== SESSION =====================
st.markdown("## 📊 SESSION")

today = yf.download(sel,period="1d",interval="5m")
sess = session_analysis(today)

for k,v in sess.items():
    color = "#00ff00" if v[2]=="UP" else "#ff4d4d"
    st.markdown(f"<div style='padding:8px;background:#1c1f26;margin:4px;border-radius:6px;'>{k}: {v[0]} → {v[1]} <span style='color:{color}'>{v[2]}</span></div>", unsafe_allow_html=True)

st.markdown("---")

# ===================== BENCHMARK =====================
st.markdown("## 📊 BENCHMARK")

yr = yf.download(sel,period="1y",interval="1d")
w = yr.tail(5)
m = yr.tail(22)

wh,wl,wa = calc(w)
mh,ml,ma = calc(m)
yh,yl,ya = calc(yr)

st.markdown(f"""
WEEK: {wh}/{wl} Avg:{wa}  
MONTH: {mh}/{ml} Avg:{ma}  
52W: {yh}/{yl} Avg:{ya}
""")

st.markdown("---")

# ===================== FINAL SIGNAL =====================
st.markdown("## 💡 FINAL SIGNAL")

cp = yr['Close'].iloc[-1]

if cp>ma and cp>wa:
    st.success("🔥 STRONG UP")
elif cp>ma:
    st.info("🟢 UP")
elif cp<ma and cp<wa:
    st.error("🔻 STRONG DOWN")
else:
    st.warning("⚠️ SIDEWAYS")

st.markdown("---")

# ===================== CHART =====================
st.markdown("## 📊 LIVE CHART")

fig = go.Figure(data=[go.Candlestick(
    x=d.index,
    open=d['Open'],
    high=d['High'],
    low=d['Low'],
    close=d['Close']
)])

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig, use_container_width=True)
