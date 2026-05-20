import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

# --- 1. 全域配置與自選股清單 (已自動填入您的真實 FinMind Token) ---
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# 預設自選股卡片清單 (名稱, 代碼)
WATCHLIST = [
    {"name": "台積電", "id": "2330"},
    {"name": "鴻海", "id": "2317"},
    {"name": "聯發科", "id": "2454"},
    {"name": "長榮", "id": "2603"},
    {"name": "陽明", "id": "2609"},
    {"name": "富邦金", "id": "2881"}
]

# --- 2. 高效並發數據抓取函數 (多執行緒加速) ---
def fetch_price_data(stock_id, start_date):
    """負責抓取股價數據"""
    URL = "https://api.finmindtrade.com/api/v4/data"
    try:
        res = requests.get(URL, params={
            "dataset": "TaiwanStockPrice", 
            "data_id": stock_id, 
            "start_date": start_date, 
            "token": FINMIND_TOKEN
        }, timeout=15).json()
        return pd.DataFrame(res.get('data', []))
    except:
        return pd.DataFrame()

def fetch_inst_data(stock_id, start_date):
    """負責抓取法人數據 (含自動重試)"""
    URL = "https://api.finmindtrade.com/api/v4/data"
    for _ in range(3):
        try:
            res = requests.get(URL, params={
                "dataset": "InstitutionalInvestorsBuySell", 
                "data_id": stock_id, 
                "start_date": start_date, 
                "token": FINMIND_TOKEN
            }, timeout=15).json()
            data = res.get('data', [])
            if data: return pd.DataFrame(data)
            time.sleep(0.5)
        except:
            time.sleep(0.5)
    return pd.DataFrame()

@st.cache_data(ttl=600)
def get_comprehensive_data(stock_id, days=730):
    """同步抓取股價 (days) 與近一年法人數據並完美對齊"""
    start_date_p = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    start_date_i = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 使用多執行緒同時請求數據，提升一倍載入效率
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_p = executor.submit(fetch_price_data, stock_id, start_date_p)
        future_i = executor.submit(fetch_inst_data, stock_id, start_date_i)
        
        df_price = future_p.result()
        df_inst = future_i.result()

    if df_price.empty:
        return None

    try:
        # 整理股價數據並統一轉換為字串型態 YYYY-MM-DD，徹底解決時間戳格式不同導致的對齊失敗問題
        df_price['date_str'] = pd.to_datetime(df_price['date']).dt.strftime('%Y-%m-%d')
        df_price = df_price.sort_values('date_str')

        # 整理法人數據，強制統一欄位為小寫後對齊
        if not df_inst.empty:
            df_inst['date_str'] = pd.to_datetime(df_inst['date']).dt.strftime('%Y-%m-%d')
            df_inst.columns = [c.lower() for c in df_inst.columns]
            
            if 'buy' in df_inst.columns and 'sell' in df_inst.columns:
                df_inst['net'] = pd.to_numeric(df_inst['buy']) - pd.to_numeric(df_inst['sell'])
                # 將三大法人當日數據加總
                daily_inst = df_inst.groupby('date_str')['net'].sum().reset_index()
                
                # 採用 merge 進行高精準度左合併 (依據 date_str)
                df = pd.merge(df_price, daily_inst, on='date_str', how='left')
                df.rename(columns={'net': 'Inst_Net'}, inplace=True)
                df['Inst_Net'] = df['Inst_Net'].fillna(0)
            else:
                df_price['Inst_Net'] = 0
                df = df_price
        else:
            df_price['Inst_Net'] = 0
            df = df_price

        # 技術指標計算 (設定 date_str 為 index)
        df.set_index('date_str', inplace=True)
        # 1. 均線 MA (5, 10, 20)
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA10'] = df['close'].rolling(10).mean()
        df['MA20'] = df['close'].rolling(20).mean()
        
        # 2. KD (9, 3, 3)
        l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
        rsv = (df['close'] - l9) / (h9 - l9) * 100
        df['K'] = rsv.ewm(com=2).mean()
        df['D'] = df['K'].ewm(com=2).mean()
        
        # 3. MACD (12, 26, 9)
        e12 = df['close'].ewm(span=12, adjust=False).mean()
        e26 = df['close'].ewm(span=26, adjust=False).mean()
        df['DIF'] = e12 - e26
        df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
        df['MACD_h'] = (df['DIF'] - df['DEA']) * 2
        
        return df
    except Exception as e:
        st.error(f"數據計算錯誤: {e}")
        return None

