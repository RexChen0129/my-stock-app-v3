import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

# --- 1. 配置與清單 ---
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# 載入您的 205 檔股票清單 (請確認此處清單完整)
WATCHLIST = [
    {"name": "台積電", "id": "2330"}, {"name": "聯電", "id": "2303"}, {"name": "鴻海", "id": "2317"},
    {"name": "聯發科", "id": "2454"}, {"name": "台達電", "id": "2308"}, {"name": "廣達", "id": "2382"},
    # ... (請保留你原有的完整 205 檔清單)
]

# --- 2. 高效資料函數 ---
def fetch_data(dataset, stock_id, start_date):
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": dataset, "data_id": stock_id, "start_date": start_date, "token": FINMIND_TOKEN}
    try:
        res = requests.get(url, params=params, timeout=10).json()
        return pd.DataFrame(res.get('data', []))
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_detail_data(stock_id):
    start = (datetime.date.today() - datetime.timedelta(days=730)).strftime("%Y-%m-%d")
    df = fetch_data("TaiwanStockPrice", stock_id, start)
    df_inst = fetch_data("InstitutionalInvestorsBuySell", stock_id, start)
    
    if df.empty: return None
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 計算五大指標
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    
    # KD
    l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
    df['K'] = ((df['close'] - l9) / (h9 - l9) * 100).ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    # MACD
    ema12, ema26 = df['close'].ewm(span=12).mean(), df['close'].ewm(span=26).mean()
    df['DIF'] = ema12 - ema26
    df['DEA'] = df['DIF'].ewm(span=9).mean()
    df['MACD_h'] = (df['DIF'] - df['DEA']) * 2
    
    # 法人籌碼
    if not df_inst.empty:
        df_inst['date'] = pd.to_datetime(df_inst['date'])
        df_inst = df_inst.groupby('date')[['buy', 'sell']].sum()
        df['Inst_Net'] = (df_inst['buy'] - df_inst['sell']).fillna(0)
    else: df['Inst_Net'] = 0
    
    return df

# --- 3. UI 介面 ---
st.set_page_config(layout="wide", page_title="台股控盤系統")

if 'selected_stock' not in st.session_state: st.session_state.selected_stock = None
if 'page' not in st.session_state: st.session_state.page = 0

if st.session_state.selected_stock:
    # 詳情頁
    if st.button("◀ 返回列表"): 
        st.session_state.selected_stock = None
        st.rerun()
    
    df = get_detail_data(st.session_state.selected_stock)
    if df is not None:
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.3, 0.1, 0.2, 0.2, 0.2])
        fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['max'], low=df['min'], close=df['close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Trading_Volume'], name='成交量'), row=2, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Inst_Net'], name='法人'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], name='K'), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['D'], name='D'), row=4, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_h'], name='MACD'), row=5, col=1)
        fig.update_layout(height=1000, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
else:
    # 首頁列表
    st.title("📈 台股自選股大廳")
    search = st.text_input("🔍 搜尋股票名稱或代號")
    data = [i for i in WATCHLIST if search in i['id'] or search in i['name']] if search else WATCHLIST
    
    pages = (len(data) + 8) // 9
    cols = st.columns(3)
    for i, stock in enumerate(data[st.session_state.page*9 : (st.session_state.page+1)*9]):
        with cols[i%3]:
            if st.button(f"{stock['name']} ({stock['id']})"):
                st.session_state.selected_stock = stock['id']
                st.rerun()
    
    if st.button("下一頁"): st.session_state.page = (st.session_state.page + 1) % pages
    st.write(f"第 {st.session_state.page + 1} 頁")
