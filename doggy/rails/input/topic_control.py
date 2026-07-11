"""主题管控护栏（DG-IN-TC-001）—— 使用 NIM 主题控制模型。"""

from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult


class TopicControlPlugin(GuardrailPlugin):
    plugin_id = "DG-IN-TC-001"
    plugin_name = "主题管控"
    stage = "input"
    maturity = "production"

    def __init__(
        self,
        nim_client=None,
        allowed_topics: list[str] | None = None,
        blocked_topics: list[str] | None = None,
    ):
        self._nim = nim_client
        self._allowed = allowed_topics or []
        self._blocked = blocked_topics or []

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        if not self._nim:
            return GuardrailResult(is_safe=True, reason="nim_unavailable", confidence=0.0)
        try:
            result = await self._nim.check(content, "topic_control")
            is_safe = result.get("is_safe", True)
            return GuardrailResult(
                is_safe=is_safe,
                reason=result.get("reason", ""),
                confidence=result.get("confidence", 0.0),
            )
        except Exception as e:
            return GuardrailResult(is_safe=False, reason=f"nim_error: {e}", confidence=0.0)
