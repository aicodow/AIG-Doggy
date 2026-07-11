"""护栏插件自动注册 —— 导入即注册所有内置插件。"""

from doggy.engine.lite_guard import LiteGuardPlugin
from doggy.rails.input.content_safety import ContentSafetyInputPlugin, ContentSafetyOutputPlugin
from doggy.rails.input.injection import (
    ContextBloatPlugin,
    InjectionDetectionPlugin,
    ToolValidationPlugin,
    ToolWhitelistPlugin,
)
from doggy.rails.input.jailbreak import JailbreakHeuristicsPlugin, JailbreakModelPlugin
from doggy.rails.input.pii_detection import PIIDetectionPlugin, PIIOutputPlugin
from doggy.rails.input.topic_control import TopicControlPlugin
from doggy.rails.plugins import register
from doggy.rails.plugins.regex_detection import RegexDetectionPlugin

# 可选插件（按需导入，取消注释即可激活）
# from doggy.rails.output.hallucination import HallucinationDetectionPlugin, SelfCheckFactsPlugin
# from doggy.rails.output.factchecking import AlignScoreFactCheckPlugin
# from doggy.rails.output.hf_classifier import HFClassifierInputPlugin, HFClassifierOutputPlugin

register(ContentSafetyInputPlugin)
register(ContentSafetyOutputPlugin)
register(TopicControlPlugin)
register(JailbreakHeuristicsPlugin)
register(JailbreakModelPlugin)
register(PIIDetectionPlugin)
register(PIIOutputPlugin)
register(InjectionDetectionPlugin)
register(ContextBloatPlugin)
register(ToolValidationPlugin)
register(ToolWhitelistPlugin)
register(RegexDetectionPlugin)
register(LiteGuardPlugin)

# ── 可选插件（按需启用，取消注释即可激活）──
# 这些模块依赖额外服务或成本较高，默认不加载。
# register(HallucinationDetectionPlugin)     # 需要 LLM 3 次额外调用
# register(SelfCheckFactsPlugin)             # 需要 LLM 事实核查
# register(AlignScoreFactCheckPlugin)        # 需要 AlignScore 服务
# register(HFClassifierInputPlugin)          # 需要 HF 模型部署
# register(HFClassifierOutputPlugin)         # 需要 HF 模型部署
