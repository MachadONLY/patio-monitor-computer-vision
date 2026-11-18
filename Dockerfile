# One container serves the React 3D interface, FastAPI, real video and local Qwen.
FROM node:24-bookworm-slim AS web
WORKDIR /src
RUN npm install -g pnpm@11.25.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web/ apps/web/
RUN pnpm build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATIO_WEB_DIST=/srv/patio/web \
    PATIO_VISION_DIR=/srv/patio/vision \
    PATIO_LLM_MODEL_PATH=/srv/patio/qwen.gguf \
    PATIO_LLM_THREADS=2 \
    PATIO_LIVE_PROVIDER=rio_brt \
    PATIO_ARCHIVE_FILE=/srv/patio/data/observations.sqlite3
WORKDIR /srv/patio
RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends ca-certificates libgomp1 libstdc++6 gosu \
    && rm -rf /var/lib/apt/lists/*
COPY services/api/requirements.txt services/api/requirements-ai.txt /tmp/
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && python -m pip install --no-cache-dir --only-binary=:all: \
       --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu \
       -r /tmp/requirements-ai.txt
COPY services/api/app/ ./app/
COPY services/vision/artifacts/ ./vision/
COPY gs/genai/model.json ./gs/genai/model.json
COPY gs/genai/download_model.py ./gs/genai/download_model.py
RUN python gs/genai/download_model.py /srv/patio/qwen.gguf
COPY --from=web /src/apps/web/dist/ ./web/
COPY deploy/start-public.sh ./start-public.sh
RUN install -d -m 0750 -o 10001 -g 10001 /srv/patio/data \
    && chmod 0555 /srv/patio/start-public.sh \
    && chmod -R a+rX /srv/patio/web /srv/patio/vision /srv/patio/app /srv/patio/gs
# Start as root only to fix the mount ownership; start-public.sh drops to 10001.
USER 0:0
EXPOSE 8000
CMD ["/bin/sh", "/srv/patio/start-public.sh"]
