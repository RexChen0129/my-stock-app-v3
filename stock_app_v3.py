import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime

# --- 1. 配置與設定 ---
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# 你的 205 檔股票清單 (建議直接使用你原本的完整清單定義)
WATCHLIST = [
    {"name": "台積電", "id": "2330"}, {"name": "聯電", "id": "2303"}, {"name": "鴻海", "id": "2317"},
    # ... (此處請確保貼上你原有的 205 檔清單)
]

# --- 2. 穩定的資料抓取函數 ---
@st.cache_data(ttl=3600)
def get_data(stock_id, days=730):
    """通用資料獲取函數，加入錯誤處理，避免程式崩潰"""
    url = "https://api.finmindtrade.com/api/v4/data"
    start = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    
    # 抓取股價
    res = requests.get(url, params={"dataset": "TaiwanStockPrice", "data_id": stock_id, "start_date": start, "token": FINMIND_TOKEN}, timeout=10)
    data = res.json().get('data', [])
    if not data: return None
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 簡單指標計算
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    
    # KD & MACD 計算 (與你需求一致)
    l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
    df['K'] = ((df['close'] - l9) / (h9 - l9) * 100).ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    ema12, ema26 = df['close'].ewm(span=12).mean(), df['close'].ewm(span=26).mean()
    df['MACD_h'] = (ema12 - ema26 - (ema12 - ema26).ewm(span=9).mean()) * 2
    
    return df

# --- 3. UI 邏輯 ---
st.set_page_config(layout="wide", page_title="專業台股系統")

if 'view' not in st.session_state: st.session_state.view = "list"
if 'stock_id' not in st.session_state: st.session_state.stock_id = None
if 'page' not in st.session_state: st.session_state.page = 0

if st.session_state.view == "list":
    st.title("📈 台股自選股大廳")
    search = st.text_input("🔍 搜尋名稱或代號", placeholder="例如: 2330 或 台積電")
    filtered = [s for s in WATCHLIST if search in s['id'] or search in s['name']] if search else WATCHLIST
    
    # 分頁控制
    page_size = 9
    total_pages = (len(filtered) + page_size - 1) // page_size
    start = st.session_state.page * page_size
    
    cols = st.columns(3)
    for i, stock in enumerate(filtered[start : start + page_size]):
        with cols[i % 3]:
            if st.button(f"{stock['name']} ({stock['id']})", key=stock['id']):
                st.session_state.stock_id = stock['id']
                st.session_state.view = "detail"
                st.rerun()

    # 翻頁按鈕
    c1, c2 = st.columns([1, 1])
    if c1.button("上一頁") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    if c2.button("下一頁") and st.session_state.page < total_pages - 1: st.session_state.page += 1; st.rerun()

else:
    # 詳情頁
    if st.button("◀ 返回列表"): st.session_state.view = "list"; st.rerun()
    df = get_data(st.session_state.stock_id)
    
    if df is not None:
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.3, 0.1, 0.15, 0.15, 0.2])
        fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['max'], low=df['min'], close=df['close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Trading_Volume'], name='成交量'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], name='K'), row=4, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_h'], name='MACD'), row=5, col=1)
        fig.update_layout(height=1000, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("暫無該股票資料")
