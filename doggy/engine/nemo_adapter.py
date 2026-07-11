"""NeMo 适配器 —— 组合模式包装 NeMo Guardrails 实例。

这是整个项目唯一直接导入 nemoguardrails 的模块。
上游 NeMo API 变更的影响范围被严格限制在此文件中。

设计原则：
  1. 组合而非继承：持有 NeMo Guardrails 作为私有成员
  2. 实现 DoggyEngineProtocol：对外暴露稳定接口
  3. 注入企业扩展点：协议适配、策略加载、审计回调、指标记录
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from nemoguardrails import Guardrails, RailsConfig

from doggy.adapters.protocol import get_adapter
from doggy.engine.protocol import DoggyEngineProtocol
from doggy.server.metrics import record_rail_result

log = logging.getLogger(__name__)


class NeMoAdapter(DoggyEngineProtocol):
    """组合模式包装 NeMo Guardrails，实现 DoggyEngineProtocol。

    上游变更应对：
      - NeMo 小改动 → 修改此文件中对应的包装方法（预计 1-2 人天）
      - NeMo 大改动 → 重写此文件，业务代码零改动
    """

    def __init__(
        self,
        config: RailsConfig,
        llm: Any = None,
        verbose: bool = False,
        *,
        audit_producer: Any = None,
        app_id: str = "",
    ):
        self._config = config
        self._audit = audit_producer
        self._app_id = app_id
        self._engine = Guardrails(config=config, llm=llm, verbose=verbose)

    async def startup(self) -> None:
        await self._engine.startup()

    async def shutdown(self) -> None:
        await self._engine.shutdown()

    # ── 核心方法 ──────────────────────────────────────────

    async def generate_async(
        self,
        messages: list[dict[str, Any]],
        protocol: str = "openai",
    ) -> Any:
        adapter = get_adapter(protocol)
        internal_messages = adapter.to_internal(messages)

        t0 = time.monotonic()
        try:
            response = await self._engine.generate_async(messages=internal_messages)
        except Exception:
            log.exception("护栏生成失败 app_id=%s", self._app_id)
            self._record_audit("ERROR", messages, int((time.monotonic() - t0) * 1000))
            raise

        duration_ms = int((time.monotonic() - t0) * 1000)
        self._record_audit("SUCCESS", messages, duration_ms)
        return adapter.to_external(response)

    async def stream_async(
        self,
        messages: list[dict[str, Any]],
        protocol: str = "openai",
    ) -> AsyncIterator[str | dict]:
        adapter = get_adapter(protocol)
        internal_messages = adapter.to_internal(messages)

        async for chunk in self._engine.stream_async(messages=internal_messages):
            yield chunk

    async def check_async(self, messages: list[dict[str, Any]]) -> Any:
        return await self._engine.check_async(messages)

    # ── 审计与指标 ────────────────────────────────────────

    def _record_audit(self, result: str, messages: list[dict], duration_ms: int) -> None:
        """记录审计事件到 Kafka 和 Prometheus。"""
        rail_type = "guardrails"
        record_rail_result(self._app_id, rail_type, result, duration_ms / 1000.0)

        if self._audit:
            asyncio.create_task(
                self._audit.send({
                    "app_id": self._app_id,
                    "result": result,
                    "duration_ms": duration_ms,
                    "summary": str(messages[-1].get("content", ""))[:200] if messages else "",
                })
            )

    # ── 配置管理 ──────────────────────────────────────────

    @classmethod
    def from_config_path(cls, config_path: str, **kwargs) -> "NeMoAdapter":
        config = RailsConfig.from_path(config_path)
        return cls(config=config, **kwargs)

    @property
    def config(self) -> RailsConfig:
        return self._config
