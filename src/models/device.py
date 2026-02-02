"""
蓝牙设备数据模型

定义蓝牙设备的信息结构和相关操作。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class BluetoothDevice:
    """蓝牙设备信息模型"""

    name: str                          # 设备名称
    mac_address: str                   # MAC地址
    rssi: int                          # 信号强度
    device_class: str                  # 设备类别
    connected: bool = False            # 连接状态
    paired: bool = False               # 配对状态
    device_type: str = "Unknown"       # 设备类型 (BLE/Classic)
    services: List[str] = field(default_factory=list)  # 支持的服务
    last_seen: datetime = field(default_factory=datetime.now)  # 最后发现时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def __post_init__(self):
        """初始化后处理"""
        if self.rssi > 0:
            self.rssi = -self.rssi  # RSSI 通常为负值

    @property
    def signal_strength(self) -> str:
        """获取信号强度描述"""
        if self.rssi >= -50:
            return "优秀"
        elif self.rssi >= -70:
            return "良好"
        elif self.rssi >= -90:
            return "一般"
        else:
            return "较弱"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "mac_address": self.mac_address,
            "rssi": self.rssi,
            "device_class": self.device_class,
            "connected": self.connected,
            "paired": self.paired,
            "device_type": self.device_type,
            "services": self.services,
            "last_seen": self.last_seen.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BluetoothDevice":
        """从字典创建实例"""
        return cls(
            name=data.get("name", "Unknown"),
            mac_address=data.get("mac_address", ""),
            rssi=data.get("rssi", -100),
            device_class=data.get("device_class", "Unknown"),
            connected=data.get("connected", False),
            paired=data.get("paired", False),
            device_type=data.get("device_type", "Unknown"),
            services=data.get("services", []),
            metadata=data.get("metadata", {})
        )

    def __str__(self) -> str:
        """字符串表示"""
        status = "已连接" if self.connected else "未连接"
        return f"{self.name} ({self.mac_address}) - {self.signal_strength} - {status}"

    def __repr__(self) -> str:
        """调试用字符串表示"""
        return f"BluetoothDevice(name={self.name!r}, mac={self.mac_address}, rssi={self.rssi})"