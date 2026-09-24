"""
中央氣象署 CWA 衛星雲圖觀測模組
支援 CWA 衛星雲圖 (O-A0058-001 ~ O-A0058-004, 台灣/東亞/全球即時雲圖) 與即時雷達迴波。
具備動態抓取最新觀測圖檔、歷程播放清單、多頻道解析與色彩強化雲圖解讀功能。
"""

import re
import time
from typing import Dict, List, Optional, Any
import requests

# CWA 即時衛星圖資目錄與最新清單 JS 來源
CWA_SAT_CATALOG_URL = "https://www.cwa.gov.tw/Data/js/obs_img/Observe_sat.js"
CWA_BASE_IMG_URL = "https://www.cwa.gov.tw/Data/satellite"

# 衛星雲圖頻道配置清單
SATELLITE_CHANNELS: Dict[str, Dict[str, Any]] = {
    "tw_ir_color": {
        "id": "tw_ir_color",
        "name": "🇹🇼 台灣彩色紅外線雲圖",
        "category": "台灣區域",
        "cwa_key": "TWI_IR1_CR_800",
        "static_url": f"{CWA_BASE_IMG_URL}/TWI_IR1_CR_800/TWI_IR1_CR_800.jpg",
        "desc": "針對台灣鄰近海域之彩色紅外線衛星影像，清晰呈現台灣上空及鄰近海域雲層分佈與厚度。",
        "resolution": "800 x 800",
        "interpretation": "色彩越濃白表示雲頂越高、對流越強；薄雲呈淺藍或淡白色，適合辨識台灣陸地降雨雲團。"
    },
    "tw_ir_enhanced": {
        "id": "tw_ir_enhanced",
        "name": "🌈 台灣色調強化雲圖",
        "category": "台灣區域",
        "cwa_key": "TWI_IR1_MB_800",
        "static_url": f"{CWA_BASE_IMG_URL}/TWI_IR1_MB_800/TWI_IR1_MB_800.jpg",
        "desc": "將紅外線雲頂溫度以色彩強化標示，特別適合追蹤午後雷陣雨、強對流或颱風暴雨核心。",
        "resolution": "800 x 800",
        "interpretation": "紅、橘、黃、綠色區塊代表低溫強對流雲頂（通常伴隨劇烈降雨或雷暴），灰色為一般中低層雲。"
    },
    "tw_true_color": {
        "id": "tw_true_color",
        "name": "🌍 台灣真實色彩雲圖 (日間)",
        "category": "台灣區域",
        "cwa_key": "TWI_TRGB_1000",
        "static_url": f"{CWA_BASE_IMG_URL}/TWI_TRGB_1000/TWI_TRGB_1000.jpg",
        "desc": "以可見光波段合成接近肉眼真實視覺的彩色雲圖，日間能清晰觀察雲系立體感與地形邊界。",
        "resolution": "1000 x 1000",
        "interpretation": "如太空視角鳥瞰台灣，白天效果最佳；夜間因無陽光反射將轉為微光或無彩色訊號。"
    },
    "tw_radar": {
        "id": "tw_radar",
        "name": "📡 台灣雷達迴波整合圖",
        "category": "雷達與降雨",
        "cwa_key": "RADAR_CV1",
        "static_url": "https://www.cwa.gov.tw/Data/radar/CV1_1000.png",
        "desc": "中央氣象署全台多普勒氣象雷達即時整合回波圖，能精準反映空中水滴強度與降雨熱區。",
        "resolution": "1000 x 1000",
        "interpretation": "綠色(15-30dBZ)輕度降雨；黃橘色(30-45dBZ)中度至強降雨；紫紅色(>50dBZ)恐有豪大雨或冰雹。"
    },
    "ea_ir_color": {
        "id": "ea_ir_color",
        "name": "🌏 東亞彩色紅外線雲圖 (全區)",
        "category": "東亞區域",
        "cwa_key": "LCC_IR1_CR_1000",
        "static_url": f"{CWA_BASE_IMG_URL}/LCC_IR1_CR_1000/LCC_IR1_CR_1000.jpg",
        "desc": "涵蓋東亞、西太平洋、日本、南海的大範圍衛星雲圖，適合觀察鋒面移入、颱風動向與大氣環流。",
        "resolution": "1000 x 1000 (可選 2750px)",
        "interpretation": "可觀察華南雲雨區東移、東北季風鋒面雲系或梅雨鋒面的完整長條形走向。"
    },
    "ea_ir_enhanced": {
        "id": "ea_ir_enhanced",
        "name": "🌪️ 東亞色調強化雲圖",
        "category": "東亞區域",
        "cwa_key": "LCC_IR1_MB_1000",
        "static_url": f"{CWA_BASE_IMG_URL}/LCC_IR1_MB_1000/LCC_IR1_MB_1000.jpg",
        "desc": "東亞大範圍色調強化圖，是氣象預報員研判熱帶低壓、颱風發展中心及強降雨帶的核心工具。",
        "resolution": "1000 x 1000",
        "interpretation": "彩色圓眼結構常為發展中颱風；長條狀鮮豔色彩帶代表冷暖氣團交界的強烈鋒面對流。"
    },
    "global_disk": {
        "id": "global_disk",
        "name": "🌐 全球全圓盤衛星雲圖",
        "category": "全球視角",
        "cwa_key": "FDK_IR1_CR_1000",
        "static_url": f"{CWA_BASE_IMG_URL}/FDK_IR1_CR_1000/FDK_IR1_CR_1000.jpg",
        "desc": "向日葵氣象衛星觀測之整個地球圓盤半球影像，呈現跨半球行星尺度之氣象景觀。",
        "resolution": "1000 x 1000",
        "interpretation": "赤道間熱帶輻合帶 (ITCZ)、南半球西風帶與北半球高空噴流雲系盡收眼底。"
    }
}

