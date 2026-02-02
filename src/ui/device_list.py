"""
设备列表组件

显示和管理蓝牙设备列表的UI组件。
"""

from typing import Optional, List, Callable
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMenu, QAction, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from src.models.device import BluetoothDevice
from src.utils.logger import Logger


class DeviceList(QWidget):
    """
    设备列表组件

    以表格形式展示蓝牙设备信息，支持选择、排序等操作。
    """

    # 信号定义
    device_selected = pyqtSignal(object)  # 设备被选中
    device_double_clicked = pyqtSignal(object)  # 设备被双击
    device_context_menu = pyqtSignal(object, object)  # 右键菜单

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化设备列表

        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.logger = Logger.get_logger(__name__)

        # 设备字典 {mac_address: row_index}
        self._device_map: dict = {}
        self._devices: List[BluetoothDevice] = []

        # 初始化UI
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 设备表格
        self._table = QTableWidget()
        self._setup_table()
        layout.addWidget(self._table)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)

        # 设备计数标签
        self._count_label = QLabel("设备数: 0")
        layout.addWidget(self._count_label)

        layout.addStretch()

        # 清空按钮
        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self.clear)
        layout.addWidget(clear_button)

        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self._on_refresh)
        layout.addWidget(refresh_button)

        return toolbar

    def _setup_table(self) -> None:
        """设置表格"""
        # 设置列
        headers = ["设备名称", "MAC地址", "信号强度", "类型", "状态"]
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)

        # 表格属性
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        self._table.verticalHeader().setVisible(False)

        # 列宽
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # 连接信号
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

    # ==================== 设备管理 ====================

    def add_device(self, device: BluetoothDevice) -> None:
        """
        添加设备到列表

        Args:
            device: 蓝牙设备
        """
        if device.mac_address in self._device_map:
            # 设备已存在，更新
            self.update_device(device)
            return

        self._devices.append(device)

        # 添加新行
        row = self._table.rowCount()
        self._table.insertRow(row)

        # 填充数据
        self._fill_row(row, device)

        # 保存映射
        self._device_map[device.mac_address] = row

        # 更新计数
        self._update_count()

        self.logger.debug(f"添加设备: {device.name}")

    def update_device(self, device: BluetoothDevice) -> None:
        """
        更新设备信息

        Args:
            device: 蓝牙设备
        """
        if device.mac_address not in self._device_map:
            return

        row = self._device_map[device.mac_address]
        self._fill_row(row, device)

        # 更新设备列表中的引用
        for i, dev in enumerate(self._devices):
            if dev.mac_address == device.mac_address:
                self._devices[i] = device
                break

        self.logger.debug(f"更新设备: {device.name}")

    def _fill_row(self, row: int, device: BluetoothDevice) -> None:
        """填充行数据"""
        # 设备名称
        name_item = QTableWidgetItem(device.name)
        name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._table.setItem(row, 0, name_item)

        # MAC地址
        mac_item = QTableWidgetItem(device.mac_address)
        mac_item.setTextAlignment(Qt.AlignCenter)
        self._table.setItem(row, 1, mac_item)

        # 信号强度
        rssi_text = f"{device.rssi} dBm ({device.signal_strength})"
        rssi_item = QTableWidgetItem(rssi_text)
        rssi_item.setTextAlignment(Qt.AlignCenter)

        # 根据信号强度设置颜色
        if device.rssi >= -50:
            rssi_item.setBackground(QColor(200, 255, 200))
        elif device.rssi >= -70:
            rssi_item.setBackground(QColor(255, 255, 200))
        elif device.rssi >= -90:
            rssi_item.setBackground(QColor(255, 220, 150))
        else:
            rssi_item.setBackground(QColor(255, 200, 200))

        self._table.setItem(row, 2, rssi_item)

        # 设备类型
        type_item = QTableWidgetItem(device.device_type)
        type_item.setTextAlignment(Qt.AlignCenter)
        self._table.setItem(row, 3, type_item)

        # 连接状态
        status_text = "已连接" if device.connected else "未连接"
        status_item = QTableWidgetItem(status_text)
        status_item.setTextAlignment(Qt.AlignCenter)

        if device.connected:
            status_item.setBackground(QColor(200, 230, 255))

        self._table.setItem(row, 4, status_item)

    def remove_device(self, mac_address: str) -> None:
        """
        从列表中移除设备

        Args:
            mac_address: 设备MAC地址
        """
        if mac_address not in self._device_map:
            return

        row = self._device_map[mac_address]
        self._table.removeRow(row)

        # 更新映射
        del self._device_map[mac_address]
        self._device_map = {
            mac: r if r < row else r - 1
            for mac, r in self._device_map.items()
        }

        # 更新设备列表
        self._devices = [d for d in self._devices if d.mac_address != mac_address]

        self._update_count()

    def get_selected_device(self) -> Optional[BluetoothDevice]:
        """
        获取当前选中的设备

        Returns:
            选中的蓝牙设备，无选中返回None
        """
        row = self._table.currentRow()
        if row < 0 or row >= len(self._devices):
            return None
        return self._devices[row]

    def clear(self) -> None:
        """清空设备列表"""
        self._table.setRowCount(0)
        self._device_map.clear()
        self._devices.clear()
        self._update_count()

    def get_all_devices(self) -> List[BluetoothDevice]:
        """获取所有设备"""
        return self._devices.copy()

    def _update_count(self) -> None:
        """更新设备计数"""
        self._count_label.setText(f"设备数: {len(self._devices)}")

    # ==================== 事件处理 ====================

    def _on_selection_changed(self) -> None:
        """选择改变事件"""
        device = self.get_selected_device()
        self.device_selected.emit(device)

    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """项目双击事件"""
        device = self.get_selected_device()
        self.device_double_clicked.emit(device)

    def _on_context_menu(self, pos) -> None:
        """右键菜单事件"""
        device = self.get_selected_device()
        if not device:
            return

        menu = QMenu(self)

        # 连接/断开操作
        if device.connected:
            connect_action = QAction("断开连接", self)
            connect_action.triggered.connect(lambda: self._on_disconnect(device))
            menu.addAction(connect_action)
        else:
            connect_action = QAction("连接", self)
            connect_action.triggered.connect(lambda: self._on_connect(device))
            menu.addAction(connect_action)

        menu.addSeparator()

        # 复制MAC地址
        copy_action = QAction("复制MAC地址", self)
        copy_action.triggered.connect(lambda: self._on_copy_mac(device))
        menu.addAction(copy_action)

        # 设备信息
        info_action = QAction("设备详情", self)
        info_action.triggered.connect(lambda: self._on_show_info(device))
        menu.addAction(info_action)

        menu.addSeparator()

        # 移除设备
        remove_action = QAction("移除", self)
        remove_action.triggered.connect(lambda: self.remove_device(device.mac_address))
        menu.addAction(remove_action)

        menu.exec_(self._table.mapToGlobal(pos))

    def _on_connect(self, device: BluetoothDevice) -> None:
        """连接设备"""
        self.device_context_menu.emit(device, "connect")

    def _on_disconnect(self, device: BluetoothDevice) -> None:
        """断开设备"""
        self.device_context_menu.emit(device, "disconnect")

    def _on_copy_mac(self, device: BluetoothDevice) -> None:
        """复制MAC地址"""
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(device.mac_address)
        self.logger.info(f"已复制MAC地址: {device.mac_address}")

    def _on_show_info(self, device: BluetoothDevice) -> None:
        """显示设备详情"""
        self.device_context_menu.emit(device, "info")

    def _on_refresh(self) -> None:
        """刷新设备列表"""
        # 触发刷新信号
        self.device_context_menu.emit(None, "refresh")