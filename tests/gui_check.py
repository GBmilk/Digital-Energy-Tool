"""GUI 布局与交互验证脚本（离屏运行，保存各页面截图）。

运行：set QT_QPA_PLATFORM=offscreen && python tests/gui_check.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from PyQt5.QtCore import Qt
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)

    # offscreen 平台不自带字体，显式加载 Windows 中文字体以便截图显示文字
    for font_file in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"):
        if os.path.exists(font_file):
            QFontDatabase.addApplicationFont(font_file)
    app.setFont(QFont("Microsoft YaHei", 10))

    # 与真实启动一致：隔离 qfluentwidgets 配置并统一字体
    from main import setup_qfluent_config
    setup_qfluent_config()
    # 从浅色主题开始截图
    from qfluentwidgets import Theme, setTheme
    setTheme(Theme.LIGHT, save=False)
    app.processEvents()

    from ui.main_window import MainWindow
    w = MainWindow()
    w.resize(1280, 800)
    w.show()
    app.processEvents()

    shots = ROOT / "exports" / "gui_check"
    shots.mkdir(parents=True, exist_ok=True)

    pages = [
        ("analysis", w.analysis_page),
        ("mapping", w.mapping_page),
        ("history", w.history_page),
        ("settings", w.settings_page),
        ("about", w.about_page),
    ]

    # 在 analysis 页先执行一次分析
    w.analysis_page.input_edit.setText("138649")
    w.analysis_page.run_analysis()
    app.processEvents()

    for name, page in pages:
        w.switchTo(page)
        app.processEvents()
        w.grab().save(str(shots / f"{name}_light.png"))
        print(f"saved {name}_light.png")

    # 切换到深色模式截图（所有页面）
    from qfluentwidgets import Theme, setTheme
    setTheme(Theme.DARK, save=False)
    app.processEvents()
    for name, page in pages:
        w.switchTo(page)
        app.processEvents()
        w.grab().save(str(shots / f"{name}_dark.png"))
        print(f"saved {name}_dark.png")

    # 验证组合卡片数量
    cards = w.analysis_page.combo_layout.count()
    print("combo cards:", cards)
    print("score:", w.analysis_page.current_result.total_score,
          "rating:", w.analysis_page.current_result.rating)
    print("history rows:", w.history_page.table.rowCount())
    print("GUI CHECK OK")
    w.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
