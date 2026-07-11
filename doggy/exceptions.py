"""Doggy 自定义异常层级。"""


class DoggyError(Exception):
    """Doggy 基础异常，所有 Doggy 异常由此派生。"""


class AppNotFoundError(DoggyError):
    """应用不存在。"""


class RailExecutionError(DoggyError):
    """护栏执行失败。"""


class ProtocolNotSupportedError(DoggyError):
    """不支持的协议类型。"""


class ConfigurationError(DoggyError):
    """配置错误。"""


class AuthenticationError(DoggyError):
    """认证失败。"""


class RateLimitError(DoggyError):
    """限流触发。"""


class NIMServiceError(DoggyError):
    """NIM 服务不可用。"""


class LiteGuardError(DoggyError):
    """轻量级 LLM 辅助检测失败。"""