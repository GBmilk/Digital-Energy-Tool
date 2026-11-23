"""关于页面：软件名称、版本、图标与简介。"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import CaptionLabel, CardWidget, SubtitleLabel, TitleLabel

from core.app_icon import get_app_icon
from core.utils import load_config
from ui.widgets.style_helper import theme_colors, ThemeAwareWidget
from ui.widgets.themed_scroll_area import ThemedScrollArea


class AboutPage(ThemedScrollArea, ThemeAwareWidget):
    """独立关于页面。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("aboutPage")
        self.enable_theme_awareness(self, self._refresh_theme)

        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("aboutScrollWidget")
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)

        root = QVBoxLayout(self.scroll_widget)
        root.setContentsMargins(36, 40, 36, 40)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignTop)

        root.addWidget(TitleLabel("关于", self.scroll_widget))

        card = CardWidget(self.scroll_widget)
        card.setObjectName("aboutCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(18)

        # 图标 + 名称 + 版本
        header = QHBoxLayout()
        icon_label = QLabel(card)
        icon_label.setObjectName("aboutIcon")
        icon_label.setPixmap(get_app_icon().pixmap(112, 112))
        header.addWidget(icon_label)

        info = QVBoxLayout()
        info.setSpacing(8)
        name = SubtitleLabel("数字能量工具", card)
        name.setObjectName("aboutName")
        info.addWidget(name)

        config = load_config()
        version = CaptionLabel(f"版本 v{config.get('version', '1.0.0')}", card)
        version.setObjectName("aboutVersion")
        info.addWidget(version)

        tech = CaptionLabel("基于 Python 3.12.3 · PyQt5 · qfluentwidgets", card)
        tech.setObjectName("aboutTech")
        info.addWidget(tech)
        header.addLayout(info)
        header.addStretch(1)
        layout.addLayout(header)

        # 简介
        intro = SubtitleLabel(
            "依据数字能量对应表，分析数字组合并识别四吉星与四凶星，"
            "提供支持历史记录、详情图与 CSV 导出的桌面工具。", card
        )
        intro.setObjectName("aboutIntro")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        root.addWidget(card)
        root.addStretch(1)
        self._refresh_theme()

    def _refresh_theme(self) -> None:
        c = theme_colors()
        self.scroll_widget.setStyleSheet(f"""
            QWidget#aboutScrollWidget {{ background: {'#202020' if c['text'] == '#E8E8E8' else '#F5F7FA'}; }}
            #aboutCard {{ background-color: {c['card_bg']}; border: 1px solid {c['card_border']}; border-radius: 16px; }}
            #aboutName {{ color: {c['text']}; background: transparent; }}
            #aboutVersion, #aboutTech {{ color: {c['subtext']}; background: transparent; }}
            #aboutIntro {{ color: {c['text']}; background: transparent; }}
        """)

    def closeEvent(self, event) -> None:
        self.disable_theme_awareness()
        super().closeEvent(event)
