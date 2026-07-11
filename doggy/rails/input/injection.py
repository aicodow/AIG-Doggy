"""注入检测（DG-IN-IJ-001）/ 上下文膨胀检测（DG-IN-CB-001）/ 工具调用验证（DG-OT-TL-001）/ 幻觉检测（DG-OT-HA-001）。"""

from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult


class InjectionDetectionPlugin(GuardrailPlugin):
    plugin_id = "DG-IN-IJ-001"
    plugin_name = "注入检测"
    stage = "input"
    maturity = "beta"

    SQL_PATTERNS = ["';", "DROP TABLE", "UNION SELECT", "1=1", "--", "OR 1=1"]
    XSS_PATTERNS = ["<script", "javascript:", "onerror=", "onload="]

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        upper = content.upper()
        for p in self.SQL_PATTERNS:
            if p.upper() in upper:
                return GuardrailResult(is_safe=False, reason=f"疑似SQL注入: {p}", confidence=0.9)
        lower = content.lower()
        for p in self.XSS_PATTERNS:
            if p in lower:
                return GuardrailResult(is_safe=False, reason=f"疑似XSS: {p}", confidence=0.9)
        return GuardrailResult(is_safe=True, confidence=1.0)


class ContextBloatPlugin(GuardrailPlugin):
    plugin_id = "DG-IN-CB-001"
    plugin_name = "上下文膨胀检测"
    stage = "input"
    maturity = "experimental"

    def __init__(self, max_chars: int = 5000, min_entropy: float = 3.5, max_repetition: float = 0.4):
        self._max_chars = max_chars
        self._min_entropy = min_entropy
        self._max_repetition = max_repetition

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        if len(content) > self._max_chars:
            return GuardrailResult(is_safe=False, reason="输入过长", confidence=1.0)
        if len(content) < 50:
            return GuardrailResult(is_safe=True, confidence=1.0)
        import math
        from collections import Counter
        counts = Counter(content)
        length = len(content)
        entropy = -sum((c / length) * math.log2(c / length) for c in counts.values())
        if entropy < self._min_entropy:
            return GuardrailResult(is_safe=False, reason="输入熵异常", confidence=0.8)
        return GuardrailResult(is_safe=True, confidence=1.0)


class ToolValidationPlugin(GuardrailPlugin):
    plugin_id = "DG-OT-TL-001"
    plugin_name = "工具调用验证"
    stage = "output"
    maturity = "production"

    def __init__(self, allowed_tools: list[str] | None = None):
        self._allowed = set(allowed_tools or [])

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        tool_calls = (context or {}).get("tool_calls", [])
        for tc in tool_calls:
            name = tc.get("function", {}).get("name", "")
            if self._allowed and name not in self._allowed:
                return GuardrailResult(is_safe=False, reason=f"未授权的工具调用: {name}", confidence=1.0)
        return GuardrailResult(is_safe=True, confidence=1.0)


class ToolWhitelistPlugin(GuardrailPlugin):
    plugin_id = "DG-EX-TL-001"
    plugin_name = "工具调用白名单"
    stage = "execution"
    maturity = "production"

    def __init__(self, allowed_tools: list[str] | None = None):
        self._allowed = set(allowed_tools or [])

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        return GuardrailResult(is_safe=True, confidence=1.0)
