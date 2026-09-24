"""
AI 創新微課程 Taiwan Weather Forecast: 從氣象資料到互動式天氣預報應用
主應用程式 (Streamlit Web App)
資料來源：中央氣象署 CWA 開放資料平臺 (O-A0003-001: 局屬氣象站-現在天氣觀測報告)
技術棧：CWA O-A0003-001 × JSON × Python × SQLite × Streamlit × Folium
"""

import os
import sys
import sqlite3
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

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

st.set_page_config(
    page_title="Taiwan Weather Observation | CWA O-A0003-001",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂高質感現代 CSS 樣式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Noto Sans TC', -apple-system, sans-serif;
    }
    
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
        background: rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(8px);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 700;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #ffffff;
    }

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

    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
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


# --- 側邊欄控制器 ---
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1592210454359-9043f067919b?w=500&auto=format&fit=crop&q=60", width='stretch')
    st.title("⚙️ 系統控制台")
    st.caption(f"氣象資料集代號：**CWA {CWA_DATASET_ID}**")
    
    st.divider()
    
    st.subheader(f"🌐 CWA {CWA_DATASET_ID} 同步")
    api_key_input = st.text_input(
        "中央氣象署 API Key (授權碼)",
        type="password",
        help="輸入後將直接向中央氣象署 O-A0003-001 即時觀測 API 請求最新數據。未填寫時使用內建標準觀測資料展示。"
    )
    
    if st.button("🔄 同步 / 更新氣象觀測庫", width='stretch', type="primary"):
        with st.spinner(f"正在自 CWA {CWA_DATASET_ID} 擷取並更新至 SQLite 資料庫..."):
            success, msg, _ = update_weather_data(api_key=api_key_input)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error("更新失敗，請檢查網路連線或 API Key。")

    st.divider()
    
    # 地區/測站選擇 (課程序號 13)
    st.subheader("📍 測站/分區選擇 (Select Station)")
    all_regions = get_regions()
    if not all_regions:
        all_regions = ["臺北", "臺中", "高雄", "花蓮", "北部地區", "中部地區", "南部地區", "東部地區"]
    
    default_idx = all_regions.index("臺北") if "臺北" in all_regions else 0
    selected_region = st.selectbox(
        "選擇氣象觀測站 / 預報分區：",
        options=all_regions,
        index=default_idx
    )

    # 日期篩選 (課程序號 18)
    st.subheader("📅 地圖觀測日期 (Select Date)")
    available_dates = get_available_dates()
    if not available_dates:
        available_dates = [pd.Timestamp.now().strftime("%Y-%m-%d")]
    
    selected_date = st.selectbox(
        "選擇地圖展示日期：",
        options=available_dates,
        index=0
    )

    st.divider()
    st.markdown(f"""
    **🎯 教授指定實作重點：**
    - ✅ **資料集來源**：CWA `{CWA_DATASET_ID}`
    - ✅ **觀測站即時氣溫**：AirTemperature
    - ✅ **當日極端高低溫**：DailyHigh / DailyLow
    - ✅ **地理位置座標**：經緯度精確定位
    - ✅ **SQLite 去重存儲**：INSERT OR REPLACE
    """)


# --- 主畫面頂部 Hero Banner ---
st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">🌤️ CWA O-A0003-001 氣象觀測與預報平台</div>
        <div class="hero-subtitle">中央氣象署局屬氣象站實測報告 × SQLite 資料庫 × 互動式視覺化儀表板</div>
    </div>
    <div class="badge-tag">
        📍 當前選取：{selected_region}
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
            label=f"🔥 當日最高溫 (DailyHigh)",
            value=f"{today_max} °C",
            delta=f"溫差 {today_diff} °C",
            delta_color="off"
        )
    with col3:
        st.metric(
            label=f"❄️ 當日最低溫 (DailyLow)",
            value=f"{today_min} °C",
            delta="實測低溫",
            delta_color="normal"
        )
    with col4:
        week_avg = round((df_region["minT"].mean() + df_region["maxT"].mean()) / 2.0, 1)
        st.metric(
            label=f"📊 觀測期平均氣溫",
            value=f"{week_avg} °C",
            delta=f"共 {len(df_region)} 筆觀測紀錄",
            delta_color="off"
        )
