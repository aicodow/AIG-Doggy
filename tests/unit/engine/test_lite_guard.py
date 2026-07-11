from unittest.mock import AsyncMock, MagicMock

import pytest

from doggy.engine.lite_guard import TASK_MAP, LiteGuardPlugin, _parse_response


class TestParseResponse:
    def test_content_safety_safe(self):
        r = _parse_response("SAFE", "content_safety")
        assert r.is_safe is True

    def test_content_safety_unsafe(self):
        r = _parse_response("UNSAFE\nviolence", "content_safety")
        assert r.is_safe is False

    def test_jailbreak_detected(self):
        r = _parse_response("JAILBREAK", "jailbreak")
        assert r.is_safe is False

    def test_hallucination_detected(self):
        r = _parse_response("HALLUCINATION\nfact error", "hallucination")
        assert r.is_safe is False

    def test_case_insensitive(self):
        r = _parse_response("  Unsafe  ", "content_safety")
        assert r.is_safe is False


class TestLiteGuardPlugin:
    @pytest.mark.asyncio
    async def test_no_llm_returns_safe(self):
        plugin = LiteGuardPlugin(lite_llm=None)
        result = await plugin.check("test")
        assert result.is_safe is True
        assert result.reason == "lite_guard_unavailable"

    @pytest.mark.asyncio
    async def test_llm_error_returns_unsafe(self):
        mock_llm = AsyncMock()
        mock_llm.generate_async.side_effect = Exception("timeout")
        plugin = LiteGuardPlugin(lite_llm=mock_llm)
        result = await plugin.check("test")
        assert result.is_safe is False
        assert "lite_guard_error" in result.reason

    @pytest.mark.asyncio
    async def test_with_task_manager(self):
        mock_llm = AsyncMock()
        mock_llm.generate_async.return_value = "SAFE"
        mock_tm = MagicMock()
        mock_tm.render_task_prompt.return_value = "Rendered prompt"

        plugin = LiteGuardPlugin(lite_llm=mock_llm, llm_task_manager=mock_tm)
        result = await plugin.check("hello", {"check_type": "content_safety"})

        mock_tm.render_task_prompt.assert_called_once_with(
            task="lite_guard_content_safety",
            context={"user_message": "hello", "bot_message": ""},
        )
        assert result.is_safe is True

    def test_task_map_complete(self):
        """确保所有 check_type 都有对应的 task 映射。"""
        assert "content_safety" in TASK_MAP
        assert "jailbreak" in TASK_MAP
        assert "hallucination" in TASK_MAP
