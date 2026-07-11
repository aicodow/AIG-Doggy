"""集成测试 —— 验证核心模块的协作。"""

from unittest.mock import AsyncMock, MagicMock


class TestNeMoAdapterIntegration:
    """NeMoAdapter 集成测试（使用 Mock NeMo 实例）。"""

    async def test_generate_with_mock_engine(self):
        from nemoguardrails import RailsConfig

        from doggy.engine.nemo_adapter import NeMoAdapter

        config = RailsConfig.from_content(
            yaml_content="""
            colang_version: "2.x"
            models: []
            rails:
              input:
                flows: []
              output:
                flows: []
            """
        )

        adapter = NeMoAdapter(config=config)
        adapter._engine = MagicMock()
        adapter._engine.generate_async = AsyncMock(return_value="mock response")
        adapter._engine.startup = AsyncMock()
        adapter._engine.shutdown = AsyncMock()

        await adapter.startup()
        result = await adapter.generate_async(
            messages=[{"role": "user", "content": "Hello"}],
            protocol="openai",
        )
        await adapter.shutdown()

        assert isinstance(result, dict)
        assert "choices" in result


class TestAuthFlow:
    """认证流程集成测试。"""

    async def test_api_key_generation_and_verification(self):
        from doggy.auth.api_key import generate_api_key, verify_api_key

        raw, hashed = generate_api_key()
        assert verify_api_key(raw, hashed) is True
        assert verify_api_key("wrong-key", hashed) is False


class TestPluginRegistry:
    """插件注册中心集成测试。"""

    def test_register_and_list_plugins(self):
        from doggy.rails.plugins import list_all, register
        from doggy.rails.plugins.base import GuardrailPlugin, GuardrailResult

        @register
        class TestPlugin(GuardrailPlugin):
            plugin_id = "DG-TEST-001"
            plugin_name = "Test Plugin"
            stage = "input"
            maturity = "experimental"

            async def check(self, content, context=None):
                return GuardrailResult(is_safe=True, confidence=1.0)

        plugins = list_all(stage="input")
        assert any(p["plugin_id"] == "DG-TEST-001" for p in plugins)
