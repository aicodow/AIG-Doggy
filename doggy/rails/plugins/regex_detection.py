"""正则检测引擎 —— 从 YAML 配置读取规则，预编译正则。"""

import re
from typing import Any

from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult


class RegexDetectionPlugin(GuardrailPlugin):
    """基于配置的正则检测护栏。

    规则从 config.yml 的 rails.config.regex_detection 中读取。
    运维人员修改 YAML 配置即可调整检测规则，无需改代码。
    """

    plugin_id = "DG-IN-REGEX-001"
    plugin_name = "正则检测引擎"
    stage = "input"
    maturity = "production"

    def __init__(self, config: dict[str, Any] | None = None):
        self._rules: list[dict] = []
        if not config:
            return

        flags = re.IGNORECASE if config.get("case_insensitive") else 0
        for rule in config.get("patterns", []):
            self._rules.append({
                "regex": re.compile(rule["pattern"], flags),
                "description": rule.get("description", ""),
                "level": rule.get("level", "warning"),
                "action": rule.get("action", "block"),
            })

    async def check(self, content: str, context: dict[str, Any] | None = None) -> GuardrailResult:
        for rule in self._rules:
            if not rule["regex"].search(content):
                continue

            if rule["action"] == "block":
                return GuardrailResult(
                    is_safe=False,
                    reason=f"匹配到检测规则: {rule['description']}",
                    confidence=1.0,
                    metadata={"rule": rule["description"], "level": rule["level"]},
                )
            elif rule["action"] == "mask":
                sanitized = rule["regex"].sub("[已脱敏]", content)
                return GuardrailResult(
                    is_safe=True, reason=f"敏感信息已脱敏: {rule['description']}",
                    sanitized_content=sanitized, confidence=0.95,
                    metadata={"rule": rule["description"], "level": rule["level"]},
                )
            elif rule["action"] == "log":
                return GuardrailResult(
                    is_safe=True, reason=f"检测到匹配但仅记录: {rule['description']}",
                    confidence=1.0,
                    metadata={"rule": rule["description"], "level": rule["level"]},
                )

        return GuardrailResult(is_safe=True, confidence=1.0)
