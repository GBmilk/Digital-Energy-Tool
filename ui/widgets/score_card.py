"""综合评分卡片控件（主题感知）。"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import CardWidget, CaptionLabel, ProgressBar

from core.energy_analyzer import AnalysisResult
from .style_helper import UNRATED_COLOR, theme_colors, ThemeAwareWidget, nsimson_font


class ScoreCard(CardWidget, ThemeAwareWidget):
    """突出展示综合评分、评级、进度条与统计信息。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("scoreCard")
        self.setMinimumHeight(180)
        self.enable_theme_awareness(self, self._refresh_theme)

        root = QHBoxLayout(self)
        root.setContentsMargins(32, 20, 32, 20)
        root.setSpacing(36)

        # 左侧：分数 + 评级
        left = QVBoxLayout()
        left.setSpacing(2)
        self.title_label = CaptionLabel("数字能量综合评价", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(nsimson_font(11))
        left.addWidget(self.title_label)

        self.score_label = QLabel("--", self)
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setFont(nsimson_font(40, bold=True))
        left.addWidget(self.score_label)

        self.rating_label = QLabel("暂无评定", self)
        self.rating_label.setAlignment(Qt.AlignCenter)
        self.rating_label.setFont(nsimson_font(18, bold=True))
        left.addWidget(self.rating_label)
        root.addLayout(left)

        # 右侧：进度条 + 统计
        right = QVBoxLayout()
        right.setSpacing(14)
        self.progress = ProgressBar(self)
        self.progress.setFixedHeight(12)
        right.addWidget(self.progress)

        self.stats_label = QLabel(
            "有效组合：--    吉星组合：--    凶星组合：--    未评定组合：--", self
        )
        self.stats_label.setWordWrap(True)
        self.stats_label.setObjectName("scoreStats")
        self.stats_label.setFont(nsimson_font(11))
        right.addWidget(self.stats_label)
        root.addLayout(right, stretch=1)

        self._refresh_theme()
        self.set_no_data()

    def _refresh_theme(self) -> None:
        c = theme_colors()
        self.setStyleSheet(f"""
            #scoreCard {{ background-color: {c['card_bg']}; border: 1px solid {c['card_border']}; border-radius: 12px; }}
            #scoreStats {{ color: {c['text']}; font-family: 'NSimSun'; font-size: 15px; background: transparent; }}
            CaptionLabel {{ background: transparent; }}
        """)
        if not hasattr(self, "_last_color"):
            return
        self.score_label.setStyleSheet(
            f"font-family: 'NSimSun'; font-size: 72px; font-weight: 700; color: {self._last_color}; background: transparent;"
        )
        self.rating_label.setStyleSheet(
            f"font-family: 'NSimSun'; font-size: 28px; font-weight: 700; color: {self._last_color}; background: transparent;"
        )

    def set_no_data(self) -> None:
        self._last_color = UNRATED_COLOR
        self.score_label.setText("--")
        self.score_label.setStyleSheet(
            f"font-family: 'NSimSun'; font-size: 72px; font-weight: 700; color: {UNRATED_COLOR}; background: transparent;"
        )
        self.rating_label.setText("暂无评定")
        self.rating_label.setStyleSheet(
            f"font-family: 'NSimSun'; font-size: 28px; font-weight: 700; color: {UNRATED_COLOR}; background: transparent;"
        )
        self.progress.setValue(0)
        self.stats_label.setText(
            "有效组合：--    吉星组合：--    凶星组合：--    未评定组合：--"
        )

    def set_data(self, result: AnalysisResult) -> None:
        color = result.rating_color or UNRATED_COLOR
        self._last_color = color
        if result.total_score is None:
            self.score_label.setText("--")
            self.progress.setValue(0)
        else:
            self.score_label.setText(str(result.total_score))
            self.progress.setValue(int(result.total_score))
        self.score_label.setStyleSheet(
            f"font-family: 'NSimSun'; font-size: 72px; font-weight: 700; color: {color}; background: transparent;"
        )
        self.rating_label.setText(result.rating)
        self.rating_label.setStyleSheet(
            f"font-family: 'NSimSun'; font-size: 28px; font-weight: 700; color: {color}; background: transparent;"
        )
        self.stats_label.setText(
            f"有效组合：{result.valid_count}    "
            f"吉星组合：{result.auspicious_count}    "
            f"凶星组合：{result.inauspicious_count}    "
            f"未评定组合：{result.unrated_count + result.unmatched_count}"
        )

    def closeEvent(self, event) -> None:
        self.disable_theme_awareness()
        super().closeEvent(event)
