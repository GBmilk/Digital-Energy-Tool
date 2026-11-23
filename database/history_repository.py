"""历史记录数据仓库。

保存每次计算的完整分析结果（JSON 快照），查看历史时不重新计算、
不覆盖原始数据。
"""

from __future__ import annotations

import json
from typing import List

from core.energy_analyzer import AnalysisResult
from core.utils import logger
from database.database_manager import DatabaseManager


class HistoryRepository:
    """历史记录的数据访问层。"""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        self.db = db or DatabaseManager()

    def save(self, result: AnalysisResult) -> int:
        """保存一次分析结果，返回新记录 ID。"""
        try:
            result_json = json.dumps(result.to_dict(), ensure_ascii=False)
            cursor = self.db.execute(
                """
                INSERT INTO history
                    (raw_input, digits, total_score, rating,
                     auspicious_count, inauspicious_count, unrated_count,
                     result_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.raw_input,
                    result.digits,
                    result.total_score,
                    result.rating,
                    result.auspicious_count,
                    result.inauspicious_count,
                    result.unrated_count + result.unmatched_count,
                    result_json,
                    result.created_at,
                ),
            )
            return cursor.lastrowid or 0
        except Exception as exc:
            logger.error("保存历史记录失败: %s", exc)
            return 0

    def get_all(self, order: str = "created_at DESC") -> List[dict]:
        """获取全部历史记录摘要。"""
        allowed = {"created_at DESC", "created_at ASC", "total_score DESC",
                   "total_score ASC", "id DESC", "id ASC"}
        if order not in allowed:
            order = "created_at DESC"
        rows = self.db.query(
            f"SELECT id, raw_input, digits, total_score, rating, "
            f"auspicious_count, inauspicious_count, unrated_count, created_at "
            f"FROM history ORDER BY {order}"
        )
        return [self._row_to_dict(row) for row in rows]

    def search(self, keyword: str, order: str = "created_at DESC") -> List[dict]:
        """按原始输入或转换数字搜索历史记录。"""
        allowed = {"created_at DESC", "created_at ASC", "total_score DESC",
                   "total_score ASC"}
        if order not in allowed:
            order = "created_at DESC"
        pattern = f"%{keyword}%"
        rows = self.db.query(
            f"SELECT id, raw_input, digits, total_score, rating, "
            f"auspicious_count, inauspicious_count, unrated_count, created_at "
            f"FROM history WHERE raw_input LIKE ? OR digits LIKE ? "
            f"OR rating LIKE ? ORDER BY {order}",
            (pattern, pattern, pattern),
        )
        return [self._row_to_dict(row) for row in rows]

    def get_by_id(self, record_id: int) -> AnalysisResult | None:
        """根据 ID 获取完整的分析结果（从 JSON 还原，不重新计算）。"""
        row = self.db.query_one(
            "SELECT result_json FROM history WHERE id = ?", (record_id,)
        )
        if not row:
            return None
        try:
            data = json.loads(row["result_json"])
            return AnalysisResult.from_dict(data)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.error("历史记录 %s 数据损坏: %s", record_id, exc)
            return None

    def delete(self, record_id: int) -> bool:
        """删除单条记录。"""
        try:
            self.db.execute("DELETE FROM history WHERE id = ?", (record_id,))
            return True
        except Exception as exc:
            logger.error("删除历史记录失败: %s", exc)
            return False

    def clear_all(self) -> bool:
        """清空全部历史记录。"""
        try:
            self.db.execute("DELETE FROM history")
            # 重置自增 ID
            self.db.execute(
                "DELETE FROM sqlite_sequence WHERE name = 'history'"
            )
            return True
        except Exception as exc:
            logger.error("清空历史记录失败: %s", exc)
            return False

    def count(self) -> int:
        row = self.db.query_one("SELECT COUNT(*) AS n FROM history")
        return row["n"] if row else 0

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "id": row["id"],
            "raw_input": row["raw_input"],
            "digits": row["digits"],
            "total_score": row["total_score"],
            "rating": row["rating"],
            "auspicious_count": row["auspicious_count"],
            "inauspicious_count": row["inauspicious_count"],
            "unrated_count": row["unrated_count"],
            "created_at": row["created_at"],
        }
