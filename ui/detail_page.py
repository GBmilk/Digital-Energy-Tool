"""历史详情对话框：展示某条历史记录的完整分析结果（只读快照）。"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel, CaptionLabel, FluentIcon, MessageBox, PushButton, SubtitleLabel,
)

from core.energy_analyzer import AnalysisResult
from ui.widgets.energy_card import EnergyInfoCard
from ui.widgets.score_card import ScoreCard
from ui.widgets.star_card import StarCard


class DetailDialog(QDialog):
    """显示完整分析结果，数据来自历史 JSON 快照。"""

    def __init__(self, result: AnalysisResult, parent=None) -> None:
        super().__init__(parent)
        self.result = result
        self.setWindowTitle("历史记录详情")
        self.setMinimumSize(760, 640)
        self.resize(860, 720)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        title = SubtitleLabel(f"分析详情（{result.created_at}）", self)
        root.addWidget(title)

        self.score_card = ScoreCard(self)
        root.addWidget(self.score_card)

        self.info_card = EnergyInfoCard(self)
        root.addWidget(self.info_card)

        combo_title = BodyLabel(
            f"数字组合分析（共 {len(result.combinations)} 组）", self
        )
        root.addWidget(combo_title)

        # 组合列表放在可滚动区域
        from qfluentwidgets import ScrollArea
        scroll = ScrollArea(self)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 8, 0)
        container_layout.setSpacing(8)
        container_layout.setAlignment(Qt.AlignTop)
        for combo in result.combinations:
            container_layout.addWidget(StarCard(combo, container))
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(220)
        root.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = PushButton("关闭", self)
        close_btn.setFixedWidth(110)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        # 填充数据
        self.score_card.set_data(result)
        self.info_card.set_data(
            raw=result.raw_input,
            digits=result.digits,
            length=len(result.digits),
            combo_count=len(result.combinations),
            time=result.created_at,
        )
