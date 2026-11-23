"""真实窗口深色模式截图验证（仅用于开发检查）。"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    QApplication.setAttribute(0x0200, True)  # AA_EnableHighDpiScaling
    app = QApplication(sys.argv)
    from main import setup_qfluent_config
    setup_qfluent_config()

    from qfluentwidgets import Theme, setTheme
    setTheme(Theme.DARK, save=False)

    from ui.main_window import MainWindow
    w = MainWindow()
    w.show()

    def capture():
        from pathlib import Path
        out = ROOT / "exports" / "gui_check"
        out.mkdir(parents=True, exist_ok=True)
        w.grab().save(str(out / "real_dark_analysis.png"))
        w.switchTo(w.mapping_page)
        app.processEvents()
        w.grab().save(str(out / "real_dark_mapping.png"))
        w.switchTo(w.settings_page)
        app.processEvents()
        w.grab().save(str(out / "real_dark_settings.png"))
        print("CAPTURED")
        w.close()

    QTimer.singleShot(1500, capture)
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
