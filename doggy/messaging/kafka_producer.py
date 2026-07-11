"""Kafka 审计事件生产者 —— 异步发送，不阻塞主请求链路。"""

import asyncio
import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

log = logging.getLogger(__name__)


class AuditEventProducer:
    """审计事件 Kafka 生产者。

    双层降级策略：
      1. Kafka 可用 → 异步发送到 audit-events topic
      2. Kafka 不可用 → 降级写入本地 JSON 日志文件
    """

    def __init__(self, bootstrap_servers: str):
        self._producer: AIOKafkaProducer | None = None
        self._bootstrap_servers = bootstrap_servers

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            compression_type="lz4",
            max_batch_size=16384,
            linger_ms=10,
        )
        await self._producer.start()
        log.info("Kafka 生产者已连接: %s", self._bootstrap_servers)

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            log.info("Kafka 生产者已关闭")

    async def send(self, event: dict[str, Any]) -> None:
        """异步发送审计事件。

        不阻塞主请求链路 —— 调用方应使用 asyncio.create_task。
        """
        if not self._producer:
            log.warning("Kafka 生产者未启动，降级到本地日志")
            log.info("AUDIT_FALLBACK: %s", json.dumps(event, ensure_ascii=False))
            return

        try:
            await self._producer.send_and_wait("audit-events", event)
        except Exception as e:
            log.error("Kafka 发送失败，降级到本地日志: %s", e)
            log.info("AUDIT_FALLBACK: %s", json.dumps(event, ensure_ascii=False))