import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime

# --- 1. 設定與 Token ---
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# --- 2. 獲取股票清單 (從 FinMind 取得最新清單) ---
@st.cache_data(ttl=86400)
def get_stock_list():
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": "TaiwanStockInfo", "token": FINMIND_TOKEN}
    res = requests.get(url, params=params).json()
    df = pd.DataFrame(res.get('data', []))
    # 過濾只保留上市櫃股票
    df = df[df['industry_category'] != '']
    return df

# --- 3. 數據抓取引擎 ---
def get_data(stock_id):
    start_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    url = "https://api.finmindtrade.com/api/v4/data"
    
    # 抓取股價
    res_p = requests.get(url, params={"dataset": "TaiwanStockPrice", "data_id": stock_id, "start_date": start_date, "token": FINMIND_TOKEN}).json()
    df = pd.DataFrame(res_p.get('data', []))
    if df.empty: return None
    df['date'] = pd.to_datetime(df['date'])
    
    # 抓取法人
    res_i = requests.get(url, params={"dataset": "TaiwanStockInstitutionalInvestorsBuySell", "data_id": stock_id, "start_date": start_date, "token": FINMIND_TOKEN}).json()
    df_i = pd.DataFrame(res_i.get('data', []))
    
    if not df_i.empty:
        df_i['date'] = pd.to_datetime(df_i['date'])
        # 將外資、投信、自營商合併
        df_i['net'] = df_i['buy'] - df_i['sell']
        df_i = df_i.groupby('date')['net'].sum().reset_index()
        df = pd.merge(df, df_i, on='date', how='left').fillna(0)
    else:
        df['net'] = 0
        
    return df

# --- 4. 儀表板 UI ---
st.set_page_config(layout="wide", page_title="專業級股市控盤系統")
st.title("📊 專業股市分析儀表板")

# 獲取清單並顯示在側邊欄
stocks = get_stock_list()
with st.sidebar:
    st.header("股票篩選")
    # 顯示兩百檔以上的搜尋選單
    search = st.text_input("搜尋股票代號或名稱")
    if search:
        filtered = stocks[stocks['stock_id'].str.contains(search) | stocks['stock_name'].str.contains(search)]
    else:
        filtered = stocks.head(200)
    
    selected_stock = st.selectbox("請選擇股票", filtered['stock_id'].astype(str) + " " + filtered['stock_name'])
    stock_id = selected_stock.split(" ")[0]
    btn = st.button("開始分析")

if btn:
    df = get_data(stock_id)
    if df is not None:
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, row_heights=[0.4, 0.2, 0.2, 0.2])
        # K線
        fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['max'], low=df['min'], close=df['close']), row=1, col=1)
        # 成交量
        fig.add_trace(go.Bar(x=df['date'], y=df['Trading_Volume'], name="成交量"), row=2, col=1)
        # 法人籌碼
        fig.add_trace(go.Bar(x=df['date'], y=df['net'], name="法人買賣超", marker_color=['red' if x>=0 else 'green' for x in df['net']]), row=3, col=1)
        # 簡單 KD (示範)
        l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
        df['K'] = ((df['close'] - l9) / (h9 - l9) * 100).fillna(50).ewm(com=2).mean()
        df['D'] = df['K'].ewm(com=2).mean()
        fig.add_trace(go.Scatter(x=df['date'], y=df['K'], name='K'), row=4, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['D'], name='D'), row=4, col=1)
        
        fig.update_layout(height=1000, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
