"""综合评分引擎。

根据每个匹配组合的星名属性、等级与配置的评分规则，计算综合评分与
六级评级。评分算法与配置完全解耦，规则由 config/config.json 提供。
"""

from __future__ import annotations

from typing import Dict

from .energy_analyzer import AnalysisResult, update_statistics
from .energy_mapping import AUSPICIOUS, INAUSPICIOUS, UNRATED

# 缺省评分规则（当配置文件缺失时使用）
DEFAULT_SCORE_RULES: Dict[str, Dict[str, int]] = {
    AUSPICIOUS: {"一级": 10, "二级": 8, "三级": 6, "四级": 4},
    INAUSPICIOUS: {"一级": -10, "二级": -8, "三级": -6, "四级": -4},
}

# 缺省评级区间
DEFAULT_RATING_RANGES = [
    {"min": 90, "max": 100, "rating": "很好", "color": "#0E7A3D"},
    {"min": 75, "max": 89, "rating": "好", "color": "#2AA36A"},
    {"min": 60, "max": 74, "rating": "一般", "color": "#2E7DD1"},
    {"min": 40, "max": 59, "rating": "不好", "color": "#E8912D"},
    {"min": 0, "max": 39, "rating": "凶", "color": "#D94242"},
]
DEFAULT_NO_RATING = {"rating": UNRATED, "color": "#8C8C8C"}


def get_combination_score(
    nature: str, level: str, rules: Dict[str, Dict[str, int]] | None = None
) -> int:
    """获取单个组合的分数。"""
    rules = rules or DEFAULT_SCORE_RULES
    try:
        return int(rules[nature][level])
    except (KeyError, TypeError, ValueError):
        return 0


def calculate_score(
    result: AnalysisResult,
    score_rules: Dict[str, Dict[str, int]] | None = None,
    rating_ranges: list | None = None,
    no_rating: dict | None = None,
) -> AnalysisResult:
    """计算综合评分并原地更新 result。

    评分算法：
    1. 对每个有效匹配组合按规则打分。
    2. 组合平均分的理论范围是 [-10, +10]（可由配置改变）。
    3. 使用线性映射 (平均分 + 10) / 20 * 100 转换到 0-100 分。
       为了兼容自定义规则，实际按规则中最大绝对值确定映射范围。
    4. 若无任何有效组合，则显示"暂无评定"("--")，不显示 0 分。
    """
    rules = normalize_rules(score_rules)
    ranges = rating_ranges or DEFAULT_RATING_RANGES
    no_rating = no_rating or DEFAULT_NO_RATING

    # 先计算每个组合的分数
    for c in result.combinations:
        if c.counted:
            c.score = get_combination_score(c.nature, c.level, rules)
        else:
            c.score = 0

    update_statistics(result)

    if result.valid_count == 0:
        result.total_score = None
        result.rating = no_rating.get("rating", UNRATED)
        result.rating_color = no_rating.get("color", "#8C8C8C")
        return result

    total = sum(c.score for c in result.combinations if c.counted)
    average = total / result.valid_count

    # 根据配置计算理论最大绝对值，用于归一化
    max_abs = 1
    for nature_rules in rules.values():
        if isinstance(nature_rules, dict):
            for value in nature_rules.values():
                try:
                    max_abs = max(max_abs, abs(int(value)))
                except (TypeError, ValueError):
                    continue

    score = (average + max_abs) / (2 * max_abs) * 100
    score = max(0, min(100, int(round(score))))
    result.total_score = score

    rating_info = find_rating(score, ranges, no_rating)
    result.rating = rating_info["rating"]
    result.rating_color = rating_info["color"]
    return result


def normalize_rules(
    rules: Dict[str, Dict[str, int]] | None
) -> Dict[str, Dict[str, int]]:
    """规范化评分规则，缺失的层级用默认值补齐。"""
    normalized: Dict[str, Dict[str, int]] = {
        nature: dict(levels) for nature, levels in DEFAULT_SCORE_RULES.items()
    }
    if not rules:
        return normalized
    for nature, levels in rules.items():
        if isinstance(levels, dict):
            normalized.setdefault(nature, {})
            for level, value in levels.items():
                try:
                    normalized[nature][level] = int(value)
                except (TypeError, ValueError):
                    continue
    return normalized


def find_rating(score: int, ranges: list | None, no_rating: dict) -> dict:
    """根据分数查找对应评级。"""
    ranges = ranges or DEFAULT_RATING_RANGES
    for item in ranges:
        try:
            low = int(item.get("min", 0))
            high = int(item.get("max", -1))
        except (TypeError, ValueError):
            continue
        if low <= score <= high:
            return {
                "rating": item.get("rating", UNRATED),
                "color": item.get("color", "#8C8C8C"),
            }
    return {
        "rating": no_rating.get("rating", UNRATED),
        "color": no_rating.get("color", "#8C8C8C"),
    }
