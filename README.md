# My Blue App - 蓝牙设备管理工具

## 项目简介

My Blue App 是一个功能完善的蓝牙设备管理工具，旨在简化蓝牙设备的发现、连接、管理和数据交互过程。本项目基于 Python 开发，支持跨平台运行，适用于桌面应用程序和嵌入式系统开发。

### 主要特性

- **设备扫描与发现**：自动扫描并发现附近的蓝牙设备
- **设备连接管理**：支持多设备同时连接与管理
- **数据传输**：稳定的蓝牙数据收发功能
- **设备信息查询**：获取蓝牙设备的详细信息（名称、MAC地址、信号强度等）
- **跨平台支持**：支持 Windows、Linux 和 macOS

## 项目架构

```
my_blue_app/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── core/              # 核心功能模块
│   │   ├── __init__.py
│   │   ├── bluetooth_manager.py    # 蓝牙管理器主类
│   │   ├── device_scanner.py       # 设备扫描模块
│   │   ├── connector.py            # 设备连接模块
│   │   └── data_handler.py         # 数据处理模块
│   ├── ui/                # 用户界面模块
│   │   ├── __init__.py
│   │   ├── main_window.py          # 主窗口
│   │   ├── device_list.py          # 设备列表组件
│   │   └── log_view.py             # 日志显示组件
│   ├── utils/             # 工具类
│   │   ├── __init__.py
│   │   ├── logger.py               # 日志工具
│   │   └── config.py               # 配置管理
│   └── models/            # 数据模型
│       ├── __init__.py
│       └── device.py               # 设备数据模型
├── tests/                  # 测试目录
│   ├── __init__.py
│   ├── test_scanner.py
│   └── test_connector.py
├── docs/                   # 文档目录
│   └── architecture.drawio           # 架构图
├── requirements.txt        # 依赖列表
├── setup.py               # 安装脚本
└── README.md              # 项目说明
```

## 蓝牙接口

### 核心接口定义

#### BluetoothManager（蓝牙管理器）

```python
class BluetoothManager:
    """蓝牙设备管理器主类"""

    def scan_devices(self, timeout: int = 10) -> List[BluetoothDevice]:
        """扫描附近的蓝牙设备
        Args:
            timeout: 扫描超时时间（秒）
        Returns:
            发现的设备列表
        """

    def connect_device(self, device_mac: str) -> bool:
        """连接指定蓝牙设备
        Args:
            device_mac: 设备MAC地址
        Returns:
            连接是否成功
        """

    def disconnect_device(self, device_mac: str) -> bool:
        """断开设备连接
        Args:
            device_mac: 设备MAC地址
        Returns:
            断开是否成功
        """

    def send_data(self, device_mac: str, data: bytes) -> bool:
        """向设备发送数据
        Args:
            device_mac: 设备MAC地址
            data: 要发送的数据
        Returns:
            发送是否成功
        """

    def receive_data(self, device_mac: str, size: int = 1024) -> bytes:
        """从设备接收数据
        Args:
            device_mac: 设备MAC地址
            size: 接收数据大小
        Returns:
            接收到的数据
        """
```

#### BluetoothDevice（设备数据模型）

```python
@dataclass
class BluetoothDevice:
    """蓝牙设备信息模型"""
    name: str              # 设备名称
    mac_address: str       # MAC地址
    rssi: int              # 信号强度
    device_class: str      # 设备类别
    connected: bool = False # 连接状态
```

### 支持的蓝牙协议

- **BLE (Bluetooth Low Energy)**：低功耗蓝牙设备支持
- **Classic Bluetooth**：经典蓝牙设备支持
- **BLE GATT**：通用属性协议支持

## 安装说明

### 环境要求

- Python 3.8+
- 操作系统：Windows / Linux / macOS
- 蓝牙适配器（支持BLE 4.0+）

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/yourusername/my_blue_app.git
cd my_blue_app

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行程序
python src/main.py
```

### 依赖库

- `pybluez` - 蓝牙通信核心库
- `bleak` - BLE低功耗蓝牙支持
- `PyQt5` / `tkinter` - GUI界面
- `asyncio` - 异步IO支持
- `pyyaml` - 配置文件解析

## 使用示例

```python
from src.core.bluetooth_manager import BluetoothManager

# 创建管理器实例
manager = BluetoothManager()

# 扫描设备
devices = manager.scan_devices(timeout=10)
for device in devices:
    print(f"发现设备: {device.name} ({device.mac_address})")

# 连接设备
if devices:
    success = manager.connect_device(devices[0].mac_address)
    if success:
        print("连接成功！")
        # 发送数据
        manager.send_data(devices[0].mac_address, b"Hello Bluetooth!")
```

## 开发计划

- [ ] 完善核心蓝牙功能模块
- [ ] 实现图形用户界面
- [ ] 添加设备配对功能
- [ ] 支持数据持久化存储
- [ ] 添加单元测试
- [ ] 性能优化与稳定性改进

## 许可证

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 项目地址：https://github.com/yourusername/my_blue_app
- 问题反馈：https://github.com/yourusername/my_blue_app/issues
