"""
日志工具模块

提供统一的日志记录功能。
"""

import logging
import sys
from typing import Optional
from pathlib import Path
from datetime import datetime


class Logger:
    """
    日志工具类

    提供统一的日志记录接口，支持控制台和文件输出。
    """

    _loggers: dict = {}
    _log_dir: Optional[Path] = None
    _log_level: int = logging.INFO
    _console_level: int = logging.INFO
    _file_level: int = logging.DEBUG

    @classmethod
    def configure(cls,
                  log_dir: Optional[str] = None,
                  log_level: str = "INFO",
                  console_level: str = "INFO",
                  file_level: str = "DEBUG",
                  format_string: Optional[str] = None) -> None:
        """
        配置全局日志设置

        Args:
            log_dir: 日志文件目录
            log_level: 默认日志级别
            console_level: 控制台日志级别
            file_level: 文件日志级别
            format_string: 日志格式字符串
        """
        cls._log_level = cls._parse_level(log_level)
        cls._console_level = cls._parse_level(console_level)
        cls._file_level = cls._parse_level(file_level)

        if log_dir:
            cls._log_dir = Path(log_dir)
            cls._log_dir.mkdir(parents=True, exist_ok=True)

        # 设置默认格式
        if format_string is None:
            format_string = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"

        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(cls._log_level)

        # 清除现有处理器
        root_logger.handlers.clear()

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(cls._console_level)
        console_formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # 文件处理器
        if cls._log_dir:
            log_file = cls._log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(cls._file_level)
            file_formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器

        Args:
            name: 日志记录器名称，通常使用 __name__

        Returns:
            日志记录器实例
        """
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(cls._log_level)
            cls._loggers[name] = logger
        return cls._loggers[name]

    @classmethod
    def _parse_level(cls, level: str) -> int:
        """解析日志级别字符串"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(level.upper(), logging.INFO)

    @classmethod
    def set_level(cls, level: str) -> None:
        """
        设置全局日志级别

        Args:
            level: 日志级别字符串
        """
        cls._log_level = cls._parse_level(level)
        for logger in cls._loggers.values():
            logger.setLevel(cls._log_level)


# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return Logger.get_logger(name)


def setup_logging(log_dir: Optional[str] = None,
                  level: str = "INFO",
                  console_level: str = "INFO",
                  file_level: str = "DEBUG") -> None:
    """
    设置日志的便捷函数

    Args:
        log_dir: 日志文件目录
        level: 默认日志级别
        console_level: 控制台日志级别
        file_level: 文件日志级别
    """
    Logger.configure(log_dir, level, console_level, file_level)


class LogContext:
    """
    日志上下文管理器

    用于临时修改日志级别或在特定操作前后添加日志。
    """

    def __init__(self, logger: logging.Logger, level: int, message: str):
        """
        初始化日志上下文

        Args:
            logger: 日志记录器
            level: 日志级别
            message: 日志消息
        """
        self.logger = logger
        self.level = level
        self.message = message

    def __enter__(self):
        self.logger.log(self.level, f"{self.message} - 开始")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.log(self.level, f"{self.message} - 完成")
        else:
            self.logger.error(f"{self.message} - 失败: {exc_val}")


def log_context(logger: logging.Logger, level: str = "INFO", message: str = ""):
    """
    创建日志上下文的便捷函数

    Args:
        logger: 日志记录器
        level: 日志级别
        message: 日志消息

    Returns:
        日志上下文管理器
    """
    level_int = Logger._parse_level(level)
    return LogContext(logger, level_int, message)