"""Doggy 服务启动引导 —— 按依赖顺序初始化中间件和引擎。"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from doggy.engine.nemo_adapter import NeMoAdapter
from doggy.server.logging_config import setup_logging
from doggy.server.metrics import setup_metrics

setup_logging(logging.DEBUG if os.environ.get("DOGGY_DEBUG") else logging.INFO)
log = logging.getLogger(__name__)

# 全局服务实例
engine: NeMoAdapter | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global engine

    log.info("正在初始化 Doggy 引擎...")
    config_path = os.environ.get("DOGGY_CONFIG_PATH", "doggy/configs/default")
    engine = NeMoAdapter.from_config_path(config_path)
    await engine.startup()
    log.info("Doggy 引擎初始化完成，开始接收请求")

    yield

    log.info("正在关闭服务...")
    if engine:
        await engine.shutdown()
    log.info("服务已关闭")


app = FastAPI(
    title="AIG-Doggy",
    version="0.1.0",
    description="企业级 LLM 安全护栏",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("DOGGY_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def setup_app() -> None:
    """注册所有路由和中间件。在 uvicorn 启动前调用。"""
    from doggy.server.api import router as api_router
    from doggy.server.admin_api import router as admin_router

    app.include_router(api_router)
    app.include_router(admin_router)
    setup_metrics(app)

    log.info("路由和中间件注册完成")


# 健康检查
@app.get("/v1/healthz")
async def healthz():
    return {"status": "healthy"}


@app.get("/v1/readyz")
async def readyz():
    if engine is None:
        return {"status": "not_ready"}, 503
    return {"status": "ready"}