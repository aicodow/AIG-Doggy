"""Doggy 引擎协议 —— 定义 Doggy 自有接口，隔离 NeMo 上游变更。

此模块是三层防御体系的核心。业务代码只依赖此接口，
不导入 nemoguardrails。上游变更仅影响 NeMoAdapter 一个文件。
"""

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DoggyEngineProtocol(Protocol):
    """Doggy 引擎协议。

    业务代码只依赖此接口，不依赖 NeMo 内部类。
    即使 NeMo 完全重构，只要适配器实现此接口，业务代码无需修改。
    """

    async def startup(self) -> None:
        """启动引擎，初始化所有依赖。"""
        ...

    async def shutdown(self) -> None:
        """关闭引擎，释放所有资源。"""
        ...

    async def generate_async(
        self,
        messages: list[dict[str, Any]],
        protocol: str = "openai",
    ) -> Any:
        """安全生成 —— 协议适配 → 护栏 → LLM → 审计。

        Args:
            messages: 原始协议格式的消息列表。
            protocol: 协议类型 ("openai" | "anthropic")。

        Returns:
            原始协议格式的响应。
        """
        ...

    async def stream_async(
        self,
        messages: list[dict[str, Any]],
        protocol: str = "openai",
    ) -> AsyncIterator[str | dict]:
        """流式安全生成。

        Args:
            messages: 原始协议格式的消息列表。
            protocol: 协议类型。

        Yields:
            流式 token 或元数据 chunk。
        """
        ...

    async def check_async(
        self,
        messages: list[dict[str, Any]],
    ) -> Any:
        """纯护栏检查（不调用 LLM）。

        Args:
            messages: 消息列表。

        Returns:
            护栏检查结果。
        """
        ...
