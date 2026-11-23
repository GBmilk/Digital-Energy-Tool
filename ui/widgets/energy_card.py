"""输入信息卡片控件（主题感知）。"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QLabel, QSizePolicy, QVBoxLayout
from qfluentwidgets import CardWidget, SubtitleLabel, CaptionLabel

from .style_helper import theme_colors, ThemeAwareWidget


class EnergyInfoCard(CardWidget, ThemeAwareWidget):
    """展示原始输入、转换数字、长度、组合数量、计算时间。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("infoCard")
        self.setMinimumHeight(150)
        self.enable_theme_awareness(self, self._refresh_theme)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(10)

        title = SubtitleLabel("输入信息", self)
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(6)
        self.labels: dict[str, QLabel] = {}
        fields = [
            ("原始输入", "raw"),
            ("转换后数字", "digits"),
            ("输入长度", "length"),
            ("数字组合数量", "combo_count"),
            ("计算时间", "time"),
        ]
        for row, (name, key) in enumerate(fields):
            key_label = CaptionLabel(name, self)
            key_label.setObjectName(f"infoKey_{key}")
            key_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label = QLabel("--", self)
            value_label.setObjectName(f"infoValue_{key}")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_label.setWordWrap(True)
            value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            grid.addWidget(key_label, row, 0)
            grid.addWidget(value_label, row, 1)
            self.labels[key] = value_label

        layout.addLayout(grid)
        self._refresh_theme()

    def _refresh_theme(self) -> None:
        c = theme_colors()
        self.setStyleSheet(f"""
            #infoCard {{ background-color: {c['card_bg']}; border: 1px solid {c['card_border']}; border-radius: 12px; }}
            QLabel[objectName^="infoValue"] {{ color: {c['text']}; background: transparent; }}
            CaptionLabel {{ background: transparent; }}
        """)

    def set_data(self, *, raw: str, digits: str, length: int,
                 combo_count: int, time: str) -> None:
        self.labels["raw"].setText(raw or "--")
        self.labels["digits"].setText(digits or "--")
        self.labels["length"].setText(str(length))
        self.labels["combo_count"].setText(str(combo_count))
        self.labels["time"].setText(time)

    def closeEvent(self, event) -> None:
        self.disable_theme_awareness()
        super().closeEvent(event)
