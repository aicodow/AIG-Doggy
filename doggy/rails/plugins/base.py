"""护栏插件基类 —— 所有自定义护栏必须实现此接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class GuardrailResult:
    """护栏检测结果。"""

    is_safe: bool
    reason: str | None = None
    confidence: float = 0.0
    sanitized_content: str | None = None
    metadata: dict[str, Any] | None = None


class GuardrailPlugin(ABC):
    """护栏插件抽象基类。

    子类必须定义以下类属性：
      - plugin_id: 唯一标识，格式 DG-{阶段}-{分类}-{序号}
      - plugin_name: 显示名称
      - stage: 检测阶段 (input/output/retrieval/dialog/execution)
      - maturity: 成熟度 (experimental/beta/production/benchmark)
    """

    plugin_id: str
    plugin_name: str
    stage: str
    maturity: str = "experimental"

    @abstractmethod
    async def check(self, content: str, context: dict[str, Any] | None = None) -> GuardrailResult:
        """执行安全检测。

        Args:
            content: 待检测的文本内容。
            context: 可选的上下文信息。

        Returns:
            GuardrailResult 包含检测结果、原因和置信度。
        """
        ...

    def get_metadata(self) -> dict[str, str]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "stage": self.stage,
            "maturity": self.maturity,
        }