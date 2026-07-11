"""HuggingFace 远程推理后端 —— vLLM / KServe / FMS。"""

import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)


class RemoteHFBackend:
    """远程 HF 推理后端（vLLM / KServe / FMS）。

    通过 HTTP POST 调用远程推理服务，兼容 OpenAI-compatible 格式。
    """

    def __init__(self, config: dict[str, Any], engine: str = "vllm"):
        self._base_url = config.get("base_url", "").rstrip("/")
        self._model = config.get("model", "")
        self._engine = engine
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=30)
        log.info("HF 远程后端已连接: %s (%s)", self._base_url, self._engine)

    async def classify(self, text: str) -> list[dict]:
        if not self._client:
            raise RuntimeError("客户端未初始化，请先调用 start()")

        resp = await self._client.post(
            f"{self._base_url}/v1/chat/completions",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": "Classify the following text. Return only the label and score."},
                    {"role": "user", "content": text},
                ],
                "max_tokens": 50,
                "temperature": 0.0,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # 解析分类结果：尝试从响应中提取 label 和 score
        return self._parse_response(content)

    def _parse_response(self, content: str) -> list[dict]:
        parts = content.strip().split()
        if len(parts) >= 2:
            try:
                return [{"label": parts[0], "score": float(parts[1])}]
            except ValueError:
                pass
        return [{"label": content.strip(), "score": 1.0}]