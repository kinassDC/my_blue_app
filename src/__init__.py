"""
My Blue App - 蓝牙设备管理工具

一个功能完善的蓝牙设备管理工具，支持设备扫描、连接、管理和数据交互。
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from src.core.bluetooth_manager import BluetoothManager
from src.models.device import BluetoothDevice

__all__ = ["BluetoothManager", "BluetoothDevice"]