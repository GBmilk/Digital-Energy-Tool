"""主题感知的滚动区域：背景色随浅色/深色模式自动切换。"""

from __future__ import annotations

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import ScrollArea
from qfluentwidgets.common.config import qconfig

from .style_helper import theme_colors


class ThemedScrollArea(ScrollArea):
    """带主题感知背景的 ScrollArea。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        qconfig.themeChanged.connect(self._refresh_background)
        self._refresh_background()

    def _refresh_background(self, *_args) -> None:
        c = theme_colors()
        bg = QColor("#202020" if c["text"] == "#E8E8E8" else "#F5F7FA")
        # 设置视口与自身的背景 palette
        palette = self.viewport().palette()
        palette.setColor(QPalette.Window, bg)
        palette.setColor(QPalette.Base, bg)
        self.viewport().setPalette(palette)
        self.viewport().setAutoFillBackground(True)
        own = self.palette()
        own.setColor(QPalette.Window, bg)
        own.setColor(QPalette.Base, bg)
        self.setPalette(own)
        self.setAutoFillBackground(True)

        # 显式覆盖 qfluentwidgets 的应用级 QSS 背景
        hex_bg = bg.name()
        for target in (self, self.viewport(), self.widget()):
            if target is None:
                continue
            target.setStyleSheet(
                f"{target.metaObject().className()} {{ background: {hex_bg} !important; border: none; }}"
            )

    def closeEvent(self, event) -> None:
        try:
            qconfig.themeChanged.disconnect(self._refresh_background)
        except (TypeError, RuntimeError):
            pass
        super().closeEvent(event)
