"""护栏插件注册中心。"""

from doggy.rails.plugins.base import GuardrailPlugin

_registry: dict[str, type[GuardrailPlugin]] = {}


def register(plugin_class: type[GuardrailPlugin]) -> type[GuardrailPlugin]:
    """注册护栏插件。"""
    instance = plugin_class()
    _registry[instance.plugin_id] = plugin_class
    return plugin_class


def get(plugin_id: str) -> GuardrailPlugin:
    """获取已注册的护栏插件实例。"""
    if plugin_id not in _registry:
        raise KeyError(f"未注册的护栏插件: {plugin_id}")
    return _registry[plugin_id]()


def list_all(stage: str | None = None) -> list[dict[str, str]]:
    """列出所有已注册的护栏插件。"""
    result = []
    for pid, cls in _registry.items():
        inst = cls()
        if stage is None or inst.stage == stage:
            result.append(inst.get_metadata())
    return result