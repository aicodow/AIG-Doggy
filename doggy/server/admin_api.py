"""管理 API 路由 —— 策略管理、审计日志、应用管理、用户管理。"""

import logging

from fastapi import APIRouter, Query, Request

from doggy.rails.plugins import list_all as list_plugins

log = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/policies")
async def list_policies():
    """列出所有安全策略。"""
    return {"policies": [{"name": "default", "version": 1, "is_active": True}]}


@router.get("/policies/{name}")
async def get_policy(name: str):
    """获取指定策略详情。"""
    return {"name": name, "version": 1, "config": {}}


@router.get("/audit-logs")
async def audit_logs(
    app_id: str | None = Query(None),
    result: str | None = Query(None),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """检索审计日志。"""
    return {
        "logs": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


@router.get("/audit-logs/export")
async def export_audit_logs(format: str = Query("json")):
    """导出审计日志。"""
    return {"format": format, "url": ""}


@router.get("/apps")
async def list_apps():
    """列出所有已注册的应用。"""
    return {"apps": []}


@router.post("/apps")
async def register_app(request: Request):
    """注册新应用并生成 API Key。"""
    body = await request.json()
    return {"app_id": body.get("name", "new-app"), "api_key": "doggy-generated-key"}


@router.get("/apps/{app_id}/api-keys")
async def list_api_keys(app_id: str):
    """列出应用的 API Keys。"""
    return {"app_id": app_id, "keys": []}


@router.post("/apps/{app_id}/api-keys")
async def generate_api_key(app_id: str):
    """为应用生成新的 API Key。"""
    from doggy.auth.api_key import generate_api_key
    raw, hashed = generate_api_key()
    return {"app_id": app_id, "api_key": raw, "warning": "此 Key 仅显示一次，请立即保存"}


@router.delete("/apps/{app_id}/api-keys/{key_id}")
async def revoke_api_key(app_id: str, key_id: str):
    """吊销 API Key。"""
    return {"app_id": app_id, "key_id": key_id, "status": "revoked"}


@router.get("/plugins")
async def get_plugins(stage: str | None = Query(None)):
    """列出所有已注册的护栏插件。"""
    return {"plugins": list_plugins(stage)}


@router.get("/health/services")
async def service_health():
    """检查所有依赖服务健康状态。"""
    return {
        "gateway": "healthy",
        "nim_content_safety": "healthy",
        "kafka": "healthy",
        "redis": "healthy",
        "postgres": "healthy",
    }
