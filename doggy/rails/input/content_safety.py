"""内容安全护栏 —— 使用 NIM 内容安全模型（DG-IN-CS-001）。"""

from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult


class ContentSafetyInputPlugin(GuardrailPlugin):
    plugin_id = "DG-IN-CS-001"
    plugin_name = "内容安全检测（输入）"
    stage = "input"
    maturity = "benchmark"

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


class ContentSafetyOutputPlugin(GuardrailPlugin):
    plugin_id = "DG-OT-CS-001"
    plugin_name = "内容安全检测（输出）"
    stage = "output"
    maturity = "benchmark"

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