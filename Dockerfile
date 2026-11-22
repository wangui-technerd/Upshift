FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    UPSHIFT_REQUIRE_MODEL=1 \
    HOME=/home/upshift

WORKDIR /app
RUN groupadd --gid 10001 upshift && useradd --uid 10001 --gid upshift --create-home upshift

COPY backend/requirements.txt backend/requirements-model.txt ./backend/
RUN python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.9.0 \
    && python -m pip install --no-cache-dir -r backend/requirements-model.txt \
    && python -m pip check

COPY backend/ ./backend/
COPY upshift_ai/ ./upshift_ai/

USER upshift
CMD ["sh", "-c", "exec python -m uvicorn backend.app:app --host 0.0.0.0 --port \"${PORT:-8080}\" --no-proxy-headers --no-access-log"]
