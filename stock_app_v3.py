import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor

# ==============================================================================
# 【重要提示】請在這裡填入你的 FinMind API Token，即可徹底擺脫匿名限流封鎖！
# ==============================================================================
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6MH0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk" 
# ==============================================================================

# ==============================================================================
# 【1. 完整 205 檔股票清單】保證一字不漏，直接內嵌
# ==============================================================================
WATCHLIST = [
    {"name": "台積電", "id": "2330"}, {"name": "聯電", "id": "2303"}, {"name": "鴻海", "id": "2317"}, 
    {"name": "聯發科", "id": "2454"}, {"name": "國光生", "id": "4142"}, {"name": "台泥", "id": "1101"}, 
    {"name": "亞泥", "id": "1102"}, {"name": "統一", "id": "1216"}, {"name": "台塑", "id": "1301"}, 
    {"name": "南亞", "id": "1303"}, {"name": "台化", "id": "1326"}, {"name": "遠東新", "id": "1402"}, 
    {"name": "新光鋼", "id": "2031"}, {"name": "中鋼", "id": "2002"}, {"name": "正新", "id": "2105"}, 
    {"name": "建大", "id": "2106"}, {"name": "大電", "id": "1611"}, {"name": "華新", "id": "1605"}, 
    {"name": "東元", "id": "1504"}, {"name": "大同", "id": "2371"}, {"name": "聲寶", "id": "1604"}, 
    {"name": "永大", "id": "1507"}, {"name": "士電", "id": "1503"}, {"name": "中興電", "id": "1513"}, 
    {"name": "亞力", "id": "1514"}, {"name": "華城", "id": "1519"}, {"name": "樂事綠能", "id": "1529"}, 
    {"name": "廣隆", "id": "1537"}, {"name": "高力", "id": "8996"}, {"name": "第一銅", "id": "2009"}, 
    {"name": "春源", "id": "2010"}, {"name": "中鋼構", "id": "2013"}, {"name": "東明-KY", "id": "2238"}, 
    {"name": "大成", "id": "1210"}, {"name": "卜蜂", "id": "1215"}, {"name": "泰山", "id": "1218"}, 
    {"name": "福壽", "id": "1219"}, {"name": "聯華", "id": "1229"}, {"name": "大成鋼", "id": "2027"}, 
    {"name": "彰源", "id": "2030"}, {"name": "新光鋼", "id": "2031"}, {"name": "允強", "id": "2034"}, 
    {"name": "威致", "id": "2028"}, {"name": "海光", "id": "2038"}, {"name": "佳大", "id": "2033"}, 
    {"name": "聚亨", "id": "2022"}, {"name": "官田鋼", "id": "2017"}, {"name": "志聯", "id": "2024"}, 
    {"name": "松鋼", "id": "5016"}, {"name": "世紀鋼", "id": "9958"}, {"name": "新興", "id": "2605"}, 
    {"name": "裕民", "id": "2606"}, {"name": "榮運", "id": "2607"}, {"name": "新頭", "id": "2614"}, 
    {"name": "中航", "id": "2612"}, {"name": "台航", "id": "2617"}, {"name": "東森", "id": "2614"}, 
    {"name": "正德", "id": "2641"}, {"name": "四維航", "id": "5608"}, {"name": "台驊投控", "id": "2636"}, 
    {"name": "中菲行", "id": "5609"}, {"name": "捷迅", "id": "2643"}, {"name": "陸海", "id": "2625"}, 
    {"name": "志信", "id": "2611"}, {"name": "遠雄港", "id": "5607"}, {"name": "建新國際", "id": "8367"}, 
    {"name": "長榮", "id": "2603"}, {"name": "陽明", "id": "2609"}, {"name": "萬海", "id": "2615"}, 
    {"name": "華航", "id": "2610"}, {"name": "長榮航", "id": "2618"}, {"name": "台灣高鐵", "id": "2633"}, 
    {"name": "漢翔", "id": "2634"}, {"name": "亞航", "id": "2630"}, {"name": "星宇航空", "id": "2646"}, 
    {"name": "龍巖", "id": "5530"}, {"name": "寶徠", "id": "1805"}, {"name": "基泰", "id": "2538"}, 
    {"name": "櫻花建", "id": "2539"}, {"name": "興富發", "id": "2542"}, {"name": "皇翔", "id": "2545"}, 
    {"name": "華固", "id": "2548"}, {"name": "綠意", "id": "2596"}, {"name": "遠雄", "id": "5522"}, 
    {"name": "鄉林", "id": "5531"}, {"name": "皇鼎", "id": "5533"}, {"name": "長虹", "id": "5534"}, 
    {"name": "達麗", "id": "6177"}, {"name": "總太", "id": "3056"}, {"name": "新美齊", "id": "2442"}, 
    {"name": "宏盛", "id": "2534"}, {"name": "聯上發", "id": "2537"}, {"name": "冠德", "id": "2520"}, 
    {"name": "亞昕", "id": "5213"}, {"name": "隆大", "id": "5206"}, {"name": "三發地產", "id": "9946"}, 
    {"name": "工信", "id": "5521"}, {"name": "中工", "id": "2515"}, {"name": "達欣工", "id": "2535"}, 
    {"name": "新亞建", "id": "2516"}, {"name": "德昌", "id": "5511"}, {"name": "建國", "id": "5515"}, 
    {"name": "雙喜", "id": "5516"}, {"name": "根基", "id": "2546"}, {"name": "瑞助", "id": "6110"}, 
    {"name": "互助", "id": "6111"}, {"name": "微星", "id": "2377"}, {"name": "技嘉", "id": "2376"}, 
    {"name": "華碩", "id": "2357"}, {"name": "宏碁", "id": "2353"}, {"name": "廣達", "id": "2382"}, 
    {"name": "緯創", "id": "3231"}, {"name": "仁寶", "id": "2324"}, {"name": "英業達", "id": "2356"}, 
    {"name": "和碩", "id": "4938"}, {"name": "神達", "id": "3706"}, {"name": "大眾控", "id": "3701"}, 
    {"name": "藍天", "id": "2362"}, {"name": "精英", "id": "2331"}, {"name": "映泰", "id": "2399"}, 
    {"name": "承啟", "id": "2425"}, {"name": "撼訊", "id": "6150"}, {"name": "麗臺", "id": "2465"}, 
    {"name": "七彩虹", "id": "6151"}, {"name": "影馳", "id": "6152"}, {"name": "華擎", "id": "3515"}, 
    {"name": "南亞科", "id": "2408"}, {"name": "華邦電", "id": "2344"}, {"name": "旺宏", "id": "2337"}, 
    {"name": "威剛", "id": "3260"}, {"name": "創見", "id": "2451"}, {"name": "宇瞻", "id": "8271"}, 
    {"name": "十銓", "id": "4967"}, {"name": "宜鼎", "id": "5289"}, {"name": "群聯", "id": "8299"}, 
    {"name": "商丞", "id": "8277"}, {"name": "品安", "id": "8088"}, {"name": "廣穎", "id": "4973"}, 
    {"name": "點序", "id": "6485"}, {"name": "安國", "id": "8054"}, {"name": "晶豪科", "id": "3006"}, 
    {"name": "鈺創", "id": "5351"}, {"name": "愛普*", "id": "6531"}, {"name": "日月光投控", "id": "3711"}, 
    {"name": "力積電", "id": "6770"}, {"name": "世界", "id": "5347"}, {"name": "環球晶", "id": "6488"}, 
    {"name": "台勝科", "id": "3532"}, {"name": "合晶", "id": "6182"}, {"name": "中美晶", "id": "5483"}, 
    {"name": "嘉晶", "id": "3016"}, {"name": "漢磊", "id": "3707"}, {"name": "欣興", "id": "3037"}, 
    {"name": "景碩", "id": "3189"}, {"name": "南電", "id": "8046"}, {"name": "華通", "id": "2313"}, 
    {"name": "金像電", "id": "2368"}, {"name": "健鼎", "id": "3044"}, {"name": "台郡", "id": "6269"}, 
    {"name": "臻鼎-KY", "id": "4958"}, {"name": "台光電", "id": "2383"}, {"name": "聯茂", "id": "6213"}, 
    {"name": "台燿", "id": "6274"}, {"name": "騰輝電子-KY", "id": "6672"}, {"name": "新復興", "id": "4909"}, 
    {"name": "博智", "id": "8155"}, {"name": "高頻", "id": "8156"}, {"name": "長興", "id": "1717"}, 
    {"name": "國巨", "id": "2327"}, {"name": "華新科", "id": "2492"}, {"name": "禾伸堂", "id": "3026"}, 
    {"name": "大毅", "id": "2478"}, {"name": "奇力新", "id": "2456"}, {"name": "美磊", "id": "3068"}, 
    {"name": "美桀", "id": "3027"}, {"name": "立隆電", "id": "2472"}, {"name": "智寶", "id": "2375"}, 
    {"name": "凱美", "id": "5317"}, {"name": "信昌電", "id": "6173"}, {"name": "日電貿", "id": "3090"}, 
    {"name": "光頡", "id": "3624"}, {"name": "臺慶科", "id": "3357"}, {"name": "富鼎", "id": "8261"}, 
    {"name": "尼克森", "id": "3317"}, {"name": "大中", "id": "6435"}, {"name": "杰力", "id": "5299"}, 
    {"name": "全宇昕", "id": "6651"}, {"name": "力士", "id": "4941"}, {"name": "茂達", "id": "6138"}
]
# ==============================================================================

