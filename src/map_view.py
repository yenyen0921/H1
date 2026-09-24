"""
台灣氣溫地圖視覺化模組 (課程序號 17, 18, 19)
支援中央氣象署 CWA O-A0003-001 觀測站經緯度與即時天氣觀測。
使用 Folium 繪製互動式地圖，依據溫度高低提供色彩標記、資訊快顯 (Popup)、圖例 (Legend) 與衛星/雷達圖層疊加。
"""

import folium
from folium import plugins
import pandas as pd

# 各地區代表經緯度坐標 (備援)
FALLBACK_COORDINATES = {
    "北部地區": {"lat": 25.0478, "lon": 121.5319, "name": "北部地區"},
    "中部地區": {"lat": 24.1477, "lon": 120.6736, "name": "中部地區"},
    "南部地區": {"lat": 22.6273, "lon": 120.3014, "name": "南部地區"},
    "東部地區": {"lat": 23.9772, "lon": 121.6044, "name": "東部地區"},
    "離島地區": {"lat": 23.5656, "lon": 119.5630, "name": "離島地區"},
}

DEFAULT_CENTER = [23.85, 120.95]


def get_temperature_color(avg_temp: float) -> str:
    """
    依據溫度獲取對應標記顏色 (課程序號 17 圖例規範)
    < 20°C: 藍色
    20 - 25°C: 綠色
    25 - 30°C: 橘黃色
    > 30°C: 紅色
    """
    if avg_temp < 20.0:
        return "#2B6CB0"
    elif avg_temp <= 25.0:
        return "#38A169"
    elif avg_temp <= 30.0:
        return "#DD6B20"
    else:
        return "#E53E3E"


def get_temperature_category_label(avg_temp: float) -> str:
    """回傳溫度區間說明標籤"""
    if avg_temp < 20.0:
        return "涼爽 (< 20°C)"
    elif avg_temp <= 25.0:
        return "舒適 (20 ~ 25°C)"
    elif avg_temp <= 30.0:
        return "溫暖 (25 ~ 30°C)"
    else:
        return "炎熱 (> 30°C)"


