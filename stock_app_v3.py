import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
import time

# --- 核心邏輯修正 ---
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

def get_data_from_finmind(dataset, stock_id, start_date):
    """通用抓取函數，加入強制型態轉換與除錯診斷"""
    URL = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": dataset, "data_id": stock_id, "start_date": start_date, "token": FINMIND_TOKEN}
    try:
        res = requests.get(URL, params=params, timeout=15).json()
        df = pd.DataFrame(res.get('data', []))
        return df
    except:
        return pd.DataFrame()

def get_final_data(stock_id):
    start_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 1. 抓取股價
    df_price = get_data_from_finmind("TaiwanStockPrice", stock_id, start_date)
    if df_price.empty: return None
    df_price['date'] = pd.to_datetime(df_price['date'])
    
    # 2. 抓取法人 (完全獨立抓取，不與股價提前合併)
    df_inst = get_data_from_finmind("InstitutionalInvestorsBuySell", stock_id, start_date)
    
    if not df_inst.empty:
        df_inst['date'] = pd.to_datetime(df_inst['date'])
        # 尋找買賣欄位名稱
        cols = [c.lower() for c in df_inst.columns]
        b_col = next((c for c in df_inst.columns if c.lower() in ['buy', 'buy_value']), None)
        s_col = next((c for c in df_inst.columns if c.lower() in ['sell', 'sell_value']), None)
        
        if b_col and s_col:
            df_inst['net'] = pd.to_numeric(df_inst[b_col]) - pd.to_numeric(df_inst[s_col])
            df_inst = df_inst.groupby('date')['net'].sum().reset_index()
        else:
            df_inst['net'] = 0
    else:
        df_inst = pd.DataFrame(columns=['date', 'net'])
        
    # 3. 確保對齊：以股價日期為基礎
    df = pd.merge(df_price, df_inst, on='date', how='left')
    df['net'] = df['net'].fillna(0)
    
    # 指標計算
    df['MA5'] = df['close'].rolling(5).mean()
    return df

st.set_page_config(layout="wide")
stock_id = st.text_input("輸入股票代碼", value="2330")

if st.button("立即分析"):
    df = get_final_data(stock_id)
    if df is not None:
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.25, 0.25])
        fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['max'], low=df['min'], close=df['close']), row=1, col=1)
        fig.add_trace(go.Bar(x=df['date'], y=df['Trading_Volume']), row=2, col=1)
        # 關鍵顯示：如果 net 全部是 0，顯示提示
        if df['net'].sum() == 0:
            st.warning(f"注意：系統抓取到該股票 {stock_id} 之法人資料淨額為 0，這可能是 API 無該股法人數據，請嘗試其他股票。")
        fig.add_trace(go.Bar(x=df['date'], y=df['net'], marker_color=['red' if x >= 0 else 'green' for x in df['net']]), row=3, col=1)
        
        fig.update_layout(height=900, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("查無資料")
