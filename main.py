"""数字能量工具 —— 程序入口。

基于 Python 3.12.3 + PyQt5 + qfluentwidgets 的 Windows 桌面应用。
启动方式：python main.py
"""

from __future__ import annotations

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from core.utils import APP_ROOT, ensure_dirs, load_config, logger
from ui.main_window import MainWindow


def setup_qfluent_config() -> None:
    """把 qfluentwidgets 的配置与字体设置隔离到独立文件。

    qfluentwidgets 默认把配置写在 CWD 的 config/config.json，会与本软件的
    配置文件冲突并覆盖主题、评分规则等内容。这里改为独立文件，并全局
    强制使用微软雅黑（M 号字体），避免默认 Segoe UI 被系统替换为等线。
    """
    from qfluentwidgets.common.config import qconfig
    from qfluentwidgets.common.font import setFontFamilies

    qconfig.file = APP_ROOT / "config" / "qfluent_config.json"
    qconfig.load()
    # 全局字体：微软雅黑；qfluentwidgets 会据此渲染所有 Fluent 控件
    setFontFamilies(["Microsoft YaHei"], save=True)
    # 主题以本软件配置为准，避免 qfluentwidgets 独立配置与软件设置不同步
    from qfluentwidgets import Theme
    from qfluentwidgets.common.config import qconfig as _qcfg
    _theme = {"light": Theme.LIGHT, "dark": Theme.DARK, "auto": Theme.AUTO}.get(
        load_config().get("theme", "light"), Theme.LIGHT
    )
    _qcfg.set(_qcfg.themeMode, _theme, save=False)


def check_dependencies() -> None:
    """启动前检查必需依赖，缺失时给出明确中文说明。"""
    missing: list[str] = []
    try:
        import PyQt5  # noqa: F401
    except ImportError:
        missing.append("PyQt5")
    try:
        import qfluentwidgets  # noqa: F401
    except ImportError:
        missing.append("PyQt-Fluent-Widgets (qfluentwidgets)")
    try:
        import PIL  # noqa: F401
    except ImportError:
        missing.append("Pillow")
    if missing:
        msg = (
            "缺少必要的依赖库，请先安装：\n\n"
            + "\n".join(f"  - {name}" for name in missing)
            + "\n\n安装命令：\n"
            "  python -m pip install -r requirements.txt\n"
        )
        print(msg)
        try:
            from PyQt5.QtWidgets import QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "依赖缺失", msg)
        except Exception:
            pass
        sys.exit(1)


def main() -> int:
    check_dependencies()

    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("数字能量工具")
    app.setApplicationDisplayName("数字能量工具")

    # 确保目录结构存在 + 初始化配置
    ensure_dirs()
    load_config()
    setup_qfluent_config()
    # 应用级基础字体：微软雅黑 M 号（14px），qfluentwidgets 各控件在 QSS 中
    # 也使用同一字体族；数字组合评定等核心数据展示使用各自独立的字号样式。
    from PyQt5.QtGui import QFont
    base_font = QFont("Microsoft YaHei")
    base_font.setPixelSize(14)
    app.setFont(base_font)
    # 设置应用图标
    from core.app_icon import get_app_icon
    app.setWindowIcon(get_app_icon())

    try:
        window = MainWindow()
        window.show()
        logger.info("数字能量工具启动成功")
        return app.exec_()
    except Exception as exc:
        logger.exception("程序启动失败: %s", exc)
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                None, "启动失败",
                f"程序启动时出现错误：\n{exc}\n\n请查看 data/app.log 获取详细信息。",
            )
        except Exception:
            print(f"程序启动失败: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
