"""数字能量分析引擎。

将转换后的数字字符串按相邻位置拆分为两位数组合，逐个匹配数字能量表，
输出结构化分析结果。所有计算逻辑都在此模块，UI 不参与任何计算。

特殊规则：
- 单个数字不构成组合。
- 任何包含数字 5 的两位组合显示为"暂无评定"，不参与匹配与评分。
- 未匹配到能量表的组合标记为"未知组合"。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from .alphabet_converter import convert
from .energy_mapping import (
    AUSPICIOUS,
    INAUSPICIOUS,
    UNKNOWN,
    UNRATED,
    EnergyMapping,
    get_mapping,
)


@dataclass
class CombinationResult:
    """单个两位数字组合的分析结果。"""

    index: int
    number: str
    star: str
    level: str
    nature: str
    description: str = ""
    score: int = 0
    # 是否参与评分：有效匹配（吉星或凶星）才参与
    counted: bool = False
    # 状态：matched（已匹配）/ unmatched（未知）/ unrated（含5或无效）
    status: str = "matched"

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "number": self.number,
            "star": self.star,
            "level": self.level,
            "nature": self.nature,
            "description": self.description,
            "score": self.score,
            "counted": self.counted,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CombinationResult":
        return cls(
            index=data.get("index", 0),
            number=data.get("number", ""),
            star=data.get("star", UNKNOWN),
            level=data.get("level", "--"),
            nature=data.get("nature", UNRATED),
            description=data.get("description", ""),
            score=data.get("score", 0),
            counted=data.get("counted", False),
            status=data.get("status", "matched"),
        )


@dataclass
class AnalysisResult:
    """一次完整分析的结果对象。"""

    raw_input: str
    cleaned_input: str
    digits: str
    combinations: List[CombinationResult] = field(default_factory=list)
    created_at: str = ""

    # 综合评分（由 score_engine 计算后填入）
    total_score: int | None = None
    rating: str = UNRATED
    rating_color: str = ""
    # 统计
    valid_count: int = 0
    auspicious_count: int = 0
    inauspicious_count: int = 0
    unrated_count: int = 0
    unmatched_count: int = 0

    def to_dict(self) -> dict:
        return {
            "raw_input": self.raw_input,
            "cleaned_input": self.cleaned_input,
            "digits": self.digits,
            "combinations": [c.to_dict() for c in self.combinations],
            "created_at": self.created_at,
            "total_score": self.total_score,
            "rating": self.rating,
            "rating_color": self.rating_color,
            "valid_count": self.valid_count,
            "auspicious_count": self.auspicious_count,
            "inauspicious_count": self.inauspicious_count,
            "unrated_count": self.unrated_count,
            "unmatched_count": self.unmatched_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AnalysisResult":
        return cls(
            raw_input=data.get("raw_input", ""),
            cleaned_input=data.get("cleaned_input", ""),
            digits=data.get("digits", ""),
            combinations=[
                CombinationResult.from_dict(c)
                for c in data.get("combinations", [])
            ],
            created_at=data.get("created_at", ""),
            total_score=data.get("total_score"),
            rating=data.get("rating", UNRATED),
            rating_color=data.get("rating_color", ""),
            valid_count=data.get("valid_count", 0),
            auspicious_count=data.get("auspicious_count", 0),
            inauspicious_count=data.get("inauspicious_count", 0),
            unrated_count=data.get("unrated_count", 0),
            unmatched_count=data.get("unmatched_count", 0),
        )


# 星名简要说明（用于卡片展示）
STAR_DESCRIPTIONS: Dict[str, str] = {
    "天医": "财星、健康星，主财富与贵人",
    "延年": "长寿星，主生命力与领导力",
    "生气": "旺气星，主活力与人缘",
    "伏位": "平稳星，主稳定与积累",
    "绝命": "主波折与挑战，需注意风险",
    "祸害": "主口舌是非，易有阻碍",
    "五鬼": "主变动与暗耗，宜谨慎",
    "六煞": "主压力与反复，需防困扰",
}


def build_combinations(digits: str) -> List[CombinationResult]:
    """按相邻位置生成两位数组合并逐个匹配能量表。

    例如 digits='139112' -> ['13','39','91','11','12']
    """
    results: List[CombinationResult] = []
    for i in range(len(digits) - 1):
        number = digits[i : i + 2]
        # 含 5 的组合：暂无评定，不参与匹配与评分
        if "5" in number:
            results.append(
                CombinationResult(
                    index=i,
                    number=number,
                    star=UNRATED,
                    level="--",
                    nature=UNRATED,
                    description="含数字 5 的组合，不参与评定",
                    score=0,
                    counted=False,
                    status="unrated",
                )
            )
            continue

        mapping: EnergyMapping | None = get_mapping(number)
        if mapping is None:
            results.append(
                CombinationResult(
                    index=i,
                    number=number,
                    star=UNKNOWN,
                    level="--",
                    nature=UNRATED,
                    description="未匹配到数字能量组合",
                    score=0,
                    counted=False,
                    status="unmatched",
                )
            )
            continue

        results.append(
            CombinationResult(
                index=i,
                number=number,
                star=mapping.star,
                level=mapping.level,
                nature=mapping.nature,
                description=STAR_DESCRIPTIONS.get(mapping.star, ""),
                score=0,
                counted=True,
                status="matched",
            )
        )
    return results


def analyze(raw_input: str) -> AnalysisResult:
    """对原始输入执行完整分析（字母转换 + 组合拆分 + 匹配）。

    评分由 score_engine.calculate_score 在之后单独调用，实现关注点分离。
    """
    raw, cleaned, digits = convert(raw_input)
    combinations = build_combinations(digits)
    result = AnalysisResult(
        raw_input=raw,
        cleaned_input=cleaned,
        digits=digits,
        combinations=combinations,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    update_statistics(result)
    return result


def update_statistics(result: AnalysisResult) -> None:
    """根据组合结果更新统计计数。"""
    result.valid_count = sum(1 for c in result.combinations if c.counted)
    result.auspicious_count = sum(
        1 for c in result.combinations if c.counted and c.nature == AUSPICIOUS
    )
    result.inauspicious_count = sum(
        1 for c in result.combinations if c.counted and c.nature == INAUSPICIOUS
    )
    result.unrated_count = sum(
        1 for c in result.combinations if c.status == "unrated"
    )
    result.unmatched_count = sum(
        1 for c in result.combinations if c.status == "unmatched"
    )