def create_weather_map(
    df_date: pd.DataFrame,
    selected_date: str,
    show_radar: bool = False,
    show_satellite: bool = False
) -> folium.Map:
    """
    建立指定日期的台灣氣溫視覺化地圖 (課程序號 17, 18, 19)
    整合 CWA O-A0003-001 測站經緯度、多底圖切換與即時氣象衛星/雷達圖層
    """
    m = folium.Map(
        location=DEFAULT_CENTER,
        zoom_start=7.4,
        tiles=None,
        control_scale=True
    )

    # 1. 基礎底圖群組
    folium.TileLayer(
        "OpenStreetMap",
        name="🗺️ 街道地圖 (OpenStreetMap)",
        control=True
    ).add_to(m)

    folium.TileLayer(
        "CartoDB positron",
        name="⚪ 極簡淺色 (CartoDB)",
        control=True
    ).add_to(m)

    folium.TileLayer(
        "CartoDB dark_matter",
        name="🌙 科技深色 (Dark Matter)",
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="🛰️ 航照衛星底圖 (Esri Satellite)",
        control=True
    ).add_to(m)

    # 2. 氣象雷達迴波圖疊加層 (CWA 雷達整合，邊界涵蓋台灣海域)
    radar_bounds = [[20.4, 118.0], [26.8, 124.0]]
    folium.raster_layers.ImageOverlay(
        name="📡 即時雷達迴波圖 (CWA)",
        image="https://www.cwa.gov.tw/Data/radar/CV1_1000.png",
        bounds=radar_bounds,
        opacity=0.65,
        interactive=False,
        cross_origin=False,
        show=show_radar,
        control=True
    ).add_to(m)

    # 3. 台灣鄰近彩色雲圖疊加層
    sat_bounds = [[19.5, 117.5], [27.2, 124.5]]
    folium.raster_layers.ImageOverlay(
        name="☁️ 台灣衛星雲圖 (CWA TWI)",
        image="https://www.cwa.gov.tw/Data/satellite/TWI_IR1_CR_800/TWI_IR1_CR_800.jpg",
        bounds=sat_bounds,
        opacity=0.60,
        interactive=False,
        cross_origin=False,
        show=show_satellite,
        control=True
    ).add_to(m)

    # 測站標記群組
    station_group = folium.FeatureGroup(name="📍 CWA 氣象測站觀測點", show=True)

    # 頂部標題
    title_html = f"""
    <div style="position: fixed; 
                top: 15px; left: 60px; width: 340px; height: 50px; 
                background-color: rgba(255, 255, 255, 0.95); 
                border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                z-index: 9999; font-size: 13px; font-weight: bold;
                display: flex; align-items: center; justify-content: center;
                border: 1px solid #e2e8f0; color: #1a202c; font-family: sans-serif;">
        🇹🇼 CWA O-A0003-001 氣象觀測站分布 ({selected_date})
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # 圖例 (Legend) - 課程序號 17
    legend_html = """
    <div style="position: fixed; 
                bottom: 25px; right: 25px; width: 175px; 
                background-color: rgba(255, 255, 255, 0.95); 
                border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                z-index: 9999; font-size: 13px; padding: 12px;
                border: 1px solid #e2e8f0; font-family: sans-serif;">
        <div style="font-weight: bold; margin-bottom: 8px; color: #2d3748; border-bottom: 1px solid #edf2f7; padding-bottom: 4px;">
            🌡️ 平均溫度色彩
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="background: #2B6CB0; width: 14px; height: 14px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
            <span style="color: #4a5568;">&lt; 20°C (低溫)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="background: #38A169; width: 14px; height: 14px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
            <span style="color: #4a5568;">20 - 25°C (舒適)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="background: #DD6B20; width: 14px; height: 14px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
            <span style="color: #4a5568;">25 - 30°C (溫暖)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="background: #E53E3E; width: 14px; height: 14px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
            <span style="color: #4a5568;">&gt; 30°C (炎熱)</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # 繪製各測站/地區氣溫標記
    for _, row in df_date.iterrows():
        region = row["regionName"]
        min_t = float(row["minT"])
        max_t = float(row["maxT"])
        cur_t = float(row["currentT"]) if pd.notna(row.get("currentT")) else round((min_t + max_t) / 2.0, 1)
        weather_text = str(row.get("weather", "良好")) if pd.notna(row.get("weather")) else "良好"
        avg_t = round((min_t + max_t) / 2.0, 1)

        # 優先使用 O-A0003-001 測站實測經緯度
        lat = row.get("latitude")
        lon = row.get("longitude")

        if pd.isna(lat) or pd.isna(lon) or not lat or not lon:
            fb = FALLBACK_COORDINATES.get(region)
            if fb:
                lat, lon = fb["lat"], fb["lon"]
            else:
                continue

        color = get_temperature_color(avg_t)
        category = get_temperature_category_label(avg_t)

        popup_content = f"""
        <div style="font-family: sans-serif; min-width: 175px; padding: 4px;">
            <h4 style="margin: 0 0 6px 0; color: #2b6cb0; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px;">
                📍 測站/分區：{region}
            </h4>
            <div style="margin: 4px 0; font-size: 13px;">
                <b>📅 觀測日期：</b>{selected_date}
            </div>
            <div style="margin: 4px 0; font-size: 13px;">
                <b>⛅ 天氣狀況：</b>{weather_text}
            </div>
            <div style="margin: 4px 0; font-size: 13px;">
                <b>🌡️ 即時/均溫：</b><span style="color: {color}; font-weight: bold;">{cur_t}°C</span>
            </div>
            <div style="margin: 4px 0; font-size: 13px;">
                <b>🔥 最高氣溫：</b><span style="color: #e53e3e; font-weight: bold;">{max_t}°C</span>
            </div>
            <div style="margin: 4px 0; font-size: 13px;">
                <b>❄️ 最低氣溫：</b><span style="color: #3182ce; font-weight: bold;">{min_t}°C</span>
            </div>
            <div style="margin-top: 6px; padding: 3px 6px; background-color: {color}22; border-left: 3px solid {color}; border-radius: 3px; font-size: 12px;">
                舒適度評級：<b>{category}</b>
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[float(lat), float(lon)],
            radius=20,
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{region}: 氣溫 {cur_t}°C ({weather_text})",
            color=color,
            weight=3,
            fill=True,
            fill_color=color,
            fill_opacity=0.75
        ).add_to(station_group)

        folium.Marker(
            location=[float(lat), float(lon)],
            icon=folium.DivIcon(
                html=f"""
                <div style="font-size: 10pt; font-weight: 800; color: #ffffff; 
                            text-align: center; text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
                            transform: translate(-50%, -50%); pointer-events: none;">
                    {cur_t}°
                </div>
                """
            )
        ).add_to(station_group)

    station_group.add_to(m)

    # 圖層控制器 (可切換底圖、雷達迴波、衛星雲圖與測站標記)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    return m
