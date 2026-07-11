"""pytest 配置 —— 共享 fixtures 和全局设置。"""

import sys
from pathlib import Path

import pytest

# 将 src 目录加入 Python 路径
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_messages():
    """标准测试消息 fixture。"""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
    ]


@pytest.fixture
def sample_app_context():
    """标准测试 AppContext fixture。"""
    from doggy.auth.api_key import AppContext
    return AppContext(
        app_id="test-app",
        app_name="Test Application",
        policy_name="default",
        rate_limit_qps=50,
        allowed_models=["*"],
    )
