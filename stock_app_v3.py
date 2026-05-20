import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

# --- 1. 全域配置 ---
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiUmF5X0NoZW4iLCJlbWFpbCI6ImNoZW5ydWl4aWFuMDBAZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiIref0.cRmVp07f_wOgMG3EZNfzZP5cmBRRX7VQX5ugV9fyVEk"

# 🚀 完整 205 檔股票清單
WATCHLIST = [
    {"name": "台積電", "id": "2330"}, {"name": "聯電", "id": "2303"}, {"name": "鴻海", "id": "2317"},
    {"name": "聯發科", "id": "2454"}, {"name": "台達電", "id": "2308"}, {"name": "廣達", "id": "2382"},
    {"name": "緯創", "id": "3231"}, {"name": "仁寶", "id": "2324"}, {"name": "英業達", "id": "2356"},
    {"name": "華碩", "id": "2357"}, {"name": "微星", "id": "2377"}, {"name": "技嘉", "id": "2376"},
    {"name": "光寶科", "id": "2301"}, {"name": "日月光投控", "id": "3711"}, {"name": "矽力*-KY", "id": "6415"},
    {"name": "瑞昱", "id": "2379"}, {"name": "聯詠", "id": "3034"}, {"name": "大立光", "id": "3008"},
    {"name": "力積電", "id": "6770"}, {"name": "旺宏", "id": "2337"}, {"name": "華邦電", "id": "2344"},
    {"name": "南亞科", "id": "2408"}, {"name": "世界", "id": "5347"}, {"name": "環球晶", "id": "6488"},
    {"name": "國巨", "id": "2327"}, {"name": "華通", "id": "2313"}, {"name": "欣興", "id": "3037"},
    {"name": "景碩", "id": "3189"}, {"name": "南電", "id": "8046"}, {"name": "臻鼎-KY", "id": "4958"},
    {"name": "台勝科", "id": "3532"}, {"name": "強茂", "id": "2481"}, {"name": "台半", "id": "5425"},
    {"name": "新唐", "id": "4919"}, {"name": "研華", "id": "2395"}, {"name": "樺漢", "id": "6414"},
    {"name": "佳世達", "id": "2352"}, {"name": "宏碁", "id": "2353"}, {"name": "神達", "id": "2315"},
    {"name": "金像電", "id": "2368"}, {"name": "奇鋐", "id": "3017"}, {"name": "雙鴻", "id": "3324"},
    {"name": "健策", "id": "3653"}, {"name": "世芯-KY", "id": "3661"}, {"name": "創意", "id": "3443"},
    {"name": "智原", "id": "3035"}, {"name": "祥碩", "id": "5269"}, {"name": "譜瑞-KY", "id": "4966"},
    {"name": "信驊", "id": "5274"}, {"name": "力旺", "id": "3529"}, {"name": "群聯", "id": "8299"},
    {"name": "威剛", "id": "3260"}, {"name": "十銓", "id": "4967"}, {"name": "宇瞻", "id": "8271"},
    {"name": "創見", "id": "2451"}, {"name": "友達", "id": "2409"}, {"name": "群創", "id": "3481"},
    {"name": "彩晶", "id": "6116"}, {"name": "精材", "id": "3374"}, {"name": "采鈺", "id": "6789"},
    {"name": "旺矽", "id": "6223"}, {"name": "穎崴", "id": "6515"}, {"name": "宏達電", "id": "2498"},
    {"name": "威盛", "id": "2388"}, {"name": "全訊", "id": "5222"}, {"name": "神準", "id": "3558"},
    {"name": "智邦", "id": "2345"}, {"name": "明泰", "id": "3380"}, {"name": "中磊", "id": "5388"},
    {"name": "啟碁", "id": "6285"}, {"name": "正文", "id": "4906"}, {"name": "合勤控", "id": "3704"},
    {"name": "兆赫", "id": "2485"}, {"name": "建漢", "id": "3062"}, {"name": "仲琦", "id": "2419"},
    {"name": "星通", "id": "3025"}, {"name": "智易", "id": "3596"}, {"name": "神腦", "id": "2450"},
    {"name": "長榮", "id": "2603"}, {"name": "陽明", "id": "2609"}, {"name": "萬海", "id": "2615"},
    {"name": "華航", "id": "2610"}, {"name": "長榮航", "id": "2618"}, {"name": "中鋼", "id": "2002"},
    {"name": "東和鋼鐵", "id": "2006"}, {"name": "新光鋼", "id": "2031"}, {"name": "中鴻", "id": "2014"},
    {"name": "大成鋼", "id": "2027"}, {"name": "官田鋼", "id": "2017"}, {"name": "台泥", "id": "1101"},
    {"name": "亞泥", "id": "1102"}, {"name": "台塑", "id": "1301"}, {"name": "南亞", "id": "1303"},
    {"name": "台化", "id": "1326"}, {"name": "台塑化", "id": "6505"}, {"name": "華夏", "id": "1305"},
    {"name": "台聚", "id": "1304"}, {"name": "亞聚", "id": "1308"}, {"name": "國喬", "id": "1312"},
    {"name": "聯成", "id": "1313"}, {"name": "中石化", "id": "1314"}, {"name": "長興", "id": "1717"},
    {"name": "統一", "id": "1216"}, {"name": "大成", "id": "1210"}, {"name": "卜蜂", "id": "1215"},
    {"name": "愛之味", "id": "1217"}, {"name": "泰山", "id": "1218"}, {"name": "聯華", "id": "1229"},
    {"name": "南僑", "id": "1702"}, {"name": "正新", "id": "2105"}, {"name": "建大", "id": "2106"},
    {"name": "南港", "id": "2101"}, {"name": "遠東新", "id": "1402"}, {"name": "新纖", "id": "1409"},
    {"name": "力麗", "id": "1444"}, {"name": "集盛", "id": "1455"}, {"name": "儒鴻", "id": "1476"},
    {"name": "聚陽", "id": "1477"}, {"name": "東和", "id": "1414"}, {"name": "裕隆", "id": "2201"},
    {"name": "中華車", "id": "2204"}, {"name": "三陽工業", "id": "2206"}, {"name": "和泰車", "id": "2207"},
    {"name": "汎德永業", "id": "2247"}, {"name": "世紀鋼", "id": "9958"}, {"name": "富邦金", "id": "2881"},
    {"name": "國泰金", "id": "2882"}, {"name": "兆豐金", "id": "2886"}, {"name": "中信金", "id": "2891"},
    {"name": "玉山金", "id": "2884"}, {"name": "第一金", "id": "2892"}, {"name": "合庫金", "id": "5880"},
    {"name": "華南金", "id": "2880"}, {"name": "元大金", "id": "2885"}, {"name": "台新金", "id": "2887"},
    {"name": "永豐金", "id": "2890"}, {"name": "開發金", "id": "2883"}, {"name": "新光金", "id": "2888"},
    {"name": "國票金", "id": "2889"}, {"name": "上海商銀", "id": "5876"}, {"name": "王道銀行", "id": "2897"},
    {"name": "臺企銀", "id": "2834"}, {"name": "台中銀", "id": "2812"}, {"name": "聯邊銀", "id": "2838"},
    {"name": "遠東銀", "id": "2845"}, {"name": "康和證", "id": "6016"}, {"name": "群益證", "id": "6005"},
    {"name": "第一保", "id": "2851"}, {"name": "新產", "id": "2850"}, {"name": "中再保", "id": "2852"},
    {"name": "三商壽", "id": "2867"}, {"name": "國產", "id": "2504"}, {"name": "國建", "id": "2501"},
    {"name": "冠德", "id": "2520"}, {"name": "興富發", "id": "2542"}, {"name": "華固", "id": "2548"},
    {"name": "長虹", "id": "5534"}, {"name": "皇翔", "id": "2545"}, {"name": "遠雄", "id": "5522"},
    {"name": "統一超", "id": "2912"}, {"name": "全家", "id": "5903"}, {"name": "寶雅", "id": "5904"},
    {"name": "遠東百", "id": "2903"}, {"name": "潤泰新", "id": "9945"}, {"name": "潤泰全", "id": "2915"},
    {"name": "巨大", "id": "9921"}, {"name": "美利達", "id": "9914"}, {"name": "愛地雅", "id": "8933"},
    {"name": "寶成", "id": "9904"}, {"name": "豐泰", "id": "9910"}, {"name": "百和", "id": "9938"},
    {"name": "中租-KY", "id": "5871"}, {"name": "裕融", "id": "9941"}, {"name": "和潤企業", "id": "6592"},
    {"name": "台汽電", "id": "8926"}, {"name": "中聯資源", "id": "9930"}, {"name": "信義", "id": "9940"},
    {"name": "鳳凰", "id": "5706"}, {"name": "雄獅", "id": "2731"}, {"name": "晶華", "id": "2707"},
    {"name": "王品", "id": "2727"}, {"name": "瓦城", "id": "2729"}, {"name": "美食-KY", "id": "2723"},
    {"name": "雲品", "id": "2748"}, {"name": "台耀", "id": "4746"}, {"name": "美時", "id": "1795"},
    {"name": "藥華藥", "id": "6446"}, {"name": "合一", "id": "4743"}, {"name": "中天", "id": "4128"},
    {"name": "智擎", "id": "4162"}, {"name": "生華科", "id": "6492"}, {"name": "大江", "id": "8436"},
    {"name": "葡萄王", "id": "1707"}, {"name": "杏輝", "id": "1734"}, {"name": "神隆", "id": "1789"},
    {"name": "永信", "id": "3705"}, {"name": "東洋", "id": "4105"}, {"name": "精華", "id": "1565"},
    {"name": "金可-KY", "id": "8406"}, {"name": "毛寶", "id": "1732"}, {"name": "康那香", "id": "9919"},
    {"name": "恆大", "id": "1325"}, {"name": "南六", "id": "6504"}, {"name": "上緯投控", "id": "3708"},
    {"name": "森崴能源", "id": "6806"}, {"name": "雲豹能源", "id": "6869"}, {"name": "泓德能源", "id": "6873"},
    {"name": "永崴投控", "id": "3712"}, {"name": "中興電", "id": "1513"}, {"name": "亞力", "id": "1514"},
    {"name": "華城", "id": "1519"}, {"name": "士電", "id": "1503"}, {"name": "樂事綠能", "id": "1529"},
    {"name": "東元", "id": "1504"}, {"name": "聲寶", "id": "1604"}, {"name": "大同", "id": "2371"},
    {"name": "中鼎", "id": "2404"}, {"name": "山隆", "id": "2616"}, {"name": "欣高", "id": "9931"},
    {"name": "欣雄", "id": "8908"}, {"name": "漢翔", "id": "2634"}, {"name": "雷虎", "id": "8033"},
    {"name": "千附精密", "id": "6829"}, {"name": "龍德造船", "id": "6753"}, {"name": "台船", "id": "2208"},
    {"name": "事欣科", "id": "4916"}, {"name": "上銀", "id": "2049"}, {"name": "直得", "id": "1597"},
    {"name": "亞德客-KY", "id": "1590"}, {"name": "川湖", "id": "2059"}, {"name": "金雨", "id": "4503"},
    {"name": "喬山", "id": "1736"}, {"name": "岱宇", "id": "1598"}, {"name": "拓凱", "id": "4536"},
    {"name": "明安", "id": "8938"}, {"name": "復盛應用", "id": "6670"}, {"name": "大魯閣", "id": "1432"},
    {"name": "好樂迪", "id": "9943"}, {"name": "錢櫃", "id": "8359"}, {"name": "特力", "id": "2908"},
    {"name": "櫻花", "id": "9911"}, {"name": "中保科", "id": "9917"}, {"name": "新保", "id": "9925"},
    {"name": "國光生", "id": "4142"}
]

