"""
AI 創新微課程 Taiwan Weather Forecast: 從氣象資料到互動式天氣預報應用
主應用程式 (Streamlit Web App)
作者：煥哥 AI Coding Agent 實作
技術棧：CWA API × JSON × Python × SQLite × Streamlit × Folium
"""

import os
import sys
import sqlite3
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# 專案路徑設定
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from src.database import (
    DEFAULT_DB_PATH,
    init_db,
    get_regions,
    get_available_dates,
    get_forecasts_by_region,
    get_all_forecasts_by_date,
    get_all_records,
    get_db_connection
)
from src.weather_api import update_weather_data
from src.map_view import create_weather_map

# 頁面配置
st.set_page_config(
    page_title="Taiwan Weather Forecast | 台灣天氣預報",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂頂級高質感 CSS 樣式 (符合 Design Aesthetics 與現代儀表板風格)
st.markdown("""
<style>
    /* 全域字體與背景美化 */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Noto Sans TC', -apple-system, sans-serif;
    }
    
    /* 頂部 Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(15, 32, 39, 0.2);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-title {
        font-size: 26px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #ffffff, #a8ff78);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #e0e6ed;
        margin-top: 6px;
        font-weight: 400;
    }
    .badge-tag {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }
    
    /* 資訊指標卡片 (Metric Cards) */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 18px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }
    .metric-label {
        font-size: 13px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 4px;
    }
    .metric-note {
        font-size: 12px;
        color: #94a3b8;
        margin-top: 4px;
    }

    /* 標籤頁樣式優化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 15px;
        font-weight: 700;
        padding: 10px 18px;
        border-radius: 8px 8px 0 0;
    }

    /* 側邊欄優化 */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


# 1. 初始化資料庫與預載資料 (課程序號 8 & 20)
@st.cache_resource
def ensure_db_ready():
    """保證資料庫與資料表就緒，若為空則自動更新資料"""
    init_db()
    regions = get_regions()
    if not regions:
        update_weather_data()
    return True

ensure_db_ready()


# --- 側邊欄控制器 (課程序號 3, 4, 13, 18) ---
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1592210454359-9043f067919b?w=500&auto=format&fit=crop&q=60", width='stretch')
    st.title("⚙️ 系統控制台")
    st.caption("AI 創新微課程實作 · Antigravity × Gemini")
    
    st.divider()
    
    # 氣象資料同步控制區
    st.subheader("🌐 CWA 氣象資料更新")
    api_key_input = st.text_input(
        "中央氣象署 API Key (授權碼)",
        type="password",
        help="登入中央氣象署開放資料平台即可免費取得。未填寫時系統將使用內建完整預報資料展示。"
    )
    
    if st.button("🔄 同步 / 更新氣象資料庫", width='stretch', type="primary"):
        with st.spinner("正在自 CWA API 擷取與同步至 SQLite 資料庫..."):
            success, msg, _ = update_weather_data(api_key=api_key_input)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error("更新失敗，請檢查網路連線或 API Key。")

    st.divider()
    
    # 地區篩選器 (課程序號 13)
    st.subheader("📍 地區篩選 (Select Region)")
    all_regions = get_regions()
    if not all_regions:
        all_regions = ["北部地區", "中部地區", "南部地區", "東部地區"]
    
    selected_region = st.selectbox(
        "選擇預報地區：",
        options=all_regions,
        index=0
    )

    # 日期篩選器 (課程序號 18)
    st.subheader("📅 地圖日期篩選 (Select Date)")
    available_dates = get_available_dates()
    if not available_dates:
        available_dates = [pd.Timestamp.now().strftime("%Y-%m-%d")]
    
    selected_date = st.selectbox(
        "選擇地圖展示日期：",
        options=available_dates,
        index=0
    )

    st.divider()
    st.markdown("""
    **💡 學習重點指引：**
    - ✅ CWA Open Data API 串接
    - ✅ SQLite 關聯式資料庫設計
    - ✅ Pandas 資料結構清洗與分析
    - ✅ Streamlit Web 互動儀表板
    - ✅ Folium 互動地圖地理空間視覺化
    """)


# --- 主畫面頂部 Hero Banner (課程序號 16) ---
st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">🌤️ Taiwan Weather Forecast Dashboard</div>
        <div class="hero-subtitle">全台一週氣象資料庫 × 互動式天氣預報可視化平台</div>
    </div>
    <div class="badge-tag">
        📍 當前選取：{selected_region}
    </div>
</div>
""", unsafe_allow_html=True)


# --- 取得當前選定地區的預報資料 (課程序號 12) ---
df_region = get_forecasts_by_region(selected_region)

if not df_region.empty:
    today_row = df_region.iloc[0]
    today_min = float(today_row["minT"])
    today_max = float(today_row["maxT"])
    today_avg = round((today_min + today_max) / 2.0, 1)
    today_diff = round(today_max - today_min, 1)
    
    # 頂部四項核心指標卡片 (課程序號 16 & 19)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label=f"🔥 {selected_region} 今日最高氣溫",
            value=f"{today_max} °C",
            delta=f"溫差 {today_diff} °C",
            delta_color="off"
        )
    with col2:
        st.metric(
            label=f"❄️ {selected_region} 今日最低氣溫",
            value=f"{today_min} °C",
            delta=f"涼爽指數",
            delta_color="normal"
        )
    with col3:
        st.metric(
            label=f"🌡️ 平均預測氣溫",
            value=f"{today_avg} °C",
            delta="均溫舒適",
            delta_color="normal"
        )
    with col4:
        # 計算一週溫差趨勢
        week_avg = round((df_region["minT"].mean() + df_region["maxT"].mean()) / 2.0, 1)
        st.metric(
            label=f"📊 一週總體均溫",
            value=f"{week_avg} °C",
            delta=f"共 {len(df_region)} 天預報",
            delta_color="off"
        )
