import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor

# --- 配置 ---
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

def fetch_data(dataset, stock_id, start_date):
    URL = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": dataset, "data_id": stock_id, "start_date": start_date, "token": FINMIND_TOKEN}
    try:
        res = requests.get(URL, params=params, timeout=10).json()
        return pd.DataFrame(res.get('data', []))
    except:
        return pd.DataFrame()

def get_full_analysis(stock_id):
    start_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 改用 TaiwanStockInstitutionalInvestorsBuySell 獲取籌碼
    df_price = fetch_data("TaiwanStockPrice", stock_id, start_date)
    df_inst = fetch_data("TaiwanStockInstitutionalInvestorsBuySell", stock_id, start_date)
    
    if df_price.empty: return None
    df_price['date'] = pd.to_datetime(df_price['date'])
    
    # 籌碼處理
    if not df_inst.empty:
        df_inst['date'] = pd.to_datetime(df_inst['date'])
        # 抓取買賣超淨額 (這欄位在該 dataset 通常是 sell/buy 欄位)
        # 如果無法直接相減，我們改用 sell_buy_total 等欄位
        df_inst['net'] = df_inst.get('buy', 0) - df_inst.get('sell', 0)
        df_inst = df_inst.groupby('date')['net'].sum().reset_index()
        df = pd.merge(df_price, df_inst, on='date', how='left').fillna(0)
    else:
        df = df_price
        df['net'] = 0
        st.sidebar.error("警告：此股票 API 無法人籌碼數據")
        
    # 計算指標
    df['MA5'] = df['close'].rolling(5).mean()
    l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
    df['K'] = ((df['close'] - l9) / (h9 - l9) * 100).fillna(50).ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

# --- UI ---
st.set_page_config(layout="wide")
st.title("🏹 專業五指標控盤系統")
stock_id = st.sidebar.text_input("輸入代碼", value="2330")
if st.sidebar.button("分析"):
    df = get_full_analysis(stock_id)
    if df is not None:
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.25, 0.25])
        fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['max'], low=df['min'], close=df['close']), row=1, col=1)
        fig.add_trace(go.Bar(x=df['date'], y=df['net'], marker_color=['red' if x>=0 else 'green' for x in df['net']]), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['K'], name='K'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['D'], name='D'), row=3, col=1)
        fig.update_layout(height=900, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
