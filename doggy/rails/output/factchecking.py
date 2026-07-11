"""事实核查护栏（DG-OT-FACT-002）—— 基于 AlignScore 信息对齐评分。

原理：计算知识库证据与 LLM 回答之间的信息对齐分数。
分数 < 0.5 → 事实不一致 → 拦截。
"""

import logging

import httpx

from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult

log = logging.getLogger(__name__)
ALIGNSCORE_THRESHOLD = 0.5


class AlignScoreFactCheckPlugin(GuardrailPlugin):
    """AlignScore 事实核查 —— 外部知识库对齐。

    依赖 AlignScore 服务（需单独部署）。
    不可用时降级到 self_check_facts（LLM 自检）。
    """

    plugin_id = "DG-OT-FACT-002"
    plugin_name = "事实核查（AlignScore）"
    stage = "output"
    maturity = "beta"

    def __init__(self, endpoint: str = "", fallback_plugin: GuardrailPlugin | None = None):
        self._endpoint = endpoint
        self._fallback = fallback_plugin

    async def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        ctx = context or {}
        evidence = ctx.get("relevant_chunks", [])
        response = ctx.get("bot_message", content)

        if not self._endpoint:
            return await self._fallback_check(content, context, "no_endpoint")

        if isinstance(evidence, str):
            evidence = [evidence]

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self._endpoint,
                    json={"evidence": evidence, "response": response},
                )
                if resp.status_code == 200:
                    score = resp.json().get("score", 0.0)
                    is_consistent = score >= ALIGNSCORE_THRESHOLD
                    return GuardrailResult(
                        is_safe=is_consistent,
                        reason=f"align_score={score:.3f}",
                        confidence=score,
                    )
        except Exception as e:
            log.warning("AlignScore 调用失败: %s，降级", e)

        return await self._fallback_check(content, context, "alignscore_error")

    async def _fallback_check(self, content: str, context: dict | None, reason: str) -> GuardrailResult:
        if self._fallback:
            result = await self._fallback.check(content, context)
            return GuardrailResult(
                is_safe=result.is_safe,
                reason=f"{reason}→{result.reason}",
                confidence=result.confidence * 0.8,
            )
        return GuardrailResult(is_safe=True, reason=f"{reason}→默认放行", confidence=0.0)
