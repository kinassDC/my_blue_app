"""
主窗口模块

应用程序的主窗口界面，整合所有UI组件。
"""

import sys
import threading
from typing import Optional, Callable, List, Any
from enum import Enum

try:
    from PyQt5.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QStatusBar, QMenuBar, QMenu,
        QAction, QMessageBox, QSplitter, QFrame
    )
    from PyQt5.QtCore import Qt, pyqtSignal, QObject
    from PyQt5.QtGui import QIcon
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

from src.models.device import BluetoothDevice
from src.core.bluetooth_manager import BluetoothManager
from src.utils.logger import Logger
from src.utils.config import Config


class ConnectionState(Enum):
    """连接状态"""
    DISCONNECTED = "未连接"
    SCANNING = "扫描中"
    CONNECTING = "连接中"
    CONNECTED = "已连接"
    ERROR = "错误"


# ==================== PyQt5 实现 ====================

if PYQT5_AVAILABLE:
    class _SignalEmitter(QObject):
        """信号发射器"""
        device_discovered = pyqtSignal(object)
        device_connected = pyqtSignal(object)
        device_disconnected = pyqtSignal(str)
        data_received = pyqtSignal(str, bytes)
        connection_state_changed = pyqtSignal(str)

    class MainWindowPyQt5(QMainWindow):
        """
        主窗口 - PyQt5实现

        提供完整的GUI界面，包含设备列表、日志显示、控制面板等组件。
        """

        def __init__(self, manager: BluetoothManager, config: Optional[Config] = None):
            """
            初始化主窗口

            Args:
                manager: 蓝牙管理器实例
                config: 配置管理器实例
            """
            super().__init__()
            self.manager = manager
            self.config = config or Config()
            self.logger = Logger.get_logger(__name__)

            # 信号发射器（用于线程间通信）
            self._emitter = _SignalEmitter()
            self._emitter.device_discovered.connect(self._on_device_discovered_ui)
            self._emitter.device_connected.connect(self._on_device_connected_ui)
            self._emitter.device_disconnected.connect(self._on_device_disconnected_ui)
            self._emitter.data_received.connect(self._on_data_received_ui)
            self._emitter.connection_state_changed.connect(self._on_connection_state_changed_ui)

            # 设备列表
            self._devices: List[BluetoothDevice] = []
            self._selected_device: Optional[BluetoothDevice] = None

            # 初始化UI
            self._init_ui()
            self._setup_callbacks()

        # ==================== UI初始化 ====================

        def _init_ui(self) -> None:
            """初始化用户界面"""
            self.setWindowTitle(self.config.get("app.name", "My Blue App"))
            self._set_window_size()

            # 创建中央组件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)

            # 主布局
            main_layout = QVBoxLayout(central_widget)

            # 控制面板
            main_layout.addWidget(self._create_control_panel())

            # 内容区域（分割器）
            splitter = QSplitter(Qt.Horizontal)

            # 左侧：设备列表
            splitter.addWidget(self._create_device_panel())

            # 右侧：日志显示
            splitter.addWidget(self._create_log_panel())

            splitter.setSizes([400, 600])
            main_layout.addWidget(splitter)

            # 状态栏
            self._create_status_bar()

            # 菜单栏
            self._create_menu_bar()

        def _set_window_size(self) -> None:
            """设置窗口大小"""
            size = self.config.get("ui.window_size", [1024, 768])
            self.resize(size[0], size[1])

        def _create_control_panel(self) -> QFrame:
            """创建控制面板"""
            panel = QFrame()
            panel.setFrameStyle(QFrame.StyledPanel)

            layout = QHBoxLayout(panel)

            # 扫描按钮
            self._scan_button = QPushButton("扫描设备")
            self._scan_button.clicked.connect(self._on_scan_clicked)
            layout.addWidget(self._scan_button)

            # 连接按钮
            self._connect_button = QPushButton("连接")
            self._connect_button.clicked.connect(self._on_connect_clicked)
            self._connect_button.setEnabled(False)
            layout.addWidget(self._connect_button)

            # 断开按钮
            self._disconnect_button = QPushButton("断开")
            self._disconnect_button.clicked.connect(self._on_disconnect_clicked)
            self._disconnect_button.setEnabled(False)
            layout.addWidget(self._disconnect_button)

            # 刷新按钮
            refresh_button = QPushButton("刷新")
            refresh_button.clicked.connect(self._on_refresh_clicked)
            layout.addWidget(refresh_button)

            layout.addStretch()

            # 状态标签
            self._status_label = QLabel("就绪")
            layout.addWidget(self._status_label)

            return panel

        def _create_device_panel(self) -> QFrame:
            """创建设备列表面板"""
            from src.ui.device_list import DeviceList

            panel = QFrame()
            panel.setFrameStyle(QFrame.StyledPanel)

            layout = QVBoxLayout(panel)

            # 标题
            title = QLabel("设备列表")
            layout.addWidget(title)

            # 设备列表组件
            self._device_list = DeviceList()
            self._device_list.device_selected.connect(self._on_device_selected)
            layout.addWidget(self._device_list)

            return panel

        def _create_log_panel(self) -> QFrame:
            """创建日志面板"""
            from src.ui.log_view import LogView

            panel = QFrame()
            panel.setFrameStyle(QFrame.StyledPanel)

            layout = QVBoxLayout(panel)

            # 标题
            title = QLabel("日志")
            layout.addWidget(title)

            # 日志视图组件
            self._log_view = LogView()
            layout.addWidget(self._log_view)

            return panel

        def _create_status_bar(self) -> None:
            """创建状态栏"""
            self._status_bar = QStatusBar()
            self.setStatusBar(self._status_bar)
            self._status_bar.showMessage("就绪")

        def _create_menu_bar(self) -> None:
            """创建菜单栏"""
            menubar = self.menuBar()

            # 文件菜单
            file_menu = menubar.addMenu("文件")

            exit_action = QAction("退出", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            # 工具菜单
            tools_menu = menubar.addMenu("工具")

            settings_action = QAction("设置", self)
            settings_action.triggered.connect(self._on_settings_clicked)
            tools_menu.addAction(settings_action)

            # 帮助菜单
            help_menu = menubar.addMenu("帮助")

            about_action = QAction("关于", self)
            about_action.triggered.connect(self._on_about_clicked)
            help_menu.addAction(about_action)

        # ==================== 回调设置 ====================

        def _setup_callbacks(self) -> None:
            """设置管理器回调"""
            self.manager.on_device_discovered(self._on_device_discovered)
            self.manager.on_device_connected(self._on_device_connected)
            self.manager.on_device_disconnected(self._on_device_disconnected)
            self.manager.on_data_received(self._on_data_received)

        # ==================== 事件处理 ====================

        def _on_scan_clicked(self) -> None:
            """扫描按钮点击事件"""
            self._scan_button.setEnabled(False)
            self._status_label.setText("扫描中...")
            self._emitter.connection_state_changed.emit("SCANNING")

            def scan_thread():
                try:
                    devices = self.manager.scan_devices(timeout=10)
                    self._devices = devices
                    self._emitter.connection_state_changed.emit("DISCONNECTED")
                except Exception as e:
                    self.logger.error(f"扫描失败: {e}")
                    self._emitter.connection_state_changed.emit("ERROR")

            threading.Thread(target=scan_thread, daemon=True).start()

        def _on_connect_clicked(self) -> None:
            """连接按钮点击事件"""
            if self._selected_device:
                self._connect_button.setEnabled(False)
                self._status_label.setText("连接中...")
                self._emitter.connection_state_changed.emit("CONNECTING")

                def connect_thread():
                    try:
                        self.manager.connect_device(self._selected_device.mac_address)
                    except Exception as e:
                        self.logger.error(f"连接失败: {e}")

                threading.Thread(target=connect_thread, daemon=True).start()

        def _on_disconnect_clicked(self) -> None:
            """断开按钮点击事件"""
            if self._selected_device:
                self.manager.disconnect_device(self._selected_device.mac_address)

        def _on_refresh_clicked(self) -> None:
            """刷新按钮点击事件"""
            self._on_scan_clicked()

        def _on_device_selected(self, device: Optional[BluetoothDevice]) -> None:
            """设备选择事件"""
            self._selected_device = device
            self._connect_button.setEnabled(device is not None and not device.connected)
            self._disconnect_button.setEnabled(device is not None and device.connected)

        def _on_settings_clicked(self) -> None:
            """设置菜单点击事件"""
            QMessageBox.information(self, "设置", "设置功能开发中...")

        def _on_about_clicked(self) -> None:
            """关于菜单点击事件"""
            QMessageBox.about(
                self,
                "关于",
                f"<h3>{self.config.get('app.name', 'My Blue App')}</h3>"
                f"<p>版本: {self.config.get('app.version', '0.1.0')}</p>"
                "<p>一个功能完善的蓝牙设备管理工具</p>"
            )

        # ==================== 管理器回调（后台线程） ====================

        def _on_device_discovered(self, device: BluetoothDevice) -> None:
            """设备发现回调"""
            self._emitter.device_discovered.emit(device)

        def _on_device_connected(self, device: BluetoothDevice) -> None:
            """设备连接回调"""
            self._emitter.device_connected.emit(device)

        def _on_device_disconnected(self, device_mac: str) -> None:
            """设备断开回调"""
            self._emitter.device_disconnected.emit(device_mac)

        def _on_data_received(self, device_mac: str, data: bytes) -> None:
            """数据接收回调"""
            self._emitter.data_received.emit(device_mac, data)

        # ==================== UI更新（主线程） ====================

        def _on_device_discovered_ui(self, device: BluetoothDevice) -> None:
            """更新设备发现到UI"""
            self._device_list.add_device(device)
            self._status_bar.showMessage(f"发现设备: {device.name}")

        def _on_device_connected_ui(self, device: BluetoothDevice) -> None:
            """更新设备连接状态到UI"""
            self._device_list.update_device(device)
            self._status_label.setText("已连接")
            self._connect_button.setEnabled(False)
            self._disconnect_button.setEnabled(True)
            self._status_bar.showMessage(f"已连接: {device.name}")

        def _on_device_disconnected_ui(self, device_mac: str) -> None:
            """更新设备断开状态到UI"""
            self._status_label.setText("未连接")
            self._connect_button.setEnabled(True)
            self._disconnect_button.setEnabled(False)
            self._status_bar.showMessage(f"已断开: {device_mac}")

        def _on_data_received_ui(self, device_mac: str, data: bytes) -> None:
            """更新接收数据到UI"""
            self._log_view.append(f"[接收] {device_mac}: {data}")

        def _on_connection_state_changed_ui(self, state: str) -> None:
            """更新连接状态到UI"""
            self._scan_button.setEnabled(state != "SCANNING")

        # ==================== 公共方法 ====================

        def add_log(self, message: str, level: str = "INFO") -> None:
            """添加日志消息"""
            self._log_view.append(f"[{level}] {message}")

        def update_devices(self, devices: List[BluetoothDevice]) -> None:
            """更新设备列表"""
            self._device_list.clear()
            for device in devices:
                self._device_list.add_device(device)


# ==================== Tkinter 实现（备用） ====================

elif TKINTER_AVAILABLE:
    class MainWindowTkinter:
        """
        主窗口 - Tkinter实现

        使用Tkinter实现的备用GUI界面。
        """

        def __init__(self, manager: BluetoothManager, config: Optional[Config] = None):
            """
            初始化主窗口

            Args:
                manager: 蓝牙管理器实例
                config: 配置管理器实例
            """
            self.manager = manager
            self.config = config or Config()
            self.logger = Logger.get_logger(__name__)

            # 设备列表
            self._devices: List[BluetoothDevice] = []
            self._selected_device: Optional[BluetoothDevice] = None

            # 创建主窗口
            self.root = tk.Tk()
            self.root.title(self.config.get("app.name", "My Blue App"))

            # 初始化UI
            self._init_ui()
            self._setup_callbacks()

        def _init_ui(self) -> None:
            """初始化用户界面"""
            # 设置窗口大小
            size = self.config.get("ui.window_size", [1024, 768])
            self.root.geometry(f"{size[0]}x{size[1]}")

            # 主框架
            main_frame = ttk.Frame(self.root, padding="5")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 控制面板
            control_frame = ttk.Frame(main_frame)
            control_frame.pack(fill=tk.X, pady=(0, 5))

            self._scan_button = ttk.Button(control_frame, text="扫描设备", command=self._on_scan_clicked)
            self._scan_button.pack(side=tk.LEFT, padx=2)

            self._connect_button = ttk.Button(control_frame, text="连接", command=self._on_connect_clicked, state=tk.DISABLED)
            self._connect_button.pack(side=tk.LEFT, padx=2)

            self._disconnect_button = ttk.Button(control_frame, text="断开", command=self._on_disconnect_clicked, state=tk.DISABLED)
            self._disconnect_button.pack(side=tk.LEFT, padx=2)

            # 状态标签
            self._status_label = ttk.Label(control_frame, text="就绪")
            self._status_label.pack(side=tk.RIGHT, padx=5)

            # 内容区域（使用PanedWindow）
            content = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
            content.pack(fill=tk.BOTH, expand=True)

            # 左侧：设备列表
            device_frame = ttk.LabelFrame(content, text="设备列表", padding="5")
            content.add(device_frame, weight=1)

            # 设备列表
            self._device_listbox = tk.Listbox(device_frame)
            self._device_listbox.pack(fill=tk.BOTH, expand=True)
            self._device_listbox.bind("<<ListboxSelect>>", self._on_device_selected)

            # 右侧：日志显示
            log_frame = ttk.LabelFrame(content, text="日志", padding="5")
            content.add(log_frame, weight=2)

            self._log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
            self._log_text.pack(fill=tk.BOTH, expand=True)

        def _setup_callbacks(self) -> None:
            """设置管理器回调"""
            # TODO: 实现回调设置
            pass

        # ==================== 事件处理 ====================

        def _on_scan_clicked(self) -> None:
            """扫描按钮点击事件"""
            self.add_log("开始扫描...")
            # TODO: 实现扫描功能

        def _on_connect_clicked(self) -> None:
            """连接按钮点击事件"""
            if self._selected_device:
                self.add_log(f"正在连接: {self._selected_device.name}")
                # TODO: 实现连接功能

        def _on_disconnect_clicked(self) -> None:
            """断开按钮点击事件"""
            if self._selected_device:
                self.add_log(f"正在断开: {self._selected_device.name}")
                # TODO: 实现断开功能

        def _on_device_selected(self, event) -> None:
            """设备选择事件"""
            selection = self._device_listbox.curselection()
            if selection:
                index = selection[0]
                if index < len(self._devices):
                    self._selected_device = self._devices[index]
                    self._connect_button.config(state=tk.NORMAL if not self._selected_device.connected else tk.DISABLED)
                    self._disconnect_button.config(state=tk.NORMAL if self._selected_device.connected else tk.DISABLED)

        # ==================== 公共方法 ====================

        def add_log(self, message: str) -> None:
            """添加日志消息"""
            self._log_text.insert(tk.END, message + "\n")
            self._log_text.see(tk.END)

        def update_devices(self, devices: List[BluetoothDevice]) -> None:
            """更新设备列表"""
            self._devices = devices
            self._device_listbox.delete(0, tk.END)
            for device in devices:
                self._device_listbox.insert(tk.END, str(device))

        def run(self) -> None:
            """运行主循环"""
            self.root.mainloop()


# ==================== 统一接口 ====================

class MainWindow:
    """
    主窗口统一接口

    根据可用的GUI库自动选择实现。
    """

    def __init__(self, manager: BluetoothManager, config: Optional[Config] = None):
        """
        初始化主窗口

        Args:
            manager: 蓝牙管理器实例
            config: 配置管理器实例
        """
        self._impl: Any

        if PYQT5_AVAILABLE:
            self._impl = MainWindowPyQt5(manager, config)
        elif TKINTER_AVAILABLE:
            self._impl = MainWindowTkinter(manager, config)
        else:
            raise RuntimeError("没有可用的GUI库，请安装 PyQt5 或确保 tkinter 可用")

    def show(self) -> None:
        """显示主窗口"""
        if hasattr(self._impl, "show"):
            self._impl.show()
        elif hasattr(self._impl, "root"):
            self._impl.root.deiconify()

    def run(self) -> None:
        """运行主窗口"""
        if hasattr(self._impl, "run"):
            self._impl.run()
        elif hasattr(self._impl, "show"):
            self._impl.show()
            # PyQt5 需要单独的 app.exec_()

    def add_log(self, message: str, level: str = "INFO") -> None:
        """添加日志消息"""
        if hasattr(self._impl, "add_log"):
            self._impl.add_log(message, level)

    def update_devices(self, devices: List[BluetoothDevice]) -> None:
        """更新设备列表"""
        if hasattr(self._impl, "update_devices"):
            self._impl.update_devices(devices)