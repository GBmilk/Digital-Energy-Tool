"""SQLite 数据库管理器。

负责数据库连接、表结构初始化与通用 CRUD 辅助。所有数据库异常都被
捕获并记录日志，避免数据库问题导致程序直接退出。
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from core.utils import app_path, logger


class DatabaseManager:
    """线程安全的 SQLite 连接管理器。"""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else app_path("data/history.db")
        self._local = threading.local()
        self.init_database()

    def _connect(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接。"""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False, timeout=10
            )
            conn.row_factory = sqlite3.Row
            # 开启外键约束与 WAL 模式，提升并发与稳定性
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                conn.execute("PRAGMA journal_mode = WAL")
            except sqlite3.DatabaseError:
                pass
            self._local.conn = conn
        return conn

    def init_database(self) -> None:
        """初始化数据库表结构（历史记录表与设置表）。"""
        try:
            conn = self._connect()
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_input       TEXT    NOT NULL,
                    digits          TEXT    NOT NULL,
                    total_score     INTEGER,
                    rating          TEXT    NOT NULL,
                    auspicious_count INTEGER NOT NULL DEFAULT 0,
                    inauspicious_count INTEGER NOT NULL DEFAULT 0,
                    unrated_count   INTEGER NOT NULL DEFAULT 0,
                    result_json     TEXT    NOT NULL,
                    created_at      TEXT    NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_history_created
                    ON history(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_history_score
                    ON history(total_score);

                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            conn.commit()
            logger.info("数据库初始化完成: %s", self.db_path)
        except sqlite3.DatabaseError as exc:
            logger.error("数据库初始化失败: %s", exc)
            # 尝试重建损坏的数据库
            self._try_rebuild(exc)

    def _try_rebuild(self, original_error: Exception) -> None:
        """数据库损坏时尝试备份并重建。"""
        logger.warning("尝试重建数据库: %s", original_error)
        try:
            conn = getattr(self._local, "conn", None)
            if conn is not None:
                try:
                    conn.close()
                except sqlite3.Error:
                    pass
                self._local.conn = None
            backup = self.db_path.with_suffix(".db.bak")
            if self.db_path.exists():
                self.db_path.rename(backup)
            conn = self._connect()
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_input TEXT NOT NULL, digits TEXT NOT NULL,
                    total_score INTEGER, rating TEXT NOT NULL,
                    auspicious_count INTEGER DEFAULT 0,
                    inauspicious_count INTEGER DEFAULT 0,
                    unrated_count INTEGER DEFAULT 0,
                    result_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL
                );
                """
            )
            conn.commit()
            logger.info("数据库重建成功，旧文件备份为 %s", backup)
        except Exception as exc:
            logger.error("数据库重建失败: %s", exc)

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行 SQL 并返回游标。"""
        conn = self._connect()
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """查询并返回所有行。"""
        try:
            conn = self._connect()
            return conn.execute(sql, params).fetchall()
        except sqlite3.DatabaseError as exc:
            logger.error("数据库查询失败: %s", exc)
            return []

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        """查询并返回第一行。"""
        try:
            conn = self._connect()
            return conn.execute(sql, params).fetchone()
        except sqlite3.DatabaseError as exc:
            logger.error("数据库查询失败: %s", exc)
            return None

    # ---------- 设置存取（配置采用 SQLite 数据库保存） ----------
    def get_setting(self, key: str, default: str = "") -> str:
        row = self.query_one("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except sqlite3.Error:
                pass
            self._local.conn = None