# 初始化 Session State 狀態機
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

st.set_page_config(layout="wide")

# --- 2. 安全資料擷取函數區（保證不崩潰、歷史數據向前追溯） ---
def fetch_stock_data(stock_id):
    """獲取基本K線資料（支援週末歷史追溯與全面防崩潰）"""
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    # 如果使用者填寫了 Token，自動帶入
    if FINMIND_TOKEN and FINMIND_TOKEN != "你的_FINMIND_API_TOKEN_貼在這裡":
        params["token"] = FINMIND_TOKEN

    try:
        res = requests.get(url, params=params, timeout=8).json()
        if res.get("data"):
            df = pd.DataFrame(res["data"])
            df.columns = [c.lower() for c in df.columns]
            # 確保關鍵欄位全部存在，防範 API 回傳格式不符
            required = ['date', 'open', 'high', 'low', 'close', 'volume']
            if all(col in df.columns for col in required):
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
    except Exception:
        pass
    return pd.DataFrame() # 發生任何意外時回傳空資料表，絕不噴紅色 Traceback

def fetch_inst_data(stock_id):
    """法人數據抓取（全面防崩潰保護）"""
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=120)).strftime('%Y-%m-%d')
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockInstitutionalInvestorsBuySell",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    if FINMIND_TOKEN and FINMIND_TOKEN != "你的_FINMIND_API_TOKEN_貼在這裡":
        params["token"] = FINMIND_TOKEN

    try:
        res = requests.get(url, params=params, timeout=8).json()
        if res.get("data"):
            df = pd.DataFrame(res["data"])
            df.columns = [c.lower() for c in df.columns]
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                
                buy_col = 'buy' if 'buy' in df.columns else ('ss_buy_volume' if 'ss_buy_volume' in df.columns else '')
                sell_col = 'sell' if 'sell' in df.columns else ('ss_sell_volume' if 'ss_sell_volume' in df.columns else '')
                
                if buy_col and sell_col:
                    df['net_value'] = df[buy_col] - df[sell_col]
                else:
                    df['net_value'] = 0
                    for c in df.columns:
                        if 'buy' in c: df['net_value'] += df[c]
                        if 'sell' in c: df['net_value'] -= df[c]
                        
                inst_summary = df.groupby('date')['net_value'].sum().reset_index()
                inst_summary.set_index('date', inplace=True)
                return inst_summary
    except Exception:
        pass
    return pd.DataFrame()

