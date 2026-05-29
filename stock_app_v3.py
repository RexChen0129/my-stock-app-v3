import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor

# ==============================================================================
# 【請在這裡保留/貼上你最完整的 205 檔股票清單】
# 格式範例：
# WATCHLIST = [
#      {"name": "台積電", "id": "2330"},
#      ... 你的兩百多檔 ...
#      {"name": "國光生", "id": "4142"}
# ]
# ==============================================================================
WATCHLIST = [
    {"name": "台積電", "id": "2330"},
    {"name": "聯電", "id": "2303"},
    {"name": "鴻海", "id": "2317"},
    {"name": "聯發科", "id": "2454"},
    {"name": "國光生", "id": "4142"}
]
# ==============================================================================

# 初始化 Session State (確保切換與導航正常)
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

st.set_page_config(layout="wide")

# --- 1. 資料擷取函數區 ---
def fetch_stock_data(stock_id):
    """獲取基本K線資料"""
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        if res.get("data"):
            df = pd.DataFrame(res["data"])
            df.columns = [c.lower() for c in df.columns]
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
    except:
        pass
    return pd.DataFrame()

def fetch_inst_data(stock_id):
    """【法人數據抓取修正】徹底解決回傳空值或找不到欄位變直線的問題"""
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=120)).strftime('%Y-%m-%d')
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockInstitutionalInvestorsBuySell",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        if res.get("data"):
            df = pd.DataFrame(res["data"])
            df.columns = [c.lower() for c in df.columns]
            df['date'] = pd.to_datetime(df['date'])
            
            # 動態檢查 API 欄位對應
            buy_col = 'buy' if 'buy' in df.columns else ('ss_buy_volume' if 'ss_buy_volume' in df.columns else '')
            sell_col = 'sell' if 'sell' in df.columns else ('ss_sell_volume' if 'ss_sell_volume' in df.columns else '')
            
            if buy_col and sell_col:
                df['net_value'] = df[buy_col] - df[sell_col]
            else:
                # 備用容錯：若有三大法人個別買賣欄位，加總計算
                df['net_value'] = 0
                for c in df.columns:
                    if 'buy' in c: df['net_value'] += df[c]
                    if 'sell' in c: df['net_value'] -= df[c]
                    
            # 依日期加總法人買賣金額並設為索引
            inst_summary = df.groupby('date')['net_value'].sum().reset_index()
            inst_summary.set_index('date', inplace=True)
            return inst_summary
    except:
        pass
    return pd.DataFrame()

# --- 2. 指標計算邏輯 ---
def calculate_indicators(df):
    """計算三均線、MACD、KD核心數據"""
    if df.empty: return df
    # 1. 三條 MA 線 (5/20/60)
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    
    # 2. MACD 計算
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['dif'] = ema12 - ema26
    df['macd_signal'] = df['dif'].ewm(span=9, adjust=False).mean()
    df['osc'] = df['dif'] - df['macd_signal']
    
    # 3. KD 計算
    low_min = df['low'].rolling(window=9).min()
    high_max = df['high'].rolling(window=9).max()
    rsv = 100 * ((df['close'] - low_min) / (high_max - low_min).replace(0, 1))
    df['k'] = rsv.ewm(com=2, adjust=False).mean()
    df['d'] = df['k'].ewm(com=2, adjust=False).mean()
    return df

def draw_mini_chart(df):
    """首頁 3x3 網格內的微型 K 線圖"""
    if df.empty or len(df) < 10: return go.Figure()
    sub_df = df.tail(15)
    fig = go.Figure(data=[go.Candlestick(
        x=sub_df.index, open=sub_df['open'], high=sub_df['high'], low=sub_df['low'], close=sub_df['close'],
        increasing_line_color='red', decreasing_line_color='green',
        increasing_fillcolor='red', decreasing_fillcolor='green'
    )])
    fig.update_layout(
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0), height=60, showlegend=False, xaxis_rangeslider_visible=False
    )
    return fig

# --- 3. 多執行緒加速首頁加載 ---
def get_homepage_data(stock_list):
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_id = {executor.submit(fetch_stock_data, s['id']): s['id'] for s in stock_list}
        for future in future_to_id:
            sid = future_to_id[future]
            results[sid] = future.result()
    return results

