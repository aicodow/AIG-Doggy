import pytest
from doggy.auth.api_key import generate_api_key, verify_api_key


class TestApiKey:
    def test_generate_format(self):
        raw, hashed = generate_api_key()
        assert raw.startswith("doggy-")
        assert len(raw) == 6 + 64
        assert len(hashed) == 64
        assert hashed != raw

    def test_verify_success(self):
        raw, hashed = generate_api_key()
        assert verify_api_key(raw, hashed) is True

    def test_verify_wrong_key(self):
        _, hashed = generate_api_key()
        assert verify_api_key("doggy-wrong-key", hashed) is False

    def test_verify_wrong_hash(self):
        raw, _ = generate_api_key()
        assert verify_api_key(raw, "invalid-hash") is False

    def test_unique_keys(self):
        keys = {generate_api_key()[0] for _ in range(10)}
        assert len(keys) == 10