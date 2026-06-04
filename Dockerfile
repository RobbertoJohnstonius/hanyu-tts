# Minimal Python container for the Edge-TTS proxy used by the Hanyu Mandarin
# app. Deployed via Fly.io (flyctl); see fly.toml.
FROM python:3.11-slim

WORKDIR /app

# Install Python deps first so Docker can cache the layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then the app itself.
COPY tts_server.py .

# Fly injects $PORT; tts_server.py reads it (defaults to 5275 for local dev).
EXPOSE 8080
ENV PORT=8080

CMD ["python", "-u", "tts_server.py"]