else:
    st.warning("⚠️ 目前資料庫尚無該地區/測站紀錄，請點選側邊欄「同步 / 更新氣象觀測庫」。")


# --- 分頁標籤導覽 (Tabs) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 氣溫趨勢與資料表格 (Trend & Table)",
    "🗺️ CWA 測站地圖視覺化 (Station Map)",
    "🛰️ 即時衛星雲圖 (Satellite View)",
    "💾 SQLite 資料庫檢查器 (SQL Inspector)"
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
        st.subheader("📋 氣象測站詳細觀測資料表")
        display_df = df_region.copy()
        display_df.rename(columns={
            "dataDate": "觀測/預報日期",
            "currentT": "即時實測溫 (°C)",
            "minT": "最低溫 MinT (°C)",
            "maxT": "最高溫 MaxT (°C)",
            "weather": "天氣概況"
        }, inplace=True)
        display_df["溫差 Range (°C)"] = display_df["最高溫 MaxT (°C)"] - display_df["最低溫 MinT (°C)"]
        
        st.dataframe(
            display_df,
            width='stretch',
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
            st.info("💡 提示：地圖右上角圖層控制器可自由切換 Esri 衛星底圖、淺色地圖與暗黑地圖。")

        col_map, col_info = st.columns([3, 2])

        with col_map:
            weather_map = create_weather_map(
                df_date_all,
                selected_date,
                show_radar=overlay_radar,
                show_satellite=overlay_sat
            )
            st_folium(weather_map, width=700, height=530)

        with col_info:
            st.markdown(f"#### 📊 {selected_date} 測站觀測列表")
            for _, r in df_date_all.iterrows():
                r_name = r["regionName"]
                r_min = r["minT"]
                r_max = r["maxT"]
                r_cur = r["currentT"] if pd.notna(r.get("currentT")) else round((r_min + r_max)/2.0, 1)
                r_w = r["weather"] if pd.notna(r.get("weather")) and r.get("weather") else "良好"
                
                badge_color = "#2B6CB0" if r_cur < 20 else ("#38A169" if r_cur <= 25 else ("#DD6B20" if r_cur <= 30 else "#E53E3E"))
                
                st.markdown(f"""
                <div style="padding: 10px 14px; margin-bottom: 8px; background: #ffffff; border-radius: 8px; border-left: 5px solid {badge_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #edf2f7; border-left: 5px solid {badge_color};">
                    <div style="font-weight: 700; font-size: 14px; color: #1a202c; display: flex; justify-content: space-between;">
                        <span>📍 {r_name}</span>
                        <span style="color: {badge_color}; font-weight: bold;">{r_cur}°C ({r_w})</span>
                    </div>
                    <div style="font-size: 12px; color: #718096; margin-top: 3px;">
                        最低: <b>{r_min}°C</b> ｜ 最高: <b>{r_max}°C</b> ｜ 溫差: <b>{round(r_max - r_min, 1)}°C</b>
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
        if st.button("🔄 刷新最新雲圖", width='stretch'):
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

    st.info("💡 **為什麼最新衛星雲圖時間約為 15:50 ~ 16:00？** 氣象衛星位於 36,000 公里高空地球同步軌道，自儀器掃描、地面站接收、幾何輻射校正到氣象署伺服器上架，常態約需 15~20 分鐘的物理傳輸與影像運算時間。因此在 16:15 前後，氣象署最新發布的觀測正是 15:50 或 16:00，此為國際氣象觀測標準正常延遲。")

    # 主圖片與詳細解說雙欄展示
    col_img, col_detail = st.columns([3, 2])

    with col_img:
        st.markdown(f"""
        <div style="background: #1a202c; padding: 12px; border-radius: 12px; border: 1px solid #2d3748; box-shadow: 0 4px 16px rgba(0,0,0,0.25);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; color: #e2e8f0; font-size: 13px;">
                <span>📡 <b>{current_channel_meta['name']}</b></span>
                <span style="background: #3182ce; padding: 3px 8px; border-radius: 12px; font-weight: bold;">🕒 {selected_frame['time']}</span>
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
            <a href="{selected_frame['url']}" target="_blank" style="font-size: 12px; color: #3182ce; text-decoration: none;">
                🔗 開啟氣象署高解析原始圖檔
            </a>
        </div>
        """, unsafe_allow_html=True)

    with col_detail:
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
            <h4 style="margin: 0 0 10px 0; color: #2b6cb0;">📋 頻道資訊與解讀</h4>
            <p style="margin: 6px 0; font-size: 14px; color: #4a5568;">
                <b>分類：</b>{current_channel_meta['category']}
            </p>
            <p style="margin: 6px 0; font-size: 14px; color: #4a5568;">
                <b>影像解析度：</b>{current_channel_meta['resolution']}
            </p>
            <p style="margin: 6px 0; font-size: 14px; color: #4a5568;">
                <b>頻道說明：</b>{current_channel_meta['desc']}
            </p>
            <div style="margin-top: 12px; padding: 12px; background: #ebf8ff; border-left: 4px solid #3182ce; border-radius: 6px; font-size: 13px; color: #2c5282;">
                <b>💡 判讀訣竅：</b><br>
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
    st.subheader(f"💾 SQLite 資料庫驗證 (符合 CWA O-A0003-001 欄位)")
    st.markdown("""
    使用標準 SQL 檢查資料庫內容（課程序號 9 & 10）：
    - **資料庫檔案**：`data/data.db`
    - **資料表名稱**：`TemperatureForecasts` (包含 `UNIQUE(regionName, dataDate)` 去重保護)
    """)

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    quick_query = None
    with col_btn1:
        if st.button("🔍 查詢所有測站/分區名稱 (DISTINCT)", width='stretch'):
            quick_query = "SELECT DISTINCT regionName FROM TemperatureForecasts;"
    with col_btn2:
        if st.button("🔍 查詢臺北與臺中觀測資料", width='stretch'):
            quick_query = "SELECT regionName, dataDate, currentT, minT, maxT, weather FROM TemperatureForecasts WHERE regionName IN ('臺北', '臺中') ORDER BY dataDate ASC;"
    with col_btn3:
        if st.button("🔍 統計資料庫總筆數 (COUNT)", width='stretch'):
            quick_query = "SELECT COUNT(*) AS total_records, COUNT(DISTINCT regionName) AS total_stations FROM TemperatureForecasts;"

    default_sql = quick_query or "SELECT id, regionName, dataDate, currentT, minT, maxT, weather, latitude, longitude FROM TemperatureForecasts LIMIT 15;"
    user_sql = st.text_area("SQL 查詢指令：", value=default_sql, height=80)

    if st.button("⚡ 執行 SQL 查詢", type="primary"):
        try:
            conn = get_db_connection()
            result_df = pd.read_sql_query(user_sql, conn)
            conn.close()
            st.success(f"查詢成功，共回傳 {len(result_df)} 筆結果：")
            st.dataframe(result_df, width='stretch')
        except Exception as e:
            st.error(f"SQL 執行失敗：{e}")

    st.divider()
    st.subheader("📊 資料庫完整紀錄一覽")
    all_records = get_all_records()
    st.dataframe(all_records, width='stretch', height=250)


# --- 頁尾署名 ---
st.divider()
st.markdown(f"""
<div style="text-align: center; color: #94a3b8; font-size: 13px; padding: 10px 0;">
    🌟 <b>AI 創新微課程 Taiwan Weather Observation</b> · 資料集來源：<b>CWA {CWA_DATASET_ID}</b> · Antigravity × Gemini 實作
</div>
""", unsafe_allow_html=True)
