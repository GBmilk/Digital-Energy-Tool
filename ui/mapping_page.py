"""数字能量表页面：现代卡片式布局，展示完整四吉星、四凶星映射。"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)
from qfluentwidgets import (
    CardWidget, CaptionLabel, ScrollArea, SubtitleLabel, TitleLabel, BodyLabel,
)

from core.energy_analyzer import STAR_DESCRIPTIONS
from core.energy_mapping import (
    AUSPICIOUS, AUSPICIOUS_STARS, INAUSPICIOUS, INAUSPICIOUS_STARS,
    LEVELS, get_star_level_combinations,
)
from ui.widgets.style_helper import theme_colors, ThemeAwareWidget
from ui.widgets.themed_scroll_area import ThemedScrollArea

# 星级配色：吉星从深到浅，凶星从深到浅
STAR_COLORS = {
    "天医": ("#0E7A3D", "#2AA36A"),
    "延年": ("#168A55", "#3CB87C"),
    "生气": ("#2E9E68", "#5CC99A"),
    "伏位": ("#4CAF7D", "#8FD9B4"),
    "绝命": ("#B52E2E", "#D94242"),
    "祸害": ("#C24A2E", "#E06545"),
    "五鬼": ("#A3305A", "#C94F79"),
    "六煞": ("#8E3B8E", "#B658B6"),
}


class StarPanel(CardWidget, ThemeAwareWidget):
    """单个星名的展示面板：标题、说明、四级组合网格。"""

    def __init__(self, star: str, nature: str, parent=None) -> None:
        super().__init__(parent)
        self.star = star
        self.nature = nature
        self.setObjectName("starPanel")
        self.enable_theme_awareness(self, self._refresh_theme)

        dark_color, light_color = STAR_COLORS.get(star, ("#666", "#999"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # 顶部：左侧色条 + 星名 + 属性标签 + 说明
        header = QHBoxLayout()
        bar = QFrame(self)
        bar.setFixedSize(6, 40)
        bar.setObjectName("colorBar")
        bar.setStyleSheet(
            f"#colorBar {{ background: {dark_color}; border-radius: 3px; }}"
        )
        header.addWidget(bar)

        text_area = QVBoxLayout()
        text_area.setSpacing(2)
        title_row = QHBoxLayout()
        title = SubtitleLabel(f"{star}", self)
        title.setObjectName("starTitle")
        title_row.addWidget(title)
        nature_badge = QLabel(nature, self)
        nature_badge.setObjectName("natureBadge")
        nature_badge.setStyleSheet(
            f"#natureBadge {{ color: {dark_color}; background: rgba({self._rgb(dark_color)},0.12); "
            f"border-radius: 8px; padding: 2px 10px; font-weight: 700; }}"
        )
        title_row.addWidget(nature_badge)
        title_row.addStretch(1)
        text_area.addLayout(title_row)

        desc = CaptionLabel(STAR_DESCRIPTIONS.get(star, ""), self)
        desc.setObjectName("starDesc")
        text_area.addWidget(desc)
        header.addLayout(text_area, stretch=1)
        layout.addLayout(header)

        # 四级组合：2×2 网格
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        for idx, level in enumerate(LEVELS):
            numbers = get_star_level_combinations(star, level)
            cell = QFrame(self)
            cell.setObjectName("levelCell")
            cell.setFixedHeight(52)
            cell_layout = QHBoxLayout(cell)
            cell_layout.setContentsMargins(10, 0, 10, 0)
            cell_layout.setSpacing(8)

            lv = CaptionLabel(level, cell)
            lv.setObjectName("levelName")
            lv.setFixedWidth(36)
            cell_layout.addWidget(lv)

            nums = QLabel("、".join(numbers), cell)
            nums.setObjectName("levelNumbers")
            nums.setStyleSheet(
                f"#levelNumbers {{ color: {dark_color}; font-weight: 700; font-size: 16px; background: transparent; }}"
            )
            cell_layout.addWidget(nums)
            cell_layout.addStretch(1)
            grid.addWidget(cell, idx // 2, idx % 2)
        layout.addLayout(grid)
        self._refresh_theme()

    @staticmethod
    def _rgb(hex_color: str) -> str:
        h = hex_color.lstrip("#")
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

    def _refresh_theme(self) -> None:
        c = theme_colors()
        self.setStyleSheet(f"""
            #starPanel {{ background-color: {c['card_bg']}; border: 1px solid {c['card_border']}; border-radius: 14px; }}
            #starTitle {{ color: {c['text']}; background: transparent; }}
            #starDesc {{ color: {c['subtext']}; background: transparent; }}
            #levelCell {{ background-color: {'rgba(255,255,255,0.06)' if c['text'] == '#E8E8E8' else 'rgba(0,0,0,0.03)'}; border-radius: 8px; }}
            #levelName {{ color: {c['subtext']}; background: transparent; }}
        """)

    def closeEvent(self, event) -> None:
        self.disable_theme_awareness()
        super().closeEvent(event)


class MappingPage(ThemedScrollArea, ThemeAwareWidget):
    """展示完整数字能量映射表，数据直接来自核心模块。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("mappingPage")
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("mappingScrollWidget")
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        self.enable_theme_awareness(self, self._refresh_theme)

        root = QVBoxLayout(self.scroll_widget)
        root.setContentsMargins(36, 28, 36, 40)
        root.setSpacing(20)
        root.setAlignment(Qt.AlignTop)

        self.title = TitleLabel("数字能量表", self.scroll_widget)
        root.addWidget(self.title)
        self.subtitle = CaptionLabel(
            "四吉星与四凶星的完整映射，共 8 星 × 4 级 × 2 组合 = 64 条。",
            self.scroll_widget,
        )
        root.addWidget(self.subtitle)

        self._add_section(root, "四吉星", " auspicious", AUSPICIOUS_STARS, AUSPICIOUS)
        self._add_section(root, "四凶星", " inauspicious", INAUSPICIOUS_STARS, INAUSPICIOUS)
        self._refresh_theme()

    def _add_section(self, root: QVBoxLayout, title: str, tag: str,
                     stars: tuple, nature: str) -> None:
        section = QWidget(self.scroll_widget)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(14)

        heading = SubtitleLabel(title, section)
        heading.setObjectName(f"sectionHeading{tag.strip()}")
        section_layout.addWidget(heading)

        grid = QGridLayout()
        grid.setSpacing(16)
        for i, star in enumerate(stars):
            grid.addWidget(StarPanel(star, nature, section), i // 2, i % 2)
        section_layout.addLayout(grid)
        root.addWidget(section)

    def _refresh_theme(self) -> None:
        c = theme_colors()
        self.scroll_widget.setStyleSheet(f"""
            QWidget#mappingScrollWidget {{ background: transparent; }}
            [objectName^="sectionHeading"] {{ color: {c['text']}; background: transparent; }}
        """)

    def closeEvent(self, event) -> None:
        self.disable_theme_awareness()
        super().closeEvent(event)