# --- 2. 資料處理 ---
def fetch_data(stock_id):
    start = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": "TaiwanStockPrice", "data_id": stock_id, "start_date": start, "token": FINMIND_TOKEN}
    try:
        res = requests.get(url, params=params, timeout=10).json()
        return pd.DataFrame(res.get('data', []))
    except: return pd.DataFrame()

# --- 3. UI 介面 ---
st.set_page_config(layout="wide", page_title="專業台股監控大廳")
if 'page' not in st.session_state: st.session_state.page = 0

st.title("📈 專業台股監控大廳 (205檔)")
search = st.text_input("搜尋股票名稱或代碼")
display_list = [s for s in WATCHLIST if search in s['name'] or search in s['id']] if search else WATCHLIST

# 分頁處理
per_page = 12
total_pages = (len(display_list) + per_page - 1) // per_page
start = st.session_state.page * per_page
end = start + per_page

cols = st.columns(4)
for i, stock in enumerate(display_list[start:end]):
    with cols[i % 4]:
        st.markdown(f"**{stock['name']} ({stock['id']})**")
        if st.button("查看分析", key=stock['id']):
            st.session_state.selected = stock['id']

# 頁碼控制
c1, c2, c3 = st.columns([1,2,1])
if c1.button("上一頁") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
c2.write(f"第 {st.session_state.page + 1} 頁 / 共 {total_pages} 頁")
if c3.button("下一頁") and st.session_state.page < total_pages - 1: st.session_state.page += 1; st.rerun()
