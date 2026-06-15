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

# 🚀 完整 205 檔熱門台股分類清單，保證一字不漏
WATCHLIST = [
    # --- 電子大廠 & 晶圓半導體 ---
    {"name": "台積電", "id": "2330"},
    {"name": "聯電", "id": "2303"},
    {"name": "鴻海", "id": "2317"},
    {"name": "聯發科", "id": "2454"},
    {"name": "台達電", "id": "2308"},
    {"name": "廣達", "id": "2382"},
    {"name": "緯創", "id": "3231"},
    {"name": "仁寶", "id": "2324"},
    {"name": "英業達", "id": "2356"},
    {"name": "華碩", "id": "2357"},
    {"name": "微星", "id": "2377"},
    {"name": "技嘉", "id": "2376"},
    {"name": "光寶科", "id": "2301"},
    {"name": "日月光投控", "id": "3711"},
    {"name": "矽力*-KY", "id": "6415"},
    {"name": "瑞昱", "id": "2379"},
    {"name": "聯詠", "id": "3034"},
    {"name": "大立光", "id": "3008"},
    {"name": "力積電", "id": "6770"},
    {"name": "旺宏", "id": "2337"},
    {"name": "華邦電", "id": "2344"},
    {"name": "南亞科", "id": "2408"},
    {"name": "世界", "id": "5347"},
    {"name": "環球晶", "id": "6488"},
    {"name": "國巨", "id": "2327"},
    {"name": "華通", "id": "2313"},
    {"name": "欣興", "id": "3037"},
    {"name": "景碩", "id": "3189"},
    {"name": "南電", "id": "8046"},
    {"name": "臻鼎-KY", "id": "4958"},
    {"name": "台勝科", "id": "3532"},
    {"name": "強茂", "id": "2481"},
    {"name": "台半", "id": "5425"},
    {"name": "新唐", "id": "4919"},
    {"name": "研華", "id": "2395"},
    {"name": "樺漢", "id": "6414"},
    {"name": "佳世達", "id": "2352"},
    {"name": "宏碁", "id": "2353"},
    {"name": "神達", "id": "2315"},
    {"name": "金像電", "id": "2368"},
    {"name": "奇鋐", "id": "3017"},
    {"name": "雙鴻", "id": "3324"},
    {"name": "健策", "id": "3653"},
    {"name": "世芯-KY", "id": "3661"},
    {"name": "創意", "id": "3443"},
    {"name": "智原", "id": "3035"},
    {"name": "祥碩", "id": "5269"},
    {"name": "譜瑞-KY", "id": "4966"},
    {"name": "信驊", "id": "5274"},
    {"name": "力旺", "id": "3529"},
    {"name": "群聯", "id": "8299"},
    {"name": "威剛", "id": "3260"},
    {"name": "十銓", "id": "4967"},
    {"name": "宇瞻", "id": "8271"},
    {"name": "創見", "id": "2451"},
    {"name": "友達", "id": "2409"},
    {"name": "群創", "id": "3481"},
    {"name": "彩晶", "id": "6116"},
    {"name": "精材", "id": "3374"},
    {"name": "采鈺", "id": "6789"},
    {"name": "旺矽", "id": "6223"},
    {"name": "穎崴", "id": "6515"},
    {"name": "宏達電", "id": "2498"},
    {"name": "威盛", "id": "2388"},
    {"name": "全訊", "id": "5222"},
    {"name": "神準", "id": "3558"},
    {"name": "智邦", "id": "2345"},
    {"name": "明泰", "id": "3380"},
    {"name": "中磊", "id": "5388"},
    {"name": "啟碁", "id": "6285"},
    {"name": "正文", "id": "4906"},
    {"name": "合勤控", "id": "3704"},
    {"name": "兆赫", "id": "2485"},
    {"name": "建漢", "id": "3062"},
    {"name": "仲琦", "id": "2419"},
    {"name": "星通", "id": "3025"},
    {"name": "智易", "id": "3596"},
    {"name": "神腦", "id": "2450"},
    # --- 航運航空 & 傳產鋼鐵水泥橡膠紡織 ---
    {"name": "長榮", "id": "2603"},
    {"name": "陽明", "id": "2609"},
    {"name": "萬海", "id": "2615"},
    {"name": "華航", "id": "2610"},
    {"name": "長榮航", "id": "2618"},
    {"name": "中鋼", "id": "2002"},
    {"name": "東和鋼鐵", "id": "2006"},
    {"name": "新光鋼", "id": "2031"},
    {"name": "中鴻", "id": "2014"},
    {"name": "大成鋼", "id": "2027"},
    {"name": "官田鋼", "id": "2017"},
    {"name": "台泥", "id": "1101"},
    {"name": "亞泥", "id": "1102"},
    {"name": "台塑", "id": "1301"},
    {"name": "南亞", "id": "1303"},
    {"name": "台化", "id": "1326"},
    {"name": "台塑化", "id": "6505"},
    {"name": "華夏", "id": "1305"},
    {"name": "台聚", "id": "1304"},
    {"name": "亞聚", "id": "1308"},
    {"name": "國喬", "id": "1312"},
    {"name": "聯成", "id": "1313"},
    {"name": "中石化", "id": "1314"},
    {"name": "長興", "id": "1717"},
    {"name": "統一", "id": "1216"},
    {"name": "大成", "id": "1210"},
    {"name": "卜蜂", "id": "1215"},
    {"name": "愛之味", "id": "1217"},
    {"name": "泰山", "id": "1218"},
    {"name": "聯華", "id": "1229"},
    {"name": "南僑", "id": "1702"},
    {"name": "正新", "id": "2105"},
    {"name": "建大", "id": "2106"},
    {"name": "南港", "id": "2101"},
    {"name": "遠東新", "id": "1402"},
    {"name": "新纖", "id": "1409"},
    {"name": "力麗", "id": "1444"},
    {"name": "集盛", "id": "1455"},
    {"name": "儒鴻", "id": "1476"},
    {"name": "聚陽", "id": "1477"},
    {"name": "東和", "id": "1414"},
    {"name": "裕隆", "id": "2201"},
    {"name": "中華車", "id": "2204"},
    {"name": "三陽工業", "id": "2206"},
    {"name": "和泰車", "id": "2207"},
    {"name": "汎德永業", "id": "2247"},
    {"name": "世紀鋼", "id": "9958"},
    # --- 金融保險集團 ---
    {"name": "富邦金", "id": "2881"},
    {"name": "國泰金", "id": "2882"},
    {"name": "兆豐金", "id": "2886"},
    {"name": "中信金", "id": "2891"},
    {"name": "玉山金", "id": "2884"},
    {"name": "第一金", "id": "2892"},
    {"name": "合庫金", "id": "5880"},
    {"name": "華南金", "id": "2880"},
    {"name": "元大金", "id": "2885"},
    {"name": "台新金", "id": "2887"},
    {"name": "永豐金", "id": "2890"},
    {"name": "開發金", "id": "2883"},
    {"name": "新光金", "id": "2888"},
    {"name": "國票金", "id": "2889"},
    {"name": "上海商銀", "id": "5876"},
    {"name": "王道銀行", "id": "2897"},
    {"name": "臺企銀", "id": "2834"},
    {"name": "台中銀", "id": "2812"},
    {"name": "聯邦銀", "id": "2838"},
    {"name": "遠東銀", "id": "2845"},
    {"name": "康和證", "id": "6016"},
    {"name": "群益證", "id": "6005"},
    {"name": "第一保", "id": "2851"},
    {"name": "新產", "id": "2850"},
    {"name": "中再保", "id": "2852"},
    {"name": "三商壽", "id": "2867"},
    # --- 營建、零售、觀光、生技能源 ---
    {"name": "國產", "id": "2504"},
    {"name": "國建", "id": "2501"},
    {"name": "冠德", "id": "2520"},
    {"name": "興富發", "id": "2542"},
    {"name": "華固", "id": "2548"},
    {"name": "長虹", "id": "5534"},
    {"name": "皇翔", "id": "2545"},
    {"name": "遠雄", "id": "5522"},
    {"name": "統一超", "id": "2912"},
    {"name": "全家", "id": "5903"},
    {"name": "寶雅", "id": "5904"},
    {"name": "遠東百", "id": "2903"},
    {"name": "潤泰新", "id": "9945"},
    {"name": "潤泰全", "id": "2915"},
    {"name": "巨大", "id": "9921"},
    {"name": "美利達", "id": "9914"},
    {"name": "愛地雅", "id": "8933"},
    {"name": "寶成", "id": "9904"},
    {"name": "豐泰", "id": "9910"},
    {"name": "百和", "id": "9938"},
    {"name": "中租-KY", "id": "5871"},
    {"name": "裕融", "id": "9941"},
    {"name": "和潤企業", "id": "6592"},
    {"name": "台汽電", "id": "8926"},
    {"name": "中聯資源", "id": "9930"},
    {"name": "信義", "id": "9940"},
    {"name": "鳳凰", "id": "5706"},
    {"name": "雄獅", "id": "2731"},
    {"name": "晶華", "id": "2707"},
    {"name": "王品", "id": "2727"},
    {"name": "瓦城", "id": "2729"},
    {"name": "美食-KY", "id": "2723"},
    {"name": "雲品", "id": "2748"},
    {"name": "台耀", "id": "4746"},
    {"name": "美時", "id": "1795"},
    {"name": "藥華藥", "id": "6446"},
    {"name": "合一", "id": "4743"},
    {"name": "中天", "id": "4128"},
    {"name": "智擎", "id": "4162"},
    {"name": "生華科", "id": "6492"},
    {"name": "大江", "id": "8436"},
    {"name": "葡萄王", "id": "1707"},
    {"name": "杏輝", "id": "1734"},
    {"name": "神隆", "id": "1789"},
    {"name": "永信", "id": "3705"},
    {"name": "東洋", "id": "4105"},
    {"name": "精華", "id": "1565"},
    {"name": "金可-KY", "id": "8406"},
    {"name": "毛寶", "id": "1732"},
    {"name": "康那香", "id": "9919"},
    {"name": "恆大", "id": "1325"},
    {"name": "南六", "id": "6504"},
    {"name": "上緯投控", "id": "3708"},
    {"name": "森崴能源", "id": "6806"},
    {"name": "雲豹能源", "id": "6869"},
    {"name": "泓德能源", "id": "6873"},
    {"name": "永崴投控", "id": "3712"},
    {"name": "中興電", "id": "1513"},
    {"name": "亞力", "id": "1514"},
    {"name": "華城", "id": "1519"},
    {"name": "士電", "id": "1503"},
    {"name": "樂事綠能", "id": "1529"},
    {"name": "東元", "id": "1504"},
    {"name": "聲寶", "id": "1604"},
    {"name": "大同", "id": "2371"},
    {"name": "中鼎", "id": "2404"},
    {"name": "山隆", "id": "2616"},
    {"name": "欣高", "id": "9931"},
    {"name": "欣雄", "id": "8908"},
    {"name": "漢翔", "id": "2634"},
    {"name": "雷虎", "id": "8033"},
    {"name": "千附精密", "id": "6829"},
    {"name": "龍德造船", "id": "6753"},
    {"name": "台船", "id": "2208"},
    {"name": "事欣科", "id": "4916"},
    {"name": "上銀", "id": "2049"},
    {"name": "直得", "id": "1597"},
    {"name": "亞德客-KY", "id": "1590"},
    {"name": "川湖", "id": "2059"},
    {"name": "金雨", "id": "4503"},
    {"name": "喬山", "id": "1736"},
    {"name": "岱宇", "id": "1598"},
    {"name": "拓凱", "id": "4536"},
    {"name": "明安", "id": "8938"},
    {"name": "復盛應用", "id": "6670"},
    {"name": "大魯閣", "id": "1432"},
    {"name": "好樂迪", "id": "9943"},
    {"name": "錢櫃", "id": "8359"},
    {"name": "特力", "id": "2908"},
    {"name": "櫻花", "id": "9911"},
    {"name": "中保科", "id": "9917"},
    {"name": "新保", "id": "9925"},
    {"name": "國光生", "id": "4142"}
]