else:
    st.warning("⚠️ 目前資料庫尚無該地區預報紀錄，請點選側邊欄「同步 / 更新氣象資料庫」。")


# --- 分頁標籤導覽 (Tabs) ---
tab1, tab2, tab3 = st.tabs([
    "📈 一週氣溫趨勢分析 (Trend & Data)",
    "🗺️ 台灣氣溫地圖視覺化 (Interactive Map)",
    "💾 SQLite 資料庫管理 (SQL Inspector)"
])


# =========================================================================
# TAB 1: 一週氣溫折線圖與詳細表格 (課程序號 14, 15, 16)
# =========================================================================
with tab1:
    st.subheader(f"📈 {selected_region} 一週最高與最低氣溫走勢圖")
    
    if not df_region.empty:
        # 準備繪圖 DataFrame
        plot_df = df_region.copy()
        plot_df["dataDate"] = pd.to_datetime(plot_df["dataDate"]).dt.strftime("%m/%d (%a)")
        plot_df["溫差 (°C)"] = plot_df["maxT"] - plot_df["minT"]

        # 使用 Streamlit 原生折線圖展示 (清晰對比 MinT 與 MaxT)
        chart_data = plot_df.set_index("dataDate")[["maxT", "minT"]].rename(
            columns={"maxT": "最高氣溫 MaxT (°C)", "minT": "最低氣溫 MinT (°C)"}
        )
        st.line_chart(
            chart_data,
            color=["#e53e3e", "#3182ce"],
            height=340
        )

        st.divider()

        # 顯示資料表格 (課程序號 15)
        st.subheader("📋 一週氣溫詳細資料表")
        display_df = df_region.copy()
        display_df.rename(columns={
            "dataDate": "預報日期 (Date)",
            "minT": "最低溫 MinT (°C)",
            "maxT": "最高溫 MaxT (°C)"
        }, inplace=True)
        display_df["溫差 Range (°C)"] = display_df["最高溫 MaxT (°C)"] - display_df["最低溫 MinT (°C)"]
        display_df["舒適度評級"] = display_df["最高溫 MaxT (°C)"].apply(
            lambda x: "炎熱" if x >= 32 else ("溫暖舒適" if x >= 26 else "涼爽")
        )
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("尚無圖表資料可供顯示。")


