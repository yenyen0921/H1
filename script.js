// 台灣即時氣象前端應用邏輯 (Vercel 相容版)
const DEFAULT_CENTER = [23.7, 120.95];
const DEFAULT_ZOOM = 7.5;

// 初始化 Leaflet 地圖
const map = L.map('map', {
    zoomControl: false,
    center: DEFAULT_CENTER,
    zoom: DEFAULT_ZOOM
});

L.control.zoom({
    position: 'bottomleft'
}).addTo(map);

// 高品質暗黑無浮水印底圖 (Esri World Dark Gray)
const darkTiles = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: '&copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
    maxZoom: 16
});

// 街道圖 (OpenStreetMap)
const streetTiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
});

// 衛星空照圖 (Esri World Imagery)
const satTiles = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: '&copy; Esri World Imagery',
    maxZoom: 18
});

darkTiles.addTo(map);

let currentLayer = 'temp'; // 'temp', 'rain', 'satellite', 'radar'
let showLabels = true;
let weatherData = [];
let markerGroup = L.layerGroup().addTo(map);

// 衛星雲圖與雷達疊加層
const TAIWAN_SAT_BOUNDS = [[19.5, 117.5], [27.2, 124.5]];
const TAIWAN_RADAR_BOUNDS = [[20.4, 118.0], [26.8, 124.0]];

let satOverlay = L.imageOverlay(
    'https://www.cwa.gov.tw/Data/satellite/TWI_IR1_CR_800/TWI_IR1_CR_800.jpg',
    TAIWAN_SAT_BOUNDS,
    { opacity: 0.70, interactive: false }
);

let radarOverlay = L.imageOverlay(
    'https://www.cwa.gov.tw/Data/radar/CV1_1000.png',
    TAIWAN_RADAR_BOUNDS,
    { opacity: 0.70, interactive: false }
);

// 色彩計算函式 (氣溫)
function getTempColor(t) {
    if (t >= 32) return '#ef4444'; // 紅色 (炎熱)
    if (t >= 28) return '#f59e0b'; // 橘黃 (溫暖)
    if (t >= 24) return '#10b981'; // 翠綠 (舒適)
    if (t >= 20) return '#0ea5e9'; // 天藍 (涼爽)
    return '#3b82f6'; // 藍色 (低溫)
}

// 色彩計算函式 (降雨機率)
function getRainColor(r) {
    if (r >= 80) return '#3b82f6';
    if (r >= 50) return '#0ea5e9';
    if (r >= 20) return '#10b981';
    return '#94a3b8';
}

// 載入氣象資料 (優先自 API 讀取，失敗時自動讀取本地資料庫/JSON 確保隨時可用)
async function loadData() {
    try {
        let res = await fetch('/api/weather');
        if (res.ok) {
            weatherData = await res.json();
        } else {
            throw new Error("API not available, fallback to local data");
        }
    } catch (e) {
        try {
            let res = await fetch('data/weather.json');
            weatherData = await res.json();
        } catch (err) {
            console.warn("Using embedded default data", err);
            weatherData = [
                {"location": "臺北市", "lat": 25.0377, "lon": 121.5149, "max_temp": 32.2, "min_temp": 23.8, "pop": 20, "weather": "晴時多雲", "time": "2026-09-23 11:00:00"},
                {"location": "臺中市", "lat": 24.1457, "lon": 120.6841, "max_temp": 33.5, "min_temp": 24.0, "pop": 10, "weather": "晴", "time": "2026-09-23 11:00:00"},
                {"location": "高雄市", "lat": 22.5660, "lon": 120.3157, "max_temp": 34.2, "min_temp": 26.0, "pop": 10, "weather": "晴", "time": "2026-09-23 11:00:00"},
                {"location": "花蓮縣", "lat": 23.9752, "lon": 121.6133, "max_temp": 31.0, "min_temp": 23.5, "pop": 30, "weather": "多雲短暫雨", "time": "2026-09-23 11:00:00"}
            ];
        }
    }

    if (weatherData && weatherData.length > 0) {
        const obsTime = weatherData[0].time || "2026-09-23 11:00";
        document.getElementById('obs-time').innerText = obsTime.substring(0, 16).replace('T', ' ');
        document.getElementById('loc-count').innerText = weatherData.length;
        updateDashboard();
        renderMarkers();
    }
}