# --- 2. 高效數據抓取與 V4 Headers 加密驗證 ---
def fetch_price_data(stock_id, start_date):
    """負責抓取原始股價數據 (V4 Headers 結構)"""
    URL = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockPrice", 
        "data_id": stock_id, 
        "start_date": start_date
    }
    headers = {}
    if FINMIND_TOKEN:
        headers["Authorization"] = f"Bearer {FINMIND_TOKEN}"
        
    try:
        res = requests.get(URL, params=params, headers=headers, timeout=15).json()
        df = pd.DataFrame(res.get('data', []))
        if df.empty:
            time.sleep(0.1)  # 👈 在走向公共通道前加上防禦性延遲配速
            res = requests.get(URL, params=params, timeout=15).json()
            df = pd.DataFrame(res.get('data', []))
        return df
    except:
        return pd.DataFrame()

def fetch_inst_data(stock_id, start_date):
    """負責抓取法人籌碼數據 (V4 Headers 結構)"""
    URL = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockInstitutionalInvestorsBuySell", 
        "data_id": stock_id, 
        "start_date": start_date
    }
    headers = {}
    if FINMIND_TOKEN:
        headers["Authorization"] = f"Bearer {FINMIND_TOKEN}"
        
    for _ in range(3):
        try:
            res = requests.get(URL, params=params, headers=headers, timeout=15).json()
            data = res.get('data', [])
            if not data:
                time.sleep(0.1)  # 👈 公共通道防禦性延遲
                res = requests.get(URL, params=params, timeout=15).json()
                data = res.get('data', [])
            if data: 
                return pd.DataFrame(data)
            time.sleep(0.5)
        except:
            time.sleep(0.5)
    return pd.DataFrame()

@st.cache_data(ttl=600)
def get_mini_price_data(stock_id):
    """大廳專用極速快取：僅抓取60天股價做迷你圖與今日/昨日價格判斷"""
    start_date_p = (datetime.date.today() - datetime.timedelta(days=60)).strftime("%Y-%m-%d")
    df_price = fetch_price_data(stock_id, start_date_p)
    if df_price.empty:
        return None
    df_price['date_str'] = pd.to_datetime(df_price['date']).dt.strftime('%Y-%m-%d')
    df_price = df_price.sort_values('date_str')
    df_price.set_index('date_str', inplace=True)
    return df_price

@st.cache_data(ttl=600)
def get_comprehensive_data(stock_id, days=730):
    """詳情頁專用：同步並行抓取股價與近一年法人數據並完美對齊"""
    start_date_p = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    start_date_i = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 這裡抓詳情頁資料保持 max_workers=2
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_p = executor.submit(fetch_price_data, stock_id, start_date_p)
        future_i = executor.submit(fetch_inst_data, stock_id, start_date_i)
        
        df_price = future_p.result()
        df_inst = future_i.result()

    if df_price.empty:
        return None

    try:
        df_price['date_str'] = pd.to_datetime(df_price['date']).dt.strftime('%Y-%m-%d')
        df_price = df_price.sort_values('date_str')

        if not df_inst.empty:
            df_inst['date_str'] = pd.to_datetime(df_inst['date']).dt.strftime('%Y-%m-%d')
            df_inst.columns = [c.lower() for c in df_inst.columns]
            
            b_col = 'buy' if 'buy' in df_inst.columns else ('buy_value' if 'buy_value' in df_inst.columns else None)
            s_col = 'sell' if 'sell' in df_inst.columns else ('sell_value' if 'sell_value' in df_inst.columns else None)
            
            if b_col and s_col:
                df_inst['net'] = pd.to_numeric(df_inst[b_col]) - pd.to_numeric(df_inst[s_col])
                daily_inst = df_inst.groupby('date_str')['net'].sum().reset_index()
                
                df = pd.merge(df_price, daily_inst, on='date_str', how='left')
                df.rename(columns={'net': 'Inst_Net'}, inplace=True)
                df['Inst_Net'] = df['Inst_Net'].fillna(0)
            else:
                df_price['Inst_Net'] = 0
                df = df_price
        else:
            df_price['Inst_Net'] = 0
            df = df_price

        df.set_index('date_str', inplace=True)
        
        # 均線指標計算 (MA 5/10/20)
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA10'] = df['close'].rolling(10).mean()
        df['MA20'] = df['close'].rolling(20).mean()
        
        # KD 指釋計算
        l9, h9 = df['min'].rolling(9).min(), df['max'].rolling(9).max()
        rsv = (df['close'] - l9) / (h9 - l9).replace(0, 1) * 100
        df['K'] = rsv.ewm(com=2).mean()
        df['D'] = df['K'].ewm(com=2).mean()
        
        # MACD 指標計算
        e12 = df['close'].ewm(span=12, adjust=False).mean()
        e26 = df['close'].ewm(span=26, adjust=False).mean()
        df['DIF'] = e12 - e26
        df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
        df['MACD_h'] = (df['DIF'] - df['DEA']) * 2
        
        return df
    except Exception as e:
        st.error(f"數據計算錯誤: {e}")
        return None

