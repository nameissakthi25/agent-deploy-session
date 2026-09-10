# One image, all three stages. STAGE picks the graph at startup.
FROM python:3.11-slim

# Layer order matters here, and it gets shown on screen at 0:40. Dependencies
# are installed before the application code is copied, so editing a .py file
# invalidates only the last layer -- a code-only rebuild is a few seconds
# instead of reinstalling everything.
WORKDIR /srv
COPY requirements.txt requirements-guards.txt ./

# Guardrails AI first, ours second, and the ORDER IS THE POINT. It declares
# openai<3.0.0 while we pin openai==3.10.0, so installing them the other way
# round fails outright and installing only the first leaves the app on a
# major-version-old client. Installing ours last lets our pin win.
#
# pip prints a dependency-conflict warning on the second command. That warning
# is expected and the build should not be "fixed" by silencing it: the 72-test
# suite passes with both present, because the guard path never touches the
# OpenAI client. See requirements-guards.txt for the full note.
#
# It is in the image so GUARD_BACKEND can be flipped at runtime with no
# rebuild, which is what makes the two backends comparable in one Phoenix
# project. It costs image size for a backend most containers will not use.
RUN pip install --no-cache-dir -r requirements-guards.txt  && pip install --no-cache-dir -r requirements.txt

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
