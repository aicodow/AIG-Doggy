"""Prometheus 指标暴露 —— /v1/metrics 端点。"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest,
)

REGISTRY = CollectorRegistry()

doggy_requests_total = Counter(
    "doggy_requests_total", "请求总数",
    ["app_id", "rail_type", "result"], registry=REGISTRY,
)

doggy_rails_blocked_total = Counter(
    "doggy_rails_blocked_total", "护栏拦截总数",
    ["app_id", "rail_type", "blocked_reason"], registry=REGISTRY,
)

doggy_request_duration_seconds = Histogram(
    "doggy_request_duration_seconds", "请求处理延迟",
    ["app_id", "stage"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 5.0],
    registry=REGISTRY,
)

doggy_rail_duration_seconds = Histogram(
    "doggy_rail_duration_seconds", "护栏执行延迟",
    ["rail_type", "result"],
    buckets=[0.005, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0],
    registry=REGISTRY,
)

doggy_errors_total = Counter(
    "doggy_errors_total", "错误总数",
    ["app_id", "error_type"], registry=REGISTRY,
)

doggy_active_connections = Gauge(
    "doggy_active_connections", "活跃连接数", registry=REGISTRY,
)


def setup_metrics(app: FastAPI) -> None:
    """注册 /v1/metrics 端点和请求计时中间件。"""

    @app.get("/v1/metrics")
    async def metrics():
        return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable):
        if request.url.path == "/v1/metrics":
            return await call_next(request)

        start = time.monotonic()
        doggy_active_connections.inc()

        try:
            response = await call_next(request)
            duration = time.monotonic() - start
            app_id = getattr(request.state, "app_id", "unknown")
            doggy_request_duration_seconds.labels(app_id=app_id, stage="total").observe(duration)
            return response
        except Exception as e:
            doggy_errors_total.labels(
                app_id=getattr(request.state, "app_id", "unknown"),
                error_type=type(e).__name__,
            ).inc()
            raise
        finally:
            doggy_active_connections.dec()


def record_rail_result(app_id: str, rail_type: str, result: str, duration_s: float, reason: str = "") -> None:
    """记录单个护栏的执行结果。"""
    doggy_requests_total.labels(app_id=app_id, rail_type=rail_type, result=result).inc()
    doggy_rail_duration_seconds.labels(rail_type=rail_type, result=result).observe(duration_s)
    if result == "BLOCKED":
        doggy_rails_blocked_total.labels(app_id=app_id, rail_type=rail_type, blocked_reason=reason).inc()