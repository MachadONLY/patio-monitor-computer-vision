FROM node:24-alpine AS web
WORKDIR /app
RUN npm install --global pnpm@11.25.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web/ apps/web/
RUN pnpm build

FROM python:3.12-slim AS model
WORKDIR /download
COPY gs/genai/download_model.py gs/genai/model.json ./
RUN python download_model.py /weights/qwen.gguf

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PATIO_WEB_DIST=/app/web PATIO_VISION_DIR=/app/vision-artifacts \
    PATIO_LLM_MODEL_PATH=/app/weights/qwen.gguf PATIO_LLM_THREADS=1 \
    PATIO_LIVE_PROVIDER=rio_brt
COPY services/api/requirements.txt services/api/requirements-ai.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-cache-dir --only-binary=:all: \
        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu \
        -r requirements-ai.txt
COPY services/api/app app/
COPY services/vision/artifacts /app/vision-artifacts/
COPY --from=web /app/apps/web/dist/ /app/web/
COPY --from=model /weights/ /app/weights/
USER 10001:10001
EXPOSE 10000
CMD ["sh", "-ec", "exec python -m uvicorn app.hosted:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --no-server-header --ws-max-size 4096 --ws-max-queue 8"]
