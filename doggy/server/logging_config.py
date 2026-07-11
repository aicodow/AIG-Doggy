"""JSON 结构化日志配置 —— 输出 JSON 格式供 Filebeat 采集。"""

import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """JSON 结构化日志格式化器。

    输出格式:
      {"timestamp": "2026-07-11T14:32:01.234Z", "level": "INFO",
       "logger": "doggy.server", "message": "...", "module": "api", "function": "chat"}
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # 注入请求上下文（由中间件设置）
        if hasattr(record, "app_id"):
            log_entry["app_id"] = record.app_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> None:
    """配置 JSON 结构化日志输出到 stdout。"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
