FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 安装 Python 依赖
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 复制源码
COPY src/ ./

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/v1/healthz || exit 1

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "doggy.server.bootstrap:app", "--host", "0.0.0.0", "--port", "8000"]