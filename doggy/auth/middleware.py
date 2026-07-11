"""FastAPI 认证中间件 —— 从请求中提取 API Key 并验证。"""

import logging
from typing import Optional

from fastapi import HTTPException, Request

from doggy.auth.api_key import AppContext, verify_api_key

log = logging.getLogger(__name__)


class AuthMiddleware:
    """认证中间件 —— 验证 API Key 并注入 AppContext。

    支持两种格式：
      - Authorization: Bearer doggy-xxx
      - x-api-key: doggy-xxx

    验证流程：
      1. Redis 缓存命中 → 直接返回 AppContext
      2. 缓存未命中 → PostgreSQL 查询 → 回写 Redis
      （Redis/PostgreSQL 查找逻辑在 api.py 中实现，此中间件仅负责提取和格式校验）
    """

    @staticmethod
    def extract_api_key(request: Request) -> str:
        """从请求中提取 API Key。"""
        # 优先从 Authorization header 提取
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth.removeprefix("Bearer ").strip()

        # 其次从 x-api-key header 提取
        api_key = request.headers.get("x-api-key", "")
        if api_key:
            return api_key.strip()

        raise HTTPException(status_code=401, detail="Missing API Key")


async def authenticate(request: Request, redis_cache=None, db_pool=None) -> AppContext:
    """验证 API Key 并返回应用上下文。

    Args:
        request: FastAPI 请求对象。
        redis_cache: Redis 缓存客户端（可选）。
        db_pool: PostgreSQL 连接池（可选）。

    Returns:
        AppContext 包含应用 ID、策略名等信息。

    Raises:
        HTTPException: 401 如果 Key 无效。
    """
    raw_key = AuthMiddleware.extract_api_key(request)

    # 1. 尝试从 Redis 缓存获取
    if redis_cache:
        from doggy.auth.api_key import _hash
        cached = await redis_cache.get_app_context(_hash(raw_key))
        if cached:
            return cached

    # 2. 从 PostgreSQL 查询
    if db_pool:
        from doggy.auth.api_key import _hash, verify_api_key
        key_hash = _hash(raw_key)
        row = await db_pool.fetch_one(
            "SELECT app_id, app_name, policy_name, rate_limit_qps, allowed_models "
            "FROM api_keys WHERE key_hash = $1 AND is_active = true",
            key_hash,
        )
        if row:
            ctx = AppContext(
                app_id=row["app_id"],
                app_name=row["app_name"],
                policy_name=row["policy_name"],
                rate_limit_qps=row["rate_limit_qps"],
                allowed_models=row["allowed_models"] or ["*"],
            )
            # 回写 Redis 缓存
            if redis_cache:
                await redis_cache.cache_app_context(key_hash, ctx)
            return ctx

    raise HTTPException(status_code=401, detail="Invalid API Key")