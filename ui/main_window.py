"""主窗口：FluentWindow + NavigationInterface，整合所有页面。"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStackedWidget
from qfluentwidgets import (
    FluentIcon, FluentWindow, InfoBar, InfoBarPosition, NavigationItemPosition,
    Theme, setTheme,
)

from core.app_icon import get_app_icon
from core.energy_analyzer import AnalysisResult
from core.utils import load_config, logger
from database.database_manager import DatabaseManager
from database.history_repository import HistoryRepository
from ui.about_page import AboutPage
from ui.analysis_page import AnalysisPage
from ui.history_page import HistoryPage
from ui.mapping_page import MappingPage
from ui.settings_page import SettingsPage


class MainWindow(FluentWindow):
    """软件主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("数字能量工具")
        self.setWindowIcon(get_app_icon())
        self.resize(1280, 800)
        self.setMinimumSize(1080, 680)

        # 初始化数据库与仓库
        self.db = DatabaseManager()
        self.repo = HistoryRepository(self.db)

        # 应用主题
        self._apply_theme(load_config().get("theme", "light"))

        # 创建页面
        self.analysis_page = AnalysisPage(self)
        self.history_page = HistoryPage(self.repo, self)
        self.mapping_page = MappingPage(self)
        self.settings_page = SettingsPage(self)
        self.about_page = AboutPage(self)

        # 导航栏
        self._init_navigation()

        # 信号连接
        self.analysis_page.analysisSaved.connect(self._on_analysis_saved)
        self.history_page.reopenAnalysis.connect(self._on_reopen_analysis)
        self.settings_page.settingsChanged.connect(self._on_settings_changed)
        self.settings_page.clearHistoryRequested.connect(self._on_clear_history)

        logger.info("主窗口初始化完成")

    def _init_navigation(self) -> None:
        self.addSubInterface(
            self.analysis_page, FluentIcon.EDIT, "数字分析",
            NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self.mapping_page, FluentIcon.BOOK_SHELF, "数字能量表",
            NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self.history_page, FluentIcon.HISTORY, "历史记录",
            NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self.settings_page, FluentIcon.SETTING, "设置",
            NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            self.about_page, FluentIcon.INFO, "关于",
            NavigationItemPosition.BOTTOM,
        )

    # ---------------- 主题 ----------------
    def _apply_theme(self, theme_name: str) -> None:
        mapping = {"light": Theme.LIGHT, "dark": Theme.DARK, "auto": Theme.AUTO}
        setTheme(mapping.get(theme_name, Theme.LIGHT), save=False)

    def _on_settings_changed(self, config: dict) -> None:
        self._apply_theme(config.get("theme", "light"))

    # ---------------- 历史记录 ----------------
    def _on_analysis_saved(self, result: AnalysisResult) -> None:
        try:
            record_id = self.repo.save(result)
            if record_id:
                self.history_page.on_history_saved()
        except Exception as exc:
            logger.error("保存历史记录失败: %s", exc)
            InfoBar.error(
                "历史记录保存失败", str(exc),
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=2500, parent=self,
            )

    def _on_reopen_analysis(self, result: AnalysisResult) -> None:
        """重新分析：用历史快照的原始输入填入分析页并重新计算（使用当前规则）。"""
        self.analysis_page.input_edit.setText(result.raw_input)
        self.switchTo(self.analysis_page)
        self.analysis_page.run_analysis()

    def _on_clear_history(self) -> None:
        self.repo.clear_all()
        self.history_page.on_history_saved()

    def closeEvent(self, event) -> None:
        try:
            self.db.close()
        except Exception:
            pass
        super().closeEvent(event)
