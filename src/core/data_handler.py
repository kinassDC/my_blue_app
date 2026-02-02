"""
数据处理模块

负责蓝牙设备的数据收发和处理。
"""

import asyncio
import threading
import queue
from typing import Optional, Dict, Any, Callable
from src.utils.logger import Logger


class DataHandler:
    """
    数据处理器

    负责蓝牙设备的数据收发、编码解码和数据处理。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据处理器

        Args:
            config: 配置参数
                - buffer_size: 接收缓冲区大小
                - timeout: 默认操作超时时间（秒）
                - encoding: 默认字符编码
                - auto_reconnect: 连接断开时是否自动重连
        """
        self.config = config or {}
        self.logger = Logger.get_logger(__name__)

        self._buffer_size = self.config.get("buffer_size", 4096)
        self._timeout = self.config.get("timeout", 5.0)
        self._encoding = self.config.get("encoding", "utf-8")

        # 接收数据队列
        self._receive_queues: Dict[str, queue.Queue] = {}
        self._receive_threads: Dict[str, threading.Thread] = {}

        # 数据回调
        self._on_data_received: Optional[Callable[[str, bytes], None]] = None
        self._on_data_sent: Optional[Callable[[str, bytes], None]] = None

    # ==================== 数据发送 ====================

    def send(self, device_mac: str, data: bytes, connection: Optional[Any] = None) -> bool:
        """
        向设备发送数据

        Args:
            device_mac: 设备MAC地址
            data: 要发送的数据
            connection: 连接对象（可选）

        Returns:
            发送是否成功
        """
        self.logger.debug(f"发送数据到 {device_mac}: {len(data)} 字节")

        try:
            # TODO: 实现实际的数据发送
            # connection = connection or self._get_connection(device_mac)
            # connection.send(data)

            if self._on_data_sent:
                self._on_data_sent(device_mac, data)

            return True
        except Exception as e:
            self.logger.error(f"发送数据失败: {e}")
            return False

    async def send_async(self, device_mac: str, data: bytes, connection: Optional[Any] = None) -> bool:
        """
        异步向设备发送数据

        Args:
            device_mac: 设备MAC地址
            data: 要发送的数据
            connection: 连接对象

        Returns:
            发送是否成功
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send, device_mac, data, connection)

    def send_text(self, device_mac: str, text: str, encoding: Optional[str] = None) -> bool:
        """
        发送文本数据

        Args:
            device_mac: 设备MAC地址
            text: 文本内容
            encoding: 字符编码

        Returns:
            发送是否成功
        """
        encoding = encoding or self._encoding
        data = text.encode(encoding)
        return self.send(device_mac, data)

    # ==================== 数据接收 ====================

    def receive(self, device_mac: str, size: int = 1024, timeout: float = 5.0, connection: Optional[Any] = None) -> Optional[bytes]:
        """
        从设备接收数据

        Args:
            device_mac: 设备MAC地址
            size: 接收数据大小
            timeout: 超时时间（秒）
            connection: 连接对象

        Returns:
            接收到的数据，超时或失败返回None
        """
        self.logger.debug(f"从 {device_mac} 接收数据，最大: {size} 字节")

        try:
            # 检查是否有队列数据
            if device_mac in self._receive_queues:
                try:
                    data = self._receive_queues[device_mac].get(timeout=timeout)
                    if self._on_data_received:
                        self._on_data_received(device_mac, data)
                    return data
                except queue.Empty:
                    return None

            # TODO: 实现实际的数据接收
            # connection = connection or self._get_connection(device_mac)
            # data = connection.recv(size)
            # return data

            return None
        except Exception as e:
            self.logger.error(f"接收数据失败: {e}")
            return None

    async def receive_async(self, device_mac: str, size: int = 1024, timeout: float = 5.0, connection: Optional[Any] = None) -> Optional[bytes]:
        """
        异步从设备接收数据

        Args:
            device_mac: 设备MAC地址
            size: 接收数据大小
            timeout: 超时时间
            connection: 连接对象

        Returns:
            接收到的数据
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.receive, device_mac, size, timeout, connection)

    def receive_text(self, device_mac: str, size: int = 1024, timeout: float = 5.0, encoding: Optional[str] = None) -> Optional[str]:
        """
        接收文本数据

        Args:
            device_mac: 设备MAC地址
            size: 接收数据大小
            timeout: 超时时间
            encoding: 字符编码

        Returns:
            接收到的文本
        """
        encoding = encoding or self._encoding
        data = self.receive(device_mac, size, timeout)
        if data:
            return data.decode(encoding, errors="ignore")
        return None

    # ==================== 持续接收 ====================

    def start_listening(self, device_mac: str, callback: Callable[[bytes], None], connection: Optional[Any] = None) -> None:
        """
        开始监听设备数据

        Args:
            device_mac: 设备MAC地址
            callback: 数据接收回调函数
            connection: 连接对象
        """
        if device_mac in self._receive_threads:
            self.logger.warning(f"设备已在监听中: {device_mac}")
            return

        self._receive_queues[device_mac] = queue.Queue()

        def listen_thread():
            """监听线程"""
            self.logger.info(f"开始监听设备: {device_mac}")

            while device_mac in self._receive_threads:
                try:
                    # TODO: 实现实际的数据监听
                    # data = connection.recv(self._buffer_size)
                    # if data:
                    #     self._receive_queues[device_mac].put(data)
                    #     callback(data)
                    pass
                except Exception as e:
                    self.logger.error(f"监听出错: {e}")
                    break

            self.logger.info(f"停止监听设备: {device_mac}")

        thread = threading.Thread(target=listen_thread, daemon=True)
        self._receive_threads[device_mac] = thread
        thread.start()

    def stop_listening(self, device_mac: str) -> None:
        """
        停止监听设备数据

        Args:
            device_mac: 设备MAC地址
        """
        if device_mac in self._receive_threads:
            del self._receive_threads[device_mac]

        if device_mac in self._receive_queues:
            del self._receive_queues[device_mac]

        self.logger.info(f"停止监听设备: {device_mac}")

    # ==================== 数据处理 ====================

    def set_data_received_callback(self, callback: Callable[[str, bytes], None]) -> None:
        """设置数据接收回调"""
        self._on_data_received = callback

    def set_data_sent_callback(self, callback: Callable[[str, bytes], None]) -> None:
        """设置数据发送回调"""
        self._on_data_sent = callback

    # ==================== 数据编码/解码 ====================

    @staticmethod
    def encode_hex(data: bytes) -> str:
        """将字节数据编码为十六进制字符串"""
        return data.hex()

    @staticmethod
    def decode_hex(hex_string: str) -> bytes:
        """将十六进制字符串解码为字节数据"""
        return bytes.fromhex(hex_string)

    @staticmethod
    def encode_base64(data: bytes) -> str:
        """将字节数据编码为Base64字符串"""
        import base64
        return base64.b64encode(data).decode("ascii")

    @staticmethod
    def decode_base64(base64_string: str) -> bytes:
        """将Base64字符串解码为字节数据"""
        import base64
        return base64.b64decode(base64_string)

    # ==================== 数据校验 ====================

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """
        计算校验和（简单累加）

        Args:
            data: 数据

        Returns:
            校验和
        """
        return sum(data) & 0xFF

    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        """
        计算CRC16校验值

        Args:
            data: 数据

        Returns:
            CRC16校验值
        """
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    # ==================== 数据包处理 ====================

    def pack_data(self, data: bytes, include_checksum: bool = True, include_length: bool = True) -> bytes:
        """
        打包数据

        Args:
            data: 原始数据
            include_checksum: 是否包含校验和
            include_length: 是否包含长度

        Returns:
            打包后的数据
        """
        packet = bytearray()

        if include_length:
            packet.extend(len(data).to_bytes(4, "big"))

        packet.extend(data)

        if include_checksum:
            checksum = self.calculate_checksum(data)
            packet.append(checksum)

        return bytes(packet)

    def unpack_data(self, packet: bytes, has_checksum: bool = True, has_length: bool = True) -> Optional[bytes]:
        """
        解包数据

        Args:
            packet: 打包的数据
            has_checksum: 是否包含校验和
            has_length: 是否包含长度

        Returns:
            原始数据，解包失败返回None
        """
        try:
            offset = 0

            if has_length:
                if len(packet) < 4:
                    return None
                length = int.from_bytes(packet[:4], "big")
                offset = 4
            else:
                length = len(packet)

            if has_checksum:
                checksum = packet[-1]
                data = packet[offset:-1]
                if self.calculate_checksum(data) != checksum:
                    self.logger.error("校验和验证失败")
                    return None
            else:
                data = packet[offset:offset + length]

            return data
        except Exception as e:
            self.logger.error(f"解包数据失败: {e}")
            return None

    # ==================== 清理 ====================

    def cleanup(self, device_mac: Optional[str] = None) -> None:
        """
        清理资源

        Args:
            device_mac: 指定设备MAC地址，None表示清理所有
        """
        if device_mac:
            self.stop_listening(device_mac)
        else:
            for mac in list(self._receive_threads.keys()):
                self.stop_listening(mac)