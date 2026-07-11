"""越狱检测护栏（DG-IN-JD-001）—— 启发式 + NIM 模型。"""

import math
from collections import Counter
from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult


class JailbreakHeuristicsPlugin(GuardrailPlugin):
    """越狱检测 —— 启发式规则（快速路径）。"""
    plugin_id = "DG-IN-JD-001-H"
    plugin_name = "越狱检测（启发式）"
    stage = "input"
    maturity = "production"

    def __init__(self, length_per_perplexity: float = 89.79, prefix_suffix_perplexity: float = 1845.65):
        self._lpp_threshold = length_per_perplexity
        self._psp_threshold = prefix_suffix_perplexity

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        if not content:
            return GuardrailResult(is_safe=True, confidence=1.0)
        # 简易启发式：长度/熵比值
        entropy = _shannon_entropy(content)
        ratio = len(content) / max(entropy, 0.01)
        if ratio > self._lpp_threshold:
            return GuardrailResult(is_safe=False, reason="suspicious_length_perplexity", confidence=0.7)
        return GuardrailResult(is_safe=True, confidence=0.8)


class JailbreakModelPlugin(GuardrailPlugin):
    """越狱检测 —— NIM 模型（深度路径）。"""
    plugin_id = "DG-IN-JD-001-M"
    plugin_name = "越狱检测（NIM 模型）"
    stage = "input"
    maturity = "production"

    def __init__(self, nim_client=None):
        self._nim = nim_client

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        if not self._nim:
            return GuardrailResult(is_safe=True, reason="nim_unavailable", confidence=0.0)
        try:
            result = await self._nim.check(content, "jailbreak")
            return GuardrailResult(is_safe=result.get("is_safe", True), reason=result.get("reason", ""), confidence=result.get("confidence", 0.0))
        except Exception as e:
            return GuardrailResult(is_safe=False, reason=f"nim_error: {e}", confidence=0.0)


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())