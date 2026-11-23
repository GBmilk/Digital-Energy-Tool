"""历史记录页面：搜索、排序、查看、重新分析、删除、CSV 导出。"""

from __future__ import annotations

from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QTableWidgetItem, QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel, CaptionLabel, ComboBox, FluentIcon, InfoBar, InfoBarPosition,
    LineEdit, MessageBox, PrimaryPushButton, PushButton, SubtitleLabel,
    TableWidget, TitleLabel,
)

from PyQt5.QtGui import QColor, QPalette
from qfluentwidgets.common.config import qconfig

from core.energy_analyzer import AnalysisResult
from core.csv_exporter import export_history
from core.utils import app_path, load_config
from database.history_repository import HistoryRepository
from ui.detail_page import DetailDialog
from ui.widgets.style_helper import theme_colors


class HistoryPage(QWidget):
    """历史记录页面。"""

    reopenAnalysis = pyqtSignal(object)  # 重新分析时把结果发回主窗口

    def __init__(self, repo: HistoryRepository, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("historyPage")
        self.repo = repo
        self._records: list[dict] = []
        qconfig.themeChanged.connect(self._on_theme_changed)
        self._on_theme_changed()
        self._build_ui()
        self._connect_signals()
        self.refresh()

    def _on_theme_changed(self, *_args) -> None:
        c = theme_colors()
        bg = QColor("#202020" if c["text"] == "#E8E8E8" else "#F5F7FA")
        palette = self.palette()
        palette.setColor(QPalette.Window, bg)
        palette.setColor(QPalette.Base, bg)
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 32)
        root.setSpacing(16)

        title = TitleLabel("历史记录", self)
        root.addWidget(title)
        subtitle = CaptionLabel(
            "所有计算结果自动保存；查看历史时使用当时保存的原始分析结果。", self
        )
        root.addWidget(subtitle)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        self.search_edit = LineEdit(self)
        self.search_edit.setPlaceholderText("搜索输入内容 / 数字 / 评级")
        self.search_edit.setFixedWidth(280)
        toolbar.addWidget(self.search_edit)

        self.sort_combo = ComboBox(self)
        self.sort_combo.addItems([
            "按日期（最新）", "按日期（最早）",
            "按分数（高→低）", "按分数（低→高）",
        ])
        self.sort_combo.setFixedWidth(160)
        toolbar.addWidget(self.sort_combo)

        self.search_btn = PushButton("搜索", self)
        self.search_btn.setFixedWidth(90)
        toolbar.addWidget(self.search_btn)

        toolbar.addStretch(1)
        self.export_all_btn = PushButton("导出全部历史记录", self)
        toolbar.addWidget(self.export_all_btn)
        self.export_filtered_btn = PushButton("导出筛选后的记录", self)
        toolbar.addWidget(self.export_filtered_btn)
        root.addLayout(toolbar)

        # 表格
        self.table = TableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "输入内容", "数字转换", "分数", "评级", "日期",
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(360)
        root.addWidget(self.table, stretch=1)

        # 底部按钮
        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        self.view_btn = PushButton("查看详情", self)
        self.reanalyze_btn = PushButton("重新分析", self)
        self.delete_btn = PushButton("删除选中", self)
        self.clear_btn = PushButton("删除全部", self)
        bottom.addWidget(self.view_btn)
        bottom.addWidget(self.reanalyze_btn)
        bottom.addWidget(self.delete_btn)
        bottom.addWidget(self.clear_btn)
        bottom.addStretch(1)
        self.count_label = CaptionLabel("共 0 条记录", self)
        bottom.addWidget(self.count_label)
        root.addLayout(bottom)

    def _connect_signals(self) -> None:
        self.search_btn.clicked.connect(self.refresh)
        self.search_edit.returnPressed.connect(self.refresh)
        self.sort_combo.currentIndexChanged.connect(self.refresh)
        self.view_btn.clicked.connect(self.view_detail)
        self.reanalyze_btn.clicked.connect(self.reanalyze)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.clear_btn.clicked.connect(self.clear_all)
        self.table.cellDoubleClicked.connect(self._on_double_click)
        self.export_all_btn.clicked.connect(self.export_all)
        self.export_filtered_btn.clicked.connect(self.export_filtered)

    # ---------------- 数据加载 ----------------
    def refresh(self) -> None:
        keyword = self.search_edit.text().strip()
        orders = [
            "created_at DESC", "created_at ASC",
            "total_score DESC", "total_score ASC",
        ]
        order = orders[self.sort_combo.currentIndex()]
        if keyword:
            self._records = self.repo.search(keyword, order)
        else:
            self._records = self.repo.get_all(order)
        self._render_table()

    def _render_table(self) -> None:
        self.table.setRowCount(len(self._records))
        for row, rec in enumerate(self._records):
            score = "--" if rec["total_score"] is None else str(rec["total_score"])
            values = [
                str(rec["id"]), rec["raw_input"], rec["digits"],
                score, rec["rating"], rec["created_at"],
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        self.count_label.setText(f"共 {len(self._records)} 条记录")

    def _selected_record(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._records):
            self._no_selection()
            return None
        return self._records[row]

    def _no_selection(self) -> None:
        InfoBar.warning(
            "未选择记录", "请先选择一条历史记录。",
            orient=Qt.Horizontal, isClosable=True,
            position=InfoBarPosition.TOP, duration=1800, parent=self,
        )

    def _on_double_click(self, row: int, col: int) -> None:
        if 0 <= row < len(self._records):
            self.view_detail()

    # ---------------- 操作 ----------------
    def view_detail(self) -> None:
        rec = self._selected_record()
        if rec is None:
            return
        result = self.repo.get_by_id(rec["id"])
        if result is None:
            InfoBar.error(
                "读取失败", "该记录数据已损坏，无法查看。",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=2500, parent=self,
            )
            return
        dlg = DetailDialog(result, self)
        dlg.exec_()

    def reanalyze(self) -> None:
        rec = self._selected_record()
        if rec is None:
            return
        result = self.repo.get_by_id(rec["id"])
        if result is None:
            return
        self.reopenAnalysis.emit(result)

    def delete_selected(self) -> None:
        rec = self._selected_record()
        if rec is None:
            return
        box = MessageBox("删除记录", f"确定要删除记录 #{rec['id']}（{rec['raw_input']}）吗？", self)
        box.hideCancelButton()
        if box.exec_():
            self.repo.delete(rec["id"])
            self.refresh()
            InfoBar.success(
                "已删除", "历史记录已删除。",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=1800, parent=self,
            )

    def clear_all(self) -> None:
        if self.repo.count() == 0:
            InfoBar.info(
                "无需清空", "当前没有历史记录。",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=1800, parent=self,
            )
            return
        box = MessageBox("清空历史", "确定要删除全部历史记录吗？此操作不可恢复。", self)
        if box.exec_():
            self.repo.clear_all()
            self.refresh()
            InfoBar.success(
                "已清空", "全部历史记录已删除。",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=1800, parent=self,
            )

    # ---------------- CSV 导出 ----------------
    def _export(self, records: list[dict], prefix: str) -> None:
        if not records:
            InfoBar.warning(
                "无数据", "当前没有可导出的记录。",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=1800, parent=self,
            )
            return
        config = load_config()
        default_dir = app_path(config.get("paths", {}).get("default_export", "exports"))
        default_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 CSV", str(default_dir / f"{prefix}_{ts}.csv"),
            "CSV 文件 (*.csv)",
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            export_history(records, self.repo, path)
            InfoBar.success(
                "导出成功", f"已导出 {len(records)} 条记录到：{path}",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self,
            )
        except Exception as exc:
            InfoBar.error(
                "导出失败", f"错误信息：{exc}",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self,
            )

    def export_all(self) -> None:
        self._export(self.repo.get_all(), "数字能量全部历史")

    def export_filtered(self) -> None:
        self._export(self._records, "数字能量筛选记录")

    def on_history_saved(self) -> None:
        """外部保存历史后调用，自动刷新。"""
        self.refresh()