# ==============================================================================
# --- 4. 網頁渲染主介面邏輯 ---
# ==============================================================================
if st.session_state.selected_stock:
    # ------------------ 【功能 3】點進去後的 5 指標分析詳細頁面 ------------------
    stock_id = st.session_state.selected_stock
    stock_name = next((s['name'] for s in WATCHLIST if s['id'] == stock_id), "")
    
    col1, col2 = st.columns([8, 1])
    with col1:
        st.title(f"{stock_name} ({stock_id}) 五指標整合分析儀表板")
    with col2:
        if st.button("⬅ 返回列表", width='stretch'):
            st.session_state.selected_stock = None
            st.rerun()
            
    with st.spinner("智慧控盤數據計算中..."):
        df = fetch_stock_data(stock_id)
        df = calculate_indicators(df)
        df_inst = fetch_inst_data(stock_id)
        
        if not df.empty:
            # 整合法人數據，若沒有則補 0 避免出錯
            if not df_inst.empty:
                df = df.join(df_inst, how='left').fillna(0)
            else:
                df['net_value'] = 0
                
            df_plot = df.tail(120)  # 畫最近 120 天數據
            
            # 正式畫出包含 5 個獨立 row 的大圖表
            fig = make_subplots(
                rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                row_heights=[0.35, 0.15, 0.15, 0.15, 0.15],
                subplot_titles=("1. K線與三條均線 (MA5/MA20/MA60)", "2. 當日交易量", "3. 三大法人買賣超變動 (修正版)", "4. MACD 指標", "5. KD 隨機指標")
            )
            
            # 1. K線與 MA 均線
            fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['open'], high=df_plot['high'], low=df_plot['low'], close=df_plot['close'], name="K線"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ma5'], line=dict(color='blue', width=1.5), name="MA5"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ma20'], line=dict(color='orange', width=1.5), name="MA20"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ma60'], line=dict(color='purple', width=1.5), name="MA60"), row=1, col=1)
            
            # 2. 成交量柱狀圖 (漲紅跌綠)
            v_colors = ['red' if c >= o else 'green' for c, o in zip(df_plot['close'], df_plot['open'])]
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
            
            # 3. 三大法人買賣超金額變動
            inst_colors = ['red' if val >= 0 else 'green' for val in df_plot['net_value']]
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['net_value'], marker_color=inst_colors, name="法人買賣超"), row=3, col=1)
            
            # 4. MACD
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['dif'], line=dict(color='black'), name="DIF"), row=4, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['macd_signal'], line=dict(color='orange'), name="MACD"), row=4, col=1)
            osc_colors = ['red' if val >= 0 else 'green' for val in df_plot['osc']]
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['osc'], marker_color=osc_colors, name="OSC柱狀圖"), row=4, col=1)
            
            # 5. KD 指標
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['k'], line=dict(color='blue'), name="K線"), row=5, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['d'], line=dict(color='orange'), name="D線"), row=5, col=1)
            
            fig.update_layout(height=950, showlegend=False, xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, width='stretch')
        else:
            st.error("該股票暫無數據，請確認 API 連線狀態。")
else:
    # ------------------ 【功能 1 & 2】首頁搜尋、價格與九宮格分頁 ------------------
    st.title("📈 智慧台股控盤系統分析大廳")
    
    # 頂部支援代號/名稱通用搜尋
    q = st.text_input("🔍 請輸入股票代號或中文名稱進行搜尋：", value=st.session_state.search_query)
    if q != st.session_state.search_query:
        st.session_state.search_query = q
        st.session_state.current_page = 0
        st.rerun()
        
    filtered = [s for s in WATCHLIST if q in s['id'] or q in s['name']]
    
    total_items = len(filtered)
    total_pages = (total_items + 8) // 9
    
    if total_items == 0:
        st.warning("沒有找到相符的股票，請確認搜尋關鍵字。")
    else:
        start_idx = st.session_state.current_page * 9
        end_idx = start_idx + 9
        page_items = filtered[start_idx:end_idx]
        
        with st.spinner("同步刷新即時盤勢中..."):
            homepage_data = get_homepage_data(page_items)
            
        # 建立 3x3 網格
        cols = st.columns(3)
        for idx, item in enumerate(page_items):
            with cols[idx % 3]:
                with st.container(border=True):
                    stock_df = homepage_data.get(item['id'], pd.DataFrame())
                    if not stock_df.empty:
                        last_row = stock_df.iloc[-1]
                        price_text = f" NT$ {last_row['close']:.2f}"
                    else:
                        price_text = " 讀取中..."
                        
                    st.markdown(f"### {item['name']} ({item['id']})")
                    st.markdown(f"**目前收盤價:** <span style='color:red;font-size:20px;'>{price_text}</span>", unsafe_allow_html=True)
                    
                    # 畫小 K 線
                    if not stock_df.empty:
                        mini_fig = draw_mini_chart(stock_df)
                        st.plotly_chart(mini_fig, config={'displayModeBar': False}, width='stretch')
                        
                    if st.button("詳細五指標分析 ➔", key=f"btn_{item['id']}", width='stretch'):
                        st.session_state.selected_stock = item['id']
                        st.rerun()
                        
        st.write("---")
        # 下方分頁控制
        p_col1, p_col2, p_col3 = st.columns([2, 6, 2])
        with p_col1:
            if st.session_state.current_page > 0:
                if st.button("⬅ 上一頁", width='stretch'):
                    st.session_state.current_page -= 1
                    st.rerun()
        with p_col2:
            st.markdown(f"<p style='text-align:center; font-size:16px;'>目前分頁： 第 {st.session_state.current_page + 1} 頁 / 共 {total_pages} 頁 (總計 {total_items} 檔股票)</p>", unsafe_allow_html=True)
        with p_col3:
            if end_idx < total_items:
                if st.button("下一頁 ➔", width='stretch'):
                    st.session_state.current_page += 1
                    st.rerun()
