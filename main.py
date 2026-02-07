#!/usr/bin/env python3
"""
My Blue App - 主入口

应用程序的启动入口点。
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.bluetooth_manager import BluetoothManager
from src.ui.main_window import MainWindow
from src.utils.config import Config
from src.utils.logger import Logger, setup_logging


def initialize_logging(config: Config) -> None:
    """
    初始化日志系统

    Args:
        config: 配置管理器实例
    """
    log_dir = config.get("logging.log_dir", "logs")
    log_level = config.get("logging.level", "INFO")
    console_level = config.get("logging.console_level", "INFO")
    file_level = config.get("logging.file_level", "DEBUG")

    setup_logging(
        log_dir=log_dir,
        level=log_level,
        console_level=console_level,
        file_level=file_level
    )

    logger = Logger.get_logger(__name__)
    logger.info("=" * 50)
    logger.info(f"启动 {config.get('app.name', 'My Blue App')} v{config.get('app.version', '0.1.0')}")
    logger.info("=" * 50)


def load_config() -> Config:
    """
    加载配置文件

    Returns:
        配置管理器实例
    """
    config_paths = [
        "config.yaml",
        "config.yml",
        "config.json",
        os.path.expanduser("~/.config/my_blue_app/config.yaml"),
    ]

    for path in config_paths:
        if os.path.exists(path):
            return Config(path)

    # 未找到配置文件，使用默认配置
    return Config()


def main_gui() -> int:
    """
    GUI模式主函数

    Returns:
        退出代码
    """
    # 加载配置
    config = load_config()

    # 初始化日志
    initialize_logging(config)
    logger = Logger.get_logger(__name__)

    # 首先创建 QApplication（必须在任何 QWidget 之前）
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
    except ImportError:
        app = None

    try:
        # 创建蓝牙管理器
        manager_config = {
            "scanner": config.get("scanner", {}),
            "connector": config.get("connector", {}),
            "data_handler": config.get("data_handler", {})
        }
        manager = BluetoothManager(manager_config)

        logger.info("初始化蓝牙管理器")

        # 创建主窗口（在 QApplication 之后）
        window = MainWindow(manager, config)

        logger.info("启动GUI界面")
        window.show()

        # 运行事件循环
        if app:
            return app.exec_()
        else:
            # 对于Tkinter，窗口已经在show()中启动
            return 0

    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        return 1

    finally:
        logger.info("应用程序退出")


def main_cli() -> int:
    """
    命令行模式主函数

    Returns:
        退出代码
    """
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="My Blue App - 蓝牙设备管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s scan                    # 扫描蓝牙设备
  %(prog)s connect 00:11:22:33:44:55  # 连接指定设备
  %(prog)s --help                  # 显示帮助信息
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 扫描命令
    scan_parser = subparsers.add_parser("scan", help="扫描蓝牙设备")
    scan_parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=10,
        help="扫描超时时间（秒）"
    )
    scan_parser.add_argument(
        "--ble",
        action="store_true",
        help="仅扫描BLE设备"
    )

    # 连接命令
    connect_parser = subparsers.add_parser("connect", help="连接蓝牙设备")
    connect_parser.add_argument(
        "mac",
        type=str,
        help="设备MAC地址"
    )
    connect_parser.add_argument(
        "-p", "--port",
        type=int,
        help="端口号（经典蓝牙）"
    )

    # 断开命令
    disconnect_parser = subparsers.add_parser("disconnect", help="断开蓝牙设备")
    disconnect_parser.add_argument(
        "mac",
        type=str,
        help="设备MAC地址"
    )

    # 发送数据命令
    send_parser = subparsers.add_parser("send", help="向设备发送数据")
    send_parser.add_argument(
        "mac",
        type=str,
        help="设备MAC地址"
    )
    send_parser.add_argument(
        "data",
        type=str,
        help="要发送的数据（文本或十六进制）"
    )
    send_parser.add_argument(
        "--hex",
        action="store_true",
        help="数据为十六进制格式"
    )

    args = parser.parse_args()

    # 加载配置
    if args.config:
        config = Config(args.config)
    else:
        config = load_config()

    # 初始化日志
    initialize_logging(config)
    logger = Logger.get_logger(__name__)

    try:
        # 创建蓝牙管理器
        manager = BluetoothManager()

        # 执行命令
        if args.command == "scan":
            return cmd_scan(manager, args)
        elif args.command == "connect":
            return cmd_connect(manager, args)
        elif args.command == "disconnect":
            return cmd_disconnect(manager, args)
        elif args.command == "send":
            return cmd_send(manager, args)
        else:
            parser.print_help()
            return 0

    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        return 1


def cmd_scan(manager: BluetoothManager, args) -> int:
    """执行扫描命令"""
    logger = Logger.get_logger(__name__)

    logger.info(f"开始扫描设备，超时: {args.timeout}秒")

    devices = manager.scan_devices(timeout=args.timeout)

    if not devices:
        print("未发现任何蓝牙设备")
        return 0

    print(f"\n发现 {len(devices)} 个设备:")
    print("-" * 80)

    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.name}")
        print(f"   MAC地址: {device.mac_address}")
        print(f"   信号强度: {device.rssi} dBm ({device.signal_strength})")
        print(f"   设备类型: {device.device_type}")
        print(f"   设备类别: {device.device_class}")
        print(f"   连接状态: {'已连接' if device.connected else '未连接'}")
        print()

    return 0


def cmd_connect(manager: BluetoothManager, args) -> int:
    """执行连接命令"""
    logger = Logger.get_logger(__name__)

    logger.info(f"正在连接设备: {args.mac}")

    success = manager.connect_device(args.mac)

    if success:
        print(f"成功连接到设备: {args.mac}")
        return 0
    else:
        print(f"连接失败: {args.mac}")
        return 1


def cmd_disconnect(manager: BluetoothManager, args) -> int:
    """执行断开命令"""
    logger = Logger.get_logger(__name__)

    logger.info(f"正在断开设备: {args.mac}")

    success = manager.disconnect_device(args.mac)

    if success:
        print(f"已断开设备: {args.mac}")
        return 0
    else:
        print(f"断开失败: {args.mac}")
        return 1


def cmd_send(manager: BluetoothManager, args) -> int:
    """执行发送数据命令"""
    logger = Logger.get_logger(__name__)

    # 准备数据
    if args.hex:
        data = bytes.fromhex(args.data)
    else:
        data = args.data.encode("utf-8")

    logger.info(f"向 {args.mac} 发送数据: {len(data)} 字节")

    success = manager.send_data(args.mac, data)

    if success:
        print(f"数据已发送")
        return 0
    else:
        print(f"发送失败")
        return 1


def main() -> int:
    """
    主入口函数

    根据参数决定启动GUI或命令行模式

    Returns:
        退出代码
    """
    # 检查是否有GUI环境
    has_display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")

    # 如果没有命令行参数且有显示环境，启动GUI
    if len(sys.argv) == 1 and has_display:
        return main_gui()
    else:
        return main_cli()



if __name__ == "__main__":
    sys.exit(main())