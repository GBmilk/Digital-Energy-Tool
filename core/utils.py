"""通用工具：路径解析、配置读写、日志初始化。"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

# 项目根目录（main.py 所在目录）
APP_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "1.0.0",
    "app_name": "数字能量工具",
    "theme": "light",
    "score_rules": {
        "吉星": {"一级": 10, "二级": 8, "三级": 6, "四级": 4},
        "凶星": {"一级": -10, "二级": -8, "三级": -6, "四级": -4},
    },
    "rating_ranges": [
        {"min": 90, "max": 100, "rating": "很好", "color": "#0E7A3D"},
        {"min": 75, "max": 89, "rating": "好", "color": "#2AA36A"},
        {"min": 60, "max": 74, "rating": "一般", "color": "#2E7DD1"},
        {"min": 40, "max": 59, "rating": "不好", "color": "#E8912D"},
        {"min": 0, "max": 39, "rating": "凶", "color": "#D94242"},
    ],
    "no_rating": {"rating": "暂无评定", "color": "#8C8C8C"},
    "paths": {
        "history_db": "data/history.db",
        "default_export": "exports",
        "default_image_save": "exports",
        "config_file": "config/config.json",
    },
    "image": {"width": 1920, "padding": 64},
}


def app_path(relative: str) -> Path:
    """将相对路径解析为项目根目录下的绝对路径（兼容中文路径）。"""
    p = Path(relative)
    if p.is_absolute():
        return p
    return APP_ROOT / p


def config_path() -> Path:
    return app_path("config/config.json")


def ensure_dirs() -> None:
    """确保必需目录存在。"""
    for d in ("config", "core", "database", "ui", "ui/widgets",
              "resources/icons", "resources/images", "resources/styles",
              "exports", "data", "tests"):
        app_path(d).mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """加载配置。优先 JSON 文件，缺失时尝试 SQLite，最后回退默认配置。"""
    path = config_path()
    data: Dict[str, Any] | None = None
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            data = None

    if data is None:
        # 尝试从 SQLite 恢复
        try:
            from database.database_manager import DatabaseManager
            db = DatabaseManager()
            raw = db.get_setting("app_config", "")
            db.close()
            if raw:
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception:
            data = None

    if data is None:
        save_config(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))

    # 用默认配置补齐缺失项
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    merged.update(data)
    return merged


def save_config(config: Dict[str, Any]) -> bool:
    """保存配置到 JSON 文件，并同步写入 SQLite 数据库。

    需求要求配置采用 SQLite 数据库保存；JSON 文件同时保留，便于人工查看
    与修改。两处内容保持一致，SQLite 为运行时读取的补充持久化层。
    """
    ok = True
    try:
        path = config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as exc:
        logging.getLogger("数字能量工具").error("保存配置 JSON 失败: %s", exc)
        ok = False

    # 同步到 SQLite
    try:
        from database.database_manager import DatabaseManager
        db = DatabaseManager()
        db.set_setting("app_config", json.dumps(config, ensure_ascii=False))
        db.close()
    except Exception as exc:
        logging.getLogger("数字能量工具").error("保存配置到 SQLite 失败: %s", exc)
        ok = False
    return ok


def setup_logger() -> logging.Logger:
    """初始化统一日志系统。"""
    logger = logging.getLogger("数字能量工具")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # 文件日志
    try:
        log_file = app_path("data/app.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass
    # 控制台日志
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


logger = setup_logger()
