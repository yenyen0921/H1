from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 優先自 data/weather.json 讀取 22 縣市完整數據
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(os.path.dirname(curr_dir), "data", "weather.json")
        
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = json.dumps([
                {"location": "臺北市", "lat": 25.0377, "lon": 121.5149, "max_temp": 32.2, "min_temp": 23.8, "pop": 20, "weather": "晴時多雲", "time": "2026-09-23 11:00:00"}
            ])
            
        self.wfile.write(content.encode('utf-8'))