# --- 3. 輔助函數：多執行緒並行預加載大廳所需的迷你數據與篩選狀態 ---
def load_single_stock_summary(item):
    """並行載入單檔股票的迷你圖與快訊計算"""
    df = get_mini_price_data(item["id"])
    if df is not None and len(df) >= 2:
        recent = df.tail(30)
        latest_price = recent['close'].iloc[-1]
        change = recent['close'].iloc[-1] - recent['close'].iloc[-2]
        
        # 判斷核心邏輯：今日 K 線高於昨日 K 線 (今日收盤 > 昨日收盤)
        is_strong = recent['close'].iloc[-1] > recent['close'].iloc[-2]
        
        # 預先生成圖表
        color = 'red' if change >= 0 else 'green'
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
            plot_bgcolor='rgba(0,0,0,0)',
            dragmode=False
        )
        return {
            "id": item["id"], "name": item["name"], "fig": fig, 
            "price": latest_price, "change": change, "is_strong": is_strong, "valid": True
        }
    return {"id": item["id"], "name": item["name"], "valid": False}

# --- 4. 網頁介面 CSS 視覺美化 ---
st.set_page_config(layout="wide", page_title="台股自選控盤系統 APP v3")
st.markdown("""
    <style>
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

# --- 5. Session State 導航與分頁管理 ---
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'last_search' not in st.session_state:
    st.session_state.last_search = ""
if 'last_filter' not in st.session_state:
    st.session_state.last_filter = False

# --- A. 【詳情頁】五指標分析詳細頁面 ---
if st.session_state.selected_stock:
    active_id = st.session_state.selected_stock
    
    if st.button("← 返回自選股列表"):
        st.session_state.selected_stock = None
        st.rerun()
        
    st.markdown(f"## 📊 股票代碼 {active_id} 五指標分析")
    
    with st.spinner('正在使用多執行緒高速調用數據與計算指標...'):
        df = get_comprehensive_data(active_id, days=730)
    
    if df is not None:
        df_plot = df.copy()
        plot_width = max(1200, len(df_plot) * 22)
        
        fig = make_subplots(
            rows=5, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03,
            row_heights=[0.35, 0.1, 0.15, 0.2, 0.2],
            subplot_titles=("1. K線棒與三均線 (5/10/20 MA)", "2. 當日成交量", "3. 三大法人買賣超 (真實籌碼起伏)", "4. KD 指標", "5. MACD 趨勢")
        )

        # 功能 3-1: K線棒 + 3MA 線 (5/10/20)
        fig.add_trace(go.Candlestick(
            x=df_plot.index, open=df_plot['open'], high=df_plot['max'], low=df_plot['min'], close=df_plot['close'],
            name='K線', increasing_line_color='red', decreasing_line_color='green'
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA5'], name='MA5', line=dict(color='white', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA10'], name='MA10', line=dict(color='yellow', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA20'], name='MA20', line=dict(color='magenta', width=1.5)), row=1, col=1)

        # 功能 3-2: 當日成交量
        v_colors = ['red' if df_plot['close'].iloc[i] >= df_plot['open'].iloc[i] else 'green' for i in range(len(df_plot))]
        fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['Trading_Volume'], name='成交量', marker_color=v_colors), row=2, col=1)

        # 功能 3-3: 三大法人買賣超
        inst_colors = ['red' if x >= 0 else 'green' for x in df_plot['Inst_Net']]
        fig.add_trace(go.Bar(
            x=df_plot.index, y=df_plot['Inst_Net'], 
            name='法人淨額', marker_color=inst_colors,
            hovertemplate='淨額: %{y:,.0f}'
        ), row=3, col=1)

        # 功能 3-5: KD 指標
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['K'], name='K值', line=dict(color='orange')), row=4, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['D'], name='D值', line=dict(color='dodgerblue')), row=4, col=1)

        # 功能 3-4: MACD 趨勢
        m_colors = ['red' if x >= 0 else 'green' for x in df_plot['MACD_h']]
        fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['MACD_h'], name='MACD柱', marker_color=m_colors), row=5, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['DIF'], name='DIF', line=dict(color='white')), row=5, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['DEA'], name='DEA', line=dict(color='yellow')), row=5, col=1)

        fig.update_layout(
            width=plot_width, height=1400,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            dragmode='pan',
            showlegend=True
        )
        
        fig.update_yaxes(autorange=True, fixedrange=False)
        fig.update_xaxes(type='category', range=[len(df_plot)-100, len(df_plot)])

        st.plotly_chart(fig, use_container_width=False, config={
            'scrollZoom': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': [
                'zoom2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'select2d', 'lasso2d'
            ]
        })
    else:
        st.error("未能載入該股之有效數據，請確認代碼或重新整理。")

# --- B. 【大廳頁】自選股首頁列表、策略篩選與搜尋面板 ---
else:
    st.write("# 📈 台股自選股大廳")
    
    sidebar_col, main_col = st.columns([1, 4])
    
    with sidebar_col:
        st.markdown("### 🛠️ 策略活頁夾")
        filter_strong = st.checkbox("🔥 K線強勢股 (今日>昨日)", value=False, help="勾選後僅列出今日收盤價高於昨日收盤價的標的")
        
    with main_col:
        # 功能 2: 搜尋欄（支援中文名稱 與 4位數代號模糊搜尋）
        search_id = st.text_input("🔍 快速搜尋任何台股代碼或中文名稱", value="", placeholder="請輸入中文名稱或4位數代碼 (如: 陽明, 2330)...")
    
    # 計算基礎搜尋過濾
    query = search_id.strip().lower() if search_id else ""
    base_filtered = [item for item in WATCHLIST if query in item["id"] or query in item["name"].lower()] if query else WATCHLIST

    # 重設頁碼控制偵測
    if st.session_state.last_search != query or st.session_state.last_filter != filter_strong:
        st.session_state.current_page = 0
        st.session_state.last_search = query
        st.session_state.last_filter = filter_strong

    # 🚀 安全降級：將 max_workers 從 10 降到 3，減緩對 API 瞬間的衝擊
    final_stocks_summary = []
    with st.spinner("正在執行多執行緒高可用資料校準與策略分析..."):
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = pool.map(load_single_stock_summary, base_filtered)
            for res in results:
                if res["valid"]:
                    if filter_strong and not res["is_strong"]:
                        continue
                    final_stocks_summary.append(res)

    # 功能 1: 一頁顯示九個（3x3 九宮格）控制機制
    STOCKS_PER_PAGE = 9
    total_pages = max(1, (len(final_stocks_summary) + STOCKS_PER_PAGE - 1) // STOCKS_PER_PAGE)
    
    if st.session_state.current_page >= total_pages:
        st.session_state.current_page = 0
        
    start_idx = st.session_state.current_page * STOCKS_PER_PAGE
    end_idx = start_idx + STOCKS_PER_PAGE
    page_stocks = final_stocks_summary[start_idx:end_idx]

    with main_col:
        st.markdown(f"### 📌 自選股看盤清單 (符合篩選條件共: {len(final_stocks_summary)} 檔)")
        
        # 3x3 九宮格佈局
        cols = st.columns(3)
        for idx, item in enumerate(page_stocks):
            col = cols[idx % 3]
            with col:
                st.markdown(f"""
                    <div class="stock-card">
                        <div class="stock-title">{item['name']}</div>
                        <div class="stock-id">TWSE: {item['id']}</div>
                """, unsafe_allow_html=True)
                
                price_class = "stock-price-rise" if item["change"] >= 0 else "stock-price-fall"
                pct_class = "change-percent-rise" if item["change"] >= 0 else "change-percent-fall"
                sign = "+" if item["change"] >= 0 else ""
                
                prev_price = item["price"] - item["change"]
                pct = (item["change"] / prev_price) * 100 if prev_price != 0 else 0
                
                # 功能 1: 顯示最新價格與漲跌幅
                st.markdown(f"""
                    <div class="{price_class}">${item['price']:.1f}</div>
                    <div style="margin-top: 8px; margin-bottom: 12px;">
                        <span class="{pct_class}">{sign}{item['change']:.1f} ({sign}{pct:.2f}%)</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # 功能 1: 顯示小 K 線走勢圖 (Sparkline)
                st.plotly_chart(item["fig"], config={'staticPlot': True}, use_container_width=False)
                
                if st.button(f"進入 {item['name']} 5指標分析", key=f"btn_{item['id']}", use_container_width=True):
                    st.session_state.selected_stock = item["id"]
                    st.rerun()
                    
                st.markdown("</div>", unsafe_allow_html=True)

        # 功能 1: 跨頁導航控制器（下一頁功能維持）
        st.markdown("---")
        p_prev, p_info, p_next = st.columns([1, 2, 1])
        with p_prev:
            if st.button("◀ 上一頁", disabled=st.session_state.current_page == 0, use_container_width=True):
                st.session_state.current_page -= 1
                st.rerun()
        with p_info:
            st.markdown(f"<div style='text-align: center; font-size: 16px; margin-top: 6px; color: #8892b0;'>第 {st.session_state.current_page + 1} 頁 / 共 {total_pages} 頁</div>", unsafe_allow_html=True)
        with p_next:
            if st.button("下一頁 ▶", disabled=st.session_state.current_page >= total_pages - 1, use_container_width=True):
                st.session_state.current_page += 1
                st.rerun()
