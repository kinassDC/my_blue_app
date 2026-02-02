"""
设备扫描模块测试

测试DeviceScanner类的各项功能。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.core.device_scanner import DeviceScanner
from src.models.device import BluetoothDevice
from datetime import datetime


class TestDeviceScanner(unittest.TestCase):
    """设备扫描器测试类"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            "scan_timeout": 5,
            "device_type": "all",
            "adapter_name": None
        }
        self.scanner = DeviceScanner(self.config)

    def tearDown(self):
        """测试后清理"""
        if self.scanner._scanning:
            self.scanner._scanning = False

    # ==================== 基础测试 ====================

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.scanner._scan_timeout, 5)
        self.assertEqual(self.scanner._device_type, "all")
        self.assertFalse(self.scanner._scanning)

    def test_init_default_config(self):
        """测试默认配置初始化"""
        scanner = DeviceScanner()
        self.assertEqual(scanner._scan_timeout, 10)
        self.assertEqual(scanner._device_type, "all")

    # ==================== 扫描测试 ====================

    def test_scan_returns_list(self):
        """测试扫描返回列表"""
        with patch.object(self.scanner, '_do_scan', return_value=[]):
            result = self.scanner.scan(5)
            self.assertIsInstance(result, list)

    def test_scan_with_timeout(self):
        """测试带超时的扫描"""
        with patch.object(self.scanner, '_do_scan', return_value=[]) as mock_scan:
            self.scanner.scan(timeout=15)
            mock_scan.assert_called_once_with(15)

    def test_scan_uses_default_timeout(self):
        """测试使用默认超时"""
        with patch.object(self.scanner, '_do_scan', return_value=[]) as mock_scan:
            self.scanner.scan()
            mock_scan.assert_called_once_with(5)

    def test_scan_prevents_concurrent(self):
        """测试防止并发扫描"""
        self.scanner._scanning = True
        with patch.object(self.scanner, '_do_scan', return_value=[]):
            result = self.scanner.scan()
            self.assertEqual(result, [])

    def test_scan_resets_flag_after_error(self):
        """测试错误后重置扫描标志"""
        with patch.object(self.scanner, '_do_scan', side_effect=Exception("Test error")):
            try:
                self.scanner.scan()
            except:
                pass
        self.assertFalse(self.scanner._scanning)

    # ==================== 异步扫描测试 ====================

    def test_scan_async(self):
        """测试异步扫描"""
        import asyncio

        async def run_test():
            with patch.object(self.scanner, 'scan', return_value=[]):
                result = await self.scanner.scan_async(5)
                self.assertIsInstance(result, list)

        asyncio.run(run_test())

    # ==================== 适配器信息测试 ====================

    def test_get_adapter_info(self):
        """测试获取适配器信息"""
        info = self.scanner.get_adapter_info()
        self.assertIsInstance(info, dict)
        self.assertIn("name", info)
        self.assertIn("address", info)
        self.assertIn("powered", info)
        self.assertIn("discoverable", info)
        self.assertIn("platform", info)

    # ==================== 持续扫描测试 ====================

    def test_start_continuous_scan(self):
        """测试开始持续扫描"""
        callback = Mock()
        self.scanner.start_continuous_scan(callback, interval=5)
        self.assertEqual(self.scanner._scan_callback, callback)

    def test_stop_continuous_scan(self):
        """测试停止持续扫描"""
        callback = Mock()
        self.scanner.start_continuous_scan(callback)
        self.scanner.stop_continuous_scan()
        self.assertIsNone(self.scanner._scan_callback)

    # ==================== BLE扫描测试 ====================

    def test_scan_ble_devices(self):
        """测试BLE设备扫描"""
        result = self.scanner.scan_ble_devices(timeout=10)
        self.assertIsInstance(result, list)

    def test_scan_ble_with_service_uuids(self):
        """测试带服务UUID过滤的BLE扫描"""
        service_uuids = ["0000180d-0000-1000-8000-00805f9b34fb"]
        result = self.scanner.scan_ble_devices(timeout=10, service_uuids=service_uuids)
        self.assertIsInstance(result, list)

    # ==================== 经典蓝牙扫描测试 ====================

    def test_scan_classic_devices(self):
        """测试经典蓝牙设备扫描"""
        result = self.scanner.scan_classic_devices(timeout=10)
        self.assertIsInstance(result, list)

    def test_scan_classic_with_lookup_names(self):
        """测试带名称查找的经典蓝牙扫描"""
        result = self.scanner.scan_classic_devices(timeout=10, lookup_names=True)
        self.assertIsInstance(result, list)


class TestDeviceScannerIntegration(unittest.TestCase):
    """设备扫描器集成测试"""

    def setUp(self):
        """测试前准备"""
        self.scanner = DeviceScanner()

    # ==================== 平台特定测试 ====================

    @patch('platform.system', return_value='Linux')
    def test_linux_scan_path(self, mock_platform):
        """测试Linux扫描路径"""
        with patch.object(self.scanner, '_scan_linux', return_value=[]) as mock_scan:
            self.scanner.scan()
            mock_scan.assert_called_once()

    @patch('platform.system', return_value='Windows')
    def test_windows_scan_path(self, mock_platform):
        """测试Windows扫描路径"""
        with patch.object(self.scanner, '_scan_windows', return_value=[]) as mock_scan:
            self.scanner.scan()
            mock_scan.assert_called_once()

    @patch('platform.system', return_value='Darwin')
    def test_macos_scan_path(self, mock_platform):
        """测试macOS扫描路径"""
        with patch.object(self.scanner, '_scan_macos', return_value=[]) as mock_scan:
            self.scanner.scan()
            mock_scan.assert_called_once()

    @patch('platform.system', return_value='Unknown')
    def test_unsupported_platform(self, mock_platform):
        """测试不支持的平台"""
        result = self.scanner.scan()
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()