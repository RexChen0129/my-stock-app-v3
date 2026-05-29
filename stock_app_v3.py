import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime

# --- 配置 ---
st.set_page_config(layout="wide", page_title="專業台股分析系統")
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# 載入你原本的 205 檔股票清單
WATCHLIST = [
    {"name": "台積電", "id": "2330"}, {"name": "聯電", "id": "2303"}, {"name": "鴻海", "id": "2317"},
    {"name": "聯發科", "id": "2454"}, {"name": "台達電", "id": "2308"}, {"name": "廣達", "id": "2382"},
    # ... 請確保你原本的 205 檔資料都在這裡
]

# --- 資料處理函數 ---
@st.cache_data(ttl=3600)
def get_full_data(stock_id):
    url = "https://api.finmindtrade.com/api/v4/data"
    start = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 抓取股價
    res = requests.get(url, params={"dataset": "TaiwanStockPrice", "data_id": stock_id, "start_date": start, "token": FINMIND_TOKEN}, timeout=5)
    df = pd.DataFrame(res.json().get('data', []))
    if df.empty: return None
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 技術指標
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    # 簡化版 KD
    l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
    df['K'] = ((df['close'] - l9) / (h9 - l9) * 100).fillna(50).ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    # 簡化版 MACD
    df['DIF'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['MACD_h'] = (df['DIF'] - df['DIF'].ewm(span=9).mean()) * 2
    return df

# --- 介面路由 ---
if 'page' not in st.session_state: st.session_state.page = 0
if 'selected' not in st.session_state: st.session_state.selected = None

if st.session_state.selected:
    # --- 詳情頁 ---
    if st.button("◀ 返回"): st.session_state.selected = None; st.rerun()
    df = get_full_data(st.session_state.selected)
    if df is not None:
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.3, 0.1, 0.15, 0.15, 0.2])
        fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['max'], low=df['min'], close=df['close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Trading_Volume'], name='量'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], name='K'), row=4, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_h'], name='MACD'), row=5, col=1)
        fig.update_layout(height=900, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

else:
    # --- 首頁 ---
    st.title("📊 台股自選股大廳")
    search = st.text_input("🔍 搜尋代碼或名稱")
    pool = [s for s in WATCHLIST if search in s['id'] or search in s['name']] if search else WATCHLIST
    
    # 分頁邏輯
    total_pages = (len(pool) + 8) // 9
    stocks = pool[st.session_state.page*9 : (st.session_state.page+1)*9]
    
    # 渲染 3x3 網格
    for i in range(0, len(stocks), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i+j < len(stocks):
                s = stocks[i+j]
                if col.button(f"進入 {s['name']} ({s['id']})", key=s['id']):
                    st.session_state.selected = s['id']
                    st.rerun()
    
    # 頁碼
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ 上一頁"): st.session_state.page = max(0, st.session_state.page-1); st.rerun()
    c2.write(f"第 {st.session_state.page+1} / {total_pages} 頁")
    if c3.button("下一頁 ▶"): st.session_state.page = min(total_pages-1, st.session_state.page+1); st.rerun()
