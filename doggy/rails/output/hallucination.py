"""幻觉检测护栏（DG-OT-HA-001）—— 基于 SelfCheckGPT 自一致性方法。

原理：同一提示词多次生成，比较语义一致性。不一致 → 判定为幻觉。
参考：https://arxiv.org/abs/2303.08896
"""

import asyncio
import logging
from typing import Any

from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult

log = logging.getLogger(__name__)
NUM_EXTRA_RESPONSES = 2


class HallucinationDetectionPlugin(GuardrailPlugin):
    """幻觉检测 —— SelfCheckGPT 自一致性方法。

    每次检测额外调用 LLM 3 次（2 次生成 + 1 次判断），成本较高。
    建议仅在 high-stakes 场景（金融/医疗）启用。
    """

    plugin_id = "DG-OT-HA-001"
    plugin_name = "幻觉检测（SelfCheckGPT）"
    stage = "output"
    maturity = "beta"

    def __init__(self, llm: Any = None, llm_task_manager: Any = None, config: Any = None):
        self._llm = llm
        self._task_manager = llm_task_manager
        self._config = config

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        if not self._llm or not self._task_manager:
            return GuardrailResult(is_safe=True, reason="llm_unavailable", confidence=0.0)

        ctx = context or {}
        bot_message = ctx.get("bot_message", content)
        last_prompt = ctx.get("_last_bot_prompt", "")

        if not bot_message or not last_prompt:
            return GuardrailResult(is_safe=True, reason="no_context", confidence=0.0)

        # 1. 额外生成 2 次回答（temperature=1.0 增加多样性）
        async def _generate_extra() -> str | None:
            try:
                response = await self._llm.generate_async(
                    prompt=last_prompt,
                    temperature=1.0,
                )
                return response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                log.warning("额外生成失败: %s", e)
                return None

        results = await asyncio.gather(*[_generate_extra() for _ in range(NUM_EXTRA_RESPONSES)])
        extra_responses = [r for r in results if r is not None]

        if len(extra_responses) == 0:
            return GuardrailResult(is_safe=True, reason="no_extra_responses", confidence=0.0)

        # 2. 用 LLM 判断一致性
        prompt = self._task_manager.render_task_prompt(
            task="self_check_hallucination",
            context={"statement": bot_message, "paragraph": ". ".join(extra_responses)},
        )

        try:
            response = await self._llm.generate_async(prompt=prompt, temperature=0.0)
            result_text = (response.content if hasattr(response, "content") else str(response)).lower().strip()
            is_hallucination = "no" in result_text
            return GuardrailResult(
                is_safe=not is_hallucination,
                reason=f"hallucination_check: {result_text}" if is_hallucination else "consistent",
                confidence=0.8 if is_hallucination else 0.9,
            )
        except Exception as e:
            return GuardrailResult(is_safe=True, reason=f"check_error: {e}", confidence=0.0)


class SelfCheckFactsPlugin(GuardrailPlugin):
    """自检事实核查 —— 使用 LLM 判断回答是否与已知事实一致。

    无外部知识库时的轻量级事实核查方案。
    """

    plugin_id = "DG-OT-FACT-001"
    plugin_name = "自检事实核查"
    stage = "output"
    maturity = "beta"

    def __init__(self, llm: Any = None, llm_task_manager: Any = None):
        self._llm = llm
        self._task_manager = llm_task_manager

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        if not self._llm or not self._task_manager:
            return GuardrailResult(is_safe=True, reason="llm_unavailable", confidence=0.0)

        ctx = context or {}
        bot_message = ctx.get("bot_message", content)
        evidence = ctx.get("relevant_chunks", "")

        prompt = self._task_manager.render_task_prompt(
            task="self_check_facts",
            context={"evidence": evidence, "response": bot_message},
        )

        try:
            response = await self._llm.generate_async(prompt=prompt, temperature=0.0)
            result = (response.content if hasattr(response, "content") else str(response)).lower().strip()
            is_safe = "yes" in result
            return GuardrailResult(is_safe=is_safe, reason=result, confidence=0.85)
        except Exception as e:
            return GuardrailResult(is_safe=True, reason=f"check_error: {e}", confidence=0.0)