// 更新左上方儀表板統計數值
function updateDashboard() {
    let maxTemp = -999, minTemp = 999, maxRain = -1;
    let maxTempLoc = '', minTempLoc = '', maxRainLoc = '';
    let weatherCounts = {};

    weatherData.forEach(d => {
        if (d.max_temp > maxTemp) { maxTemp = d.max_temp; maxTempLoc = d.location; }
        if (d.min_temp < minTemp) { minTemp = d.min_temp; minTempLoc = d.location; }
        if (d.pop > maxRain) { maxRain = d.pop; maxRainLoc = d.location; }

        weatherCounts[d.weather] = (weatherCounts[d.weather] || 0) + 1;
    });

    document.getElementById('max-temp').innerText = maxTemp !== -999 ? maxTemp : '-';
    document.getElementById('max-temp-loc').innerText = maxTempLoc;

    document.getElementById('min-temp').innerText = minTemp !== 999 ? minTemp : '-';
    document.getElementById('min-temp-loc').innerText = minTempLoc;

    document.getElementById('max-rain').innerText = maxRain !== -1 ? maxRain : '-';
    document.getElementById('max-rain-loc').innerText = maxRainLoc;

    let commonWeather = Object.keys(weatherCounts).reduce((a, b) => weatherCounts[a] > weatherCounts[b] ? a : b, '晴時多雲');
    document.getElementById('common-weather').innerText = commonWeather;
}

// 繪製地圖標記 (Markers)
function renderMarkers() {
    markerGroup.clearLayers();

    weatherData.forEach(d => {
        let val = currentLayer === 'temp' ? d.max_temp : d.pop;
        let suffix = currentLayer === 'temp' ? '°C' : '%';
        let color = currentLayer === 'temp' ? getTempColor(d.max_temp) : getRainColor(d.pop);

        let labelHtml = showLabels
            ? `<div class="custom-pill-label" style="border-left: 4px solid ${color};">${d.location} ${val}${suffix}</div>`
            : `<div class="custom-pill-label" style="width:16px;height:16px;border-radius:50%;padding:0;background:${color};border:2px solid white;"></div>`;

        let icon = L.divIcon({
            html: labelHtml,
            className: '',
            iconSize: showLabels ? [95, 28] : [16, 16],
            iconAnchor: showLabels ? [47, 14] : [8, 8]
        });

        let popupContent = `
            <div class="popup-custom">
                <h3>📍 ${d.location}</h3>
                <p><b>天氣概況：</b>${d.weather}</p>
                <p><b>預估氣溫：</b>${d.min_temp}°C ~ ${d.max_temp}°C</p>
                <p><b>降雨機率：</b>${d.pop !== null && d.pop !== undefined ? d.pop + '%' : '-'}</p>
            </div>
        `;

        L.marker([d.lat, d.lon], { icon: icon })
            .bindPopup(popupContent)
            .addTo(markerGroup);
    });
}

function clearActiveLayerButtons() {
    document.getElementById('btn-temp').classList.remove('active');
    document.getElementById('btn-rain').classList.remove('active');
    document.getElementById('btn-satellite').classList.remove('active');
    document.getElementById('btn-radar').classList.remove('active');
    document.getElementById('sat-control-group').style.display = 'none';
}

// 事件監聽：切換氣溫圖層
document.getElementById('btn-temp').addEventListener('click', (e) => {
    clearActiveLayerButtons();
    currentLayer = 'temp';
    e.target.classList.add('active');

    map.removeLayer(satOverlay);
    map.removeLayer(radarOverlay);

    document.getElementById('legend-title').innerText = '°C';
    document.getElementById('legend-gradient').style.background = 'linear-gradient(to right, #3b82f6, #0ea5e9, #10b981, #f59e0b, #ef4444)';
    document.getElementById('legend-labels').innerHTML = '<span>5</span><span>10</span><span>15</span><span>20</span><span>24</span><span>28</span><span>32</span><span>36</span>';

    renderMarkers();
});