# =========================================================================
# TAB 2: 台灣地圖視覺化 (課程序號 17, 18, 19)
# =========================================================================
with tab2:
    st.subheader(f"🗺️ 全台氣溫分布視覺化地圖 — 【{selected_date}】")
    st.caption("運用 Folium 地理圖層與溫度分級渲染，直觀呈現台灣北、中、南、東各大氣象分區均溫。")

    # 取得選定日期的全台資料
    df_date_all = get_all_forecasts_by_date(selected_date)

    if not df_date_all.empty:
        col_map, col_info = st.columns([3, 2])

        with col_map:
            # 建立並渲染 Folium 地圖
            weather_map = create_weather_map(df_date_all, selected_date)
            st_folium(weather_map, width=700, height=520)

        with col_info:
            st.markdown(f"#### 📊 {selected_date} 各區氣溫速報")
            for _, r in df_date_all.iterrows():
                r_name = r["regionName"]
                r_min = r["minT"]
                r_max = r["maxT"]
                r_avg = r["avgT"]
                
                # 依均溫選擇徽章顏色
                badge_color = "#2B6CB0" if r_avg < 20 else ("#38A169" if r_avg <= 25 else ("#DD6B20" if r_avg <= 30 else "#E53E3E"))
                
                st.markdown(f"""
                <div style="padding: 12px 16px; margin-bottom: 10px; background: #ffffff; border-radius: 8px; border-left: 6px solid {badge_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border-top: 1px solid #edf2f7; border-right: 1px solid #edf2f7; border-bottom: 1px solid #edf2f7;">
                    <div style="font-weight: 700; font-size: 15px; color: #1a202c; display: flex; justify-content: space-between;">
                        <span>📍 {r_name}</span>
                        <span style="color: {badge_color};">均溫 {r_avg}°C</span>
                    </div>
                    <div style="font-size: 13px; color: #718096; margin-top: 4px;">
                        最低溫：<b>{r_min}°C</b> ｜ 最高溫：<b>{r_max}°C</b> ｜ 日溫差：<b>{round(r_max - r_min, 1)}°C</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ 找不到日期 {selected_date} 的地圖資料。")


# =========================================================================
# TAB 3: SQLite 資料庫管理與 SQL 查詢驗證 (課程序號 8, 9, 10, 20)
# =========================================================================
with tab3:
    st.subheader("💾 SQLite 資料庫檢查與 SQL 語法驗證")
    st.markdown("""
    符合作業課程序號 9 & 10：使用標準 SQL 檢查資料庫設計與內容。
    - **資料庫檔案**：`data/data.db`
    - **資料表名稱**：`TemperatureForecasts` (包含 `UNIQUE(regionName, dataDate)` 去重保護)
    """)

    # 快捷 SQL 測試按鈕
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    quick_query = None
    with col_btn1:
        if st.button("🔍 執行：查詢所有地區 (SELECT DISTINCT)", use_container_width=True):
            quick_query = "SELECT DISTINCT regionName FROM TemperatureForecasts;"
    with col_btn2:
        if st.button("🔍 執行：查詢中部地區預報 (WHERE regionName='中部地區')", use_container_width=True):
            quick_query = "SELECT * FROM TemperatureForecasts WHERE regionName='中部地區' ORDER BY dataDate ASC;"
    with col_btn3:
        if st.button("🔍 執行：查詢全表總筆數 (COUNT)", use_container_width=True):
            quick_query = "SELECT COUNT(*) AS total_records, COUNT(DISTINCT regionName) AS total_regions FROM TemperatureForecasts;"

    # SQL 輸入框
    default_sql = quick_query or "SELECT id, regionName, dataDate, minT, maxT FROM TemperatureForecasts LIMIT 15;"
    user_sql = st.text_area("SQL 查詢指令：", value=default_sql, height=80)

    if st.button("⚡ 執行 SQL 查詢", type="primary"):
        try:
            conn = get_db_connection()
            result_df = pd.read_sql_query(user_sql, conn)
            conn.close()
            st.success(f"查詢成功，共回傳 {len(result_df)} 筆結果：")
            st.dataframe(result_df, use_container_width=True)
        except Exception as e:
            st.error(f"SQL 執行失敗：{e}")

    st.divider()
    st.subheader("📊 資料庫完整紀錄一覽")
    all_records = get_all_records()
    st.dataframe(all_records, use_container_width=True, height=250)


# --- 頁尾署名 ---
st.divider()
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 13px; padding: 10px 0;">
    🌟 <b>AI 創新微課程 Taiwan Weather Forecast</b> · Vibe Coding 實作專案 · 由 Google Antigravity & Gemini 賦能打造
</div>
""", unsafe_allow_html=True)
