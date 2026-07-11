"""安全有效性测试 —— 验证各护栏的检出率和误报率。"""

import json
import pytest
from pathlib import Path

from doggy.rails.input.pii_detection import PIIDetectionPlugin
from doggy.rails.input.injection import InjectionDetectionPlugin
from doggy.rails.plugins.regex_detection import RegexDetectionPlugin

FIXTURES = Path(__file__).parent / "fixtures"


def load_json(name: str) -> list[dict]:
    with open(FIXTURES / name, "r", encoding="utf-8") as f:
        return json.load(f)


class TestPIIDetectionEffectiveness:
    """PII 检测护栏有效性测试。"""

    @pytest.fixture
    def plugin(self):
        return PIIDetectionPlugin()

    @pytest.mark.parametrize("sample", load_json("attack_samples.json"))
    async def test_detect_pii_attacks(self, plugin, sample):
        if sample["rail"] != "pii_detection":
            pytest.skip()
        result = await plugin.check(sample["text"])
        if sample["expected"] == "BLOCKED":
            assert result.is_safe is False, f"漏报: {sample['id']} - {sample['text'][:50]}"
        elif sample["expected"] == "MASKED":
            if result.is_safe is True and result.sanitized_content:
                assert "[已脱敏]" in result.sanitized_content

    @pytest.mark.parametrize("sample", load_json("normal_samples.json"))
    async def test_pass_normal_content(self, plugin, sample):
        result = await plugin.check(sample["text"])
        assert result.is_safe is True, f"误报: {sample['id']} - {sample['text'][:50]}"


class TestInjectionDetectionEffectiveness:
    """注入检测护栏有效性测试。"""

    @pytest.fixture
    def plugin(self):
        return InjectionDetectionPlugin()

    @pytest.mark.parametrize("sample", load_json("attack_samples.json"))
    async def test_detect_injection_attacks(self, plugin, sample):
        if sample["rail"] != "injection_detection":
            pytest.skip()
        result = await plugin.check(sample["text"])
        assert result.is_safe is False, f"漏报: {sample['id']} - {sample['text'][:50]}"

    @pytest.mark.parametrize("sample", load_json("normal_samples.json"))
    async def test_pass_normal_content(self, plugin, sample):
        result = await plugin.check(sample["text"])
        assert result.is_safe is True, f"误报: {sample['id']} - {sample['text'][:50]}"