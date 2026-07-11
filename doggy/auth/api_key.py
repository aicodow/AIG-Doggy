"""API Key 生成、哈希与验证。"""

import hashlib
import secrets
from dataclasses import dataclass, field


@dataclass(slots=True)
class AppContext:
    """API Key 关联的应用上下文 —— 认证时从数据库加载并注入请求。"""

    app_id: str
    app_name: str
    policy_name: str
    rate_limit_qps: int = 50
    allowed_models: list[str] = field(default_factory=lambda: ["*"])


def generate_api_key(prefix: str = "doggy") -> tuple[str, str]:
    """生成 API Key 及其哈希值。

    Returns:
        (原始 Key, SHA-256 哈希值)。原始 Key 仅展示一次，哈希值存入数据库。
    """
    random_part = secrets.token_hex(32)
    raw_key = f"{prefix}-{random_part}"
    hashed_key = _hash(raw_key)
    return raw_key, hashed_key


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """验证 API Key 是否匹配存储的哈希值。"""
    return _hash(raw_key) == stored_hash


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