// 事件監聽：切換降雨機率圖層
document.getElementById('btn-rain').addEventListener('click', (e) => {
    clearActiveLayerButtons();
    currentLayer = 'rain';
    e.target.classList.add('active');

    map.removeLayer(satOverlay);
    map.removeLayer(radarOverlay);

    document.getElementById('legend-title').innerText = '% 降雨機率';
    document.getElementById('legend-gradient').style.background = 'linear-gradient(to right, #94a3b8, #10b981, #0ea5e9, #3b82f6)';
    document.getElementById('legend-labels').innerHTML = '<span>0</span><span>20</span><span>50</span><span>80</span><span>100</span>';

    renderMarkers();
});

// 事件監聽：切換衛星雲圖圖層
document.getElementById('btn-satellite').addEventListener('click', (e) => {
    clearActiveLayerButtons();
    currentLayer = 'satellite';
    e.target.classList.add('active');
    document.getElementById('sat-control-group').style.display = 'block';

    map.removeLayer(radarOverlay);
    satOverlay.addTo(map);

    document.getElementById('legend-title').innerText = '☁️ 雲頂厚度/對流';
    document.getElementById('legend-gradient').style.background = 'linear-gradient(to right, #38bdf8, #818cf8, #f472b6, #fb7185, #ffffff)';
    document.getElementById('legend-labels').innerHTML = '<span>薄雲</span><span>一般</span><span>對流</span><span>強烈</span><span>雲頂最高</span>';

    renderMarkers();
});

// 事件監聽：切換雷達迴波圖層
document.getElementById('btn-radar').addEventListener('click', (e) => {
    clearActiveLayerButtons();
    currentLayer = 'radar';
    e.target.classList.add('active');
    document.getElementById('sat-control-group').style.display = 'block';

    map.removeLayer(satOverlay);
    radarOverlay.addTo(map);

    document.getElementById('legend-title').innerText = 'dBZ 雷達回波強度';
    document.getElementById('legend-gradient').style.background = 'linear-gradient(to right, #00ffff, #0000ff, #00ff00, #ffff00, #ff0000, #ff00ff)';
    document.getElementById('legend-labels').innerHTML = '<span>10</span><span>20</span><span>30</span><span>40</span><span>50</span><span>60+</span>';

    renderMarkers();
});

// 透明度滑桿事件
document.getElementById('sat-opacity').addEventListener('input', (e) => {
    let val = parseFloat(e.target.value) / 100.0;
    if (map.hasLayer(satOverlay)) {
        satOverlay.setOpacity(val);
    }
    if (map.hasLayer(radarOverlay)) {
        radarOverlay.setOpacity(val);
    }
});

// 事件監聽：切換數值標籤顯示
document.getElementById('toggle-marker').addEventListener('change', (e) => {
    showLabels = e.target.checked;
    renderMarkers();
});

// 底圖切換：深色
document.getElementById('base-dark').addEventListener('click', (e) => {
    document.getElementById('base-dark').classList.add('active');
    document.getElementById('base-street').classList.remove('active');
    document.getElementById('base-sat').classList.remove('active');
    map.removeLayer(streetTiles);
    map.removeLayer(satTiles);
    darkTiles.addTo(map);
});

// 底圖切換：街道圖
document.getElementById('base-street').addEventListener('click', (e) => {
    document.getElementById('base-street').classList.add('active');
    document.getElementById('base-dark').classList.remove('active');
    document.getElementById('base-sat').classList.remove('active');
    map.removeLayer(darkTiles);
    map.removeLayer(satTiles);
    streetTiles.addTo(map);
});

// 底圖切換：衛星空照圖
document.getElementById('base-sat').addEventListener('click', (e) => {
    document.getElementById('base-sat').classList.add('active');
    document.getElementById('base-dark').classList.remove('active');
    document.getElementById('base-street').classList.remove('active');
    map.removeLayer(darkTiles);
    map.removeLayer(streetTiles);
    satTiles.addTo(map);
});

