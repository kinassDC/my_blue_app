"""
日志视图组件

显示应用程序日志的UI组件。
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum

from PyQt5.QtWidgets import (
    QTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QLineEdit,
    QMenu, QAction, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QFont

from src.utils.logger import Logger


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogView(QWidget):
    """
    日志视图组件

    提供日志显示、过滤、搜索、导出等功能。
    """

    # 信号定义
    log_cleared = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化日志视图

        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.logger = Logger.get_logger(__name__)

        # 日志设置
        self._max_lines = 10000  # 最大行数
        self._auto_scroll = True  # 自动滚动
        self._show_timestamp = True  # 显示时间戳
        self._show_level = True  # 显示日志级别

        # 日志颜色映射
        self._level_colors = {
            LogLevel.DEBUG: QColor(150, 150, 150),
            LogLevel.INFO: QColor(0, 0, 0),
            LogLevel.WARNING: QColor(200, 100, 0),
            LogLevel.ERROR: QColor(200, 0, 0),
            LogLevel.CRITICAL: QColor(150, 0, 50)
        }

        # 初始化UI
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 日志文本框
        self._text_edit = QTextEdit()
        self._setup_text_edit()
        layout.addWidget(self._text_edit)

        # 搜索栏
        search_bar = self._create_search_bar()
        layout.addWidget(search_bar)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)

        # 日志级别过滤
        self._level_filter = QComboBox()
        self._level_filter.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self._level_filter.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(QLabel("级别:"))
        layout.addWidget(self._level_filter)

        layout.addStretch()

        # 清空按钮
        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self.clear)
        layout.addWidget(clear_button)

        # 导出按钮
        export_button = QPushButton("导出")
        export_button.clicked.connect(self._on_export)
        layout.addWidget(export_button)

        # 设置按钮
        settings_button = QPushButton("设置")
        settings_button.clicked.connect(self._on_settings)
        layout.addWidget(settings_button)

        return toolbar

    def _setup_text_edit(self) -> None:
        """设置文本编辑框"""
        self._text_edit.setReadOnly(True)
        self._text_edit.setLineWrapMode(QTextEdit.NoWrap)

        # 设置字体
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)
        self._text_edit.setFont(font)

        # 设置右键菜单
        self._text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self._text_edit.customContextMenuRequested.connect(self._on_context_menu)

    def _create_search_bar(self) -> QWidget:
        """创建搜索栏"""
        search_bar = QWidget()
        layout = QHBoxLayout(search_bar)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("搜索:"))

        self._search_input = QLineEdit()
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.setPlaceholderText("输入关键词搜索...")
        layout.addWidget(self._search_input)

        # 搜索选项
        self._case_sensitive = QPushButton("Aa")
        self._case_sensitive.setCheckable(True)
        self._case_sensitive.setMaximumWidth(30)
        self._case_sensitive.setToolTip("区分大小写")
        layout.addWidget(self._case_sensitive)

        return search_bar

    # ==================== 日志操作 ====================

    def append(self, message: str, level: str = "INFO") -> None:
        """
        添加日志消息

        Args:
            message: 日志消息
            level: 日志级别
        """
        try:
            log_level = LogLevel(level)
        except ValueError:
            log_level = LogLevel.INFO

        # 构建日志文本
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_str = f"[{level}]"

        if self._show_timestamp and self._show_level:
            log_text = f"[{timestamp}] {level_str} {message}"
        elif self._show_timestamp:
            log_text = f"[{timestamp}] {message}"
        elif self._show_level:
            log_text = f"{level_str} {message}"
        else:
            log_text = message

        # 获取当前光标位置
        cursor = self._text_edit.textCursor()

        # 移动到末尾
        cursor.movePosition(QTextCursor.End)

        # 设置颜色
        char_format = QTextCharFormat()
        char_format.setForeground(self._level_colors.get(log_level, QColor(0, 0, 0)))
        cursor.setCharFormat(char_format)

        # 插入文本
        cursor.insertText(log_text + "\n")

        # 限制行数
        self._limit_lines()

        # 自动滚动
        if self._auto_scroll:
            self._scroll_to_bottom()

    def clear(self) -> None:
        """清空日志"""
        self._text_edit.clear()
        self.log_cleared.emit()

    def _limit_lines(self) -> None:
        """限制日志行数"""
        document = self._text_edit.document()
        if document.blockCount() > self._max_lines:
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(
                QTextCursor.NextBlock,
                QTextCursor.KeepAnchor,
                document.blockCount() - self._max_lines
            )
            cursor.removeSelectedText()

    def _scroll_to_bottom(self) -> None:
        """滚动到底部"""
        scrollbar = self._text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ==================== 搜索 ====================

    def _on_search_changed(self, text: str) -> None:
        """搜索文本改变事件"""
        # TODO: 实现日志搜索高亮
        pass

    def _on_filter_changed(self, level: str) -> None:
        """日志级别过滤改变事件"""
        # TODO: 实现日志级别过滤
        pass

    # ==================== 导出 ====================

    def _on_export(self) -> None:
        """导出日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._text_edit.toPlainText())
                self.logger.info(f"日志已导出到: {file_path}")
            except Exception as e:
                self.logger.error(f"导出日志失败: {e}")

    # ==================== 设置 ====================

    def _on_settings(self) -> None:
        """设置菜单"""
        menu = QMenu(self)

        # 自动滚动
        auto_scroll_action = QAction("自动滚动", self)
        auto_scroll_action.setCheckable(True)
        auto_scroll_action.setChecked(self._auto_scroll)
        auto_scroll_action.triggered.connect(self._toggle_auto_scroll)
        menu.addAction(auto_scroll_action)

        # 显示时间戳
        timestamp_action = QAction("显示时间戳", self)
        timestamp_action.setCheckable(True)
        timestamp_action.setChecked(self._show_timestamp)
        timestamp_action.triggered.connect(self._toggle_timestamp)
        menu.addAction(timestamp_action)

        # 显示日志级别
        level_action = QAction("显示级别", self)
        level_action.setCheckable(True)
        level_action.setChecked(self._show_level)
        level_action.triggered.connect(self._toggle_level)
        menu.addAction(level_action)

        menu.exec_(self.mapToGlobal(self._text_edit.pos()))

    def _toggle_auto_scroll(self, checked: bool) -> None:
        """切换自动滚动"""
        self._auto_scroll = checked

    def _toggle_timestamp(self, checked: bool) -> None:
        """切换时间戳显示"""
        self._show_timestamp = checked

    def _toggle_level(self, checked: bool) -> None:
        """切换级别显示"""
        self._show_level = checked

    # ==================== 右键菜单 ====================

    def _on_context_menu(self, pos) -> None:
        """右键菜单"""
        menu = QMenu(self)

        # 复制
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self._text_edit.copy)
        menu.addAction(copy_action)

        # 全选
        select_all_action = QAction("全选", self)
        select_all_action.triggered.connect(self._text_edit.selectAll)
        menu.addAction(select_all_action)

        menu.addSeparator()

        # 清空
        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self.clear)
        menu.addAction(clear_action)

        menu.exec_(self._text_edit.mapToGlobal(pos))

    # ==================== 属性设置 ====================

    def set_max_lines(self, max_lines: int) -> None:
        """设置最大行数"""
        self._max_lines = max_lines

    def get_text(self) -> str:
        """获取所有日志文本"""
        return self._text_edit.toPlainText()

    def set_text(self, text: str) -> None:
        """设置日志文本"""
        self._text_edit.setPlainText(text)