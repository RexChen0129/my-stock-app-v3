import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime

# --- 1. 配置與完整清單 ---
st.set_page_config(layout="wide", page_title="專業台股控盤系統")
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# --- [重要] 請在此處貼上您完整的 200+ 檔股票清單 ---
# 格式為 [{"name": "股票名稱", "id": "代號"}, ...]
WATCHLIST = [
    {"name": "台積電", "id": "2330"}, {"name": "聯電", "id": "2303"}, {"name": "鴻海", "id": "2317"},
    # ... 在此處補齊您的完整清單
]

# --- 2. 資料獲取核心 ---
@st.cache_data(ttl=3600)
def get_full_analysis(stock_id):
    url = "https://api.finmindtrade.com/api/v4/data"
    start = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 抓取股價 (包含 MA 計算)
    params = {"dataset": "TaiwanStockPrice", "data_id": stock_id, "start_date": start, "token": FINMIND_TOKEN}
    res = requests.get(url, params=params).json().get('data', [])
    if not res: return None
    df = pd.DataFrame(res)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 計算五大指標
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    
    # KD
    l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
    df['K'] = ((df['close'] - l9) / (h9 - l9) * 100).fillna(50).ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    # MACD
    diff = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    dea = diff.ewm(span=9).mean()
    df['MACD_h'] = (diff - dea) * 2
    
    # 法人 (簡單處理)
    res_i = requests.get(url, params={"dataset": "InstitutionalInvestorsBuySell", "data_id": stock_id, "start_date": start, "token": FINMIND_TOKEN}).json().get('data', [])
    df['Inst'] = 0
    if res_i:
        df_i = pd.DataFrame(res_i).groupby('date')['buy'].sum() - pd.DataFrame(res_i).groupby('date')['sell'].sum()
        df.update(df_i)
    return df

# --- 3. 頁面邏輯 ---
if 'selected_id' not in st.session_state: st.session_state.selected_id = None
if 'page' not in st.session_state: st.session_state.page = 0

if st.session_state.selected_id:
    # 詳情頁：五大資訊
    if st.button("◀ 返回列表"): st.session_state.selected_id = None; st.rerun()
    df = get_full_analysis(st.session_state.selected_id)
    if df is not None:
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.3, 0.1, 0.15, 0.15, 0.2])
        fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['max'], low=df['min'], close=df['close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='MA5'), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Trading_Volume'], name='成交量'), row=2, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Inst'], name='法人'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_h'], name='MACD'), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], name='KD'), row=5, col=1)
        fig.update_layout(height=1000, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
else:
    # 首頁：搜尋與 200+ 檔股票清單
    st.title("📈 台股自選股大廳")
    query = st.text_input("🔍 搜尋名稱或代號")
    filtered = [s for s in WATCHLIST if query in s['id'] or query in s['name']]
    
    # 分頁邏輯 (一頁 9 個)
    page_size = 9
    total_pages = (len(filtered) + page_size - 1) // page_size
    current_list = filtered[st.session_state.page * page_size : (st.session_state.page + 1) * page_size]
    
    for i in range(0, len(current_list), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i+j < len(current_list):
                s = current_list[i+j]
                if col.button(f"{s['name']} ({s['id']})", key=s['id']):
                    st.session_state.selected_id = s['id']
                    st.rerun()

    # 翻頁
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("上一頁") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    c2.write(f"第 {st.session_state.page+1} 頁 / 共 {total_pages} 頁")
    if c3.button("下一頁") and st.session_state.page < total_pages - 1: st.session_state.page += 1; st.rerun()
