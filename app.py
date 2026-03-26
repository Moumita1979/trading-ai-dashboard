import streamlit as st
import yfinance as yf
import pandas as pd
import time
import matplotlib.pyplot as plt
import pyttsx3
import requests
import os, sys

# ===== AUTO UPDATE =====
def auto_update():
    try:
        os.system("pip install --upgrade yfinance pandas streamlit matplotlib pyttsx3")
    except:
        pass

# ===== INTERNET CHECK =====
def check_net():
    try:
        requests.get("https://google.com", timeout=3)
        return True
    except:
        return False

# ===== RETRY FETCH =====
def fetch(stock):
    for _ in range(5):
        try:
            data = yf.download(stock, period="5d", interval="5m", progress=False)
            if not data.empty:
                return data
        except:
            pass
        time.sleep(2)
    return None

# ===== ERROR LOG =====
def log_error(e):
    with open("error_log.txt", "a") as f:
        f.write(str(e)+"\n")

# ===== RESTART =====
def restart():
    os.execv(sys.executable, ['python'] + sys.argv)

# ===== SAFE VALUE =====
def val(x):
    try: return float(x)
    except: return float(x.iloc[0]) if hasattr(x,"iloc") else 0

# ===== ANALYSIS =====
def analyze(d):
    c,h,l,o,v = d['Close'],d['High'],d['Low'],d['Open'],d['Volume']
    s=0
    if c.iloc[-1]>val(c.mean()): s+=1
    if c.iloc[-1]>c.iloc[-2]: s+=1
    if v.iloc[-1]>val(v.mean()): s+=1
    if c.iloc[-1]>o.iloc[-1]: s+=1
    if c.iloc[-1]>val(h.max()): s+=2
    if c.iloc[-1]<val(l.min()): s-=2
    return s

# ===== PREDICT =====
def predict(s):
    return "BUY 🟢" if s>=5 else "SELL 🔴" if s<=-3 else "WAIT 🟡"

# ===== MOVEMENT =====
def movement(d):
    return "GOOD 💰" if abs(d['Close'].iloc[-1]-d['Close'].iloc[-2])>=2 else "LOW ⚠️"

# ===== TRAP =====
def trap(d):
    if d['Volume'].iloc[-1] < val(d['Volume'].mean()):
        return "⚠️ LOW VOL"
    return "OK"

# ===== SR =====
def sr(d):
    return round(d['Low'].tail(20).min(),2), round(d['High'].tail(20).max(),2)

# ===== TRADE PLAN =====
def plan(d,sup,res):
    p=d['Close'].iloc[-1]
    if p<=sup*1.01: return "BUY",p,p-1,p+2
    if p>=res*0.99: return "SELL",p,p+1,p-2
    return "WAIT",None,None,None

# ===== SESSION =====
def session(d):
    out=[]
    n=len(d)//4
    for i in range(4):
        seg=d.iloc[i*n:(i+1)*n]
        if len(seg)<2: continue
        a,b=seg['Close'].iloc[0],seg['Close'].iloc[-1]
        out.append((f"S{i+1}",a,b,"🟢" if b>a else "🔴"))
    return out

# ===== START =====
auto_update()

stocks=["TATASTEEL.NS","ITC.NS","WIPRO.NS","IDFC.NS","BANKBARODA.NS","ONGC.NS"]

st.set_page_config(layout="wide")
st.title("📊 PRO TRADING DASHBOARD")

if not check_net():
    st.warning("No Internet...")
    time.sleep(5)
    st.rerun()

res=[]
best=None;bs=-999;bd=None

for s in stocks:
    try:
        d=fetch(s)
        if d is None or len(d)<10: continue
        sc=analyze(d)
        res.append((s,predict(sc),sc,movement(d),trap(d)))
        if sc>bs:
            bs=sc;best=s;bd=d
    except Exception as e:
        log_error(e)

df=pd.DataFrame(res,columns=["Stock","Signal","Score","Move","Trap"])
st.dataframe(df,use_container_width=True)

if bd is not None:
    st.subheader(f"🔥 {best}")
    sup,resi=sr(bd)
    act,en,sl,tg=plan(bd,sup,resi)

    st.write(f"Support: {sup} | Resistance: {resi}")
    st.write(f"Action: {act}")

    if en:
        st.write(f"Entry: {en} SL: {sl} Target: {tg}")

    fig,ax=plt.subplots()
    ax.plot(bd['Close'])
    ax.axhline(sup,color='green')
    ax.axhline(resi,color='red')
    if en: ax.scatter(len(bd)-1,en,color='blue')
    st.pyplot(fig)

    st.subheader("Sessions")
    for s in session(bd):
        st.write(s)

st.write("Refreshing 30 sec...")
time.sleep(30)
st.rerun()