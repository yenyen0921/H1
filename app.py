"""
AI 創新微課程 Taiwan Weather Forecast: 從氣象資料到互動式天氣預報應用
主應用程式 (Streamlit Web App)
資料來源：中央氣象署 CWA 開放資料平臺 (O-A0003-001: 局屬氣象站-現在天氣觀測報告)
技術棧：CWA O-A0003-001 × JSON × Python × SQLite × Streamlit × Folium
開發工具：Google Antigravity IDE × Gemini 內建 AI Agent × GitHub
"""

import os
import sys
import sqlite3
from io import StringIO
import pandas as pd
import streamlit as st

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
from src.weather_api import update_weather_data, CWA_DATASET_ID
from src.map_view import create_weather_map
from src.satellite import get_satellite_channels, get_channel_frames, get_latest_satellite_image

# 頁面基礎配置
st.set_page_config(
    page_title="Taiwan Weather Observation | CWA O-A0003-001",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================================
# 自訂高質感現代深色玻璃擬態樣式 (徹底根治側邊欄看不見問題，全面升級 UI)
# =========================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ------------------------------------------------------------- */
    /* 側邊欄專屬深色現代樣式 (防止出現白底白字、確保 100% 清晰可見) */
    /* ------------------------------------------------------------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0e1526 0%, #080c16 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    [data-testid="stSidebar"] * {
        font-family: 'Plus Jakarta Sans', 'Noto Sans TC', sans-serif !important;
    }

    /* 強制側邊欄所有標題、文字、標籤高對比度顯示 */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] strong {
        color: #f1f5f9 !important;
    }

    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #94a3b8 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.12) !important;
        margin: 1.2rem 0 !important;
    }

    /* 側邊欄文字輸入框與密碼框 */
    [data-testid="stSidebar"] input {
        background: rgba(15, 23, 42, 0.85) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }

    [data-testid="stSidebar"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
    }

    /* 側邊欄下拉選單 (Selectbox) */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: rgba(15, 23, 42, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }

    /* 側邊欄按鈕視覺增強 */
    [data-testid="stSidebar"] button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5) !important;
        transform: translateY(-1px);
    }

    /* 教授重點實作卡片 */
    .sidebar-feature-box {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(59, 130, 246, 0.35);
        border-left: 4px solid #10b981;
        border-radius: 10px;
        padding: 14px 16px;
        margin-top: 15px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }

    /* ------------------------------------------------------------- */
    /* 主畫面視覺元件樣式 (Hero Banner, Metric Cards, Tabs)           */
    /* ------------------------------------------------------------- */
    .hero-banner {
        background: linear-gradient(135deg, rgba(15, 32, 67, 0.95) 0%, rgba(17, 24, 39, 0.98) 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .hero-title {
        font-size: 26px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #ffffff, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .hero-subtitle {
        font-size: 14px;
        color: #94a3b8;
        margin-top: 6px;
        font-weight: 400;
    }
    
    .badge-tag {
        background: rgba(59, 130, 246, 0.15);
        backdrop-filter: blur(8px);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 700;
        border: 1px solid rgba(59, 130, 246, 0.4);
        color: #93c5fd;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* 指標數據卡片 (Metric Cards) 深色玻璃擬態 */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(20, 27, 45, 0.85) 0%, rgba(15, 23, 42, 0.85) 100%) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15) !important;
    }

    [data-testid="stMetricLabel"] p {
        font-size: 13px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] div {
        font-size: 28px !important;
        font-weight: 800 !important;
        color: #f8fafc !important;
    }

    /* 頂部頁籤 (Tabs) 優化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        font-weight: 700;
        padding: 10px 18px;
        border-radius: 8px 8px 0 0;
        color: #94a3b8;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #60a5fa !important;
        background: rgba(59, 130, 246, 0.1);
    }

    /* 現代深色資訊卡片通用類別 */
    .glass-card {
        background: rgba(20, 27, 45, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def ensure_db_ready():
    init_db()
    regions = get_regions()
    if not regions:
        update_weather_data()
    return True

ensure_db_ready()


# =========================================================================
# --- 側邊欄控制器 (已修正白色背景導致文字看不見之問題) ---
# =========================================================================
with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1592210454359-9043f067919b?w=600&auto=format&fit=crop&q=80",
        use_container_width=True
    )
    
    st.markdown("""
    <div style="margin-top: 10px; margin-bottom: 4px;">
        <h2 style="margin: 0; font-size: 22px; font-weight: 800; color: #f8fafc;">⚙️ 系統控制台</h2>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
            氣象資料集代號：<b style="color: #60a5fa;">CWA O-A0003-001</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("#### 🌐 CWA 資料同步 (API Sync)")
    api_key_input = st.text_input(
        "中央氣象署 API Key (授權碼)",
        type="password",
        help="輸入授權碼後將直接向中央氣象署 O-A0003-001 即時觀測 API 請求最新數據。未填寫時使用內建標準實測快取。"
    )
    
    if st.button("🔄 同步 / 更新氣象觀測庫", use_container_width=True, type="primary"):
        with st.spinner(f"正在自 CWA {CWA_DATASET_ID} 擷取並更新至 SQLite 資料庫..."):
            success, msg, _ = update_weather_data(api_key=api_key_input)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error("更新失敗，請檢查網路連線或 API Key。")

    st.divider()
    
    # 地區/測站選擇 (課程序號 13)
    st.markdown("#### 📍 測站 / 分區選擇")
    all_regions = get_regions()
    if not all_regions:
        all_regions = ["臺北", "臺中", "高雄", "花蓮", "北部地區", "中部地區", "南部地區", "東部地區"]
    
    default_idx = all_regions.index("臺北") if "臺北" in all_regions else 0
    selected_region = st.selectbox(
        "選擇氣象觀測站 / 預報分區：",
        options=all_regions,
        index=default_idx,
        key="sidebar_station_select"
    )

    # 日期篩選 (課程序號 18)
    st.markdown("#### 📅 地圖展示日期")
    available_dates = get_available_dates()
    if not available_dates:
        available_dates = [pd.Timestamp.now().strftime("%Y-%m-%d")]
    
    selected_date = st.selectbox(
        "選擇地圖展示日期：",
        options=available_dates,
        index=0,
        key="sidebar_date_select"
    )

    st.divider()
    
    # 教授指定實作重點卡片 (深色玻璃擬態高對比度卡片)
    st.markdown(f"""
    <div class="sidebar-feature-box">
        <div style="font-weight: 800; font-size: 14px; color: #34d399; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span>🎯</span> 教授指定實作重點
        </div>
        <div style="font-size: 13px; line-height: 1.8; color: #e2e8f0;">
            <div>✅ <b>資料集來源</b>：<code style="background:rgba(59,130,246,0.25);color:#93c5fd;padding:2px 6px;border-radius:4px;">CWA {CWA_DATASET_ID}</code></div>
            <div>✅ <b>即時觀測溫</b>：AirTemperature</div>
            <div>✅ <b>極端高低溫</b>：DailyHigh / Low</div>
            <div>✅ <b>測站坐標定位</b>：真實經緯度</div>
            <div>✅ <b>去重寫入</b>：INSERT OR REPLACE</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================================
# --- 主畫面頂部 Hero Banner ---
# =========================================================================
st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">🌤️ CWA O-A0003-001 氣象觀測與預報平台</div>
        <div class="hero-subtitle">中央氣象署局屬氣象站實測報告 × SQLite 資料庫 × 互動式視覺化儀表板</div>
    </div>
    <div class="badge-tag">
        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#34d399;box-shadow:0 0 8px #34d399;"></span>
        📍 當前選取測站：<b style="color:#ffffff;">{selected_region}</b>
    </div>
</div>
""", unsafe_allow_html=True)


# --- 取得所選測站/地區預報與實測紀錄 ---
df_region = get_forecasts_by_region(selected_region)

if not df_region.empty:
    today_row = df_region.iloc[0]
    today_min = float(today_row["minT"])
    today_max = float(today_row["maxT"])
    today_cur = float(today_row["currentT"]) if pd.notna(today_row.get("currentT")) else round((today_min + today_max) / 2.0, 1)
    weather_desc = str(today_row.get("weather", "晴時多雲")) if pd.notna(today_row.get("weather")) else "晴時多雲"
    today_diff = round(today_max - today_min, 1)
    
    # 頂部四項核心指標卡片 (課程序號 16 & 19)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label=f"🌡️ {selected_region} 即時觀測氣溫",
            value=f"{today_cur} °C",
            delta=f"天氣：{weather_desc}",
            delta_color="normal"
        )
    with col2:
        st.metric(
            label="🔥 當日最高溫 (DailyHigh)",
            value=f"{today_max} °C",
            delta=f"日溫差 {today_diff} °C",
            delta_color="off"
        )
    with col3:
        st.metric(
            label="❄️ 當日最低溫 (DailyLow)",
            value=f"{today_min} °C",
            delta="實測低溫紀錄",
            delta_color="normal"
        )
    with col4:
        week_avg = round((df_region["minT"].mean() + df_region["maxT"].mean()) / 2.0, 1)
        st.metric(
            label="📊 觀測期平均氣溫",
            value=f"{week_avg} °C",
            delta=f"共 {len(df_region)} 筆觀測紀錄",
            delta_color="off"
        )
else:
    st.warning("⚠️ 目前資料庫尚無該地區/測站紀錄，請點選側邊欄「同步 / 更新氣象觀測庫」。")


# =========================================================================
# --- 分頁標籤導覽 (Tabs) ---
# =========================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 氣溫趨勢與資料表格 (Trend & Table)",
    "🗺️ CWA 測站地圖視覺化 (Station Map)",
    "🛰️ 即時衛星雲圖 (Satellite View)",
    "💾 SQLite 資料庫檢查器 (SQL Inspector)",
    "🤖 AI 智能生活與穿著建議 (AI Weather Advisor)"
])


# =========================================================================
# TAB 1: 氣溫趨勢走勢圖與詳細表格 (課程序號 14, 15, 16)
# =========================================================================
with tab1:
    st.subheader(f"📈 【{selected_region}】氣象站最高溫與最低溫走勢圖")
    
    if not df_region.empty:
        plot_df = df_region.copy()
        plot_df["dataDate"] = pd.to_datetime(plot_df["dataDate"]).dt.strftime("%m/%d (%a)")
        
        # 準備雙線折線圖
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
        col_tbl_title, col_tbl_dl = st.columns([3, 1])
        with col_tbl_title:
            st.subheader(f"📋 【{selected_region}】氣象測站詳細觀測資料表")
        with col_tbl_dl:
            # 支援 CSV 匯出功能
            csv_data = df_region.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 匯出資料為 CSV",
                data=csv_data,
                file_name=f"weather_{selected_region}.csv",
                mime="text/csv",
                use_container_width=True
            )

        display_df = df_region.copy()
        display_df.rename(columns={
            "dataDate": "觀測/預報日期",
            "currentT": "即時實測溫 (°C)",
            "minT": "最低溫 MinT (°C)",
            "maxT": "最高溫 MaxT (°C)",
            "weather": "天氣概況"
        }, inplace=True)
        display_df["溫差 Range (°C)"] = round(display_df["最高溫 MaxT (°C)"] - display_df["最低溫 MinT (°C)"], 1)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("尚無圖表資料可供顯示。")


# =========================================================================
# TAB 2: CWA 測站地圖視覺化 (課程序號 17, 18, 19)
# =========================================================================
with tab2:
    st.subheader(f"🗺️ 全台氣象測站即時分布地圖 — 【{selected_date}】")
    st.caption("依據 CWA O-A0003-001 測站經緯度坐標精準繪製，並依照實測氣溫進行四級分色渲染。可隨時疊加雷達與衛星圖層。")

    df_date_all = get_all_forecasts_by_date(selected_date)

    if not df_date_all.empty:
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 2])
        with col_ctrl1:
            overlay_radar = st.checkbox("📡 疊加 CWA 即時雷達迴波", value=False, help="將中央氣象署全台雷達整合迴波圖疊加於地圖上")
        with col_ctrl2:
            overlay_sat = st.checkbox("☁️ 疊加台灣衛星雲圖 (TWI)", value=False, help="將最新台灣鄰近海域彩色紅外線雲圖疊加於地圖上")
        with col_ctrl3:
            st.info("💡 提示：地圖右上角圖層控制器可自由切換 Esri 航照衛星底圖、淺色地圖與深色地圖。")

        col_map, col_info = st.columns([3, 2])

        with col_map:
            try:
                from streamlit_folium import st_folium
                weather_map = create_weather_map(
                    df_date_all,
                    selected_date,
                    show_radar=overlay_radar,
                    show_satellite=overlay_sat
                )
                st_folium(weather_map, width=700, height=540)
            except Exception as e:
                st.warning(f"地圖載入提醒：{e}。若 streamlit_folium 尚未安裝，請使用 pip install streamlit-folium。")

        with col_info:
            st.markdown(f"#### 📊 {selected_date} 測站觀測列表 ({len(df_date_all)} 測站)")
            
            # 分區篩選器
            filter_region = st.selectbox(
                "篩選區域：",
                options=["全部測站 (All)", "北部地區", "中部地區", "南部地區", "東部地區", "離島地區"],
                index=0,
                key="map_region_filter"
            )

            filtered_df = df_date_all
            if filter_region != "全部測站 (All)":
                filtered_df = df_date_all[df_date_all["regionName"].str.contains(filter_region[:2]) | (df_date_all["regionName"] == filter_region)]
                if filtered_df.empty:
                    filtered_df = df_date_all

            # 滾動清單呈現 (已優化為深色高質感卡片，不再有白色背板衝突)
            st_container = st.container(height=480)
            with st_container:
                for _, r in filtered_df.iterrows():
                    r_name = r["regionName"]
                    r_min = r["minT"]
                    r_max = r["maxT"]
                    r_cur = r["currentT"] if pd.notna(r.get("currentT")) else round((r_min + r_max)/2.0, 1)
                    r_w = r["weather"] if pd.notna(r.get("weather")) and r.get("weather") else "良好"
                    
                    badge_color = "#3b82f6" if r_cur < 20 else ("#10b981" if r_cur <= 25 else ("#f59e0b" if r_cur <= 30 else "#ef4444"))
                    
                    st.markdown(f"""
                    <div style="padding: 12px 16px; margin-bottom: 10px; background: rgba(20, 27, 45, 0.85); border-radius: 10px; border-left: 5px solid {badge_color}; border-top: 1px solid rgba(255,255,255,0.08); border-right: 1px solid rgba(255,255,255,0.08); border-bottom: 1px solid rgba(255,255,255,0.08); box-shadow: 0 4px 12px rgba(0,0,0,0.25);">
                        <div style="font-weight: 700; font-size: 15px; color: #f8fafc; display: flex; justify-content: space-between; align-items: center;">
                            <span>📍 {r_name}</span>
                            <span style="background: {badge_color}22; color: {badge_color}; padding: 3px 10px; border-radius: 20px; font-weight: bold; border: 1px solid {badge_color}55; font-size: 13px;">{r_cur}°C ({r_w})</span>
                        </div>
                        <div style="font-size: 13px; color: #94a3b8; margin-top: 6px;">
                            最低: <b style="color: #60a5fa;">{r_min}°C</b> ｜ 最高: <b style="color: #f87171;">{r_max}°C</b> ｜ 溫差: <b style="color: #fbbf24;">{round(r_max - r_min, 1)}°C</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ 找不到日期 {selected_date} 的地圖資料。")


# =========================================================================
# TAB 3: 即時氣象衛星雲圖 (CWA Satellite Imagery Hub)
# =========================================================================
with tab3:
    st.subheader("🛰️ 中央氣象署 (CWA) 即時高解析衛星雲圖")
    st.caption("支援多波段衛星影像、台灣鄰近與東亞全區、色調強化、可見光與縮時動態歷程播放。")

    channels = get_satellite_channels()
    channel_options = {cid: cdata["name"] for cid, cdata in channels.items()}

    col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
    with col_sel1:
        selected_cid = st.selectbox(
            "選擇衛星雲圖觀測頻道：",
            options=list(channel_options.keys()),
            format_func=lambda x: channel_options[x],
            index=0
        )
    with col_sel2:
        view_mode = st.radio(
            "檢視模式：",
            options=["即時最新觀測", "動態縮時歷程 (Timelapse)"],
            horizontal=True
        )
    with col_sel3:
        if st.button("🔄 刷新最新雲圖", use_container_width=True):
            st.rerun()

    current_channel_meta = channels[selected_cid]

    # 縮時歷程長度選擇
    num_frames = 12
    if view_mode == "動態縮時歷程 (Timelapse)":
        col_frame_opt, col_tip = st.columns([1, 2])
        with col_frame_opt:
            num_frames = st.selectbox(
                "歷程跨度：",
                options=[6, 12, 18, 24],
                format_func=lambda n: f"過去 {n} 幀 (~{n*10//60} 小時)",
                index=1
            )
        with col_tip:
            st.caption("每 10 分鐘一幀，可回溯長時間的大氣雲系移動趨勢。")

    frames = get_channel_frames(selected_cid, limit=num_frames)

    # 選擇目前要顯示的影格
    selected_frame = frames[-1] if frames else {
        "url": current_channel_meta["static_url"],
        "time": "最新即時"
    }

    if view_mode == "動態縮時歷程 (Timelapse)" and len(frames) > 1:
        st.markdown("##### ⏱️ 縮時時間軸控制 (每 10 分鐘一幀)")
        time_labels = [f["time"] for f in frames]
        time_idx = st.select_slider(
            "滑動以回溯過去雲系演變歷程：",
            options=list(range(len(frames))),
            value=len(frames) - 1,
            format_func=lambda idx: time_labels[idx]
        )
        selected_frame = frames[time_idx]

    st.info("💡 **為什麼最新衛星雲圖時間約為 15~20 分鐘前？** 氣象衛星位於 36,000 公里高空地球同步軌道，自儀器掃描、地面站接收、幾何輻射校正到氣象署伺服器上架，常態約需 15~20 分鐘的物理傳輸與影像運算時間。此為國際氣象觀測標準正常延遲。")

    # 主圖片與詳細解說雙欄展示
    col_img, col_detail = st.columns([3, 2])

    with col_img:
        st.markdown(f"""
        <div style="background: #111827; padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: 0 4px 16px rgba(0,0,0,0.3); margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; color: #e2e8f0; font-size: 13px;">
                <span>📡 <b>{current_channel_meta['name']}</b></span>
                <span style="background: #2563eb; color: #ffffff; padding: 3px 10px; border-radius: 12px; font-weight: bold;">🕒 {selected_frame['time']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.image(
            selected_frame["url"],
            caption=f"中央氣象署 CWA 觀測時間：{selected_frame['time']} ｜ 頻道：{current_channel_meta['name']}",
            use_container_width=True
        )

        st.markdown(f"""
        <div style="text-align: right; margin-top: 4px;">
            <a href="{selected_frame['url']}" target="_blank" style="font-size: 13px; color: #60a5fa; text-decoration: none; font-weight: bold;">
                🔗 開啟氣象署高解析原始圖檔 ↗
            </a>
        </div>
        """, unsafe_allow_html=True)

    with col_detail:
        # 深色現代玻璃擬態頻道解說卡 (徹底替代原淺色背景)
        st.markdown(f"""
        <div style="background: rgba(20, 27, 45, 0.85); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 14px; padding: 20px; margin-bottom: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);">
            <h4 style="margin: 0 0 12px 0; color: #60a5fa; font-weight: 800;">📋 頻道資訊與專業解讀</h4>
            <p style="margin: 8px 0; font-size: 14px; color: #cbd5e1;">
                <b style="color: #94a3b8;">分類：</b><span style="color: #f1f5f9;">{current_channel_meta['category']}</span>
            </p>
            <p style="margin: 8px 0; font-size: 14px; color: #cbd5e1;">
                <b style="color: #94a3b8;">影像解析度：</b><span style="color: #f1f5f9;">{current_channel_meta['resolution']}</span>
            </p>
            <p style="margin: 8px 0; font-size: 14px; color: #cbd5e1;">
                <b style="color: #94a3b8;">頻道說明：</b><span style="color: #e2e8f0;">{current_channel_meta['desc']}</span>
            </p>
            <div style="margin-top: 14px; padding: 12px 14px; background: rgba(59, 130, 246, 0.12); border-left: 4px solid #3b82f6; border-radius: 8px; font-size: 13px; color: #93c5fd; line-height: 1.6;">
                <b style="color: #bfdbfe;">💡 判讀訣竅：</b><br>
                {current_channel_meta['interpretation']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 氣象判讀教學小百科
        with st.expander("📚 衛星雲圖判讀知識庫 (專業氣象心法)", expanded=True):
            st.markdown("""
            1. **彩色紅外線 (IR Color)**：
               - 紅外線測量的是**雲頂溫度**。溫度越低（代表雲頂高聳發展旺盛），顯示為純白色或濃郁色塊。
               - 不受日夜限制，全天候 24 小時均可觀測。
            2. **色調強化 (Enhanced IR)**：
               - 將強烈對流低溫雲頂（約 -40°C 至 -80°C）以鮮豔色彩區分（綠色、黃色、橘紅色、粉紫色）。
               - **對流旺盛的降雨核心**（如雷陣雨或颱風眼牆）會呈現紅色或紫色。
            3. **真實色彩 (True Color)**：
               - 日間使用可見光紅綠藍三原色合成，最接近人眼太空俯瞰畫面。
               - 能清晰分辨陸地綠地、海洋湛藍與捲雲、積雲的立體層次。
            4. **雷達迴波 (Radar)**：
               - 主動發射微波偵測水滴粒子，數值越高 (dBZ) 代表降雨越強烈，適合評估未來 1-2 小時即時降雨。
            """)

        # 快捷頻道卡片切換
        st.markdown("##### ⚡ 快速頻道推薦")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            st.markdown("""
            - 🇹🇼 **台灣彩色紅外線**：日常降雨預警首選
            - 🌈 **色調強化**：強烈午後雷雨與颱風觀測
            """)
        with col_q2:
            st.markdown("""
            - 📡 **雷達整合圖**：即時降水與豪大雨監控
            - 🌏 **東亞全區**：觀察冷鋒南下與華南雲系
            """)


# =========================================================================
# TAB 4: SQLite 資料庫檢查器 (課程序號 8, 9, 10, 20)
# =========================================================================
with tab4:
    st.subheader("💾 SQLite 資料庫驗證 (符合 CWA O-A0003-001 欄位)")
    st.markdown("""
    使用標準 SQL 檢查資料庫內容（課程序號 9 & 10）：
    - **資料庫檔案**：`data/data.db`
    - **資料表名稱**：`TemperatureForecasts` (包含 `UNIQUE(regionName, dataDate)` 去重保護)
    """)

    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
    quick_query = None
    with col_btn1:
        if st.button("🔍 查詢所有測站名稱", use_container_width=True):
            quick_query = "SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName;"
    with col_btn2:
        if st.button("🏆 今日高溫榜 TOP 5", use_container_width=True):
            quick_query = "SELECT regionName, dataDate, maxT, weather FROM TemperatureForecasts ORDER BY maxT DESC LIMIT 5;"
    with col_btn3:
        if st.button("❄️ 今日低溫榜 TOP 5", use_container_width=True):
            quick_query = "SELECT regionName, dataDate, minT, weather FROM TemperatureForecasts ORDER BY minT ASC LIMIT 5;"
    with col_btn4:
        if st.button("📊 統計總筆數與測站數", use_container_width=True):
            quick_query = "SELECT COUNT(*) AS total_records, COUNT(DISTINCT regionName) AS total_stations FROM TemperatureForecasts;"

    default_sql = quick_query or "SELECT id, regionName, dataDate, currentT, minT, maxT, weather, latitude, longitude FROM TemperatureForecasts LIMIT 15;"
    user_sql = st.text_area("SQL 查詢指令：", value=default_sql, height=80)

    col_exec, col_exp = st.columns([1, 1])
    with col_exec:
        exec_clicked = st.button("⚡ 執行 SQL 查詢", type="primary", use_container_width=True)

    if exec_clicked or quick_query:
        try:
            conn = get_db_connection()
            result_df = pd.read_sql_query(user_sql, conn)
            conn.close()
            st.success(f"查詢成功，共回傳 {len(result_df)} 筆結果：")
            st.dataframe(result_df, use_container_width=True)
            
            # 提供查詢結果下載
            if not result_df.empty:
                res_csv = result_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 匯出此 SQL 查詢結果為 CSV",
                    data=res_csv,
                    file_name="sql_query_result.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"SQL 執行失敗：{e}")

    st.divider()
    st.subheader("📊 資料庫完整紀錄一覽 (最新 50 筆)")
    all_records = get_all_records()
    st.dataframe(all_records.head(50), use_container_width=True, height=260)


# =========================================================================
# TAB 5 (全新亮點功能): 🤖 AI 智能生活與穿著建議 (AI Weather Advisor)
# 結合煥哥《打造你的 AI Coding Agent》微課程概念，為作業注入強大實用性！
# =========================================================================
with tab5:
    st.subheader(f"🤖 AI 氣象顧問 — 【{selected_region}】智能生活與穿搭指南")
    st.caption("根據 CWA O-A0003-001 即時實測氣溫、極端溫差與當日天候，透過智慧演算法提供全方位生活穿搭提醒。")

    if not df_region.empty:
        # 智能運算指標
        diff = today_diff
        cur_t = today_cur
        
        # 體感與穿著邏輯
        if cur_t >= 30:
            comfort_title = "炎熱高溫 (Hot)"
            comfort_badge = "🔥 炎熱高溫"
            badge_bg = "#ef4444"
            outfit_advice = "建議穿著**透氣排汗短袖、短褲或輕薄棉質衣物**。室內冷氣房可備一件薄襯衫防溫差。"
            umbrella_advice = "紫外線指數高，戶外活動請務必攜帶**陽傘、防曬乳與太陽眼鏡**，並定時補充水分。"
            activity_advice = "中午 11:00 ~ 15:00 避免長時間劇烈戶外運動，晨間或傍晚較適合慢跑與散步。"
        elif cur_t >= 25:
            comfort_title = "溫暖舒適 (Comfortable)"
            comfort_badge = "☀️ 溫暖宜人"
            badge_bg = "#10b981"
            outfit_advice = "適合穿著**短袖上衣、薄長褲或休閒襯衫**。早晚若有微風可備輕薄防風外套。"
            umbrella_advice = "外出可隨身攜帶**折疊晴雨兩用傘**，兼具防曬與防午後短暫陣雨功能。"
            activity_advice = "極為適合各類戶外運動、登山健行、洗曬厚重衣物與外出踏青。"
        elif cur_t >= 20:
            comfort_title = "舒適微涼 (Pleasant & Cool)"
            comfort_badge = "🍃 舒適微涼"
            badge_bg = "#3b82f6"
            outfit_advice = "建議採用**洋蔥式穿搭**：內層短袖/薄長袖，外加**針織衫、連帽外套或牛仔外套**，方便隨氣溫調節。"
            umbrella_advice = "天候多雲或轉陰，建議隨身攜帶輕便折傘以備不時之需。"
            activity_advice = "氣溫適中，非常適合慢跑、單車巡航與戶外攝影。"
        else:
            comfort_title = "偏涼微冷 (Cool / Chilly)"
            comfort_badge = "❄️ 偏涼微冷"
            badge_bg = "#6366f1"
            outfit_advice = "建議穿著**保暖長袖、厚長褲，並搭配防風厚外套或羽絨背心**。怕冷者可搭配圍巾。"
            umbrella_advice = "出門建議帶傘，並攜帶保溫瓶盛裝溫開水保持身體暖和。"
            activity_advice = "戶外運動前務必充分做好熱身運動，避免肌肉拉傷。"

        # 溫差提醒
        diff_alert = ""
        if diff >= 8.0:
            diff_alert = f"⚠️ **今日日夜溫差達 {diff}°C**！早出晚歸者請務必攜帶禦寒外套，預防著涼感冒或心血管不適。"
        elif diff >= 5.0:
            diff_alert = f"💡 今日日夜溫差為 {diff}°C，屬於常見日夜溫差範圍，早晚感受較涼。"
        else:
            diff_alert = f"💡 今日溫差僅 {diff}°C，整天體感溫度起伏較平緩。"

        # 四大生活卡片
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown(f"""
            <div style="background: rgba(20, 27, 45, 0.85); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 14px; padding: 20px; margin-bottom: 16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <h4 style="margin:0; color:#60a5fa;">👕 今日推薦穿搭</h4>
                    <span style="background:{badge_bg}; color:#ffffff; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold;">{comfort_badge}</span>
                </div>
                <p style="color:#e2e8f0; font-size:14px; line-height:1.7;">
                    {outfit_advice}
                </p>
                <div style="margin-top:12px; padding:10px 14px; background:rgba(59,130,246,0.12); border-left:3px solid #3b82f6; border-radius:6px; font-size:13px; color:#93c5fd;">
                    {diff_alert}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: rgba(20, 27, 45, 0.85); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 14px; padding: 20px;">
                <h4 style="margin:0 0 10px 0; color:#34d399;">🏃 戶外活動與日曬指數</h4>
                <p style="color:#e2e8f0; font-size:14px; line-height:1.7;">
                    {activity_advice}
                </p>
                <div style="font-size:13px; color:#94a3b8; margin-top:10px;">
                    <b>天候概況：</b>{weather_desc} ｜ <b>實測即時溫：</b>{cur_t}°C
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_c2:
            st.markdown(f"""
            <div style="background: rgba(20, 27, 45, 0.85); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 14px; padding: 20px; margin-bottom: 16px;">
                <h4 style="margin:0 0 10px 0; color:#fbbf24;">🌂 外出隨身配備與防護</h4>
                <p style="color:#e2e8f0; font-size:14px; line-height:1.7;">
                    {umbrella_advice}
                </p>
                <div style="margin-top:12px; padding:10px 14px; background:rgba(245,158,11,0.12); border-left:3px solid #f59e0b; border-radius:6px; font-size:13px; color:#fde68a;">
                    <b>💡 貼心提醒：</b>隨身攜帶環保水瓶，多喝水促進身體代謝與散熱。
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: rgba(20, 27, 45, 0.85); border: 1px solid rgba(139, 92, 246, 0.35); border-radius: 14px; padding: 20px;">
                <h4 style="margin:0 0 10px 0; color:#a78bfa;">🧺 居家生活與洗曬評估</h4>
                <p style="color:#e2e8f0; font-size:14px; line-height:1.7;">
                    {"今日天候良好、陽光充沛，極適合清洗床單、被套與厚重衣物，室外曬衣可在傍晚前自然風乾！" if "晴" in weather_desc else "今日雲量偏多或有偶陣雨，衣物洗曬建議置於通風陽台或使用室內除濕機加速乾燥。"}
                </p>
                <div style="font-size:13px; color:#94a3b8; margin-top:10px;">
                    <b>開窗通風：</b>{"晨間及傍晚氣溫適宜時開窗換氣，保持室內空氣清新。" if cur_t < 32 else "中午高溫炎熱時段建議關窗並開啟空調或風扇。"}
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.info("尚無測站觀測資料，無法產生 AI 穿著建議。")


# =========================================================================
# --- 頁尾署名 ---
# =========================================================================
st.divider()
st.markdown(f"""
<div style="text-align: center; color: #64748b; font-size: 13px; padding: 12px 0;">
    🌟 <b>AI 創新微課程 Taiwan Weather Observation</b> · 資料集來源：<b>CWA {CWA_DATASET_ID} (局屬氣象站)</b> · Antigravity × Gemini 實作
</div>
""", unsafe_allow_html=True)
