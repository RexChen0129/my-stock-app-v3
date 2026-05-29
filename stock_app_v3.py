import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

# --- 1. 設定與配置 ---
st.set_page_config(layout="wide", page_title="專業台股自選控盤系統")
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# (保持您原有的 WATCHLIST 清單，因篇幅關係此處省略，請確保完整貼上)
# WATCHLIST = [...] 

# --- 2. 資料處理函數 (保持與您原先邏輯一致) ---
@st.cache_data(ttl=600)
def get_mini_price_data(stock_id):
    start_date = (datetime.date.today() - datetime.timedelta(days=60)).strftime("%Y-%m-%d")
    # 此處調用您原有的抓取邏輯
    # ... (略)
    return df_price

@st.cache_data(ttl=600)
def get_comprehensive_data(stock_id):
    # 此處調用您原有的五指標詳細邏輯
    # ... (略)
    return df

# --- 3. 初始化 Session State ---
if 'selected_stock' not in st.session_state: st.session_state.selected_stock = None
if 'page' not in st.session_state: st.session_state.page = 0
if 'search_query' not in st.session_state: st.session_state.search_query = ""

# --- 4. 介面渲染 ---

# 詳情頁模式
if st.session_state.selected_stock:
    if st.button("⬅ 返回列表"):
        st.session_state.selected_stock = None
        st.rerun()
    
    # 渲染五指標圖表 (保留您原本的 make_subplots 邏輯)
    # ... (渲染邏輯)

# 首頁列表模式
else:
    st.title("📈 台股自選股大廳")
    
    # 搜尋列
    new_search = st.text_input("🔍 搜尋名稱或代號", value=st.session_state.search_query)
    if new_search != st.session_state.search_query:
        st.session_state.search_query = new_search
        st.session_state.page = 0 # 搜尋時強制回到第一頁
        st.rerun()

    # 篩選與分頁
    filtered = [s for s in WATCHLIST if st.session_state.search_query in s['id'] or st.session_state.search_query in s['name']]
    total_pages = (len(filtered) + 8) // 9
    
    # 網格渲染
    cols = st.columns(3)
    start = st.session_state.page * 9
    for i, stock in enumerate(filtered[start : start + 9]):
        with cols[i % 3]:
            st.markdown(f"### {stock['name']} ({stock['id']})")
            # 渲染迷你圖 (config={'staticPlot': True} 防止崩潰)
            # ... 您的繪圖邏輯 ...
            if st.button(f"查看詳情", key=f"btn_{stock['id']}"):
                st.session_state.selected_stock = stock['id']
                st.rerun()

    # 分頁控制
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("上一頁") and st.session_state.page > 0:
        st.session_state.page -= 1
        st.rerun()
    c2.write(f"第 {st.session_state.page + 1} / {total_pages} 頁")
    if c3.button("下一頁") and st.session_state.page < total_pages - 1:
        st.session_state.page += 1
        st.rerun()
