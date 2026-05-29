import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

# --- 1. 全域配置與自選股清單 ---
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# (註: WATCHLIST 清單內容與您原先的一模一樣，為節省篇幅，請保留您原本定義的 WATCHLIST)
WATCHLIST = [
    {"name": "台積電", "id": "2330"}, {"name": "聯電", "id": "2303"}, {"name": "鴻海", "id": "2317"},
    # ... 請確保這裡放回您原本的 205 檔清單
]

# --- 2. 資料處理函數 ---
def fetch_price_data(stock_id, start_date):
    URL = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": "TaiwanStockPrice", "data_id": stock_id, "start_date": start_date}
    if FINMIND_TOKEN: params["token"] = FINMIND_TOKEN
    try:
        res = requests.get(URL, params=params, timeout=15).json()
        return pd.DataFrame(res.get('data', []))
    except: return pd.DataFrame()

def fetch_inst_data(stock_id, start_date):
    URL = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": "InstitutionalInvestorsBuySell", "data_id": stock_id, "start_date": start_date}
    if FINMIND_TOKEN: params["token"] = FINMIND_TOKEN
    try:
        res = requests.get(URL, params=params, timeout=15).json()
        return pd.DataFrame(res.get('data', []))
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_comprehensive_data(stock_id, days=730):
    start_date_p = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    df_price = fetch_price_data(stock_id, start_date_p)
    df_inst = fetch_inst_data(stock_id, start_date_p)
    
    if df_price.empty: return None
    
    df_price['date'] = pd.to_datetime(df_price['date'])
    df_price.set_index('date', inplace=True)
    
    # 計算指標
    df = df_price
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    
    # 處理法人數據
    if not df_inst.empty:
        df_inst['date'] = pd.to_datetime(df_inst['date'])
        # 將三大法人買賣超加總
        df_inst = df_inst.groupby('date')[['buy', 'sell']].sum()
        df['Inst_Net'] = (df_inst['buy'] - df_inst['sell']).fillna(0)
    else:
        df['Inst_Net'] = 0
        
    return df

# --- 3. 主程式介面 ---
st.set_page_config(layout="wide", page_title="專業台股控盤系統")

if 'selected_stock' not in st.session_state: st.session_state.selected_stock = None

if st.session_state.selected_stock:
    # --- A. 詳情頁 ---
    active_id = st.session_state.selected_stock
    if st.button("← 返回列表"):
        st.session_state.selected_stock = None
        st.rerun()
    
    df = get_comprehensive_data(active_id)
    
    # 儀表板
    latest = df.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最新價", f"{latest['close']:.2f}")
    c2.metric("MA5", f"{latest['MA5']:.2f}")
    c3.metric("MA20", f"{latest['MA20']:.2f}")
    
    # 訊號計算
    df['Signal'] = 0
    df.loc[(df['MA5'] > df['MA20']) & (df['MA5'].shift(1) <= df['MA20'].shift(1)), 'Signal'] = 1
    
    # 繪圖
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.2, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['max'], low=df['min'], close=df['close']), row=1, col=1)
    
    # 買賣訊號標記
    buys = df[df['Signal'] == 1]
    fig.add_trace(go.Scatter(x=buys.index, y=buys['low']*0.98, mode='markers', name='黃金交叉', marker=dict(size=12, color='red')), row=1, col=1)
    
    # 法人累計動能
    df['Inst_Accum'] = df['Inst_Net'].cumsum()
    fig.add_trace(go.Scatter(x=df.index, y=df['Inst_Accum'], fill='tozeroy', name='法人累積'), row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

else:
    # --- B. 列表頁 (您的原架構) ---
    # (此處放入您原本的搜尋、分頁、卡片渲染邏輯)
    st.write("這是您的自選股大廳...")
