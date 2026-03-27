import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

stocks = ["TATASTEEL.NS","ITC.NS","WIPRO.NS","IDFC.NS","BANKBARODA.NS","ONGC.NS"]

# ===================== DATA =====================
def get_data(stock, period, interval):
    return yf.download(stock, period=period, interval=interval)

# ===================== 12 RULE ENGINE =====================
def analyze(data):
    score = 0
    rules = {}
    
    close = data['Close']
    open_ = data['Open']
    high = data['High']
    low = data['Low']
    volume = data['Volume']
    
    # 1 Trend
    rules["Trend"] = close.iloc[-1] > close.mean()
    score += 1 if rules["Trend"] else -1
    
    # 2 Momentum
    rules["Momentum"] = close.iloc[-1] > close.iloc[-2]
    score += 1 if rules["Momentum"] else -1
    
    # 3 Volume
    rules["Volume"] = volume.iloc[-1] > volume.mean()
    score += 1 if rules["Volume"] else 0
    
    # 4 Candle
    rules["Candle"] = close.iloc[-1] > open_.iloc[-1]
    score += 1 if rules["Candle"] else -1
    
    # 5 Breakout
    rules["Breakout"] = close.iloc[-1] > high[:-1].max()
    score += 2 if rules["Breakout"] else 0
    
    # 6 Breakdown
    rules["Breakdown"] = close.iloc[-1] < low[:-1].min()
    score -= 2 if rules["Breakdown"] else 0
    
    # 7 Volatility
    rules["Volatility"] = (high.iloc[-1]-low.iloc[-1]) > (high.mean()-low.mean())
    score += 1 if rules["Volatility"] else 0
    
    # 8 Buyer vs Seller
    mid = (high.iloc[-1] + low.iloc[-1]) / 2
    rules["BuyerStrength"] = close.iloc[-1] > mid
    score += 1 if rules["BuyerStrength"] else -1
    
    # 9 Prev High
    rules["PrevHigh"] = close.iloc[-1] > high.iloc[-2]
    score += 1 if rules["PrevHigh"] else -1
    
    # 10 Prev Low
    rules["PrevLow"] = close.iloc[-1] > low.iloc[-2]
    score += 1 if rules["PrevLow"] else -1
    
    # 11 Gap
    rules["GapUp"] = open_.iloc[-1] > close.iloc[-2]
    score += 1 if rules["GapUp"] else 0
    
    # 12 MA Cross
    ma5 = close.rolling(5).mean()
    ma10 = close.rolling(10).mean()
    rules["MA Cross"] = ma5.iloc[-1] > ma10.iloc[-1]
    score += 1 if rules["MA Cross"] else -1
    
    return score, rules

# ===================== PREDICT =====================
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

# ===================== CONFIDENCE =====================
def confidence(score):
    return min(100, abs(score)*10)

# ===================== SESSION =====================
def session_analysis(data):
    step = len(data)//4
    parts = [data.iloc[i*step:(i+1)*step] for i in range(4)]
    
    result = {}
    for i, df in enumerate(parts):
        if len(df) < 2: continue
        s = df['Close'].iloc[0]
        e = df['Close'].iloc[-1]
        d = "UP" if e>s else "DOWN"
        result[f"S{i+1}"] = (round(s,2),round(e,2),d)
    
    return result

# ===================== BENCHMARK =====================
def calc(df):
    return round(df['High'].max(),2), round(df['Low'].min(),2), round(df['Close'].mean(),2)

# ===================== TIMEFRAME =====================
tf = st.selectbox("Timeframe",["Today","3 Days","Weekly","Monthly","Yearly"])

if tf=="Today": period,interval="1d","5m"
elif tf=="3 Days": period,interval="3d","5m"
elif tf=="Weekly": period,interval="7d","15m"
elif tf=="Monthly": period,interval="1mo","30m"
else: period,interval="1y","1d"

st.title("📊 AI TRADING DASHBOARD (PRO)")

# ===================== MAIN =====================
rows=[]

for s in stocks:
    d=get_data(s,period,interval)
    if len(d)<10: continue
    
    sc, rules = analyze(d)
    sig = predict(sc)
    conf = confidence(sc)
    
    rows.append([s,sig,sc,conf])

df=pd.DataFrame(rows,columns=["Stock","Signal","Score","Confidence %"])

st.dataframe(df,use_container_width=True)

# ===================== BEST =====================
best=df.sort_values("Score",ascending=False).iloc[0]

st.markdown(f"""
## 🔥 BEST TRADE
{best['Stock']} | {best['Signal']} | Confidence: {best['Confidence %']}%
""")

# ===================== RULE BREAKDOWN =====================
st.markdown("## 🧠 RULE BREAKDOWN")

sel=st.selectbox("Select Stock",stocks)

d=get_data(sel,period,interval)
sc,rules=analyze(d)

for k,v in rules.items():
    st.write(f"{k}: {'🟢' if v else '🔴'}")

# ===================== SESSION =====================
st.markdown("## 📊 SESSION")

today=yf.download(sel,period="1d",interval="5m")
sess=session_analysis(today)

for k,v in sess.items():
    st.write(f"{k}: {v[0]} → {v[1]} ({'🟢' if v[2]=='UP' else '🔴'} {v[2]})")

# ===================== HISTORY =====================
st.markdown("## 📅 3 DAY HISTORY")

d3=yf.download(sel,period="3d",interval="30m")
d3['Date']=d3.index.date

for dt,g in d3.groupby("Date"):
    s=session_analysis(g)
    line=f"{dt}: "
    for k,v in s.items():
        line+=f"{k}:{v[0]}-{v[1]} | "
    st.text(line)

# ===================== BENCHMARK =====================
st.markdown("## 📊 BENCHMARK")

yr=yf.download(sel,period="1y",interval="1d")

w=yr.tail(5)
m=yr.tail(22)

wh,wl,wa=calc(w)
mh,ml,ma=calc(m)
yh,yl,ya=calc(yr)

st.markdown(f"""
WEEK: {wh}/{wl} Avg:{wa}  
MONTH: {mh}/{ml} Avg:{ma}  
52W: {yh}/{yl} Avg:{ya}
""")

# ===================== PRED =====================
st.markdown("## 💡 FINAL SIGNAL")

cp=yr['Close'].iloc[-1]

if cp>ma and cp>wa:
    st.success("🔥 STRONG UP")
elif cp>ma:
    st.info("🟢 UP")
elif cp<ma and cp<wa:
    st.error("🔻 STRONG DOWN")
else:
    st.warning("⚠️ SIDEWAYS")

# ===================== CHART =====================
st.markdown("## 📊 CHART")

fig=go.Figure(data=[go.Candlestick(
    x=d.index,
    open=d['Open'],
    high=d['High'],
    low=d['Low'],
    close=d['Close']
)])

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)
