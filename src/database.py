"""
SQLite 資料庫模組 (課程序號 8, 9, 10, 20)
負責建立資料表 TemperatureForecasts、去重寫入 (INSERT OR REPLACE) 與查詢操作。
支援 CWA O-A0003-001 觀測站觀測報告與各地區預報資料。
"""

import os
import sqlite3
from typing import List, Optional
import pandas as pd

DEFAULT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "data.db")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """取得 SQLite 資料庫連線，若目錄不存在則自動建立"""
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    初始化資料表 (課程序號 8 & 9)
    資料表 TemperatureForecasts 包含 CWA O-A0003-001 所需之觀測欄位
    UNIQUE(regionName, dataDate) 確保重複執行不重複插入 (課程序號 20)
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TemperatureForecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regionName TEXT NOT NULL,
            dataDate TEXT NOT NULL,
            minT REAL NOT NULL,
            maxT REAL NOT NULL,
            currentT REAL,
            weather TEXT,
            latitude REAL,
            longitude REAL,
            UNIQUE(regionName, dataDate)
        );
    """)
    # 檢查並自動升級欄位 (若先前已建立過舊結構)
    cursor.execute("PRAGMA table_info(TemperatureForecasts);")
    existing_cols = [col["name"] for col in cursor.fetchall()]
    
    for col_name, col_type in [
        ("currentT", "REAL"),
        ("weather", "TEXT"),
        ("latitude", "REAL"),
        ("longitude", "REAL")
    ]:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE TemperatureForecasts ADD COLUMN {col_name} {col_type};")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_region_date 
        ON TemperatureForecasts (regionName, dataDate);
    """)
    conn.commit()
    conn.close()


def save_forecasts(df: pd.DataFrame, db_path: Optional[str] = None) -> int:
    """
    批次儲存氣溫預報資料至 SQLite (課程序號 8 & 20)
    使用 INSERT OR REPLACE 避免重複資料
    """
    if df.empty:
        return 0

    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    insert_sql = """
        INSERT OR REPLACE INTO TemperatureForecasts (
            regionName, dataDate, minT, maxT, currentT, weather, latitude, longitude
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """

    records = []
    for _, row in df.iterrows():
        records.append((
            str(row["regionName"]),
            str(row["dataDate"]),
            float(row.get("minT", 0.0)),
            float(row.get("maxT", 0.0)),
            float(row["currentT"]) if pd.notna(row.get("currentT")) else None,
            str(row["weather"]) if pd.notna(row.get("weather")) else "",
            float(row["latitude"]) if pd.notna(row.get("latitude")) else None,
            float(row["longitude"]) if pd.notna(row.get("longitude")) else None,
        ))

    cursor.executemany(insert_sql, records)
    conn.commit()
    inserted_count = cursor.rowcount
    conn.close()
    return inserted_count


def get_regions(db_path: Optional[str] = None) -> List[str]:
    """查詢所有不重複的地區/測站名稱 (課程序號 10 & 13)"""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName;")
    regions = [row["regionName"] for row in cursor.fetchall()]
    conn.close()
    return regions


def get_available_dates(db_path: Optional[str] = None) -> List[str]:
    """查詢所有不重複的預報日期 (課程序號 18)"""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT dataDate FROM TemperatureForecasts ORDER BY dataDate ASC;")
    dates = [row["dataDate"] for row in cursor.fetchall()]
    conn.close()
    return dates


def get_forecasts_by_region(region_name: str, db_path: Optional[str] = None) -> pd.DataFrame:
    """查詢指定地區/測站的氣溫紀錄 (課程序號 10 & 12)"""
    init_db(db_path)
    conn = get_db_connection(db_path)
    query = """
        SELECT dataDate, minT, maxT, currentT, weather
        FROM TemperatureForecasts
        WHERE regionName = ?
        ORDER BY dataDate ASC;
    """
    df = pd.read_sql_query(query, conn, params=(region_name,))
    conn.close()
    return df


def get_all_forecasts_by_date(date_str: str, db_path: Optional[str] = None) -> pd.DataFrame:
    """查詢指定日期的全台各地區/測站氣溫預報 (課程序號 17 & 18)"""
    init_db(db_path)
    conn = get_db_connection(db_path)
    query = """
        SELECT regionName, dataDate, minT, maxT, currentT, weather, latitude, longitude,
               ROUND((minT + maxT) / 2.0, 1) AS avgT
        FROM TemperatureForecasts
        WHERE dataDate = ?
        ORDER BY regionName ASC;
    """
    df = pd.read_sql_query(query, conn, params=(date_str,))
    conn.close()
    return df


def get_all_records(db_path: Optional[str] = None) -> pd.DataFrame:
    """取得資料庫中全部紀錄"""
    init_db(db_path)
    conn = get_db_connection(db_path)
    df = pd.read_sql_query(
        "SELECT id, regionName, dataDate, currentT, minT, maxT, weather, latitude, longitude FROM TemperatureForecasts ORDER BY dataDate ASC, regionName ASC;",
        conn
    )
    conn.close()
    return df