// 重新定位全台
document.getElementById('btn-locate').addEventListener('click', () => {
    map.flyTo(DEFAULT_CENTER, DEFAULT_ZOOM, {
        animate: true,
        duration: 0.8
    });
});

// =========================================================================
// 衛星雲圖分析中心彈窗互動邏輯 (Satellite Hub Modal)
// =========================================================================
const satChannels = {
    'TWI_IR1_CR_800': {
        name: '🇹🇼 台灣彩色紅外線雲圖',
        url: 'https://www.cwa.gov.tw/Data/satellite/TWI_IR1_CR_800/TWI_IR1_CR_800.jpg',
        desc: '針對台灣鄰近海域之彩色紅外線影像，濃白處代表雲頂高、水氣充足，能掌握即時雨帶進程。'
    },
    'TWI_IR1_MB_800': {
        name: '🌈 台灣色調強化雲圖',
        url: 'https://www.cwa.gov.tw/Data/satellite/TWI_IR1_MB_800/TWI_IR1_MB_800.jpg',
        desc: '依據雲頂溫度分級色彩強化，紅色與橘色區域代表強對流胞發展，常用於掌握午後豪雨與雷暴。'
    },
    'TWI_TRGB_1000': {
        name: '🌍 台灣真實色彩雲圖 (日間)',
        url: 'https://www.cwa.gov.tw/Data/satellite/TWI_TRGB_1000/TWI_TRGB_1000.jpg',
        desc: '以可見光紅綠藍三原色合成，太空視角清晰俯瞰台灣地形輪廓與積雲、層雲細膩紋理。'
    },
    'CV1_1000': {
        name: '📡 台灣雷達迴波整合圖',
        url: 'https://www.cwa.gov.tw/Data/radar/CV1_1000.png',
        desc: '全台都卜勒氣象雷達合成圖，即時反應空中水滴降水訊號（黃色、紅色為大雨或豪雨區）。'
    },
    'LCC_IR1_CR_1000': {
        name: '🌏 東亞全區彩色雲圖',
        url: 'https://www.cwa.gov.tw/Data/satellite/LCC_IR1_CR_1000/LCC_IR1_CR_1000.jpg',
        desc: '涵蓋東亞、西太平洋與南海廣袤區域，適合觀察跨國鋒面系統、颱風移動軌跡與季風環流。'
    }
};

const satModal = document.getElementById('sat-modal');
const satPreviewImg = document.getElementById('sat-preview-img');
const satLoading = document.getElementById('sat-loading');
const satChannelTitle = document.getElementById('sat-channel-title');
const satChannelDesc = document.getElementById('sat-channel-desc');
const modalSatTime = document.getElementById('modal-sat-time');

document.getElementById('btn-open-sat-hub').addEventListener('click', () => {
    satModal.style.display = 'flex';
    let now = new Date();
    let pad = (n) => n.toString().padStart(2, '0');
    modalSatTime.innerText = `觀測時間：${now.getFullYear()}/${pad(now.getMonth()+1)}/${pad(now.getDate())} ${pad(now.getHours())}:${pad(Math.floor(now.getMinutes()/10)*10)} (每10分鐘更新)`;
});

document.getElementById('btn-close-modal').addEventListener('click', () => {
    satModal.style.display = 'none';
});

satModal.addEventListener('click', (e) => {
    if (e.target === satModal) {
        satModal.style.display = 'none';
    }
});

// 切換雲圖頻道
document.querySelectorAll('.sat-tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.sat-tab-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');

        let chKey = e.target.dataset.channel;
        let ch = satChannels[chKey];
        if (ch) {
            satChannelTitle.innerText = ch.name;
            satChannelDesc.innerText = ch.desc;
            satLoading.style.display = 'block';
            satPreviewImg.style.opacity = '0.4';

            satPreviewImg.src = `${ch.url}?t=${Date.now()}`;
            satPreviewImg.onload = () => {
                satLoading.style.display = 'none';
                satPreviewImg.style.opacity = '1';
            };
        }
    });
});

// 啟動資料載入
loadData();

