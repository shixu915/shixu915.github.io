"""统一日志服务 - 供所有模块使用"""

import logging
import re
import os
from datetime import datetime
from pathlib import Path


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    创建并配置 logger 实例

    Args:
        name: 模块名称，通常使用 __name__
        level: 日志级别

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"fund_predictor_{datetime.now().strftime('%Y%m%d')}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def desensitize(message: str) -> str:
    """
    脱敏处理 - 隐藏日志中的敏感信息（API密钥、token等）

    Args:
        message: 原始日志消息

    Returns:
        脱敏后的消息
    """
    # 隐藏 API key / token / secret 类参数
    message = re.sub(r'(api[_-]?key|token|secret|password)\s*[=:]\s*\S+',
                     r'\1=***', message, flags=re.IGNORECASE)
    return message


class DesensitizingLogger:
    """带脱敏功能的日志包装器"""

    def __init__(self, name: str, level: int = logging.INFO):
        self._logger = setup_logger(name, level)

    def _log(self, level, msg, *args, **kwargs):
        msg = desensitize(str(msg))
        self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)
