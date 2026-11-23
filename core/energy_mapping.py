"""数字能量映射规则。

本模块集中保存四吉星、四凶星的数字组合与等级对应关系，是软件分析的
唯一数据依据。UI 展示（数字能量表页面）也从此模块读取数据，避免展示
数据与分析引擎数据不一致。

规则来源：用户提供的数字能量对应表图片。数据为原始规则，不得随意更改。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# 四个吉星与四个凶星的名称列表（按图片顺序）
AUSPICIOUS_STARS: Tuple[str, ...] = ("天医", "延年", "生气", "伏位")
INAUSPICIOUS_STARS: Tuple[str, ...] = ("绝命", "祸害", "五鬼", "六煞")

ALL_STARS: Tuple[str, ...] = AUSPICIOUS_STARS + INAUSPICIOUS_STARS

# 等级列表（按图片顺序）
LEVELS: Tuple[str, ...] = ("一级", "二级", "三级", "四级")

# 属性常量
AUSPICIOUS = "吉星"
INAUSPICIOUS = "凶星"
UNRATED = "暂无评定"
UNKNOWN = "未知组合"


@dataclass(frozen=True)
class EnergyMapping:
    """单个数字组合的映射条目。"""

    number: str
    star: str
    level: str
    nature: str

    @property
    def level_weight(self) -> int:
        """等级序号（一级=1，二级=2，三级=3，四级=4），用于视觉强调。"""
        return LEVELS.index(self.level) + 1 if self.level in LEVELS else 0

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "star": self.star,
            "level": self.level,
            "nature": self.nature,
        }


def _build_table() -> Dict[str, EnergyMapping]:
    """根据图片规则构建 数字组合 -> 映射条目 的字典。"""
    # 每个星按 一级/二级/三级/四级 顺序排列的组合
    star_combinations: Dict[str, Dict[str, List[str]]] = {
        # ==================== 四吉星 ====================
        "天医": {
            "一级": ["13", "31"],
            "二级": ["68", "86"],
            "三级": ["49", "94"],
            "四级": ["27", "72"],
        },
        "延年": {
            "一级": ["19", "91"],
            "二级": ["78", "87"],
            "三级": ["34", "43"],
            "四级": ["26", "62"],
        },
        "生气": {
            "一级": ["14", "41"],
            "二级": ["67", "76"],
            "三级": ["39", "93"],
            "四级": ["28", "82"],
        },
        "伏位": {
            "一级": ["11", "22"],
            "二级": ["88", "99"],
            "三级": ["66", "77"],
            "四级": ["33", "44"],
        },
        # ==================== 四凶星 ====================
        "绝命": {
            "一级": ["12", "21"],
            "二级": ["69", "96"],
            "三级": ["48", "84"],
            "四级": ["37", "73"],
        },
        "祸害": {
            "一级": ["17", "71"],
            "二级": ["89", "98"],
            "三级": ["46", "64"],
            "四级": ["23", "32"],
        },
        "五鬼": {
            "一级": ["18", "81"],
            "二级": ["79", "97"],
            "三级": ["36", "63"],
            "四级": ["24", "42"],
        },
        "六煞": {
            "一级": ["16", "61"],
            "二级": ["47", "74"],
            "三级": ["38", "83"],
            "四级": ["29", "92"],
        },
    }

    table: Dict[str, EnergyMapping] = {}
    for star, level_map in star_combinations.items():
        nature = AUSPICIOUS if star in AUSPICIOUS_STARS else INAUSPICIOUS
        for level, numbers in level_map.items():
            for number in numbers:
                if number in table:
                    raise ValueError(f"数字组合 {number} 重复定义")
                table[number] = EnergyMapping(number, star, level, nature)
    return table


# 全局唯一的映射表
ENERGY_TABLE: Dict[str, EnergyMapping] = _build_table()


def get_mapping(number: str) -> EnergyMapping | None:
    """查询某个两位数字组合的映射，未匹配返回 None。"""
    return ENERGY_TABLE.get(number)


def get_star_combinations(star: str) -> List[EnergyMapping]:
    """返回指定星名的所有组合（按等级顺序）。"""
    return [m for m in ENERGY_TABLE.values() if m.star == star]


def get_star_level_combinations(star: str, level: str) -> List[str]:
    """返回指定星名、指定等级的数字组合列表。"""
    return [
        m.number for m in ENERGY_TABLE.values()
        if m.star == star and m.level == level
    ]


def is_auspicious(star: str) -> bool:
    return star in AUSPICIOUS_STARS


def is_inauspicious(star: str) -> bool:
    return star in INAUSPICIOUS_STARS


def validate_table() -> bool:
    """校验映射表完整性：8 星 × 4 级 × 2 组合 = 64 条。"""
    if len(ENERGY_TABLE) != 64:
        return False
    for star in ALL_STARS:
        for level in LEVELS:
            if len(get_star_level_combinations(star, level)) != 2:
                return False
    return True