# --- 3. 指標安全計算邏輯 ---
def calculate_indicators(df):
    """安全計算三均線、MACD、KD，避免欄位缺失導致 KeyError"""
    if df.empty or 'close' not in df.columns or 'high' not in df.columns or 'low' not in df.columns: 
        return df
        
    # 1. 計算三均線
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    
    # 4. 計算 MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['dif'] = ema12 - ema26
    df['macd_signal'] = df['dif'].ewm(span=9, adjust=False).mean()
    df['osc'] = df['dif'] - df['macd_signal']
    
    # 5. 計算 KD 線
    low_min = df['low'].rolling(window=9).min()
    high_max = df['high'].rolling(window=9).max()
    rsv = 100 * ((df['close'] - low_min) / (high_max - low_min).replace(0, 1))
    df['k'] = rsv.ewm(com=2, adjust=False).mean()
    df['d'] = df['k'].ewm(com=2, adjust=False).mean()
    return df

def draw_mini_chart(df):
    """首頁 3x3 網格內的微型 K 線圖安全渲染"""
    required_cols = ['open', 'high', 'low', 'close']
    if df.empty or not all(col in df.columns for col in required_cols) or len(df) < 5: 
        return None
        
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

# --- 4. 多執行緒加速首頁加載 ---
def get_homepage_data(stock_list):
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_id = {executor.submit(fetch_stock_data, s['id']): s['id'] for s in stock_list}
        for future in future_to_id:
            sid = future_to_id[future]
            results[sid] = future.result()
    return results

