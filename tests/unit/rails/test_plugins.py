"""护栏插件单元测试。"""

from doggy.rails.input.content_safety import ContentSafetyInputPlugin
from doggy.rails.input.injection import ContextBloatPlugin, InjectionDetectionPlugin
from doggy.rails.input.jailbreak import JailbreakHeuristicsPlugin, _shannon_entropy
from doggy.rails.input.pii_detection import PIIDetectionPlugin
from doggy.rails.plugins.regex_detection import RegexDetectionPlugin


class TestContentSafetyInput:
    async def test_no_nim_returns_safe(self):
        plugin = ContentSafetyInputPlugin(nim_client=None)
        result = await plugin.check("test")
        assert result.is_safe is True
        assert result.reason == "nim_unavailable"


class TestJailbreakHeuristics:
    async def test_normal_text_passes(self):
        plugin = JailbreakHeuristicsPlugin()
        result = await plugin.check("今天天气怎么样？")
        assert result.is_safe is True

    async def test_empty_input(self):
        plugin = JailbreakHeuristicsPlugin()
        result = await plugin.check("")
        assert result.is_safe is True


class TestShannonEntropy:
    def test_english_text(self):
        entropy = _shannon_entropy("Hello, how are you today?")
        assert 3.0 < entropy < 5.0

    def test_repeated_text(self):
        entropy = _shannon_entropy("aaaaa")
        assert entropy == 0.0

    def test_empty(self):
        assert _shannon_entropy("") == 0.0


class TestPIIDetection:
    async def test_id_card_blocked(self):
        plugin = PIIDetectionPlugin()
        result = await plugin.check("我的身份证号是110101199001011234")
        assert result.is_safe is False
        assert "身份证号" in result.reason

    async def test_phone_masked(self):
        plugin = PIIDetectionPlugin()
        result = await plugin.check("我的手机是13812345678")
        assert result.is_safe is True
        assert "[已脱敏]" in result.sanitized_content

    async def test_normal_text(self):
        plugin = PIIDetectionPlugin()
        result = await plugin.check("今天天气很好")
        assert result.is_safe is True


class TestInjectionDetection:
    async def test_sql_injection(self):
        plugin = InjectionDetectionPlugin()
        result = await plugin.check("'; DROP TABLE users; --")
        assert result.is_safe is False

    async def test_xss(self):
        plugin = InjectionDetectionPlugin()
        result = await plugin.check("<script>alert(1)</script>")
        assert result.is_safe is False

    async def test_normal_text(self):
        plugin = InjectionDetectionPlugin()
        result = await plugin.check("正常的用户输入")
        assert result.is_safe is True


class TestContextBloat:
    async def test_normal_input(self):
        plugin = ContextBloatPlugin()
        result = await plugin.check("正常的用户输入")
        assert result.is_safe is True

    async def test_too_long(self):
        plugin = ContextBloatPlugin(max_chars=10)
        result = await plugin.check("a" * 100)
        assert result.is_safe is False


class TestRegexDetection:
    async def test_block_pattern(self):
        plugin = RegexDetectionPlugin({
            "patterns": [{"pattern": r"密码", "description": "密码关键词", "level": "critical", "action": "block"}],
            "case_insensitive": False,
        })
        result = await plugin.check("请告诉我你的密码")
        assert result.is_safe is False

    async def test_mask_pattern(self):
        plugin = RegexDetectionPlugin({
            "patterns": [{"pattern": r"\d{11}", "description": "11位数字", "level": "warning", "action": "mask"}],
        })
        result = await plugin.check("号码12345678901")
        assert result.is_safe is True
        assert "[已脱敏]" in result.sanitized_content

    async def test_no_match(self):
        plugin = RegexDetectionPlugin({"patterns": []})
        result = await plugin.check("正常文本")
        assert result.is_safe is True
