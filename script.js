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

darkTiles.addTo(map);

let currentLayer = 'temp'; // 'temp' 或 'rain'
let showLabels = true;
let weatherData = [];
let markerGroup = L.layerGroup().addTo(map);

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

// 事件監聽：切換氣溫圖層
document.getElementById('btn-temp').addEventListener('click', (e) => {
    currentLayer = 'temp';
    e.target.classList.add('active');
    document.getElementById('btn-rain').classList.remove('active');

    document.getElementById('legend-title').innerText = '°C';
    document.getElementById('legend-gradient').style.background = 'linear-gradient(to right, #3b82f6, #0ea5e9, #10b981, #f59e0b, #ef4444)';
    document.getElementById('legend-labels').innerHTML = '<span>5</span><span>10</span><span>15</span><span>20</span><span>24</span><span>28</span><span>32</span><span>36</span>';

    renderMarkers();
});

// 事件監聽：切換降雨機率圖層
document.getElementById('btn-rain').addEventListener('click', (e) => {
    currentLayer = 'rain';
    e.target.classList.add('active');
    document.getElementById('btn-temp').classList.remove('active');

    document.getElementById('legend-title').innerText = '% 降雨機率';
    document.getElementById('legend-gradient').style.background = 'linear-gradient(to right, #94a3b8, #10b981, #0ea5e9, #3b82f6)';
    document.getElementById('legend-labels').innerHTML = '<span>0</span><span>20</span><span>50</span><span>80</span><span>100</span>';

    renderMarkers();
});

// 事件監聽：切換數值標籤顯示
document.getElementById('toggle-marker').addEventListener('change', (e) => {
    showLabels = e.target.checked;
    renderMarkers();
});

// 底圖切換：深色
document.getElementById('base-dark').addEventListener('click', (e) => {
    e.target.classList.add('active');
    document.getElementById('base-street').classList.remove('active');
    map.removeLayer(streetTiles);
    darkTiles.addTo(map);
});

// 底圖切換：街道圖
document.getElementById('base-street').addEventListener('click', (e) => {
    e.target.classList.add('active');
    document.getElementById('base-dark').classList.remove('active');
    map.removeLayer(darkTiles);
    streetTiles.addTo(map);
});

// 重新定位全台
document.getElementById('btn-locate').addEventListener('click', () => {
    map.flyTo(DEFAULT_CENTER, DEFAULT_ZOOM, {
        animate: true,
        duration: 0.8
    });
});

// 啟動資料載入
loadData();
