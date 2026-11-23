"""数字能量详情图生成模块（基于 Pillow）。

生成高清 PNG 图片，包含软件名称、输入信息、综合评分、评级、统计与
所有数字组合详细结果。自动检测 Windows 中文字体，支持长数字换行。
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .energy_analyzer import AnalysisResult
from .energy_mapping import AUSPICIOUS, INAUSPICIOUS
from .utils import app_path

# 候选中文字体（按优先级）
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",    # 微软雅黑粗体
    "C:/Windows/Fonts/simsun.ttc",    # 宋体
    "C:/Windows/Fonts/simhei.ttf",    # 黑体
    "C:/Windows/Fonts/Deng.ttf",      # 等线
    "C:/Windows/Fonts/SimHei.ttf",
]

# 清晰度预设：名称 -> 图片宽度（像素）。高度按内容自适应。
RESOLUTION_PRESETS: dict[str, int] = {
    "720P": 1280,
    "1080P": 1920,
    "2K": 2560,
    "4K": 3840,
    "8K": 7680,
}

# 导出图片固定 DPI（不显示在 UI 中）
IMAGE_DPI = (600, 600)

# 配色
COLOR_BG = "#F5F7FA"
COLOR_HEADER_BG = "#1F3A5F"
COLOR_CARD_BG = "#FFFFFF"
COLOR_TEXT = "#1F2937"
COLOR_SUBTEXT = "#6B7280"
COLOR_BORDER = "#E5E7EB"
COLOR_AUSPICIOUS = "#2AA36A"
COLOR_AUSPICIOUS_BG = "#E8F6EF"
COLOR_INAUSPICIOUS = "#D94242"
COLOR_INAUSPICIOUS_BG = "#FCEDED"
COLOR_UNRATED = "#8C8C8C"
COLOR_UNRATED_BG = "#F0F1F3"
COLOR_ACCENT = "#2E7DD1"

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """获取中文字体，失败则回退到默认字体。"""
    key = ("bold" if bold else "regular", size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    for path in FONT_CANDIDATES:
        p = Path(path)
        if p.exists():
            try:
                font = ImageFont.truetype(str(p), size)
                _FONT_CACHE[key] = font
                return font
            except OSError:
                continue
    # 回退
    font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int,
              draw: ImageDraw.ImageDraw) -> list[str]:
    """按像素宽度对文本换行（支持中文）。"""
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = trial
    if current:
        lines.append(current)
    return lines or [""]


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def level_color(level: str) -> str:
    """等级对应的强调色（一级最深）。"""
    return {
        "一级": "#0E7A3D",
        "二级": "#2AA36A",
        "三级": "#6BBF94",
        "四级": "#A7D8BF",
    }.get(level, COLOR_UNRATED)


def generate_detail_image(result: AnalysisResult, output_path: str | Path,
                          width: int = 1920) -> Path:
    """生成详情图并保存到 output_path，返回实际保存路径。

    width 为目标图片宽度（像素），由清晰度预设决定；所有字体与布局尺寸
    按 width/1920 等比缩放，保证任意分辨率下排版一致、文字清晰。
    图片以固定 DPI 保存（不在界面展示该信息）。
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scale = width / 1920.0

    def px(value: int) -> int:
        """按分辨率缩放尺寸。"""
        return max(1, int(round(value * scale)))

    def scaled_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        return get_font(px(size), bold)

    padding = px(64)
    inner_width = width - 2 * padding

    # 预计算字体（随分辨率等比放大）
    f_title = scaled_font(52, bold=True)
    f_subtitle = scaled_font(30, bold=True)
    f_heading = scaled_font(28, bold=True)
    f_body = scaled_font(24)
    f_small = scaled_font(20)
    f_score = scaled_font(72, bold=True)
    f_table_header = scaled_font(22, bold=True)

    # 估算高度
    combos = result.combinations
    row_height = px(56)
    table_header_height = px(56)
    base_height = px(
        180 + 220 + 180 + 120 + 56 + 56 * len(combos) + 120
    )
    height = max(px(1080), base_height)

    img = Image.new("RGB", (width, height), hex_to_rgb(COLOR_BG))
    draw = ImageDraw.Draw(img)

    y = 0

    # ===== 顶部标题栏 =====
    header_h = px(160)
    draw.rectangle([0, 0, width, header_h], fill=hex_to_rgb(COLOR_HEADER_BG))
    draw.text((padding, px(42)), "数字能量工具", font=f_title, fill=(255, 255, 255))
    draw.text(
        (padding, px(108)), "数字能量分析报告",
        font=f_small, fill=(198, 214, 235),
    )
    date_text = f"分析日期：{result.created_at}"
    bbox = draw.textbbox((0, 0), date_text, font=f_small)
    draw.text(
        (width - padding - (bbox[2] - bbox[0]), px(52)), date_text,
        font=f_small, fill=(220, 230, 245),
    )
    y = header_h + px(32)

    # ===== 输入信息卡片 =====
    def draw_card(x0: int, y0: int, x1: int, y1: int, bg: str = COLOR_CARD_BG,
                  border: str = COLOR_BORDER) -> None:
        draw.rounded_rectangle(
            [x0, y0, x1, y1], radius=px(18),
            fill=hex_to_rgb(bg), outline=hex_to_rgb(border), width=px(2),
        )

    info_lines = [
        ("原始输入", result.raw_input),
        ("字母转数字", result.digits),
        ("输入长度", str(len(result.digits))),
        ("组合数量", str(len(combos))),
    ]
    info_height = px(60 + 44 * len(info_lines) + 20)
    draw_card(padding, y, width - padding, y + info_height)
    draw.text((padding + px(32), y + px(24)), "输入信息", font=f_heading,
              fill=hex_to_rgb(COLOR_TEXT))
    iy = y + px(76)
    for label, value in info_lines:
        draw.text((padding + px(32), iy), f"{label}：", font=f_body,
                  fill=hex_to_rgb(COLOR_SUBTEXT))
        value_x = padding + px(32) + px(160)
        # 长数字换行
        value_font = f_body
        lines = wrap_text(value, value_font, inner_width - px(220), draw)
        for li, line in enumerate(lines):
            draw.text((value_x, iy + li * px(34)), line, font=value_font,
                      fill=hex_to_rgb(COLOR_TEXT))
        iy += max(px(44), px(34) * len(lines))
    y += info_height + px(24)

    # ===== 综合评分卡片 =====
    score_height = px(210)
    draw_card(padding, y, width - padding, y + score_height)
    draw.text((padding + px(32), y + px(24)), "综合评分", font=f_heading,
              fill=hex_to_rgb(COLOR_TEXT))
    score_color = result.rating_color or COLOR_UNRATED
    score_text = str(result.total_score) if result.total_score is not None else "--"
    draw.text((padding + px(32), y + px(72)), score_text, font=f_score,
              fill=hex_to_rgb(score_color))
    draw.text((padding + px(32) + px(200), y + px(110)), "分", font=f_subtitle,
              fill=hex_to_rgb(COLOR_SUBTEXT))
    rating_text = result.rating
    draw.text((padding + px(380), y + px(96)), rating_text, font=scaled_font(44, bold=True),
              fill=hex_to_rgb(score_color))

    # 统计
    stats = [
        ("有效组合", result.valid_count, COLOR_ACCENT),
        ("吉星组合", result.auspicious_count, COLOR_AUSPICIOUS),
        ("凶星组合", result.inauspicious_count, COLOR_INAUSPICIOUS),
        ("未评定组合", result.unrated_count + result.unmatched_count, COLOR_UNRATED),
    ]
    stat_x = padding + px(780)
    for label, count, color in stats:
        draw.text((stat_x, y + px(70)), label, font=f_small,
                  fill=hex_to_rgb(COLOR_SUBTEXT))
        draw.text((stat_x, y + px(104)), str(count), font=scaled_font(36, bold=True),
                  fill=hex_to_rgb(color))
        stat_x += px(260)
    y += score_height + px(24)

    # ===== 数字组合明细表 =====
    table_title = "数字组合分析明细"
    draw.text((padding, y), table_title, font=f_heading,
              fill=hex_to_rgb(COLOR_TEXT))
    y += px(52)

    col_widths = [px(w) for w in (120, 180, 240, 180, 240, 200)]
    col_x = [padding]
    for w in col_widths:
        col_x.append(col_x[-1] + w)
    table_width = sum(col_widths)

    # 表头
    draw.rounded_rectangle(
        [padding, y, padding + table_width, y + table_header_height],
        radius=px(12), fill=hex_to_rgb("#E8EEF5"),
    )
    headers = ["序号", "数字组合", "星名", "等级", "属性", "组合分数"]
    for i, header in enumerate(headers):
        draw.text((col_x[i] + px(20), y + px(16)), header, font=f_table_header,
                  fill=hex_to_rgb(COLOR_TEXT))
    y += table_header_height

    # 数据行
    for idx, c in enumerate(combos):
        row_bg = COLOR_CARD_BG if idx % 2 == 0 else "#FAFBFC"
        draw.rectangle(
            [padding, y, padding + table_width, y + row_height],
            fill=hex_to_rgb(row_bg),
        )
        draw.line(
            [padding, y + row_height, padding + table_width, y + row_height],
            fill=hex_to_rgb(COLOR_BORDER), width=px(1),
        )

        # 数字颜色按属性
        if c.status == "matched" and c.nature == AUSPICIOUS:
            number_color = COLOR_AUSPICIOUS
        elif c.status == "matched" and c.nature == INAUSPICIOUS:
            number_color = COLOR_INAUSPICIOUS
        else:
            number_color = COLOR_UNRATED

        values = [
            str(idx + 1), c.number, c.star, c.level, c.nature,
            (f"{c.score:+d}" if c.counted else "--"),
        ]
        # 星名颜色
        for i, value in enumerate(values):
            color = hex_to_rgb(COLOR_TEXT)
            font = f_body
            if i == 1:
                color = hex_to_rgb(number_color)
                font = scaled_font(24, bold=True)
            elif i == 2:
                color = hex_to_rgb(number_color)
            elif i == 5:
                color = hex_to_rgb(number_color)
            draw.text((col_x[i] + px(20), y + px(14)), value, font=font, fill=color)
        y += row_height

    img.save(str(output_path), format="PNG", dpi=IMAGE_DPI)
    return output_path


def default_image_path(result: AnalysisResult) -> Path:
    """生成默认图片保存路径（exports 目录，文件名含时间戳）。"""
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_input = "".join(
        ch for ch in result.cleaned_input if ch.isalnum()
    )[:20] or "result"
    return app_path("exports") / f"数字能量详情_{safe_input}_{ts}.png"
