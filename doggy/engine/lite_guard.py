"""轻量级 LLM 辅助检测模块 —— 三级递进架构的第三级。

提示词模板从 prompts.yml 读取，运维人员无需修改代码。
"""

import logging
from typing import Any

from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult

log = logging.getLogger(__name__)

# check_type → prompts.yml 中的 task 名称映射
TASK_MAP = {
    "content_safety": "lite_guard_content_safety",
    "jailbreak": "lite_guard_jailbreak_check",
    "hallucination": "lite_guard_hallucination_check",
}


class LiteGuardPlugin(GuardrailPlugin):
    """轻量级 LLM 辅助检测插件。

    使用 GPT-4o-mini / Claude Haiku 进行模糊边界场景的二次裁决。
    提示词从 prompts.yml 读取，支持 Jinja2 模板变量。
    """

    plugin_id = "DG-LITE-001"
    plugin_name = "轻量级 LLM 辅助检测"
    stage = "input"
    maturity = "beta"

    def __init__(
        self,
        lite_llm: Any = None,
        llm_task_manager: Any = None,
    ):
        self._lite_llm = lite_llm
        self._task_manager = llm_task_manager

    async def check(self, content: str, context: dict[str, Any] | None = None) -> GuardrailResult:
        if self._lite_llm is None:
            return GuardrailResult(is_safe=True, reason="lite_guard_unavailable")

        ctx = context or {}
        check_type = ctx.get("check_type", "content_safety")
        task_name = TASK_MAP.get(check_type, TASK_MAP["content_safety"])

        # 从 prompts.yml 渲染提示词
        if self._task_manager:
            prompt = self._task_manager.render_task_prompt(
                task=task_name,
                context={
                    "user_message": content,
                    "bot_message": ctx.get("bot_message", ""),
                },
            )
        else:
            prompt = f"Classify: {content}\nSAFE/UNSAFE:"

        try:
            response = await self._lite_llm.generate_async(
                prompt=prompt, stop=["\n\n"],
            )
            result = _parse_response(response, check_type)
        except Exception as e:
            log.error("轻量级 LLM 调用失败: %s", e)
            result = GuardrailResult(is_safe=False, reason=f"lite_guard_error: {e}", confidence=0.0)

        return result


def _parse_response(response: str, check_type: str) -> GuardrailResult:
    upper = response.strip().upper()
    if check_type == "jailbreak":
        is_safe = "JAILBREAK" not in upper
    elif check_type == "hallucination":
        is_safe = "HALLUCINATION" not in upper
    else:
        is_safe = "UNSAFE" not in upper

    return GuardrailResult(
        is_safe=is_safe,
        reason=response.strip(),
        confidence=0.8 if is_safe else 0.9,
    )