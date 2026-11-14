# Scam classifier service image (CPU only). Build context = repository root:
#   docker build -f deploy/azure/Dockerfile -t scam-service .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/opt/hf HF_HUB_DISABLE_TELEMETRY=1

WORKDIR /app
COPY deploy/azure/requirements-service.txt /tmp/requirements-service.txt
RUN pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r /tmp/requirements-service.txt

# Bake the small embedding model (all-MiniLM-L6-v2, ~90 MB) into the image -> fast, offline startup.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY src/ /app/src/
COPY config/ /app/config/

RUN useradd --create-home --uid 10001 app && chown -R app /app /opt/hf
USER app
ENV HF_HUB_OFFLINE=1

EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=5s --start-period=600s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8100/healthz', timeout=4)"
CMD ["python", "-m", "uvicorn", "service.app:create_app", "--factory", "--app-dir", "src", \
     "--host", "0.0.0.0", "--port", "8100", "--workers", "1"]
