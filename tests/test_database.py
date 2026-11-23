"""数据库与历史记录单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.energy_analyzer import analyze
from core.score_engine import calculate_score
from database.database_manager import DatabaseManager
from database.history_repository import HistoryRepository


class TestDatabase(unittest.TestCase):
    """SQLite 历史记录测试。"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "history.db"
        self.db = DatabaseManager(self.db_path)
        self.repo = HistoryRepository(self.db)

    def tearDown(self):
        self.db.close()
        self.tmpdir.cleanup()

    def _make_result(self, text: str):
        r = analyze(text)
        calculate_score(r)
        return r

    def test_save_and_count(self):
        r = self._make_result("138649")
        rid = self.repo.save(r)
        self.assertGreater(rid, 0)
        self.assertEqual(self.repo.count(), 1)

    def test_snapshot_not_recomputed(self):
        """历史记录保存当时结果，查看时不重新计算。"""
        r = self._make_result("138649")
        original_score = r.total_score
        rid = self.repo.save(r)

        loaded = self.repo.get_by_id(rid)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.total_score, original_score)
        self.assertEqual(loaded.digits, "138649")

        # 修改原对象不影响已保存快照
        r.total_score = 0
        loaded2 = self.repo.get_by_id(rid)
        self.assertEqual(loaded2.total_score, original_score)

    def test_get_all_order(self):
        self.repo.save(self._make_result("138649"))
        self.repo.save(self._make_result("121212"))
        rows = self.repo.get_all("created_at DESC")
        self.assertEqual(len(rows), 2)
        rows_asc = self.repo.get_all("total_score ASC")
        scores = [r["total_score"] for r in rows_asc]
        self.assertEqual(scores, sorted(scores))

    def test_search(self):
        self.repo.save(self._make_result("138649"))
        self.repo.save(self._make_result("MILK"))
        self.assertEqual(len(self.repo.search("138")), 1)
        self.assertEqual(len(self.repo.search("MI")), 1)

    def test_delete_and_clear(self):
        rid = self.repo.save(self._make_result("138649"))
        self.repo.save(self._make_result("121212"))
        self.assertTrue(self.repo.delete(rid))
        self.assertEqual(self.repo.count(), 1)
        self.assertTrue(self.repo.clear_all())
        self.assertEqual(self.repo.count(), 0)

    def test_settings_storage(self):
        self.db.set_setting("theme", "dark")
        self.assertEqual(self.db.get_setting("theme"), "dark")
        self.db.set_setting("theme", "light")
        self.assertEqual(self.db.get_setting("theme"), "light")
        self.assertEqual(self.db.get_setting("missing", "default"), "default")

    def test_corrupted_db_recovery(self):
        """损坏的数据库不应导致程序崩溃。"""
        self.db.close()
        self.db_path.write_text("this is not a database", encoding="utf-8")
        db2 = DatabaseManager(self.db_path)
        repo2 = HistoryRepository(db2)
        self.assertEqual(repo2.count(), 0)  # 自动重建后可正常使用
        db2.close()


if __name__ == "__main__":
    unittest.main()
