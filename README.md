# hanyu-tts

Edge-TTS proxy server for the Hanyu Mandarin learning app. Streams synthesised
Chinese audio from Microsoft Edge's neural voices over HTTP.

Deployed on Render via the `render.yaml` blueprint; can also be run locally
(`python tts_server.py`) or in Docker (`docker build -t hanyu-tts . && docker run -p 8080:8080 hanyu-tts`).

## Endpoints

- `GET /tts?text=...&voice=zh-CN-XiaoxiaoNeural&rate=+0%` — returns MP3
- `GET /voices` — JSON list of voice ids
- `GET /health` — `200 ok` (Render uses this for the health check)
