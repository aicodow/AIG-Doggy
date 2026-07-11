import pytest

from doggy.adapters.protocol import AnthropicAdapter, OpenAIAdapter, get_adapter
from doggy.exceptions import ProtocolNotSupportedError


class TestOpenAIAdapter:
    @pytest.fixture
    def adapter(self):
        return OpenAIAdapter()

    def test_user_message(self, adapter):
        result = adapter.to_internal([{"role": "user", "content": "Hello"}])
        assert result == [{"role": "user", "content": "Hello"}]

    def test_system_to_context(self, adapter):
        result = adapter.to_internal([{"role": "system", "content": "You are helpful"}])
        assert result[0]["role"] == "context"
        assert result[0]["content"]["system_prompt"] == "You are helpful"

    def test_assistant_with_tool_calls(self, adapter):
        result = adapter.to_internal([{
            "role": "assistant", "content": None,
            "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "f", "arguments": "{}"}}]
        }])
        assert len(result[0]["tool_calls"]) == 1

    def test_tool_message(self, adapter):
        result = adapter.to_internal([{
            "role": "tool", "content": "result", "tool_call_id": "c1", "name": "f"
        }])
        assert result[0]["tool_call_id"] == "c1"

    def test_empty_messages(self, adapter):
        assert adapter.to_internal([]) == []

    def test_to_external_dict(self, adapter):
        resp = adapter.to_external({"role": "assistant", "content": "Hi"})
        assert resp["choices"][0]["message"]["content"] == "Hi"


class TestAnthropicAdapter:
    @pytest.fixture
    def adapter(self):
        return AnthropicAdapter()

    def test_content_array(self, adapter):
        result = adapter.to_internal([{
            "role": "user", "content": [{"type": "text", "text": "A"}, {"type": "text", "text": "B"}]
        }])
        assert result[0]["content"] == "A\nB"

    def test_to_external(self, adapter):
        resp = adapter.to_external({"role": "assistant", "content": "Hi"})
        assert resp["type"] == "message"
        assert resp["content"][0]["text"] == "Hi"


class TestGetAdapter:
    def test_openai(self):
        assert isinstance(get_adapter("openai"), OpenAIAdapter)

    def test_anthropic(self):
        assert isinstance(get_adapter("anthropic"), AnthropicAdapter)

    def test_unsupported(self):
        with pytest.raises(ProtocolNotSupportedError):
            get_adapter("unknown")
