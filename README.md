# 🌤️ Taiwan Weather Observation & Forecast (CWA O-A0003-001)

> **AI 創新微課程實作專案**：從氣象資料到互動式天氣預報應用  
> **教授指定資料集**：**中央氣象署 CWA `O-A0003-001`**（局屬氣象站-現在天氣觀測報告 / 10分鐘綜觀資料）  
> **技術棧**：`CWA O-A0003-001` × `JSON` × `Python` × `SQLite` × `Streamlit` × `Folium`  
> **開發工具**：Google Antigravity IDE × Gemini 內建 AI Agent × GitHub

---

## 📖 專案簡介 (Project Overview)

本專案完全遵循**煥哥《打造你的 AI Coding Agent》微課程教學之 24 個步驟**，並因應課堂指定，精確對接**中央氣象署開放資料平臺之 `O-A0003-001` 局屬氣象測站即時觀測報告**。

系統自 CWA API / 觀測報告中提取全台測站的即時氣溫（`AirTemperature`）、當日最高溫（`DailyHigh`）、當日最低溫（`DailyLow`）、天氣概況（`Weather`）與測站經緯度坐標（`GeoInfo.Coordinates`），清洗後存入 SQLite 資料庫（`data/data.db`），並透過 Streamlit 網頁應用與 Folium 互動地圖進行全方位的視覺化分析。

---

## 🌟 核心功能特色 (Key Features)

1. **CWA O-A0003-001 資料擷取與備援 (課程序號 3-7)**：
   - 支援線上 CWA API 授權碼即時擷取 `O-A0003-001` 觀測資料。
   - 內建標準測站格式備援 JSON 資料（`data/sample_cwa_weather.json`），免填 Key 亦能隨開即用。
2. **SQLite 關聯式資料庫與防重複機制 (課程序號 8-10, 20)**：
   - 資料表 `TemperatureForecasts` 包含測站名稱、觀測日期、即時溫、高低溫、天氣與經緯度。
   - 設定 `UNIQUE(regionName, dataDate)` 與 `INSERT OR REPLACE`，重複執行自動去重更新。
3. **測站走勢與資料表 (課程序號 11-16)**：
   - 下拉選單支援切換全台各大氣象測站（臺北、臺中、高雄、花蓮、基隆、新竹、宜蘭、臺南、恆春、臺東、澎湖等）與分區匯總。
   - 雙色折線圖動態呈現最高與最低溫趨勢。
4. **Folium 測站真實經緯度地圖 (課程序號 17-18)**：
   - 直接依據 CWA 測站實測經緯度坐標繪製地圖。
   - 依照氣溫自動進行四級色彩渲染（藍、綠、橘黃、紅），並附詳細 Popup 快顯卡片與圖例。
5. **內建 SQL Inspector (課程序號 10)**：
   - 支援在網頁上直接輸入並執行標準 SQL 語法進行驗證。

---

## 📂 專案結構 (Directory Structure)

```
Taiwan-Weather-Project/
├── data/
│   ├── data.db                   # SQLite 資料庫 (儲存 O-A0003-001 觀測資料)
│   └── sample_cwa_weather.json   # CWA O-A0003-001 標準格式範例資料
├── src/
│   ├── __init__.py
│   ├── database.py               # SQLite 資料庫連線、Schema 定義、去重寫入與查詢函式
│   ├── weather_api.py            # CWA O-A0003-001 API 請求與 JSON 解析
│   └── map_view.py               # Folium 測站經緯度地圖與四級色彩渲染
├── app.py                        # Streamlit 主程式 (視覺化儀表板)
├── requirements.txt              # 專案相依套件清單
├── .gitignore                    # Git 忽略檔案設定
└── README.md                     # 專案詳細說明文件
```

---

## 🚀 快速啟動 (Quick Start)

```bash
# 1. 安裝相依套件
pip install -r requirements.txt

# 2. 測試資料庫同步 (O-A0003-001)
python src/weather_api.py

# 3. 啟動 Streamlit Web 應用
python -m streamlit run app.py
```
啟動後於瀏覽器造訪 `http://localhost:8501` 即可進行操作。

---

## 🔗 GitHub 儲存庫
`https://github.com/yenyen0921/H1.git`
