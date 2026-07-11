"""幻觉检测、事实核查、HF 分类器 —— 单元测试。"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from doggy.rails.output.hallucination import HallucinationDetectionPlugin, SelfCheckFactsPlugin
from doggy.rails.output.factchecking import AlignScoreFactCheckPlugin
from doggy.rails.output.hf_classifier import HFClassifierInputPlugin, HFClassifierOutputPlugin


class TestHallucinationPlugin:
    async def test_no_llm_returns_safe(self):
        plugin = HallucinationDetectionPlugin()
        result = await plugin.check("test")
        assert result.is_safe is True

    async def test_no_context_returns_safe(self):
        mock_llm = AsyncMock()
        mock_tm = MagicMock()
        plugin = HallucinationDetectionPlugin(llm=mock_llm, llm_task_manager=mock_tm)
        result = await plugin.check("test", {})
        assert result.is_safe is True

    async def test_consistent_response(self):
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(side_effect=[
            MagicMock(content="extra response 1"),
            MagicMock(content="extra response 2"),
            MagicMock(content="yes, the statement is consistent"),
        ])
        mock_tm = MagicMock()
        mock_tm.render_task_prompt.return_value = "check prompt"

        plugin = HallucinationDetectionPlugin(llm=mock_llm, llm_task_manager=mock_tm)
        result = await plugin.check(
            "original response",
            {"bot_message": "original response", "_last_bot_prompt": "user prompt"},
        )
        assert result.is_safe is True
        assert mock_llm.generate_async.call_count == 3

    async def test_hallucination_detected(self):
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(side_effect=[
            MagicMock(content="extra 1"),
            MagicMock(content="extra 2"),
            MagicMock(content="no, the statement contradicts"),
        ])
        mock_tm = MagicMock()
        mock_tm.render_task_prompt.return_value = "check prompt"

        plugin = HallucinationDetectionPlugin(llm=mock_llm, llm_task_manager=mock_tm)
        result = await plugin.check(
            "original",
            {"bot_message": "original", "_last_bot_prompt": "prompt"},
        )
        assert result.is_safe is False


class TestSelfCheckFactsPlugin:
    async def test_no_llm_returns_safe(self):
        plugin = SelfCheckFactsPlugin()
        result = await plugin.check("test")
        assert result.is_safe is True

    async def test_facts_consistent(self):
        mock_llm = AsyncMock()
        mock_llm.generate_async.return_value = MagicMock(content="yes, consistent")
        mock_tm = MagicMock()
        mock_tm.render_task_prompt.return_value = "check prompt"

        plugin = SelfCheckFactsPlugin(llm=mock_llm, llm_task_manager=mock_tm)
        result = await plugin.check("response", {"bot_message": "response", "relevant_chunks": "evidence"})
        assert result.is_safe is True


class TestAlignScorePlugin:
    async def test_no_endpoint_falls_back(self):
        plugin = AlignScoreFactCheckPlugin(endpoint="")
        result = await plugin.check("test", {"bot_message": "test"})
        assert result.is_safe is True
        assert "no_endpoint" in result.reason


class TestHFClassifierPlugin:
    async def test_unknown_classifier_returns_safe(self):
        plugin = HFClassifierInputPlugin()
        result = await plugin.classify("nonexistent", "test")
        assert result.is_safe is True

    async def test_empty_text_returns_safe(self):
        plugin = HFClassifierInputPlugin({"toxicity": {"engine": "local", "model": "test"}})
        result = await plugin.classify("toxicity", "")
        assert result.is_safe is True