# --- 3. 繪製首頁自選股卡片的迷你 K 線 (Sparkline) ---
def render_mini_chart(stock_id):
    """繪製過去 30 天的迷你折線，代表近期走勢 (無背景與網格線，簡潔設計)"""
    df = get_comprehensive_data(stock_id, days=60)
    if df is not None and len(df) > 0:
        recent = df.tail(30)
        color = 'red' if recent['close'].iloc[-1] >= recent['close'].iloc[0] else 'green'
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=recent.index, y=recent['close'],
            line=dict(color=color, width=2.5),
            hoverinfo='none',
            mode='lines'
        ))
        
        fig.update_layout(
            width=220, height=70,
            margin=dict(l=5, r=5, t=5, b=5),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig, recent['close'].iloc[-1], recent['close'].iloc[-1] - recent['close'].iloc[-2]
    return None, None, None

# --- 4. 網頁介面 CSS 視覺美化 ---
st.set_page_config(layout="wide", page_title="專業台股自選控盤系統 APP v3")
st.markdown("""
    <style>
    /* 整體深色調背景與 APP 質感卡片 */
    .stApp { background-color: #0E1117; }
    .stock-card {
        background-color: #1a1c24;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2d313f;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        transition: transform 0.2s ease;
    }
    .stock-card:hover {
        transform: translateY(-3px);
        border-color: #4f5b7a;
    }
    .stock-title { font-size: 20px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
    .stock-id { font-size: 14px; color: #8892b0; margin-bottom: 12px; }
    .stock-price-rise { font-size: 28px; font-weight: bold; color: #ff3333; margin-top: 10px; }
    .stock-price-fall { font-size: 28px; font-weight: bold; color: #00aa00; margin-top: 10px; }
    .change-percent-rise { background-color: rgba(255,51,51,0.1); color: #ff3333; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 14px; }
    .change-percent-fall { background-color: rgba(0,170,0,0.1); color: #00aa00; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- 5. Session State 導航狀態管理 ---
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None

# --- A. 詳情分析頁面 (Detail View) ---
if st.session_state.selected_stock:
    active_id = st.session_state.selected_stock
    
    # 返回自選股按鈕
    if st.button("← 返回自選股列表"):
        st.session_state.selected_stock = None
        st.rerun()
        
    st.markdown(f"## 📊 股票代碼 {active_id} 專業五指標分析")
    
    with st.spinner('正在使用多執行緒高速調用數據與計算指標...'):
        df = get_comprehensive_data(active_id, days=730)
    
    if df is not None:
        df_plot = df.copy()
        plot_width = max(1200, len(df_plot) * 22)
        
        # 建立五層垂直子圖
        fig = make_subplots(
            rows=5, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03,
            row_heights=[0.35, 0.1, 0.15, 0.2, 0.2],
            subplot_titles=("1. K線棒與三均線 (5/10/20 MA)", "2. 當日成交量", "3. 三大法人買賣超 (真實籌碼起伏)", "4. KD 指標", "5. MACD 趨勢")
        )

        # 軌道 1: K線棒 + 3MA
        fig.add_trace(go.Candlestick(
            x=df_plot.index, open=df_plot['open'], high=df_plot['max'], low=df_plot['min'], close=df_plot['close'],
            name='K線', increasing_line_color='red', decreasing_line_color='green'
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA5'], name='MA5', line=dict(color='white', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA10'], name='MA10', line=dict(color='yellow', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA20'], name='MA20', line=dict(color='magenta', width=1.5)), row=1, col=1)

        # 軌道 2: 成交量
        v_colors = ['red' if df_plot['close'].iloc[i] >= df_plot['open'].iloc[i] else 'green' for i in range(len(df_plot))]
        fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['Trading_Volume'], name='成交量', marker_color=v_colors), row=2, col=1)

        # 軌道 3: 法人買賣超 (柱狀圖，紅買綠賣)
        inst_colors = ['red' if x >= 0 else 'green' for x in df_plot['Inst_Net']]
        fig.add_trace(go.Bar(
            x=df_plot.index, y=df_plot['Inst_Net'], 
            name='法人淨額', marker_color=inst_colors,
            hovertemplate='淨額: %{y:,.0f}'
        ), row=3, col=1)

        # 軌道 4: KD 指標
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['K'], name='K值', line=dict(color='orange')), row=4, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['D'], name='D值', line=dict(color='dodgerblue')), row=4, col=1)

        # 軌道 5: MACD
        m_colors = ['red' if x >= 0 else 'green' for x in df_plot['MACD_h']]
        fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['MACD_h'], name='MACD柱', marker_color=m_colors), row=5, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['DIF'], name='DIF', line=dict(color='white')), row=5, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['DEA'], name='DEA', line=dict(color='yellow')), row=5, col=1)

        # 佈局與滑動設定
        fig.update_layout(
            width=plot_width, height=1400,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            dragmode='pan',
            showlegend=True
        )
        
        # 強制 Y 軸自適應，讓法人和成交量有正確的起伏，拒絕一條線
        fig.update_yaxes(autorange=True, fixedrange=False)
        # 初始視野設定在最近的 100 根 K 線 (約半年)，保留剩餘 2 年資料供左右拖曳
        fig.update_xaxes(type='category', range=[len(df_plot)-100, len(df_plot)])

        st.plotly_chart(fig, use_container_width=False, config={
            'scrollZoom': True,           # 保留滑鼠滾輪縮放核心功能
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': [   # 隱藏右上角縮放與放大鏡按鈕
                'zoom2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'select2d', 'lasso2d'
            ]
        })
    else:
        st.error("未能載入該股之有效數據，請確認代碼或重新整理。")

# --- B. 自選股首頁列表 (Dashboard View) ---
else:
    st.write("# 📈 專業台股自選股大廳")
    st.write("點選自選股卡片，或使用下方搜尋框，即可進入**五指標精確控盤**分析頁面。")
    
    # 搜尋欄
    search_id = st.text_input("🔍 輸入任何台股代碼 (例如 2317 或 2454) 直接查閱", value="", placeholder="輸入4位數台股代碼後按 Enter...")
    if search_id:
        st.session_state.selected_stock = search_id.strip()
        st.rerun()

    st.markdown("### 📌 熱門看盤自選股清單")
    
    # 2x3 卡片網格布局
    cols = st.columns(3)
    
    for idx, item in enumerate(WATCHLIST):
        col = cols[idx % 3]
        with col:
            with st.spinner(f"正在載入 {item['name']} 走勢..."):
                fig_mini, latest_price, change = render_mini_chart(item["id"])
                
            st.markdown(f"""
                <div class="stock-card">
                    <div class="stock-title">{item['name']}</div>
                    <div class="stock-id">TWSE: {item['id']}</div>
            """, unsafe_allow_html=True)
            
            if latest_price is not None:
                # 判斷正負
                price_class = "stock-price-rise" if change >= 0 else "stock-price-fall"
                pct_class = "change-percent-rise" if change >= 0 else "change-percent-fall"
                sign = "+" if change >= 0 else ""
                
                # 計算漲跌幅百分比 (以昨日收盤為基礎)
                prev_price = latest_price - change
                pct = (change / prev_price) * 100 if prev_price != 0 else 0
                
                st.markdown(f"""
                    <div class="{price_class}">${latest_price:.1f}</div>
                    <div style="margin-top: 8px; margin-bottom: 12px;">
                        <span class="{pct_class}">{sign}{change:.1f} ({sign}{pct:.2f}%)</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # 顯示迷你 Sparkline 走勢
                st.plotly_chart(fig_mini, config={'displayModeBar': False}, use_container_width=False)
            else:
                st.write("暫無連線數據")
                
            # 詳細分析按鈕
            if st.button(f"進入 {item['name']} 分析", key=f"btn_{item['id']}", use_container_width=True):
                st.session_state.selected_stock = item["id"]
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)
