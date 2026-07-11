"""多协议适配器 —— 将 OpenAI/Anthropic 格式转换为 NeMo 内部统一格式。"""

from abc import ABC, abstractmethod
from typing import Any

from doggy.exceptions import ProtocolNotSupportedError


class ProtocolAdapter(ABC):
    """协议适配器抽象基类。"""

    @abstractmethod
    def to_internal(self, messages: list[dict]) -> list[dict]:
        """将外部协议消息转换为内部统一格式。"""
        ...

    @abstractmethod
    def to_external(self, response: Any) -> dict:
        """将内部响应转换为外部协议格式。"""
        ...


class OpenAIAdapter(ProtocolAdapter):
    """OpenAI 协议适配器。"""

    def to_internal(self, messages: list[dict]) -> list[dict]:
        internal = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                internal.append({"role": "context", "content": {"system_prompt": content}})
            elif role == "user":
                internal.append({"role": "user", "content": content})
            elif role == "assistant":
                entry: dict = {"role": "assistant", "content": content or ""}
                if msg.get("tool_calls"):
                    entry["tool_calls"] = msg["tool_calls"]
                internal.append(entry)
            elif role == "tool":
                internal.append({
                    "role": "tool",
                    "content": content,
                    "tool_call_id": msg.get("tool_call_id", ""),
                    "name": msg.get("name", "unknown"),
                })

        return internal

    def to_external(self, response: Any) -> dict:
        if hasattr(response, "response"):
            content = (
                response.response
                if isinstance(response.response, str)
                else response.response[-1].get("content", "")
            )
            return {
                "id": f"doggy-{_short_id()}",
                "object": "chat.completion",
                "model": getattr(response, "model", "doggy-guard"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
            }
        if isinstance(response, dict):
            return {
                "id": f"doggy-{_short_id()}",
                "object": "chat.completion",
                "choices": [{"index": 0, "message": response, "finish_reason": "stop"}],
            }
        return {"content": str(response)}


class AnthropicAdapter(ProtocolAdapter):
    """Anthropic 协议适配器。

    Anthropic content 数组格式 → 内部纯文本格式。
    """

    def to_internal(self, messages: list[dict]) -> list[dict]:
        internal = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                content = "\n".join(text_parts)

            if role == "system":
                internal.append({"role": "context", "content": {"system_prompt": content}})
            else:
                internal.append({"role": role, "content": content})

        return internal

    def to_external(self, response: Any) -> dict:
        if hasattr(response, "response"):
            text = response.response if isinstance(response.response, str) else response.response[-1].get("content", "")
        elif isinstance(response, dict):
            text = response.get("content", "")
        else:
            text = str(response)

        return {
            "id": f"msg_doggy_{id(response):x}",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
            "model": "doggy-guard",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }


_ADAPTERS: dict[str, ProtocolAdapter] = {
    "openai": OpenAIAdapter(),
    "anthropic": AnthropicAdapter(),
}


def get_adapter(protocol: str) -> ProtocolAdapter:
    if protocol not in _ADAPTERS:
        raise ProtocolNotSupportedError(f"不支持的协议: {protocol}。支持: {list(_ADAPTERS.keys())}")
    return _ADAPTERS[protocol]


def _short_id() -> str:
    import uuid
    return uuid.uuid4().hex[:12]
