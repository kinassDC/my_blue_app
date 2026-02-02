"""
蓝牙管理器主类

提供蓝牙设备管理的统一接口，整合扫描、连接、数据传输等功能。
"""

import asyncio
from typing import List, Optional, Callable, Dict, Any
from src.models.device import BluetoothDevice
from src.core.device_scanner import DeviceScanner
from src.core.connector import Connector
from src.core.data_handler import DataHandler
from src.utils.logger import Logger


class BluetoothManager:
    """
    蓝牙设备管理器主类

    整合设备扫描、连接管理、数据传输等核心功能。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化蓝牙管理器

        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self.logger = Logger.get_logger(__name__)

        # 初始化子模块
        self.scanner = DeviceScanner(self.config.get("scanner", {}))
        self.connector = Connector(self.config.get("connector", {}))
        self.data_handler = DataHandler(self.config.get("data_handler", {}))

        # 已连接设备集合
        self._connected_devices: Dict[str, BluetoothDevice] = {}

        # 事件回调
        self._on_device_discovered: Optional[Callable[[BluetoothDevice], None]] = None
        self._on_device_connected: Optional[Callable[[BluetoothDevice], None]] = None
        self._on_device_disconnected: Optional[Callable[[str], None]] = None
        self._on_data_received: Optional[Callable[[str, bytes], None]] = None

    # ==================== 设备扫描 ====================

    def scan_devices(self, timeout: int = 10) -> List[BluetoothDevice]:
        """
        扫描附近的蓝牙设备

        Args:
            timeout: 扫描超时时间（秒）

        Returns:
            发现的设备列表
        """
        self.logger.info(f"开始扫描蓝牙设备，超时时间: {timeout}秒")
        devices = self.scanner.scan(timeout)

        # 触发设备发现回调
        if self._on_device_discovered:
            for device in devices:
                self._on_device_discovered(device)

        self.logger.info(f"扫描完成，发现 {len(devices)} 个设备")
        return devices

    async def scan_devices_async(self, timeout: int = 10) -> List[BluetoothDevice]:
        """
        异步扫描附近的蓝牙设备

        Args:
            timeout: 扫描超时时间（秒）

        Returns:
            发现的设备列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scan_devices, timeout)

    # ==================== 设备连接管理 ====================

    def connect_device(self, device_mac: str) -> bool:
        """
        连接指定蓝牙设备

        Args:
            device_mac: 设备MAC地址

        Returns:
            连接是否成功
        """
        self.logger.info(f"正在连接设备: {device_mac}")
        success = self.connector.connect(device_mac)

        if success:
            self.logger.info(f"设备连接成功: {device_mac}")
            if self._on_device_connected:
                device = self._get_device_info(device_mac)
                if device:
                    self._on_device_connected(device)
        else:
            self.logger.error(f"设备连接失败: {device_mac}")

        return success

    async def connect_device_async(self, device_mac: str) -> bool:
        """
        异步连接指定蓝牙设备

        Args:
            device_mac: 设备MAC地址

        Returns:
            连接是否成功
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.connect_device, device_mac)

    def disconnect_device(self, device_mac: str) -> bool:
        """
        断开设备连接

        Args:
            device_mac: 设备MAC地址

        Returns:
            断开是否成功
        """
        self.logger.info(f"正在断开设备: {device_mac}")
        success = self.connector.disconnect(device_mac)

        if success:
            self.logger.info(f"设备已断开: {device_mac}")
            if device_mac in self._connected_devices:
                del self._connected_devices[device_mac]
            if self._on_device_disconnected:
                self._on_device_disconnected(device_mac)
        else:
            self.logger.error(f"断开设备失败: {device_mac}")

        return success

    def is_connected(self, device_mac: str) -> bool:
        """
        检查设备是否已连接

        Args:
            device_mac: 设备MAC地址

        Returns:
            是否已连接
        """
        return self.connector.is_connected(device_mac)

    def get_connected_devices(self) -> List[BluetoothDevice]:
        """
        获取所有已连接的设备

        Returns:
            已连接设备列表
        """
        return list(self._connected_devices.values())

    # ==================== 数据传输 ====================

    def send_data(self, device_mac: str, data: bytes) -> bool:
        """
        向设备发送数据

        Args:
            device_mac: 设备MAC地址
            data: 要发送的数据

        Returns:
            发送是否成功
        """
        if not self.is_connected(device_mac):
            self.logger.error(f"设备未连接，无法发送数据: {device_mac}")
            return False

        self.logger.debug(f"发送数据到 {device_mac}: {len(data)} 字节")
        return self.data_handler.send(device_mac, data)

    async def send_data_async(self, device_mac: str, data: bytes) -> bool:
        """
        异步向设备发送数据

        Args:
            device_mac: 设备MAC地址
            data: 要发送的数据

        Returns:
            发送是否成功
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_data, device_mac, data)

    def receive_data(self, device_mac: str, size: int = 1024, timeout: float = 5.0) -> Optional[bytes]:
        """
        从设备接收数据

        Args:
            device_mac: 设备MAC地址
            size: 接收数据大小
            timeout: 超时时间（秒）

        Returns:
            接收到的数据，超时或失败返回None
        """
        if not self.is_connected(device_mac):
            self.logger.error(f"设备未连接，无法接收数据: {device_mac}")
            return None

        data = self.data_handler.receive(device_mac, size, timeout)
        if data and self._on_data_received:
            self._on_data_received(device_mac, data)

        return data

    async def receive_data_async(self, device_mac: str, size: int = 1024, timeout: float = 5.0) -> Optional[bytes]:
        """
        异步从设备接收数据

        Args:
            device_mac: 设备MAC地址
            size: 接收数据大小
            timeout: 超时时间（秒）

        Returns:
            接收到的数据，超时或失败返回None
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.receive_data, device_mac, size, timeout)

    # ==================== 事件回调 ====================

    def on_device_discovered(self, callback: Callable[[BluetoothDevice], None]) -> None:
        """设置设备发现回调"""
        self._on_device_discovered = callback

    def on_device_connected(self, callback: Callable[[BluetoothDevice], None]) -> None:
        """设置设备连接回调"""
        self._on_device_connected = callback

    def on_device_disconnected(self, callback: Callable[[str], None]) -> None:
        """设置设备断开回调"""
        self._on_device_disconnected = callback

    def on_data_received(self, callback: Callable[[str, bytes], None]) -> None:
        """设置数据接收回调"""
        self._on_data_received = callback

    # ==================== 辅助方法 ====================

    def _get_device_info(self, device_mac: str) -> Optional[BluetoothDevice]:
        """获取设备信息"""
        return self._connected_devices.get(device_mac)

    def get_adapter_info(self) -> Dict[str, Any]:
        """
        获取蓝牙适配器信息

        Returns:
            适配器信息字典
        """
        return self.scanner.get_adapter_info()

    def cleanup(self) -> None:
        """清理资源"""
        self.logger.info("清理蓝牙管理器资源")
        for device_mac in list(self._connected_devices.keys()):
            self.disconnect_device(device_mac)

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.cleanup()