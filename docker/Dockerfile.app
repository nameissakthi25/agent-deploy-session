# One image, all three stages. STAGE picks the graph at startup.
FROM python:3.11-slim

# Layer order matters here, and it gets shown on screen at 0:40. Dependencies
# are installed before the application code is copied, so editing a .py file
# invalidates only the last layer -- a code-only rebuild is a few seconds
# instead of reinstalling everything.
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the ONNX embedding model at build time, not at container start.
# Baked into this layer, so the containers need no network at runtime and a
# code-only rebuild does not re-download it.
ENV FASTEMBED_CACHE_PATH=/srv/.fastembed
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

COPY app/ ./app/

# Unbuffered, or nothing appears in `docker compose logs` until the buffer
# flushes, which makes a live demo look broken.
ENV PYTHONUNBUFFERED=1

# APP_PORT is validated by app/config.py at import, so a missing value
# crashes with a clear message rather than binding a nonsense port.
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${APP_PORT}"]
