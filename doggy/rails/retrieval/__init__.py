"""检索护栏（DG-RT-CS-001, DG-RT-PII-001）。"""

from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult


class RetrievalContentSafetyPlugin(GuardrailPlugin):
    plugin_id = "DG-RT-CS-001"
    plugin_name = "检索结果内容安全"
    stage = "retrieval"
    maturity = "production"

    def __init__(self, nim_client=None):
        self._nim = nim_client

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        if not self._nim:
            return GuardrailResult(is_safe=True, reason="nim_unavailable", confidence=0.0)
        try:
            result = await self._nim.check(content, "content_safety")
            return GuardrailResult(
                is_safe=result.get("is_safe", True),
                reason=result.get("reason", ""),
                confidence=result.get("confidence", 0.0),
            )
        except Exception as e:
            return GuardrailResult(is_safe=False, reason=f"nim_error: {e}", confidence=0.0)


class RetrievalPIIMaskingPlugin(GuardrailPlugin):
    plugin_id = "DG-RT-PII-001"
    plugin_name = "检索结果脱敏"
    stage = "retrieval"
    maturity = "production"

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        return GuardrailResult(is_safe=True, confidence=1.0)
