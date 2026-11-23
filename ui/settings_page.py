"""设置页面：主题、路径、数据管理（精简版，关于已独立成页）。"""

from __future__ import annotations

import json

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QLineEdit, QVBoxLayout, QWidget,
)
from qfluentwidgets import (
    CaptionLabel, CardWidget, ComboBox, InfoBar, InfoBarPosition,
    MessageBox, PushButton, SubtitleLabel, TitleLabel,
)

from core.utils import DEFAULT_CONFIG, load_config, save_config
from ui.widgets.style_helper import theme_colors, ThemeAwareWidget
from ui.widgets.themed_scroll_area import ThemedScrollArea


class SettingsPage(ThemedScrollArea, ThemeAwareWidget):
    """设置页面。修改立即保存到 JSON 与 SQLite。"""

    settingsChanged = pyqtSignal(dict)
    clearHistoryRequested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.config = load_config()

        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("settingsScrollWidget")
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        self.enable_theme_awareness(self, self._refresh_theme)

        root = QVBoxLayout(self.scroll_widget)
        root.setContentsMargins(36, 28, 36, 40)
        root.setSpacing(20)
        root.setAlignment(Qt.AlignTop)

        root.addWidget(TitleLabel("设置", self.scroll_widget))
        root.addWidget(CaptionLabel(
            "管理界面主题、存储位置与历史数据。", self.scroll_widget
        ))

        self._build_theme_section(root)
        self._build_path_section(root)
        self._build_data_section(root)
        self._refresh_theme()

    def _build_theme_section(self, root: QVBoxLayout) -> None:
        card = CardWidget(self.scroll_widget)
        card.setObjectName("settingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(SubtitleLabel("外观主题", card))

        row = QHBoxLayout()
        self.theme_combo = ComboBox(card)
        self.theme_combo.addItems(["浅色模式", "深色模式", "跟随系统"])
        theme = self.config.get("theme", "light")
        self.theme_combo.setCurrentIndex({"light": 0, "dark": 1, "auto": 2}.get(theme, 0))
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        row.addWidget(CaptionLabel("界面主题：", card))
        row.addWidget(self.theme_combo)
        row.addStretch(1)
        layout.addLayout(row)
        root.addWidget(card)

    def _build_path_section(self, root: QVBoxLayout) -> None:
        card = CardWidget(self.scroll_widget)
        card.setObjectName("settingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(SubtitleLabel("存储与导出位置", card))

        paths = self.config.get("paths", {})
        self.path_edits: dict[str, QLineEdit] = {}
        path_fields = [
            ("history_db", "历史记录数据库"),
            ("default_export", "默认导出目录"),
            ("default_image_save", "详情图默认保存目录"),
        ]
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        for row_idx, (key, label) in enumerate(path_fields):
            grid.addWidget(CaptionLabel(label, card), row_idx, 0)
            edit = QLineEdit(str(paths.get(key, "")), card)
            edit.setMinimumWidth(320)
            self.path_edits[key] = edit
            grid.addWidget(edit, row_idx, 1)
            browse_btn = PushButton("浏览", card)
            browse_btn.clicked.connect(lambda _, k=key: self._browse_path(k))
            grid.addWidget(browse_btn, row_idx, 2)
        layout.addLayout(grid)

        btn_row = QHBoxLayout()
        save_btn = PushButton("保存路径设置", card)
        save_btn.clicked.connect(self._save_paths)
        btn_row.addWidget(save_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        root.addWidget(card)

    def _build_data_section(self, root: QVBoxLayout) -> None:
        card = CardWidget(self.scroll_widget)
        card.setObjectName("settingsCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(SubtitleLabel("数据管理", card))
        layout.addStretch(1)

        clear_btn = PushButton("清除历史记录", card)
        clear_btn.clicked.connect(self._clear_history)
        layout.addWidget(clear_btn)

        reset_btn = PushButton("恢复默认设置", card)
        reset_btn.clicked.connect(self._reset_settings)
        layout.addWidget(reset_btn)
        root.addWidget(card)

    def _browse_path(self, key: str) -> None:
        edit = self.path_edits[key]
        if key == "history_db":
            path, _ = QFileDialog.getSaveFileName(
                self, "选择数据库文件", edit.text(), "数据库文件 (*.db)"
            )
        else:
            path = QFileDialog.getExistingDirectory(self, "选择目录", edit.text())
        if path:
            edit.setText(path)

    def _refresh_theme(self) -> None:
        c = theme_colors()
        self.setStyleSheet(f"""
            #settingsCard {{
                background-color: {c['card_bg']};
                border: 1px solid {c['card_border']};
                border-radius: 12px;
            }}
            QLineEdit, ComboBox {{ background-color: {'#333' if c['text'] == '#E8E8E8' else '#FFF'}; }}
        """)

    def _on_theme_changed(self, index: int) -> None:
        mapping = {0: "light", 1: "dark", 2: "auto"}
        self.config["theme"] = mapping.get(index, "light")
        save_config(self.config)
        self.settingsChanged.emit(self.config)
        InfoBar.success(
            "主题已切换", "界面主题已更新。",
            orient=Qt.Horizontal, isClosable=True,
            position=InfoBarPosition.TOP, duration=1800, parent=self,
        )

    def _save_paths(self) -> None:
        for key, edit in self.path_edits.items():
            self.config.setdefault("paths", {})[key] = edit.text().strip()
        if save_config(self.config):
            self.settingsChanged.emit(self.config)
            InfoBar.success("已保存", "路径设置已保存。",
                            orient=Qt.Horizontal, isClosable=True,
                            position=InfoBarPosition.TOP, duration=2200, parent=self)
        else:
            InfoBar.error("保存失败", "无法写入配置文件。",
                          orient=Qt.Horizontal, isClosable=True,
                          position=InfoBarPosition.TOP, duration=2200, parent=self)

    def _clear_history(self) -> None:
        box = MessageBox("清除历史记录", "确定要清除全部历史记录吗？此操作不可恢复。", self)
        if box.exec_():
            self.clearHistoryRequested.emit()
            InfoBar.success("已清除", "历史记录已清除。",
                            orient=Qt.Horizontal, isClosable=True,
                            position=InfoBarPosition.TOP, duration=2200, parent=self)

    def _reset_settings(self) -> None:
        box = MessageBox("恢复默认设置", "确定要将所有设置恢复为默认值吗？", self)
        if not box.exec_():
            return
        self.config = json.loads(json.dumps(DEFAULT_CONFIG))
        save_config(self.config)
        self.theme_combo.setCurrentIndex(0)
        for key, edit in self.path_edits.items():
            edit.setText(self.config["paths"].get(key, ""))
        self.settingsChanged.emit(self.config)
        InfoBar.success("已恢复", "设置已恢复为默认值。",
                        orient=Qt.Horizontal, isClosable=True,
                        position=InfoBarPosition.TOP, duration=2200, parent=self)

    def closeEvent(self, event) -> None:
        self.disable_theme_awareness()
        super().closeEvent(event)
