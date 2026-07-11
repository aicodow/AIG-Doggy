"""PII 检测护栏（DG-IN-PII-001）—— 身份证/电话/邮箱/银行卡。"""

import re
from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult

CRITICAL_PATTERNS = [
    (re.compile(r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])\d{6}(?!\d)"), "身份证号"),
    (re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*\S+"), "疑似密钥/凭证"),
]
WARNING_PATTERNS = [
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "手机号"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "邮箱"),
    (re.compile(r"(?<!\d)\d{15,19}(?!\d)"), "银行卡号"),
]


class PIIDetectionPlugin(GuardrailPlugin):
    plugin_id = "DG-IN-PII-001"
    plugin_name = "敏感信息检测"
    stage = "input"
    maturity = "production"

    def __init__(self, presidio_client=None):
        self._presidio = presidio_client

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        # 高危检测
        for pattern, desc in CRITICAL_PATTERNS:
            if pattern.search(content):
                return GuardrailResult(is_safe=False, reason=f"检测到{desc}", confidence=1.0, metadata={"entity": desc, "level": "critical"})
        # 警告检测
        sanitized = content
        for pattern, desc in WARNING_PATTERNS:
            if pattern.search(content):
                sanitized = pattern.sub("[已脱敏]", sanitized)
        if sanitized != content:
            return GuardrailResult(is_safe=True, reason="敏感信息已脱敏", sanitized_content=sanitized, confidence=0.95)
        return GuardrailResult(is_safe=True, confidence=1.0)


class PIIOutputPlugin(GuardrailPlugin):
    plugin_id = "DG-OT-PII-001"
    plugin_name = "输出脱敏"
    stage = "output"
    maturity = "production"

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        sanitized = content
        for pattern, desc in WARNING_PATTERNS:
            sanitized = pattern.sub("[已脱敏]", sanitized)
        if sanitized != content:
            return GuardrailResult(is_safe=True, reason="敏感信息已脱敏", sanitized_content=sanitized, confidence=0.95)
        return GuardrailResult(is_safe=True, confidence=1.0)