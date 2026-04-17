FROM python:3.13-slim

ENV UV_CACHE_DIR=/opt/zagent/cache/uv \
    npm_config_cache=/opt/zagent/cache/npm

WORKDIR /opt/zagent

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY packages/runtime /opt/zagent/packages/runtime

RUN pip install --no-cache-dir /opt/zagent/packages/runtime

ENTRYPOINT ["zagent-runtime"]