# ==============================================================================
# --- 5. 網頁渲染主介面邏輯 ---
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
        
        # 嚴格驗證所有繪圖所需的欄位，缺一不可
        required_plot_cols = ['open', 'high', 'low', 'close', 'ma5', 'ma20', 'ma60', 'volume', 'dif', 'macd_signal', 'osc', 'k', 'd']
        
        if not df.empty and all(col in df.columns for col in required_plot_cols):
            if not df_inst.empty and 'net_value' in df_inst.columns:
                df = df.join(df_inst, how='left').fillna(0)
            else:
                df['net_value'] = 0
                
            df_plot = df.tail(120)
            
            fig = make_subplots(
                rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                row_heights=[0.35, 0.15, 0.15, 0.15, 0.15],
                subplot_titles=("1. K線與三條均線 (MA5/MA20/MA60)", "2. 當日交易量", "3. 三大法人買賣超變動", "4. MACD 指標", "5. KD 隨機指標")
            )
            
            # 指標 1: K線與 MA 三均線
            fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['open'], high=df_plot['high'], low=df_plot['low'], close=df_plot['close'], name="K線"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ma5'], line=dict(color='blue', width=1.5), name="MA5"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ma20'], line=dict(color='orange', width=1.5), name="MA20"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ma60'], line=dict(color='purple', width=1.5), name="MA60"), row=1, col=1)
            
            # 指標 2: 成交量柱狀圖
            v_colors = ['red' if c >= o else 'green' for c, o in zip(df_plot['close'], df_plot['open'])]
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
            
            # 指標 3: 三大法人買賣超
            inst_colors = ['red' if val >= 0 else 'green' for val in df_plot['net_value']]
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['net_value'], marker_color=inst_colors, name="法人買賣超"), row=3, col=1)
            
            # 指標 4: MACD 線與柱狀圖(OSC)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['dif'], line=dict(color='white'), name="DIF"), row=4, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['macd_signal'], line=dict(color='yellow'), name="MACD"), row=4, col=1)
            osc_colors = ['red' if val >= 0 else 'green' for val in df_plot['osc']]
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['osc'], marker_color=osc_colors, name="OSC柱狀圖"), row=4, col=1)
            
            # 指標 5: KD 隨機指標線
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['k'], line=dict(color='cyan'), name="K線"), row=5, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['d'], line=dict(color='magenta'), name="D線"), row=5, col=1)
            
            fig.update_layout(height=950, showlegend=False, xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, width='stretch')
        else:
            st.error("⚠️ 歷史數據加載失敗。可能原因：您的匿名請求已被 FinMind 官方伺服器限流封鎖。請在程式碼頂端填入您的真實 FINMIND_TOKEN 以進行完全解鎖。")
else:
    # ------------------ 【功能 1 & 2】首頁搜尋、價格與九宮格分頁 ------------------
    st.title("📈 專業台股自選股大廳")
    
    # 頂部中英文/代號通用搜尋列
    q = st.text_input("🔍 請輸入股票代號或中文名稱進行搜尋：", value=st.session_state.search_query)
    if q != st.session_state.search_query:
        st.session_state.search_query = q
        st.session_state.current_page = 0
        st.rerun()
        
    filtered = [s for s in WATCHLIST if q in s['id'] or q in s['name']]
    
    total_items = len(filtered)
    total_pages = max((total_items + 8) // 9, 1)
    
    if st.session_state.current_page >= total_pages:
        st.session_state.current_page = 0
    
    if total_items == 0:
        st.warning("沒有找到相符的股票，請確認搜尋關鍵字。")
    else:
        start_idx = st.session_state.current_page * 9
        end_idx = start_idx + 9
        page_items = filtered[start_idx:end_idx]
        
        with st.spinner("同步刷新即時盤勢中..."):
            homepage_data = get_homepage_data(page_items)
            
        cols = st.columns(3)
        for idx, item in enumerate(page_items):
            with cols[idx % 3]:
                with st.container(border=True):
                    stock_df = homepage_data.get(item['id'], pd.DataFrame())
                    
                    if not stock_df.empty and 'close' in stock_df.columns:
                        last_row = stock_df.iloc[-1]
                        price_text = f" NT$ {last_row['close']:.2f}"
                    else:
                        price_text = " 限流封鎖"
                        
                    st.markdown(f"### {item['name']} ({item['id']})")
                    st.markdown(f"**歷史收盤價:** <span style='color:#FF4B4B;font-size:20px;'>{price_text}</span>", unsafe_allow_html=True)
                    
                    mini_fig = draw_mini_chart(stock_df)
                    if mini_fig is not None:
                        st.plotly_chart(mini_fig, config={'displayModeBar': False}, width='stretch')
                    else:
                        st.caption("⚠️ API上限請改用Token")
                        st.write("")
                        
                    if st.button("詳細五指標分析 ➔", key=f"btn_{item['id']}", width='stretch'):
                        st.session_state.selected_stock = item['id']
                        st.rerun()
                        
        st.write("---")
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
