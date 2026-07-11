"""HuggingFace 分类器护栏 —— 通用 HF 模型分类器框架。

支持 4 种推理后端：local（transformers）、vllm、kserve、fms。
通过配置即可接入任意 HF 分类模型，无需改代码。
"""

import logging
from typing import Any

from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult

log = logging.getLogger(__name__)


class HFClassifierPlugin(GuardrailPlugin):
    """通用 HuggingFace 分类器护栏。

    配置示例（config.yml）:
      hf_classifier:
        toxicity:
          engine: local
          model: "unitary/toxic-bert"
          task: text-classification
          threshold: 0.5
          blocked_labels: ["toxic", "severe_toxic"]
    """

    plugin_id = "DG-HF-CLS-001"
    plugin_name = "HuggingFace 分类器"
    stage = "input"
    maturity = "production"

    SUPPORTED_ENGINES = {"local", "vllm", "kserve", "fms"}

    def __init__(self, classifier_configs: dict[str, Any] | None = None):
        self._configs = classifier_configs or {}
        self._backends: dict[str, Any] = {}

    async def _get_backend(self, name: str, config: dict) -> Any:
        if name in self._backends:
            return self._backends[name]

        engine = config.get("engine", "local")
        if engine == "local":
            from doggy.rails.output.hf_local import LocalHFBackend
            backend = LocalHFBackend(config)
        elif engine == "vllm":
            from doggy.rails.output.hf_remote import RemoteHFBackend
            backend = RemoteHFBackend(config, engine="vllm")
        elif engine in ("kserve", "fms"):
            from doggy.rails.output.hf_remote import RemoteHFBackend
            backend = RemoteHFBackend(config, engine=engine)
        else:
            raise ValueError(f"不支持的后端: {engine}。支持: {self.SUPPORTED_ENGINES}")

        await backend.start()
        self._backends[name] = backend
        return backend

    async def classify(self, classifier_name: str, text: str) -> GuardrailResult:
        """使用指定分类器对文本进行分类。

        Args:
            classifier_name: 分类器名称（对应 config.yml 中的 key）。
            text: 待分类文本。

        Returns:
            GuardrailResult 包含检测结果。
        """
        if classifier_name not in self._configs:
            return GuardrailResult(is_safe=True, reason=f"unknown_classifier: {classifier_name}", confidence=0.0)

        if not text:
            return GuardrailResult(is_safe=True, confidence=1.0)

        config = self._configs[classifier_name]
        backend = await self._get_backend(classifier_name, config)

        try:
            results = await backend.classify(text)
        except Exception as e:
            log.error("HF 分类器 '%s' 推理失败: %s", classifier_name, e)
            return GuardrailResult(is_safe=False, reason=f"hf_error: {e}", confidence=0.0)

        if not results:
            return GuardrailResult(is_safe=True, confidence=1.0)

        blocked_labels = set(config.get("blocked_labels", []))
        threshold = config.get("threshold", 0.5)

        triggered = [
            (r["label"], r["score"])
            for r in results
            if r["label"] in blocked_labels and r["score"] >= threshold
        ]

        if triggered:
            return GuardrailResult(
                is_safe=False,
                reason=f"blocked: {triggered}",
                confidence=max(s for _, s in triggered),
                metadata={"classifier": classifier_name, "detections": triggered},
            )

        return GuardrailResult(is_safe=True, confidence=1.0)

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        ctx = context or {}
        classifier_name = ctx.get("classifier", list(self._configs.keys())[0] if self._configs else "")
        return await self.classify(classifier_name, content)


class HFClassifierInputPlugin(HFClassifierPlugin):
    plugin_id = "DG-IN-HF-001"
    plugin_name = "HF 分类器（输入）"
    stage = "input"


class HFClassifierOutputPlugin(HFClassifierPlugin):
    plugin_id = "DG-OT-HF-001"
    plugin_name = "HF 分类器（输出）"
    stage = "output"
