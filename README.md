# 🌤️ Taiwan Weather Forecast (台灣天氣預報 Web 應用)

> **AI 創新微課程實作專案**：從氣象資料到互動式天氣預報應用  
> **技術棧**：`CWA API` × `JSON` × `Python` × `SQLite` × `Streamlit` × `Folium`  
> **開發工具**：Google Antigravity IDE × Gemini 內建 AI Agent × GitHub

---

## 📖 專案簡介 (Project Overview)

本專案依據煥哥《打造你的 AI Coding Agent》微課程教學，完整實踐 24 個開發步驟。透過串接台灣中央氣象署（CWA Open Data）開放資料，將全台各地區的一週氣溫預報（最低溫 MinT 與最高溫 MaxT）結構化清洗後存入 SQLite 資料庫，並建置互動式 Streamlit Web 應用程式與 Folium 台灣地理空間可視化地圖。

---

## 🌟 核心特色 (Key Features)

1. **中央氣象署 CWA API 串接與備援機制 (課程序號 3-7)**：
   - 支援線上 CWA API 即時取得最新氣象資料。
   - 內建台灣地區標準格式備援資料，無須 API Key 即可隨開即用。
2. **SQLite 關聯式資料庫與去重機制 (課程序號 8-10, 20)**：
   - 設計 `TemperatureForecasts` 表，欄位包含 `id`, `regionName`, `dataDate`, `minT`, `maxT`。
   - 設定 `UNIQUE(regionName, dataDate)` 複合唯一限制，採用 `INSERT OR REPLACE` 確保重複執行不重複寫入。
3. **動態互動式 Web 儀表板 (課程序號 11-16, 19)**：
   - **地區下拉選單**：即時切換北部、中部、南部、東部地區。
   - **雙溫走勢折線圖**：紅藍雙色直觀呈現一週高低氣溫波動。
   - **詳細資料表**：清晰呈現每日溫差與舒適度等級。
4. **台灣氣溫地圖視覺化 (課程序號 17-18)**：
   - 結合 Folium 與台灣中心坐標，依照溫度自動渲染色彩：
     - 🔵 `< 20°C` (低溫/涼爽)
     - 🟢 `20 - 25°C` (舒適)
     - 🟡 `25 - 30°C` (溫暖)
     - 🔴 `> 30°C` (炎熱)
   - 提供日期下拉選單動態更新全台預報標記與 Popup 詳細資訊卡。
5. **內嵌 SQL Inspector (課程序號 10)**：
   - 支援線上直接執行 SQL 指令（如 `SELECT DISTINCT regionName ...`），便於課堂驗證與查詢檢查。

---

## 📂 專案結構 (Directory Structure)

```
Taiwan-Weather-Project/
├── data/
│   ├── data.db                   # SQLite 資料庫 (儲存 TemperatureForecasts 資料表)
│   └── sample_cwa_weather.json   # 預設 CWA 格式氣象預報範例資料
├── src/
│   ├── __init__.py
│   ├── database.py               # SQLite 資料庫連線、Schema 定義、去重寫入與查詢函式
│   ├── weather_api.py            # CWA Open Data API 請求與 JSON 結構解析
│   └── map_view.py               # Folium 台灣氣溫互動地圖與圖例渲染
├── app.py                        # Streamlit 主程式 (視覺化儀表板)
├── requirements.txt              # 專案相依套件清單
├── .gitignore                    # Git 忽略檔案設定
└── README.md                     # 專案詳細說明文件
```

---

## 🚀 快速開始 (Quick Start)

### 1. 安裝相依套件
在終端機執行以下指令：
```bash
pip install -r requirements.txt
```

### 2. 測試資料庫同步
可直接執行測試腳本，自動初始化資料庫並載入氣象資料：
```bash
python src/weather_api.py
```

### 3. 啟動 Streamlit Web 應用
```bash
python -m streamlit run app.py
```
啟動後瀏覽器將自動開啟 `http://localhost:8501`。

---

## 📊 資料庫結構 (Database Schema)

```sql
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate TEXT NOT NULL,
    minT REAL NOT NULL,
    maxT REAL NOT NULL,
    UNIQUE(regionName, dataDate)
);
```

### 常用 SQL 查詢範例：
- **查詢所有地區**：
  ```sql
  SELECT DISTINCT regionName FROM TemperatureForecasts;
  ```
- **查詢中部地區一週預報**：
  ```sql
  SELECT * FROM TemperatureForecasts WHERE regionName='中部地區' ORDER BY dataDate ASC;
  ```

---

## 🔗 版本管理與 GitHub 連結

本專案已連結至 GitHub 儲存庫：
`https://github.com/yenyen0921/H1.git`
