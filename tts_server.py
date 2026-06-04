#!/usr/bin/env python3
"""
Edge-TTS proxy server for Hanyu Mandarin app.
Serves synthesised audio at GET /tts?text=...&voice=...
Lists voices at GET /voices
Caches audio files in /tmp/hanyu_tts_cache/
Run: python3 tts_server.py
"""
import asyncio, hashlib, json, os, pathlib, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import edge_tts

CACHE = pathlib.Path("/tmp/hanyu_tts_cache")
CACHE.mkdir(exist_ok=True)
# Render (and most PaaS) inject a PORT env var; fall back to 5275 for local dev.
PORT = int(os.environ.get("PORT", "5275"))

VOICES = [
    {"id": "zh-CN-XiaoxiaoNeural",  "name": "Xiaoxiao",  "gender": "Female", "style": "Warm"},
    {"id": "zh-CN-XiaoyiNeural",    "name": "Xiaoyi",    "gender": "Female", "style": "Lively"},
    {"id": "zh-CN-YunxiNeural",     "name": "Yunxi",     "gender": "Male",   "style": "Lively"},
    {"id": "zh-CN-YunyangNeural",   "name": "Yunyang",   "gender": "Male",   "style": "Professional"},
    {"id": "zh-CN-YunjianNeural",   "name": "Yunjian",   "gender": "Male",   "style": "Passionate"},
    {"id": "zh-CN-YunxiaNeural",    "name": "Yunxia",    "gender": "Male",   "style": "Cute"},
]

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


async def synth(text: str, voice: str, rate: str = "+0%") -> bytes:
    key = hashlib.md5(f"{voice}|{rate}|{text}".encode()).hexdigest()
    cached = CACHE / f"{key}.mp3"
    if cached.exists():
        return cached.read_bytes()
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            data += chunk["data"]
    cached.write_bytes(data)
    return data


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silence request logs

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        # Health check — Render pings this to mark the service ready.
        if parsed.path in ("/", "/health"):
            self.send_response(200)
            self.send_cors()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
            return

        if parsed.path == "/voices":
            body = json.dumps(VOICES).encode()
            self.send_response(200)
            self.send_cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/tts":
            text = params.get("text", [""])[0]
            voice = params.get("voice", [DEFAULT_VOICE])[0]
            rate = params.get("rate", ["+0%"])[0]
            if not text:
                self.send_response(400)
                self.end_headers()
                return
            try:
                audio = asyncio.run(synth(text, voice, rate))
                self.send_response(200)
                self.send_cors()
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", len(audio))
                self.end_headers()
                self.wfile.write(audio)
            except Exception as e:
                print(f"TTS error: {e}")
                self.send_response(500)
                self.end_headers()
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"TTS server running on http://0.0.0.0:{PORT}")
    server.serve_forever()
