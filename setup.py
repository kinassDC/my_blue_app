"""
My Blue App 安装脚本

用于打包和安装应用程序。
"""

from setuptools import setup, find_packages
from pathlib import Path


# 读取 README.md
def read_readme():
    """读取README文件内容"""
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        with open(readme_path, encoding="utf-8") as f:
            return f.read()
    return ""


# 读取版本号
def get_version():
    """从 __init__.py 读取版本号"""
    init_path = Path(__file__).parent / "src" / "__init__.py"
    if init_path.exists():
        with open(init_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"


# 读取依赖
def read_requirements():
    """读取requirements.txt"""
    requirements_path = Path(__file__).parent / "requirements.txt"
    requirements = []

    if requirements_path.exists():
        with open(requirements_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if line and not line.startswith("#"):
                    # 移除版本限制外的注释
                    if "#" in line:
                        line = line.split("#")[0].strip()
                    requirements.append(line)

    return requirements


setup(
    name="my-blue-app",
    version=get_version(),
    author="Your Name",
    author_email="your.email@example.com",
    description="一个功能完善的蓝牙设备管理工具",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/my_blue_app",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/my_blue_app/issues",
        "Source": "https://github.com/yourusername/my_blue_app",
        "Documentation": "https://github.com/yourusername/my_blue_app/wiki",
    },

    # 包配置
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    zip_safe=False,

    # Python 版本要求
    python_requires=">=3.8",

    # 依赖
    install_requires=[
        "pybluez>=0.23",
        "bleak>=0.21.0",
        "PyQt5>=5.15.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.4.0",
            "types-PyYAML>=6.0.12",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },

    # 入口点
    entry_points={
        "console_scripts": [
            "my-blue-app=main:main",
        ],
        "gui_scripts": [
            "my-blue-app-gui=main:main_gui",
        ],
    },

    # 分类信息
    classifiers=[
        # 开发状态
        "Development Status :: 3 - Alpha",

        # 目标用户
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",

        # 主题
        "Topic :: System :: Hardware",
        "Topic :: Utilities",

        # 许可证
        "License :: OSI Approved :: MIT License",

        # Python 版本
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",

        # 操作系统
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",

        # 界面
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],

    # 关键词
    keywords="bluetooth ble device manager gui cross-platform",

    # 许可证
    license="MIT",
)