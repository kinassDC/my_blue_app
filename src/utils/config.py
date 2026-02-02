"""
配置管理模块

提供应用程序的配置加载、保存和管理功能。
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from src.utils.logger import Logger


class Config:
    """
    配置管理类

    支持从YAML或JSON文件加载配置，并提供运行时配置修改和保存功能。
    """

    def __init__(self, config_path: Optional[str] = None, auto_save: bool = True):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
            auto_save: 是否自动保存配置更改
        """
        self.logger = Logger.get_logger(__name__)
        self._config_path = config_path
        self._auto_save = auto_save
        self._config: Dict[str, Any] = {}

        # 默认配置
        self._defaults = self._get_defaults()

        # 加载配置
        if config_path:
            self.load(config_path)
        else:
            self._config = self._defaults.copy()

    # ==================== 配置加载 ====================

    def load(self, config_path: str) -> bool:
        """
        从文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            加载是否成功
        """
        self._config_path = config_path
        path = Path(config_path)

        if not path.exists():
            self.logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            self._config = self._defaults.copy()
            return False

        try:
            if path.suffix in [".yaml", ".yml"]:
                self._load_yaml(path)
            elif path.suffix == ".json":
                self._load_json(path)
            else:
                self.logger.error(f"不支持的配置文件格式: {path.suffix}")
                return False

            self.logger.info(f"配置加载成功: {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            self._config = self._defaults.copy()
            return False

    def _load_yaml(self, path: Path) -> None:
        """加载YAML配置文件"""
        with open(path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

    def _load_json(self, path: Path) -> None:
        """加载JSON配置文件"""
        with open(path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    # ==================== 配置保存 ====================

    def save(self, config_path: Optional[str] = None) -> bool:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径，默认使用初始化时的路径

        Returns:
            保存是否成功
        """
        save_path = config_path or self._config_path

        if not save_path:
            self.logger.error("未指定配置文件保存路径")
            return False

        try:
            path = Path(save_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            if path.suffix in [".yaml", ".yml"]:
                self._save_yaml(path)
            elif path.suffix == ".json":
                self._save_json(path)
            else:
                self.logger.error(f"不支持的配置文件格式: {path.suffix}")
                return False

            self.logger.info(f"配置保存成功: {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False

    def _save_yaml(self, path: Path) -> None:
        """保存为YAML格式"""
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._config, f, allow_unicode=True, sort_keys=False)

    def _save_json(self, path: Path) -> None:
        """保存为JSON格式"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    # ==================== 配置访问 ====================

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）

        Args:
            key: 配置键，如 "scanner.timeout" 或 "server.host"
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any, auto_save: Optional[bool] = None) -> None:
        """
        设置配置值（支持点号分隔的嵌套键）

        Args:
            key: 配置键
            value: 配置值
            auto_save: 是否自动保存，默认使用初始化时的设置
        """
        keys = key.split(".")
        config = self._config

        # 创建嵌套字典结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

        # 自动保存
        if auto_save or (auto_save is None and self._auto_save):
            self.save()

    def update(self, config: Dict[str, Any], auto_save: Optional[bool] = None) -> None:
        """
        批量更新配置

        Args:
            config: 配置字典
            auto_save: 是否自动保存
        """
        def deep_update(base: dict, updates: dict) -> dict:
            """深度更新字典"""
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    base[key] = deep_update(base[key], value)
                else:
                    base[key] = value
            return base

        self._config = deep_update(self._config, config)

        if auto_save or (auto_save is None and self._auto_save):
            self.save()

    def delete(self, key: str) -> bool:
        """
        删除配置项

        Args:
            key: 配置键

        Returns:
            删除是否成功
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return False

        if keys[-1] in config:
            del config[keys[-1]]
            if self._auto_save:
                self.save()
            return True

        return False

    # ==================== 配置检查 ====================

    def has(self, key: str) -> bool:
        """
        检查配置项是否存在

        Args:
            key: 配置键

        Returns:
            是否存在
        """
        return self.get(key) is not None

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    # ==================== 默认配置 ====================

    def _get_defaults(self) -> Dict[str, Any]:
        """
        获取默认配置

        Returns:
            默认配置字典
        """
        return {
            "app": {
                "name": "My Blue App",
                "version": "0.1.0",
                "debug": False
            },
            "scanner": {
                "timeout": 10,
                "device_type": "all",
                "adapter_name": None
            },
            "connector": {
                "timeout": 10,
                "retry_count": 3,
                "retry_delay": 1,
                "auto_reconnect": False
            },
            "data_handler": {
                "buffer_size": 4096,
                "timeout": 5.0,
                "encoding": "utf-8"
            },
            "ui": {
                "theme": "default",
                "language": "zh_CN",
                "window_size": [1024, 768]
            },
            "logging": {
                "level": "INFO",
                "console_level": "INFO",
                "file_level": "DEBUG",
                "log_dir": "logs"
            }
        }

    # ==================== 环境变量支持 ====================

    @classmethod
    def from_env(cls, prefix: str = "APP_") -> "Config":
        """
        从环境变量加载配置

        Args:
            prefix: 环境变量前缀

        Returns:
            配置实例
        """
        config = cls()
        env_config = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 转换环境变量键为配置键
                # 例如: APP_SCANNER_TIMEOUT -> scanner.timeout
                config_key = key[len(prefix):].lower().replace("__", ".")
                env_config[config_key] = value

        if env_config:
            config.update(env_config)

        return config

    # ==================== 字典接口 ====================

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """支持字典式赋值"""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.has(key)

    def __repr__(self) -> str:
        return f"Config(path={self._config_path})"