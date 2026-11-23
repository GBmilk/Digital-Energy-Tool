"""CSV 数据导出模块。

使用标准 csv 模块，UTF-8-SIG 编码确保 Excel 打开中文不乱码。
支持导出当前分析、全部历史记录与筛选后的记录。
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from core.energy_analyzer import AnalysisResult
from database.history_repository import HistoryRepository
from .utils import app_path, logger

# CSV 字段
FIELDNAMES = [
    "原始输入", "转换后数字", "组合序号", "数字组合", "星名", "吉凶属性",
    "等级", "组合分数", "综合分数", "综合评级", "分析时间",
]


def _default_filename(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.csv"


def export_analysis(result: AnalysisResult, file_path: str | Path | None = None,
                    directory: str | Path | None = None) -> Path:
    """导出当前分析结果为 CSV。

    若 file_path 为 None，则在 directory（默认 exports）下生成带时间戳的文件名。
    """
    path = _resolve_path(file_path, directory, "数字能量分析")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for c in result.combinations:
                writer.writerow({
                    "原始输入": result.raw_input,
                    "转换后数字": result.digits,
                    "组合序号": c.index + 1,
                    "数字组合": c.number,
                    "星名": c.star,
                    "吉凶属性": c.nature,
                    "等级": c.level,
                    "组合分数": c.score if c.counted else "--",
                    "综合分数": (result.total_score if result.total_score is not None
                                 else "--"),
                    "综合评级": result.rating,
                    "分析时间": result.created_at,
                })
        logger.info("CSV 导出成功: %s", path)
        return path
    except (OSError, csv.Error) as exc:
        logger.error("CSV 导出失败: %s", exc)
        raise RuntimeError(f"导出 CSV 失败：{exc}") from exc


def export_history(records: list[dict], repo: HistoryRepository,
                   file_path: str | Path | None = None,
                   directory: str | Path | None = None) -> Path:
    """导出历史记录为 CSV。records 为摘要列表（可全部或筛选后）。"""
    path = _resolve_path(file_path, directory, "数字能量历史记录")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for record in records:
                full = repo.get_by_id(record["id"])
                if full is None:
                    continue
                for c in full.combinations:
                    writer.writerow({
                        "原始输入": full.raw_input,
                        "转换后数字": full.digits,
                        "组合序号": c.index + 1,
                        "数字组合": c.number,
                        "星名": c.star,
                        "吉凶属性": c.nature,
                        "等级": c.level,
                        "组合分数": c.score if c.counted else "--",
                        "综合分数": (full.total_score
                                     if full.total_score is not None else "--"),
                        "综合评级": full.rating,
                        "分析时间": full.created_at,
                    })
        logger.info("历史记录 CSV 导出成功: %s (%s 条)", path, len(records))
        return path
    except (OSError, csv.Error) as exc:
        logger.error("历史记录 CSV 导出失败: %s", exc)
        raise RuntimeError(f"导出历史记录 CSV 失败：{exc}") from exc


def _resolve_path(file_path: str | Path | None, directory: str | Path | None,
                  prefix: str) -> Path:
    if file_path:
        p = Path(file_path)
        if not p.is_absolute():
            p = app_path(str(p))
        return p
    d = Path(directory) if directory else app_path("exports")
    if not d.is_absolute():
        d = app_path(str(d))
    return d / _default_filename(prefix)