# 簡單記憶體快取 (60 秒更新一次)
_CACHE_DATA: Dict[str, Any] = {
    "last_fetched": 0,
    "catalog": {}
}


def get_satellite_channels() -> Dict[str, Dict[str, Any]]:
    """回傳所有支援的衛星雲圖頻道清單"""
    return SATELLITE_CHANNELS


def fetch_cwa_catalog(max_age_seconds: int = 60) -> Dict[str, List[Dict[str, str]]]:
    """
    從中央氣象署 Observe_sat.js 即時抓取最新衛星雲圖時間序列清單。
    回傳字典：{ cwa_key: [{"img": url, "time": "2026/09/24 15:40"}, ...] }
    """
    now = time.time()
    if _CACHE_DATA["catalog"] and (now - _CACHE_DATA["last_fetched"] < max_age_seconds):
        return _CACHE_DATA["catalog"]

    catalog: Dict[str, List[Dict[str, str]]] = {}
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WeatherAgent/1.0"
        }
        resp = requests.get(CWA_SAT_CATALOG_URL, headers=headers, timeout=6)
        if resp.status_code == 200:
            text = resp.text
            # 格式：{"img":'TWI_IR1_CR_800/TWI_IR1_CR_800-2026-09-24-15-40.jpg', 'text':'2026/09/24 15:40'}
            pattern = re.compile(r'\{"img":\'([^\']+)\',\s*\'text\':\'([^\']+)\'\}')
            matches = pattern.findall(text)

            for rel_path, obs_time in matches:
                # 分離目錄名稱，例如 TWI_IR1_CR_800
                prefix = rel_path.split("/")[0] if "/" in rel_path else rel_path
                full_url = f"{CWA_BASE_IMG_URL}/{rel_path}"

                if prefix not in catalog:
                    catalog[prefix] = []

                catalog[prefix].append({
                    "url": full_url,
                    "time": obs_time,
                    "rel_path": rel_path
                })

            _CACHE_DATA["catalog"] = catalog
            _CACHE_DATA["last_fetched"] = now
    except Exception as e:
        print(f"[satellite] Warning: Failed to fetch CWA satellite catalog: {e}")

    return catalog


def get_channel_frames(channel_id: str, limit: int = 12) -> List[Dict[str, str]]:
    """
    獲取指定頻道的最新序列圖檔列表 (供縮時動畫或時間滑桿播放)
    若查無動態清單，則自動回退至即時靜態固定 URL。
    """
    channel = SATELLITE_CHANNELS.get(channel_id)
    if not channel:
        return []

    cwa_key = channel["cwa_key"]
    catalog = fetch_cwa_catalog()

    if cwa_key in catalog and catalog[cwa_key]:
        # 取得最新 limit 筆（時間由舊到新，以便播放動態動畫）
        recent_frames = catalog[cwa_key][:limit]
        # 反轉順序讓最早的時間在 index 0，最新的在最後，利於動畫播放
        return list(reversed(recent_frames))

    # 備援：回傳單張即時靜態影像
    return [{
        "url": channel["static_url"],
        "time": "即時最新觀測",
        "rel_path": channel["static_url"]
    }]


def get_latest_satellite_image(channel_id: str) -> Dict[str, Any]:
    """
    獲取指定頻道最即時的單張衛星影像與說明
    """
    channel = SATELLITE_CHANNELS.get(channel_id, SATELLITE_CHANNELS["tw_ir_color"])
    frames = get_channel_frames(channel_id, limit=1)

    latest_frame = frames[-1] if frames else {
        "url": channel["static_url"],
        "time": "即時最新"
    }

    return {
        "channel_id": channel["id"],
        "channel_name": channel["name"],
        "category": channel["category"],
        "url": latest_frame["url"],
        "time": latest_frame["time"],
        "desc": channel["desc"],
        "resolution": channel["resolution"],
        "interpretation": channel["interpretation"]
    }
