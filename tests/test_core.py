"""核心计算模块单元测试。

运行：python -m unittest discover -s tests -v
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core import energy_mapping as em
from core.alphabet_converter import (
    convert, filter_invalid_chars, is_valid_input, letters_to_digits,
)
from core.csv_exporter import export_analysis, FIELDNAMES
from core.energy_analyzer import analyze, build_combinations
from core.image_generator import generate_detail_image
from core.score_engine import (
    calculate_score, find_rating, get_combination_score, normalize_rules,
)


class TestEnergyMapping(unittest.TestCase):
    """数字能量映射规则测试。"""

    def test_table_complete(self):
        self.assertTrue(em.validate_table())
        self.assertEqual(len(em.ENERGY_TABLE), 64)

    def test_auspicious_levels(self):
        expected = {
            "天医": {"一级": ["13", "31"], "二级": ["68", "86"],
                     "三级": ["49", "94"], "四级": ["27", "72"]},
            "延年": {"一级": ["19", "91"], "二级": ["78", "87"],
                     "三级": ["34", "43"], "四级": ["26", "62"]},
            "生气": {"一级": ["14", "41"], "二级": ["67", "76"],
                     "三级": ["39", "93"], "四级": ["28", "82"]},
            "伏位": {"一级": ["11", "22"], "二级": ["88", "99"],
                     "三级": ["66", "77"], "四级": ["33", "44"]},
            "绝命": {"一级": ["12", "21"], "二级": ["69", "96"],
                     "三级": ["48", "84"], "四级": ["37", "73"]},
            "祸害": {"一级": ["17", "71"], "二级": ["89", "98"],
                     "三级": ["46", "64"], "四级": ["23", "32"]},
            "五鬼": {"一级": ["18", "81"], "二级": ["79", "97"],
                     "三级": ["36", "63"], "四级": ["24", "42"]},
            "六煞": {"一级": ["16", "61"], "二级": ["47", "74"],
                     "三级": ["38", "83"], "四级": ["29", "92"]},
        }
        for star, levels in expected.items():
            for level, numbers in levels.items():
                self.assertEqual(em.get_star_level_combinations(star, level), numbers)

    def test_mapping_lookup(self):
        m = em.get_mapping("13")
        self.assertIsNotNone(m)
        self.assertEqual((m.star, m.level, m.nature), ("天医", "一级", "吉星"))
        m = em.get_mapping("37")
        self.assertEqual((m.star, m.level, m.nature), ("绝命", "四级", "凶星"))
        self.assertIsNone(em.get_mapping("10"))


class TestAlphabetConverter(unittest.TestCase):
    """字母转换测试。"""

    def test_conversion(self):
        self.assertEqual(letters_to_digits("ABC"), "123")
        self.assertEqual(letters_to_digits("MILK"), "1391211")  # M=13 I=9 L=12 K=11
        self.assertEqual(letters_to_digits("GTA"), "7201")      # G=7 T=20 A=1
        self.assertEqual(letters_to_digits("Z"), "26")
        self.assertEqual(letters_to_digits("a1B"), "112")

    def test_case_insensitive(self):
        self.assertEqual(letters_to_digits("abc"), letters_to_digits("ABC"))

    def test_filter_invalid(self):
        self.assertEqual(filter_invalid_chars("12a中@# "), "12a")
        self.assertFalse(is_valid_input("12 3"))
        self.assertFalse(is_valid_input("中文"))
        self.assertTrue(is_valid_input("AbC123"))
        self.assertTrue(is_valid_input(""))

    def test_convert_keeps_raw(self):
        raw, cleaned, digits = convert("aB-9")
        self.assertEqual(raw, "aB-9")
        self.assertEqual(cleaned, "aB9")
        self.assertEqual(digits, "129")


class TestEnergyAnalyzer(unittest.TestCase):
    """数字组合分析测试。"""

    def test_build_combinations_order(self):
        combos = build_combinations("139112")
        self.assertEqual([c.number for c in combos],
                         ["13", "39", "91", "11", "12"])
        combos = build_combinations("123456")
        self.assertEqual([c.number for c in combos],
                         ["12", "23", "34", "45", "56"])

    def test_single_digit_no_combinations(self):
        self.assertEqual(build_combinations("5"), [])
        result = analyze("5")
        self.assertEqual(len(result.combinations), 0)

    def test_match_result(self):
        combos = build_combinations("138649")
        self.assertEqual(
            [(c.number, c.star, c.level, c.nature) for c in combos],
            [
                ("13", "天医", "一级", "吉星"),
                ("38", "六煞", "三级", "凶星"),
                ("86", "天医", "二级", "吉星"),
                ("64", "祸害", "三级", "凶星"),
                ("49", "天医", "三级", "吉星"),
            ],
        )

    def test_unmatched_combination(self):
        combos = build_combinations("10")
        self.assertEqual(len(combos), 1)
        self.assertEqual(combos[0].star, "未知组合")
        self.assertFalse(combos[0].counted)

    def test_number_5_unrated(self):
        combos = build_combinations("15519")
        for c in combos:
            if "5" in c.number:
                self.assertEqual(c.star, "暂无评定")
                self.assertEqual(c.level, "--")
                self.assertEqual(c.nature, "暂无评定")
                self.assertFalse(c.counted)

    def test_letters_analysis(self):
        result = analyze("ABC")
        self.assertEqual(result.digits, "123")
        self.assertEqual([c.number for c in result.combinations], ["12", "23"])

    def test_repeated_combinations_allowed(self):
        combos = build_combinations("131313")
        self.assertEqual([c.number for c in combos], ["13", "31", "13", "31", "13"])
        self.assertTrue(all(c.counted for c in combos))

    def test_statistics(self):
        result = analyze("138649")
        self.assertEqual(result.valid_count, 5)
        self.assertEqual(result.auspicious_count, 3)
        self.assertEqual(result.inauspicious_count, 2)


class TestScoreEngine(unittest.TestCase):
    """评分引擎测试。"""

    def test_combination_score(self):
        self.assertEqual(get_combination_score("吉星", "一级"), 10)
        self.assertEqual(get_combination_score("凶星", "四级"), -4)

    def test_custom_rules(self):
        custom = {"吉星": {"一级": 20}, "凶星": {"一级": -20}}
        rules = normalize_rules(custom)
        self.assertEqual(rules["吉星"]["一级"], 20)
        self.assertEqual(rules["吉星"]["二级"], 8)  # 默认值补齐

    def test_no_rating_when_single_digit(self):
        result = analyze("5")
        calculate_score(result)
        self.assertIsNone(result.total_score)
        self.assertEqual(result.rating, "暂无评定")

    def test_no_rating_when_all_5(self):
        result = analyze("1551")
        calculate_score(result)
        self.assertIsNone(result.total_score)
        self.assertEqual(result.rating, "暂无评定")

    def test_no_rating_when_all_unmatched(self):
        result = analyze("1010")
        calculate_score(result)
        self.assertIsNone(result.total_score)

    def test_partial_valid(self):
        # 13(有效+10) 35(含5无效) 50(含5无效) 01(未匹配) 19(有效+10)
        result = analyze("1350019")
        calculate_score(result)
        self.assertEqual(result.valid_count, 2)
        self.assertEqual(result.total_score, 100)  # 平均+10 -> 满分
        self.assertEqual(result.rating, "很好")

    def test_all_auspicious_high_score(self):
        result = analyze("131319")  # 13,31,13,19 全是一级吉星
        calculate_score(result)
        self.assertEqual(result.total_score, 100)
        self.assertEqual(result.rating, "很好")

    def test_all_inauspicious_low(self):
        result = analyze("121212")  # 12,21,12 全是一级凶星
        calculate_score(result)
        self.assertEqual(result.total_score, 0)
        self.assertEqual(result.rating, "凶")

    def test_rating_ranges(self):
        ranges = [
            {"min": 90, "max": 100, "rating": "很好", "color": "#0E7A3D"},
            {"min": 0, "max": 39, "rating": "凶", "color": "#D94242"},
        ]
        no_rating = {"rating": "暂无评定", "color": "#8C8C8C"}
        self.assertEqual(find_rating(95, ranges, no_rating)["rating"], "很好")
        self.assertEqual(find_rating(20, ranges, no_rating)["rating"], "凶")


class TestExportAndImage(unittest.TestCase):
    """CSV 导出与图片生成测试。"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.result = analyze("138649")
        calculate_score(self.result)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_csv_export(self):
        path = Path(self.tmpdir.name) / "test.csv"
        export_analysis(self.result, path)
        self.assertTrue(path.exists())
        content = path.read_text(encoding="utf-8-sig")
        self.assertIn("原始输入", content)
        self.assertIn("138649", content)
        self.assertIn("天医", content)
        for field in FIELDNAMES:
            self.assertIn(field, content)

    def test_image_generation(self):
        path = Path(self.tmpdir.name) / "test.png"
        generate_detail_image(self.result, path)
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 10000)
        from PIL import Image
        with Image.open(path) as img:
            self.assertEqual(img.format, "PNG")
            self.assertGreaterEqual(img.width, 1920)

    def test_resolution_presets(self):
        """五档清晰度均可生成，宽度与 DPI 正确。"""
        from core.image_generator import RESOLUTION_PRESETS
        from PIL import Image
        self.assertEqual(
            list(RESOLUTION_PRESETS.keys()),
            ["720P", "1080P", "2K", "4K", "8K"],
        )
        for name, expected_width in RESOLUTION_PRESETS.items():
            path = Path(self.tmpdir.name) / f"{name}.png"
            generate_detail_image(self.result, path, width=expected_width)
            with Image.open(path) as img:
                self.assertEqual(img.width, expected_width)
                dpi = img.info.get("dpi", (0, 0))
                self.assertAlmostEqual(dpi[0], 600, delta=1)

    def test_image_has_no_disclaimer(self):
        """详情图不应出现免责声明文案（通过源码检查）。"""
        import inspect
        from core import image_generator
        source = inspect.getsource(image_generator)
        for phrase in ("科学依据", "娱乐", "不构成", "仅供"):
            self.assertNotIn(phrase, source)


if __name__ == "__main__":
    unittest.main()
