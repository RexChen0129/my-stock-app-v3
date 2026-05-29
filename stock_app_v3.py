import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime

# --- 1. 配置 ---
st.set_page_config(layout="wide", page_title="台股控盤系統")
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# 確保這裡放入你完整的 205 檔清單
WATCHLIST = [{"name": "台積電", "id": "2330"}, {"name": "聯電", "id": "2303"}, {"name": "鴻海", "id": "2317"}] 

# --- 2. 資料獲取與計算 (穩定版) ---
@st.cache_data(ttl=3600)
def get_full_analysis(stock_id):
    """抓取詳情頁需要的完整五指標數據"""
    url = "https://api.finmindtrade.com/api/v4/data"
    start = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 抓取股價
    res = requests.get(url, params={"dataset": "TaiwanStockPrice", "data_id": stock_id, "start_date": start, "token": FINMIND_TOKEN})
    df = pd.DataFrame(res.json().get('data', []))
    if df.empty: return None
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 1. K線 + 三條 MA
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    
    # 4. MACD & 5. KD
    l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
    df['K'] = ((df['close'] - l9) / (h9 - l9) * 100).fillna(50).ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    df['DIF'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['MACD_h'] = (df['DIF'] - df['DIF'].ewm(span=9).mean()) * 2
    
    # 3. 法人買賣超 (需另外抓取)
    res_inst = requests.get(url, params={"dataset": "InstitutionalInvestorsBuySell", "data_id": stock_id, "start_date": start, "token": FINMIND_TOKEN})
    df_inst = pd.DataFrame(res_inst.json().get('data', []))
    if not df_inst.empty:
        df_inst['date'] = pd.to_datetime(df_inst['date'])
        df_inst = df_inst.groupby('date')['buy'].sum() - df_inst.groupby('date')['sell'].sum()
        df['Inst'] = df_inst
    else: df['Inst'] = 0
    
    return df

# --- 3. 頁面邏輯 ---
if 'selected_stock' not in st.session_state: st.session_state.selected_stock = None
if 'page' not in st.session_state: st.session_state.page = 0

if st.session_state.selected_stock:
    # 詳情頁
    if st.button("◀ 返回大廳"): st.session_state.selected_stock = None; st.rerun()
    df = get_full_analysis(st.session_state.selected_stock)
    
    if df is not None:
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.3, 0.1, 0.15, 0.15, 0.2])
        fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['max'], low=df['min'], close=df['close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='MA5'), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Trading_Volume'], name='成交量'), row=2, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Inst'], name='法人買賣超'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['DIF'], name='MACD'), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], name='KD'), row=5, col=1)
        fig.update_layout(height=1000, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
else:
    # 首頁列表
    st.title("📈 台股自選股大廳")
    search = st.text_input("🔍 搜尋名稱或代號")
    pool = [s for s in WATCHLIST if search in s['id'] or search in s['name']] if search else WATCHLIST
    
    # 一頁 9 個
    page_size = 9
    total_pages = (len(pool) + page_size - 1) // page_size
    current_stocks = pool[st.session_state.page * page_size : (st.session_state.page + 1) * page_size]
    
    # 網格渲染
    for i in range(0, len(current_stocks), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i+j < len(current_stocks):
                s = current_stocks[i+j]
                if col.button(f"查看 {s['name']} ({s['id']})", key=s['id']):
                    st.session_state.selected_stock = s['id']
                    st.rerun()
                    
    # 頁碼控制
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ 上一頁"): st.session_state.page = max(0, st.session_state.page-1); st.rerun()
    c2.write(f"第 {st.session_state.page+1} / {total_pages} 頁")
    if c3.button("下一頁 ▶"): st.session_state.page = min(total_pages-1, st.session_state.page+1); st.rerun()
