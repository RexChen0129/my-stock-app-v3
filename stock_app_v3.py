import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

# --- 配置與設定 ---
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# 抓取邏輯
def fetch_data(dataset, stock_id, start_date):
    URL = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": dataset, "data_id": stock_id, "start_date": start_date, "token": FINMIND_TOKEN}
    try:
        res = requests.get(URL, params=params, timeout=15).json()
        return pd.DataFrame(res.get('data', []))
    except:
        return pd.DataFrame()

def get_full_analysis(stock_id):
    start_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 並行抓取
    with ThreadPoolExecutor(max_workers=2) as executor:
        f_price = executor.submit(fetch_data, "TaiwanStockPrice", stock_id, start_date)
        f_inst = executor.submit(fetch_data, "InstitutionalInvestorsBuySell", stock_id, start_date)
        df = f_price.result()
        inst = f_inst.result()
    
    if df.empty: return None
    df['date'] = pd.to_datetime(df['date'])
    
    # 法人數據對齊
    if not inst.empty:
        inst['date'] = pd.to_datetime(inst['date'])
        # 處理欄位對齊，支援不同 API 回傳格式
        cols = {c.lower(): c for c in inst.columns}
        buy_col = cols.get('buy', cols.get('buy_value'))
        sell_col = cols.get('sell', cols.get('sell_value'))
        
        if buy_col and sell_col:
            inst['net'] = pd.to_numeric(inst[buy_col]) - pd.to_numeric(inst[sell_col])
            inst = inst.groupby('date')['net'].sum().reset_index()
            df = pd.merge(df, inst, on='date', how='left').fillna(0)
        else:
            df['net'] = 0
    else:
        df['net'] = 0
        
    # 計算五指標
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
    df['K'] = ((df['close'] - l9) / (h9 - l9) * 100).ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    e12 = df['close'].ewm(span=12, adjust=False).mean()
    e26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD_h'] = (e12 - e26) - (e12 - e26).ewm(span=9, adjust=False).mean()
    return df

# --- 介面渲染 ---
st.set_page_config(layout="wide", page_title="專業五指標控盤系統")
st.title("🏹 專業五指標全能控盤系統")

with st.sidebar:
    st.header("股票選擇")
    stock_options = {
        "台積電": "2330",
        "鴻海": "2317",
        "聯發科": "2454",
        "台中銀": "2812",
        "廣達": "2382",
        "長榮": "2603"
    }
    selected_name = st.selectbox("選擇熱門股", list(stock_options.keys()))
    manual_id = st.text_input("或輸入代碼", value=stock_options[selected_name])
    btn = st.button("開始分析")
    
    # 若手動輸入與選單不同，優先使用手動輸入
    stock_id = manual_id

if btn or stock_id:
    df = get_full_analysis(stock_id)
    if df is not None:
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.35, 0.1, 0.15, 0.2, 0.2], 
                           subplot_titles=("K線與均線", "成交量", "法人籌碼淨額", "KD 指標", "MACD"))
        
        # 軌道 1: K線
        fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['max'], low=df['min'], close=df['close']), row=1, col=1)
        # 軌道 2: 量
        fig.add_trace(go.Bar(x=df['date'], y=df['Trading_Volume']), row=2, col=1)
        # 軌道 3: 法人
        fig.add_trace(go.Bar(x=df['date'], y=df['net'], marker_color=['red' if x>=0 else 'green' for x in df['net']]), row=3, col=1)
        # 軌道 4: KD
        fig.add_trace(go.Scatter(x=df['date'], y=df['K'], name='K'), row=4, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['D'], name='D'), row=4, col=1)
        # 軌道 5: MACD
        fig.add_trace(go.Bar(x=df['date'], y=df['MACD_h'], marker_color=['red' if x>=0 else 'green' for x in df['MACD_h']]), row=5, col=1)
        
        fig.update_layout(height=1200, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"無法獲取股票 {stock_id} 的數據，請檢查代碼或 API 權限。")
