"""UI 样式辅助：统一的颜色与主题感知样式表。

所有自定义卡片根据当前主题动态生成样式，并连接 qfluentwidgets 的
themeChanged 信号，在浅色/深色模式切换时自动刷新，避免"白字浅底"问题。
"""

from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget
from qfluentwidgets.common.config import qconfig, isDarkTheme

# 特定区域字体：新宋体（第一版设计），用于"数字能量综合评价"与"数字组合分析"
NSIMSON_FONT = "NSimSun"


def nsimson_font(point_size: int = 12, bold: bool = False) -> "QFont":
    """返回新宋体字体（用于能量评价与分析标题区域）。"""
    from PyQt5.QtGui import QFont
    font = QFont(NSIMSON_FONT)
    font.setPointSize(point_size)
    font.setBold(bold)
    return font


# 属性颜色
AUSPICIOUS_COLOR = "#2AA36A"
INAUSPICIOUS_COLOR = "#D94242"
UNRATED_COLOR = "#8C8C8C"

# 等级强调色（一级最深）
LEVEL_COLORS = {
    "一级": "#0E7A3D",
    "二级": "#2AA36A",
    "三级": "#6BBF94",
    "四级": "#A7D8BF",
}

# 主题感知的中性色（前景/背景）
def theme_colors() -> dict:
    """返回当前主题下的一组协调颜色。"""
    if isDarkTheme():
        return {
            "text": "#E8E8E8",
            "subtext": "#A0A0A0",
            "card_bg": "#2B2B2B",
            "card_border": "#3F3F3F",
            "info_bg": "#2B2B2B",
            "table_alt": "#292929",
        }
    return {
        "text": "#1F2937",
        "subtext": "#6B7280",
        "card_bg": "#FFFFFF",
        "card_border": "#E5E7EB",
        "info_bg": "#FFFFFF",
        "table_alt": "#FAFBFC",
    }


def nature_color(nature: str) -> str:
    if nature == "吉星":
        return AUSPICIOUS_COLOR
    if nature == "凶星":
        return INAUSPICIOUS_COLOR
    return UNRATED_COLOR


def combo_card_style(nature: str, level: str) -> str:
    """数字组合卡片样式：根据主题生成，吉绿凶红灰未评定。"""
    dark = isDarkTheme()
    color = nature_color(nature)
    if nature == "吉星":
        bg = "rgba(42,163,106,0.16)" if dark else "rgba(42,163,106,0.10)"
    elif nature == "凶星":
        bg = "rgba(217,66,66,0.16)" if dark else "rgba(217,66,66,0.10)"
    else:
        bg = "rgba(140,140,140,0.16)" if dark else "rgba(140,140,140,0.10)"
    width = 2 if level == "一级" else 1
    return f"""
        QWidget#comboCard {{
            background-color: {bg};
            border: {width}px solid {color};
            border-radius: 12px;
        }}
        QLabel {{ background: transparent; }}
    """


def page_background_style() -> str:
    """页面滚动区域背景样式（跟随主题）。"""
    bg = "#202020" if isDarkTheme() else "#F5F7FA"
    return f"""
        QWidget {{ background: {bg}; }}
        QScrollArea {{ background: {bg}; border: none; }}
    """


class ThemeAwareWidget:
    """为自定义控件提供主题切换时的样式刷新能力。

    使用方式：在自定义 QWidget 类中多重继承本类，并重写 on_theme_changed()。
    """

    def enable_theme_awareness(self, widget: QWidget, refresh_func) -> None:
        self._refresh_func = refresh_func
        self._theme_widget = widget
        qconfig.themeChanged.connect(self._on_theme_changed)

    def _on_theme_changed(self, *_args) -> None:
        try:
            self._refresh_func()
        except RuntimeError:
            pass

    def disable_theme_awareness(self) -> None:
        try:
            qconfig.themeChanged.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass
