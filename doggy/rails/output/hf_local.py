"""HuggingFace 本地推理后端 —— 使用 transformers.pipeline()。"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

log = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)


class LocalHFBackend:
    """本地 HF Transformers Pipeline 推理后端。"""

    def __init__(self, config: dict[str, Any]):
        self._model = config.get("model", "")
        self._task = config.get("task", "text-classification")
        self._params = config.get("parameters", {})
        self._pipeline = None

    async def start(self) -> None:
        if self._pipeline:
            return
        loop = asyncio.get_event_loop()
        self._pipeline = await loop.run_in_executor(_executor, self._load_pipeline)

    def _load_pipeline(self):
        from transformers import pipeline
        log.info("加载 HF 模型: %s (task=%s)", self._model, self._task)
        return pipeline(self._task, model=self._model, **self._params)

    async def classify(self, text: str) -> list[dict]:
        if not self._pipeline:
            raise RuntimeError("模型未加载，请先调用 start()")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(_executor, lambda: self._pipeline(text))

        if isinstance(result, list) and result and isinstance(result[0], dict) and "label" in result[0]:
            return result
        if isinstance(result, dict) and "label" in result:
            return [result]
        return [{"label": str(r), "score": 1.0} for r in (result if isinstance(result, list) else [result])]