"""Redis Cluster 缓存客户端。"""

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from doggy.auth.api_key import AppContext

log = logging.getLogger(__name__)


class RedisCacheManager:
    """Redis Cluster 缓存管理器。

    缓存策略：
      - API Key 验证结果: TTL 5 分钟
      - 策略配置: TTL 10 分钟
      - 限流计数器: Sliding Window
    """

    TTL_APP_CTX = 300      # API Key → AppContext: 5 分钟
    TTL_POLICY = 600       # 策略配置: 10 分钟

    def __init__(self, startup_nodes: list[dict]):
        self._client: Optional[aioredis.RedisCluster] = None
        self._startup_nodes = startup_nodes

    async def start(self) -> None:
        self._client = aioredis.RedisCluster(
            startup_nodes=self._startup_nodes,
            decode_responses=True,
            max_connections_per_node=50,
            retry_on_timeout=True,
        )
        log.info("Redis Cluster 已连接: %d 节点", len(self._startup_nodes))

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> aioredis.RedisCluster:
        if not self._client:
            raise RuntimeError("Redis 客户端未初始化，请先调用 start()")
        return self._client

    # ── AppContext 缓存 ─────────────────────────────────

    async def cache_app_context(self, key_hash: str, ctx: AppContext) -> None:
        data = json.dumps({
            "app_id": ctx.app_id, "app_name": ctx.app_name,
            "policy_name": ctx.policy_name, "rate_limit_qps": ctx.rate_limit_qps,
            "allowed_models": ctx.allowed_models,
        })
        await self.client.setex(f"apikey:{key_hash}", self.TTL_APP_CTX, data)

    async def get_app_context(self, key_hash: str) -> Optional[AppContext]:
        data = await self.client.get(f"apikey:{key_hash}")
        if not data:
            return None
        d = json.loads(data)
        return AppContext(
            app_id=d["app_id"], app_name=d["app_name"],
            policy_name=d["policy_name"], rate_limit_qps=d["rate_limit_qps"],
            allowed_models=d.get("allowed_models", ["*"]),
        )

    # ── 限流 ────────────────────────────────────────────

    async def check_rate_limit(self, app_id: str, qps: int) -> bool:
        """检查是否超过限流阈值。返回 True 表示允许通过。"""
        minute_key = f"rate:{app_id}:{_current_minute()}"
        count = await self.client.incr(minute_key)
        await self.client.expire(minute_key, 60)
        return count <= qps


def _current_minute() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M")