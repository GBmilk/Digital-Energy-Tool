"""数字分析页面：输入、计算、评分展示、组合明细、详情图与 CSV 导出。"""

from __future__ import annotations

import os
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)
from qfluentwidgets import (
    BodyLabel, CaptionLabel, ComboBox, FluentIcon, InfoBar, InfoBarPosition, LineEdit,
    PrimaryPushButton, PushButton, SubtitleLabel, TitleLabel, CardWidget,
)

from core.alphabet_converter import is_valid_input
from core.energy_analyzer import AnalysisResult, analyze
from core import score_engine
from core.csv_exporter import export_analysis
from core.image_generator import (
    RESOLUTION_PRESETS, default_image_path, generate_detail_image,
)
from core.utils import app_path, load_config
from qfluentwidgets.common.config import qconfig
from ui.widgets.style_helper import theme_colors, nsimson_font
from ui.widgets.energy_card import EnergyInfoCard
from ui.widgets.score_card import ScoreCard
from ui.widgets.star_card import StarCard
from ui.widgets.themed_scroll_area import ThemedScrollArea


class AnalysisPage(ThemedScrollArea):
    """数字分析主页面。"""

    analysisSaved = pyqtSignal(object)  # 通知主窗口保存历史并刷新

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("analysisPage")
        self.current_result: AnalysisResult | None = None
        qconfig.themeChanged.connect(self._on_theme_changed)

        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("analysisScrollWidget")
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self.scroll_widget)
        root.setContentsMargins(36, 28, 36, 40)
        root.setSpacing(20)
        root.setAlignment(Qt.AlignTop)

        # 标题
        title = TitleLabel("数字能量分析", self.scroll_widget)
        root.addWidget(title)
        subtitle = CaptionLabel(
            "输入数字或英文字母，按数字能量规则分析相邻两位数组合。", self.scroll_widget
        )
        root.addWidget(subtitle)

        # ===== 输入卡片 =====
        input_card = CardWidget(self.scroll_widget)
        input_card.setObjectName("inputCard")
        self.input_card = input_card
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(24, 20, 24, 20)
        input_layout.setSpacing(12)

        hint = BodyLabel("请输入数字或英文字母（0-9 / A-Z / a-z）：", input_card)
        input_layout.addWidget(hint)

        input_row = QHBoxLayout()
        input_row.setSpacing(12)
        self.input_edit = LineEdit(input_card)
        self.input_edit.setPlaceholderText("例如：138649 或 ABC 或 MILK")
        self.input_edit.setFixedHeight(48)
        self.input_edit.setClearButtonEnabled(True)
        input_row.addWidget(self.input_edit, stretch=1)

        self.calc_btn = PrimaryPushButton("计算", input_card)
        self.calc_btn.setFixedHeight(48)
        self.calc_btn.setFixedWidth(120)
        input_row.addWidget(self.calc_btn)

        self.clear_btn = PushButton("清空", input_card)
        self.clear_btn.setFixedHeight(48)
        self.clear_btn.setFixedWidth(100)
        input_row.addWidget(self.clear_btn)
        input_layout.addLayout(input_row)

        status_row = QHBoxLayout()
        self.length_label = CaptionLabel("输入长度：0", input_card)
        self.convert_label = CaptionLabel("字母转换：--", input_card)
        self.validate_label = CaptionLabel("", input_card)
        status_row.addWidget(self.length_label)
        status_row.addWidget(self.convert_label)
        status_row.addWidget(self.validate_label, stretch=1)
        input_layout.addLayout(status_row)
        root.addWidget(input_card)

        # ===== 评分卡片 =====
        self.score_card = ScoreCard(self.scroll_widget)
        root.addWidget(self.score_card)

        # ===== 输入信息卡片 =====
        self.info_card = EnergyInfoCard(self.scroll_widget)
        root.addWidget(self.info_card)

        # ===== 数字组合分析卡片 =====
        combo_header = QHBoxLayout()
        combo_title = SubtitleLabel("数字组合分析", self.scroll_widget)
        combo_title.setFont(nsimson_font(14, bold=True))
        combo_title.setStyleSheet("font-family: 'NSimSun'; background: transparent;")
        combo_header.addWidget(combo_title)
        self.combo_count_label = CaptionLabel("（共 0 组）", self.scroll_widget)
        combo_header.addWidget(self.combo_count_label)
        combo_header.addStretch(1)
        root.addLayout(combo_header)

        self.combo_container = QWidget(self.scroll_widget)
        self.combo_layout = QVBoxLayout(self.combo_container)
        self.combo_layout.setContentsMargins(0, 0, 0, 0)
        self.combo_layout.setSpacing(10)
        self.combo_layout.setAlignment(Qt.AlignTop)
        root.addWidget(self.combo_container)

        # 空状态提示
        self.empty_label = BodyLabel(
            "暂无分析结果，请输入数字或字母后点击「计算」。", self.scroll_widget
        )
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setMinimumHeight(100)
        self.empty_label.setStyleSheet("color: #8C8C8C;")
        root.addWidget(self.empty_label)

        # ===== 操作按钮 =====
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self.image_btn = PushButton("生成详情图", self.scroll_widget)
        self.image_btn.setFixedHeight(42)
        btn_row.addWidget(self.image_btn)

        # 详情图清晰度选择（仅显示分辨率，不显示 DPI）
        self.resolution_combo = ComboBox(self.scroll_widget)
        self.resolution_combo.addItems(list(RESOLUTION_PRESETS.keys()))
        default_resolution = load_config().get("image", {}).get("resolution", "1080P")
        if default_resolution in RESOLUTION_PRESETS:
            self.resolution_combo.setCurrentText(default_resolution)
        self.resolution_combo.setFixedHeight(42)
        btn_row.addWidget(CaptionLabel("清晰度：", self.scroll_widget))
        btn_row.addWidget(self.resolution_combo)

        self.export_btn = PushButton("导出当前分析 CSV", self.scroll_widget)
        self.export_btn.setFixedHeight(42)
        btn_row.addWidget(self.export_btn)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

    def _connect_signals(self) -> None:
        self.input_edit.textChanged.connect(self._on_input_changed)
        self.calc_btn.clicked.connect(self.run_analysis)
        self.clear_btn.clicked.connect(self.clear_input)
        self.input_edit.returnPressed.connect(self.run_analysis)
        self.image_btn.clicked.connect(self.generate_image)
        self.export_btn.clicked.connect(self.export_csv)
        self._on_input_changed("")
        self._on_theme_changed()

    def _on_theme_changed(self, *_args) -> None:
        c = theme_colors()
        if hasattr(self, "input_card"):
            self.input_card.setStyleSheet(f"""
                #inputCard {{
                    background-color: {c['card_bg']};
                    border: 1px solid {c['card_border']};
                    border-radius: 12px;
                }}
                QLabel {{ background: transparent; }}
            """)
        if hasattr(self, "empty_label"):
            self.empty_label.setStyleSheet(f"color: {c['subtext']};")

    # ---------------- 输入处理 ----------------
    def _on_input_changed(self, text: str) -> None:
        """实时验证输入并更新长度、字母转换显示。"""
        from core.alphabet_converter import filter_invalid_chars, letters_to_digits

        cleaned = filter_invalid_chars(text)
        digits = letters_to_digits(cleaned)
        self.length_label.setText(f"输入长度：{len(cleaned)}")
        self.convert_label.setText(f"字母转换：{digits or '--'}")
        if text and not is_valid_input(text):
            self.validate_label.setText("已自动过滤非法字符")
            self.validate_label.setStyleSheet("color: #D94242;")
            # 将过滤后的内容写回（阻塞信号避免递归）
            self.input_edit.blockSignals(True)
            self.input_edit.setText(cleaned)
            self.input_edit.blockSignals(False)
        else:
            self.validate_label.setText("")
            self.validate_label.setStyleSheet("")

    def clear_input(self) -> None:
        self.input_edit.clear()
        self.current_result = None
        self.empty_label.show()
        self.combo_count_label.setText("（共 0 组）")

    # ---------------- 分析 ----------------
    def run_analysis(self) -> None:
        text = self.input_edit.text().strip()
        if not text:
            InfoBar.warning(
                "输入为空", "请先输入数字或英文字母。",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=2000, parent=self,
            )
            return
        if not is_valid_input(text):
            InfoBar.error(
                "输入包含非法字符", "只允许输入数字 0-9 与英文字母 A-Z / a-z。",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=2500, parent=self,
            )
            return

        try:
            config = load_config()
            result = analyze(text)
            score_engine.calculate_score(
                result,
                score_rules=config.get("score_rules"),
                rating_ranges=config.get("rating_ranges"),
                no_rating=config.get("no_rating"),
            )
        except Exception as exc:
            InfoBar.error(
                "分析失败", f"计算过程中出现错误：{exc}",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self,
            )
            return

        self.current_result = result
        self._render_result(result)
        self.analysisSaved.emit(result)
        InfoBar.success(
            "分析完成", f"已分析 {len(result.combinations)} 组数字组合。",
            orient=Qt.Horizontal, isClosable=True,
            position=InfoBarPosition.TOP, duration=1800, parent=self,
        )

    def _render_result(self, result: AnalysisResult) -> None:
        self.score_card.set_data(result)
        self.info_card.set_data(
            raw=result.raw_input,
            digits=result.digits,
            length=len(result.digits),
            combo_count=len(result.combinations),
            time=result.created_at,
        )

        # 清空旧卡片
        while self.combo_layout.count():
            item = self.combo_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for combo in result.combinations:
            self.combo_layout.addWidget(StarCard(combo, self.combo_container))

        self.combo_count_label.setText(f"（共 {len(result.combinations)} 组）")
        self.empty_label.hide()

    # ---------------- 详情图 ----------------
    def generate_image(self) -> None:
        if self.current_result is None:
            InfoBar.warning(
                "暂无分析结果", "请先完成一次计算。",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=2000, parent=self,
            )
            return
        default_path = default_image_path(self.current_result)
        path, _ = QFileDialog.getSaveFileName(
            self, "保存详情图", str(default_path), "PNG 图片 (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        try:
            resolution = self.resolution_combo.currentText()
            width = RESOLUTION_PRESETS.get(resolution, 1920)
            generate_detail_image(self.current_result, path, width=width)
            InfoBar.success(
                "详情图已生成", f"已保存到：{path}",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self,
            )
        except Exception as exc:
            InfoBar.error(
                "生成详情图失败", f"错误信息：{exc}",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self,
            )

    # ---------------- CSV 导出 ----------------
    def export_csv(self) -> None:
        if self.current_result is None:
            InfoBar.warning(
                "暂无分析结果", "请先完成一次计算。",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=2000, parent=self,
            )
            return
        config = load_config()
        default_dir = app_path(config.get("paths", {}).get("default_export", "exports"))
        default_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = default_dir / f"数字能量分析_{ts}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出当前分析 CSV", str(default_file), "CSV 文件 (*.csv)"
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            export_analysis(self.current_result, path)
            InfoBar.success(
                "导出成功", f"CSV 已保存到：{path}",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self,
            )
        except Exception as exc:
            InfoBar.error(
                "导出失败", f"错误信息：{exc}",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self,
            )
