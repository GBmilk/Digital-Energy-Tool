"""单个数字组合分析卡片控件（主题感知）。"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import CardWidget, CaptionLabel, BodyLabel

from core.energy_analyzer import CombinationResult
from core.energy_mapping import LEVELS
from .style_helper import LEVEL_COLORS, nature_color, combo_card_style, ThemeAwareWidget


class StarCard(CardWidget, ThemeAwareWidget):
    """展示一个两位数字组合的分析结果。

    布局：左侧数字（大字，属性色），中间星名/属性/等级，右侧说明。
    """

    def __init__(self, combo: CombinationResult, parent=None) -> None:
        super().__init__(parent)
        self.combo = combo
        self.setObjectName("comboCard")
        self.setFixedHeight(92)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.enable_theme_awareness(self, self._refresh_theme)
        self._refresh_theme()

        color = nature_color(combo.nature)
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 10, 18, 10)
        root.setSpacing(18)

        # 数字（保持原有字体风格）
        self.number_label = QLabel(combo.number, self)
        self.number_label.setFixedWidth(72)
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setObjectName("comboNumber")
        root.addWidget(self.number_label)

        # 中间信息
        info = QVBoxLayout()
        info.setSpacing(3)
        self.star_label = BodyLabel(combo.star, self)
        self.star_label.setObjectName("comboStar")
        info.addWidget(self.star_label)

        self.meta_label = CaptionLabel(
            f"属性：{combo.nature}    等级：{combo.level}", self
        )
        self.meta_label.setObjectName("comboMeta")
        info.addWidget(self.meta_label)
        root.addLayout(info, stretch=1)

        # 等级标记（保持原有字体风格）
        self.level_label = QLabel(combo.level, self)
        self.level_label.setObjectName("comboLevel")
        self.level_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.level_label)

        # 说明
        self.desc_label = CaptionLabel(combo.description or "—", self)
        self.desc_label.setObjectName("comboDesc")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMinimumWidth(160)
        root.addWidget(self.desc_label, stretch=2)

        self._refresh_labels()

    def _refresh_theme(self) -> None:
        self.setStyleSheet(combo_card_style(self.combo.nature, self.combo.level))

    def _refresh_labels(self) -> None:
        combo = self.combo
        color = nature_color(combo.nature)
        self.number_label.setStyleSheet(
            f"#comboNumber {{ font-size: 34px; font-weight: 700; color: {color}; background: transparent; }}"
        )
        self.star_label.setStyleSheet(
            f"#comboStar {{ font-weight: 700; color: {color}; background: transparent; }}"
        )
        self.level_label.setStyleSheet(
            f"#comboLevel {{ color: {LEVEL_COLORS.get(combo.level, '#8C8C8C')}; "
            f"font-weight: 700; font-size: 18px; background: transparent; }}"
        )

    def closeEvent(self, event) -> None:
        self.disable_theme_awareness()
        super().closeEvent(event)
