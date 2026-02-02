"""
设备连接模块测试

测试Connector类的各项功能。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.core.connector import Connector


class TestConnector(unittest.TestCase):
    """设备连接器测试类"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            "connect_timeout": 10,
            "retry_count": 3,
            "retry_delay": 1,
            "auto_reconnect": False
        }
        self.connector = Connector(self.config)
        self.test_mac = "00:11:22:33:44:55"

    def tearDown(self):
        """测试后清理"""
        self.connector.disconnect_all()

    # ==================== 基础测试 ====================

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.connector._connect_timeout, 10)
        self.assertEqual(self.connector._retry_count, 3)
        self.assertEqual(self.connector._retry_delay, 1)
        self.assertFalse(self.connector._auto_reconnect)
        self.assertEqual(len(self.connector._connections), 0)

    def test_init_default_config(self):
        """测试默认配置初始化"""
        connector = Connector()
        self.assertEqual(connector._connect_timeout, 10)
        self.assertEqual(connector._retry_count, 3)

    # ==================== 连接测试 ====================

    def test_connect_returns_bool(self):
        """测试连接返回布尔值"""
        with patch.object(self.connector, '_do_connect', return_value=MagicMock()):
            result = self.connector.connect(self.test_mac)
            self.assertIsInstance(result, bool)

    def test_connect_stores_connection(self):
        """测试连接存储连接对象"""
        mock_connection = MagicMock()
        with patch.object(self.connector, '_do_connect', return_value=mock_connection):
            self.connector.connect(self.test_mac)
            self.assertIn(self.test_mac, self.connector._connections)
            self.assertEqual(self.connector._connections[self.test_mac], mock_connection)

    def test_connect_already_connected(self):
        """测试已连接设备的连接"""
        mock_connection = MagicMock()
        self.connector._connections[self.test_mac] = mock_connection

        with patch.object(self.connector, '_do_connect', return_value=None) as mock_connect:
            result = self.connector.connect(self.test_mac)
            # 不应调用_do_connect
            mock_connect.assert_not_called()
            self.assertTrue(result)

    def test_connect_with_port(self):
        """测试带端口的连接"""
        mock_connection = MagicMock()
        with patch.object(self.connector, '_do_connect', return_value=mock_connection) as mock_connect:
            self.connector.connect(self.test_mac, port=1)
            mock_connect.assert_called_once_with(self.test_mac, 1)

    def test_connect_retry_on_failure(self):
        """测试连接失败重试"""
        with patch.object(self.connector, '_do_connect', side_effect=[None, None, MagicMock()]):
            result = self.connector.connect(self.test_mac)
            # 应该在第3次尝试成功
            self.assertTrue(result)

    def test_connect_fails_after_max_retries(self):
        """测试达到最大重试次数后失败"""
        with patch.object(self.connector, '_do_connect', return_value=None):
            result = self.connector.connect(self.test_mac)
            self.assertFalse(result)

    # ==================== 断开测试 ====================

    def test_disconnect_returns_bool(self):
        """测试断开返回布尔值"""
        self.connector._connections[self.test_mac] = MagicMock()
        result = self.connector.disconnect(self.test_mac)
        self.assertIsInstance(result, bool)

    def test_disconnect_removes_connection(self):
        """测试断开移除连接"""
        mock_connection = MagicMock()
        self.connector._connections[self.test_mac] = mock_connection

        with patch.object(self.connector, '_do_disconnect'):
            self.connector.disconnect(self.test_mac)
            self.assertNotIn(self.test_mac, self.connector._connections)

    def test_disconnect_not_connected(self):
        """测试断开未连接的设备"""
        result = self.connector.disconnect(self.test_mac)
        self.assertFalse(result)

    def test_disconnect_all(self):
        """测试断开所有连接"""
        self.connector._connections["00:11:22:33:44:55"] = MagicMock()
        self.connector._connections["00:11:22:33:44:56"] = MagicMock()

        with patch.object(self.connector, 'disconnect'):
            self.connector.disconnect_all()
            self.assertEqual(len(self.connector._connections), 0)

    # ==================== 连接状态测试 ====================

    def test_is_connected_true(self):
        """测试检查连接状态-已连接"""
        self.connector._connections[self.test_mac] = MagicMock()
        self.assertTrue(self.connector.is_connected(self.test_mac))

    def test_is_connected_false(self):
        """测试检查连接状态-未连接"""
        self.assertFalse(self.connector.is_connected(self.test_mac))

    def test_get_connections(self):
        """测试获取所有连接"""
        mock_conn1 = MagicMock()
        mock_conn2 = MagicMock()
        self.connector._connections["00:11:22:33:44:55"] = mock_conn1
        self.connector._connections["00:11:22:33:44:56"] = mock_conn2

        connections = self.connector.get_connections()
        self.assertEqual(len(connections), 2)
        self.assertIn("00:11:22:33:44:55", connections)
        self.assertIn("00:11:22:33:44:56", connections)

    def test_get_connection_count(self):
        """测试获取连接数"""
        self.assertEqual(self.connector.get_connection_count(), 0)

        self.connector._connections["00:11:22:33:44:55"] = MagicMock()
        self.assertEqual(self.connector.get_connection_count(), 1)

        self.connector._connections["00:11:22:33:44:56"] = MagicMock()
        self.assertEqual(self.connector.get_connection_count(), 2)

    def test_get_connection(self):
        """测试获取指定连接"""
        mock_connection = MagicMock()
        self.connector._connections[self.test_mac] = mock_connection

        result = self.connector.get_connection(self.test_mac)
        self.assertEqual(result, mock_connection)

    def test_get_connection_not_exists(self):
        """测试获取不存在的连接"""
        result = self.connector.get_connection(self.test_mac)
        self.assertIsNone(result)

    # ==================== 异步测试 ====================

    def test_connect_async(self):
        """测试异步连接"""
        import asyncio

        async def run_test():
            with patch.object(self.connector, 'connect', return_value=True):
                result = await self.connector.connect_async(self.test_mac)
                self.assertTrue(result)

        asyncio.run(run_test())

    def test_disconnect_async(self):
        """测试异步断开"""
        import asyncio

        async def run_test():
            with patch.object(self.connector, 'disconnect', return_value=True):
                result = await self.connector.disconnect_async(self.test_mac)
                self.assertTrue(result)

        asyncio.run(run_test())

    # ==================== BLE连接测试 ====================

    def test_connect_ble(self):
        """测试BLE连接"""
        result = self.connector.connect_ble(self.test_mac)
        self.assertIsInstance(result, bool)

    def test_connect_ble_async(self):
        """测试异步BLE连接"""
        import asyncio

        async def run_test():
            with patch.object(self.connector, 'connect_ble', return_value=True):
                result = await self.connector.connect_ble_async(self.test_mac)
                self.assertTrue(result)

        asyncio.run(run_test())

    # ==================== 经典蓝牙连接测试 ====================

    def test_connect_classic(self):
        """测试经典蓝牙连接"""
        result = self.connector.connect_classic(self.test_mac, port=1)
        self.assertIsInstance(result, bool)

    def test_connect_classic_async(self):
        """测试异步经典蓝牙连接"""
        import asyncio

        async def run_test():
            with patch.object(self.connector, 'connect_classic', return_value=True):
                result = await self.connector.connect_classic_async(self.test_mac, port=1)
                self.assertTrue(result)

        asyncio.run(run_test())

    # ==================== 配对测试 ====================

    def test_pair(self):
        """测试配对"""
        result = self.connector.pair(self.test_mac)
        self.assertIsInstance(result, bool)

    def test_pair_with_pin(self):
        """测试带PIN码的配对"""
        result = self.connector.pair(self.test_mac, pin="1234")
        self.assertIsInstance(result, bool)

    def test_unpair(self):
        """测试取消配对"""
        result = self.connector.unpair(self.test_mac)
        self.assertIsInstance(result, bool)

    def test_is_paired(self):
        """测试检查配对状态"""
        result = self.connector.is_paired(self.test_mac)
        self.assertIsInstance(result, bool)

    # ==================== 平台特定测试 ====================

    @patch('platform.system', return_value='Linux')
    def test_linux_connect_path(self, mock_platform):
        """测试Linux连接路径"""
        with patch.object(self.connector, '_connect_linux', return_value=None) as mock_connect:
            self.connector.connect(self.test_mac)
            mock_connect.assert_called_once()

    @patch('platform.system', return_value='Windows')
    def test_windows_connect_path(self, mock_platform):
        """测试Windows连接路径"""
        with patch.object(self.connector, '_connect_windows', return_value=None) as mock_connect:
            self.connector.connect(self.test_mac)
            mock_connect.assert_called_once()

    @patch('platform.system', return_value='Darwin')
    def test_macos_connect_path(self, mock_platform):
        """测试macOS连接路径"""
        with patch.object(self.connector, '_connect_macos', return_value=None) as mock_connect:
            self.connector.connect(self.test_mac)
            mock_connect.assert_called_once()


class TestConnectorCleanup(unittest.TestCase):
    """连接器清理测试"""

    def test_cleanup(self):
        """测试清理"""
        connector = Connector()
        connector._connections["00:11:22:33:44:55"] = MagicMock()
        connector._connections["00:11:22:33:44:56"] = MagicMock()

        with patch.object(connector, 'disconnect'):
            connector.cleanup()
            self.assertEqual(len(connector._connections), 0)


if __name__ == '__main__':
    unittest.main()