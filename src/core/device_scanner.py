"""
设备扫描模块

负责扫描和发现附近的蓝牙设备。
"""

import asyncio
import platform
from typing import List, Optional, Dict, Any, Callable
from src.models.device import BluetoothDevice
from src.utils.logger import Logger


class DeviceScanner:
    """
    设备扫描器

    负责扫描和发现附近的蓝牙设备。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化设备扫描器

        Args:
            config: 配置参数
                - scan_timeout: 默认扫描超时时间（秒）
                - device_type: 扫描的设备类型 ("all", "ble", "classic")
                - adapter_name: 指定蓝牙适配器名称
        """
        self.config = config or {}
        self.logger = Logger.get_logger(__name__)

        self._scan_timeout = self.config.get("scan_timeout", 10)
        self._device_type = self.config.get("device_type", "all")
        self._adapter_name = self.config.get("adapter_name", None)

        self._scanning = False
        self._scan_callback: Optional[Callable[[BluetoothDevice], None]] = None

    # ==================== 同步扫描 ====================

    def scan(self, timeout: Optional[int] = None) -> List[BluetoothDevice]:
        """
        扫描附近的蓝牙设备

        Args:
            timeout: 扫描超时时间（秒），默认使用配置值

        Returns:
            发现的设备列表
        """
        if self._scanning:
            self.logger.warning("扫描正在进行中，请等待当前扫描完成")
            return []

        timeout = timeout or self._scan_timeout
        self._scanning = True

        try:
            self.logger.info(f"开始扫描设备，超时: {timeout}秒")
            devices = self._do_scan(timeout)
            self.logger.info(f"扫描完成，发现 {len(devices)} 个设备")
            return devices
        finally:
            self._scanning = False

    # ==================== 异步扫描 ====================

    async def scan_async(self, timeout: Optional[int] = None) -> List[BluetoothDevice]:
        """
        异步扫描附近的蓝牙设备

        Args:
            timeout: 扫描超时时间（秒）

        Returns:
            发现的设备列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scan, timeout)

    # ==================== 持续扫描 ====================

    def start_continuous_scan(self, callback: Callable[[BluetoothDevice], None], interval: int = 5) -> None:
        """
        开始持续扫描模式

        Args:
            callback: 发现设备时的回调函数
            interval: 扫描间隔（秒）
        """
        self._scan_callback = callback
        self.logger.info(f"开始持续扫描模式，间隔: {interval}秒")

    def stop_continuous_scan(self) -> None:
        """停止持续扫描"""
        self._scan_callback = None
        self.logger.info("停止持续扫描")

    # ==================== 适配器信息 ====================

    def get_adapter_info(self) -> Dict[str, Any]:
        """
        获取蓝牙适配器信息

        Returns:
            适配器信息字典
                - name: 适配器名称
                - address: 适配器MAC地址
                - powered: 是否已开启
                - discoverable: 是否可发现
                - platform: 操作系统平台
        """
        return {
            "name": self._adapter_name or "Default Adapter",
            "address": self._get_adapter_address(),
            "powered": self._is_adapter_powered(),
            "discoverable": self._is_adapter_discoverable(),
            "platform": platform.system()
        }

    # ==================== 内部实现方法 ====================

    def _do_scan(self, timeout: int) -> List[BluetoothDevice]:
        """
        执行扫描的实际实现

        Args:
            timeout: 超时时间

        Returns:
            设备列表
        """
        system = platform.system()

        if system == "Linux":
            return self._scan_linux(timeout)
        elif system == "Windows":
            return self._scan_windows(timeout)
        elif system == "Darwin":  # macOS
            return self._scan_macos(timeout)
        else:
            self.logger.error(f"不支持的操作系统: {system}")
            return []

    def _scan_linux(self, timeout: int) -> List[BluetoothDevice]:
        """Linux平台扫描实现"""
        self.logger.debug("使用Linux蓝牙扫描 (bleak)")

        try:
            import bleak
        except ImportError:
            self.logger.error("bleak 未安装，无法扫描蓝牙设备")
            return []

        devices = []

        async def scan_with_bleak():
            from bleak import BleakScanner

            discovered = []

            def detection_callback(device, advertisement_data):
                discovered.append({
                    "address": device.address,
                    "name": device.name or advertisement_data.local_name or "Unknown",
                    "rssi": advertisement_data.rssi,
                    "raw_data": str(advertisement_data)
                })

            scanner = BleakScanner(detection_callback=detection_callback)
            await scanner.start()
            await asyncio.sleep(timeout)
            await scanner.stop()

            return discovered

        # 运行异步扫描
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            raw_devices = loop.run_until_complete(scan_with_bleak())
        finally:
            loop.close()

        # 转换为 BluetoothDevice 对象
        for dev in raw_devices:
            device = BluetoothDevice(
                name=dev["name"],
                mac_address=dev["address"],
                rssi=dev["rssi"],
                device_class="Unknown"
            )
            devices.append(device)

        return devices

    def _scan_windows(self, timeout: int) -> List[BluetoothDevice]:
        """Windows平台扫描实现"""
        self.logger.debug("使用Windows蓝牙扫描")
        # TODO: 实现基于Windows Bluetooth APIs的扫描
        return []

    def _scan_macos(self, timeout: int) -> List[BluetoothDevice]:
        """macOS平台扫描实现"""
        self.logger.debug("使用macOS蓝牙扫描")
        # TODO: 实现基于CoreBluetooth的扫描
        return []

    def _get_adapter_address(self) -> str:
        """获取适配器MAC地址"""
        # TODO: 实现获取适配器地址
        return "00:00:00:00:00:00"

    def _is_adapter_powered(self) -> bool:
        """检查适配器是否已开启"""
        # TODO: 实现检查适配器状态
        return True

    def _is_adapter_discoverable(self) -> bool:
        """检查适配器是否可发现"""
        # TODO: 实现检查可发现状态
        return True

    # ==================== BLE设备发现 ====================

    def scan_ble_devices(self, timeout: int = 10, service_uuids: Optional[List[str]] = None) -> List[BluetoothDevice]:
        """
        扫描BLE设备

        Args:
            timeout: 扫描超时时间
            service_uuids: 服务UUID过滤列表

        Returns:
            发现的BLE设备列表
        """
        self.logger.info(f"扫描BLE设备，服务过滤: {service_uuids}")
        # TODO: 实现BLE设备扫描
        return []

    async def scan_ble_devices_async(self, timeout: int = 10, service_uuids: Optional[List[str]] = None) -> List[BluetoothDevice]:
        """异步扫描BLE设备"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scan_ble_devices, timeout, service_uuids)

    # ==================== 经典蓝牙设备发现 ====================

    def scan_classic_devices(self, timeout: int = 10, lookup_names: bool = True) -> List[BluetoothDevice]:
        """
        扫描经典蓝牙设备

        Args:
            timeout: 扫描超时时间
            lookup_names: 是否查找设备名称

        Returns:
            发现的经典蓝牙设备列表
        """
        self.logger.info(f"扫描经典蓝牙设备，查找名称: {lookup_names}")
        # TODO: 实现经典蓝牙设备扫描
        return []

    async def scan_classic_devices_async(self, timeout: int = 10, lookup_names: bool = True) -> List[BluetoothDevice]:
        """异步扫描经典蓝牙设备"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scan_classic_devices, timeout, lookup_names)