"""软件图标生成模块。

设计：字母 E，背景为倾斜的粉紫渐变，带苹果软件图标风格的圆角裁剪。
使用 Pillow 生成高清 PNG 与 Windows ICO，无需外部图片资源。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    from .utils import APP_ROOT
except ImportError:  # 直接以脚本方式运行时
    from utils import APP_ROOT

ICON_DIR = APP_ROOT / "resources" / "icons"
ICON_PNG = ICON_DIR / "app_icon.png"
ICON_ICO = ICON_DIR / "app_icon.ico"

# 配色：粉紫渐变
GRADIENT_START = (255, 143, 178)   # 粉
GRADIENT_MIDDLE = (193, 126, 235)  # 紫粉
GRADIENT_END = (126, 118, 226)     # 紫


def _rounded_mask(size: int, exponent: float = 4.0) -> Image.Image:
    """生成 Apple 图标风格的 squircle（超椭圆）遮罩。

    超椭圆公式 |x/a|^n + |y/b|^n = 1，n=4 时接近 iOS/macOS 应用图标的
    连续圆角效果，比普通圆弧圆角更自然。
    """
    import numpy as np

    yy, xx = np.mgrid[0:size, 0:size]
    # 归一化到 [-1, 1]，留出 1 像素边缘
    a = size / 2 - 1
    nx = np.abs((xx - (size - 1) / 2) / a)
    ny = np.abs((yy - (size - 1) / 2) / a)
    inside = np.power(nx, exponent) + np.power(ny, exponent) <= 1.0
    mask = Image.fromarray((inside * 255).astype("uint8"), mode="L")
    return mask


def _tilted_gradient(size: int) -> Image.Image:
    """生成倾斜（约 30°）的粉紫渐变背景。"""
    import math

    w = h = size
    # 渐变方向向量（倾斜）
    angle = math.radians(35)
    dx, dy = math.cos(angle), math.sin(angle)
    # 投影范围
    max_proj = abs(w * dx) + abs(h * dy)

    image = Image.new("RGB", (w, h))
    pixels = image.load()
    for y in range(h):
        for x in range(w):
            # 相对中心点的投影
            proj = ((x - w / 2) * dx + (y - h / 2) * dy) / max_proj + 0.5
            proj = max(0.0, min(1.0, proj))
            if proj < 0.5:
                t = proj / 0.5
                color = tuple(
                    int(GRADIENT_START[i] + (GRADIENT_MIDDLE[i] - GRADIENT_START[i]) * t)
                    for i in range(3)
                )
            else:
                t = (proj - 0.5) / 0.5
                color = tuple(
                    int(GRADIENT_MIDDLE[i] + (GRADIENT_END[i] - GRADIENT_MIDDLE[i]) * t)
                    for i in range(3)
                )
            pixels[x, y] = color
    return image


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    """寻找粗体英文字体绘制字母 E。"""
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",   # Segoe UI Bold
        "C:/Windows/Fonts/msyhbd.ttc",     # 微软雅黑粗体
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def generate_icon(size: int = 1024) -> Image.Image:
    """生成 RGBA 图标图像（圆角裁剪，带字母 E）。"""
    bg = _tilted_gradient(size)
    # 轻微高光：左上角更亮
    highlight = Image.new("L", (size, size), 0)
    hd = ImageDraw.Draw(highlight)
    hd.ellipse([-size // 4, -size // 3, size, size // 2], fill=40)
    bg = Image.composite(
        Image.new("RGB", (size, size), (255, 255, 255)), bg, highlight
    )

    draw = ImageDraw.Draw(bg)
    font = _find_font(int(size * 0.62))
    # 用锚点精确定位字母中心
    text = "E"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # 稍微偏上，视觉居中
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1] - size * 0.02
    # 柔和阴影
    shadow_offset = int(size * 0.012)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font,
              fill=(120, 60, 150, 180))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    # 圆角裁剪
    rgba = bg.convert("RGBA")
    rgba.putalpha(_rounded_mask(size))
    return rgba


def generate_svg(size: int = 1024) -> str:
    """生成矢量 SVG 图标源码（斜向粉紫渐变 + 字母 E + squircle 裁剪）。

    可直接保存为 app_icon.svg 使用，也可在浏览器中查看。
    """
    # 超椭圆 squircle 路径（n≈4，Apple 风格连续圆角），用三次贝塞尔近似
    s = size
    m = s * 0.055          # 边距
    r = s * 0.23           # 圆角半径
    inset = m + r
    sq = (
        f"M {m:.1f} {inset:.1f} "
        f"C {m:.1f} {m:.1f} {m:.1f} {m:.1f} {inset:.1f} {m:.1f} "
        f"L {s-inset:.1f} {m:.1f} "
        f"C {s-m:.1f} {m:.1f} {s-m:.1f} {m:.1f} {s-m:.1f} {inset:.1f} "
        f"L {s-m:.1f} {s-inset:.1f} "
        f"C {s-m:.1f} {s-m:.1f} {s-m:.1f} {s-m:.1f} {s-inset:.1f} {s-m:.1f} "
        f"L {inset:.1f} {s-m:.1f} "
        f"C {m:.1f} {s-m:.1f} {m:.1f} {s-m:.1f} {m:.1f} {s-inset:.1f} Z"
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 {s} {s}">
  <defs>
    <linearGradient id="pinkPurple" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF8FB2"/>
      <stop offset="50%" stop-color="#C17EEB"/>
      <stop offset="100%" stop-color="#7E76E2"/>
    </linearGradient>
    <clipPath id="squircle"><path d="{sq}"/></clipPath>
  </defs>
  <g clip-path="url(#squircle)">
    <rect width="{s}" height="{s}" fill="url(#pinkPurple)"/>
    <ellipse cx="{s*0.35:.1f}" cy="{s*0.22:.1f}" rx="{s*0.55:.1f}" ry="{s*0.42:.1f}" fill="#FFFFFF" opacity="0.10"/>
    <text x="50%" y="50%" dy="0.35em" text-anchor="middle"
          font-family="Segoe UI Bold, Microsoft YaHei, Arial Bold, sans-serif"
          font-weight="700" font-size="{int(s*0.62)}"
          fill="#FFFFFF" opacity="0.35"
          transform="translate({int(s*0.012)},{int(s*0.012)})">E</text>
    <text x="50%" y="50%" dy="0.35em" text-anchor="middle"
          font-family="Segoe UI Bold, Microsoft YaHei, Arial Bold, sans-serif"
          font-weight="700" font-size="{int(s*0.62)}" fill="#FFFFFF">E</text>
  </g>
</svg>
"""


def ensure_icon_files() -> None:
    """生成并保存图标文件（PNG + ICO + SVG）。"""
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    if not ICON_PNG.exists():
        generate_icon(1024).save(ICON_PNG, format="PNG")
    if not ICON_ICO.exists():
        icon = generate_icon(512)
        icon.save(
            ICON_ICO, format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
        )
    svg_path = ICON_DIR / "app_icon.svg"
    if not svg_path.exists():
        svg_path.write_text(generate_svg(), encoding="utf-8")


@lru_cache(maxsize=1)
def get_app_icon():
    """返回 QIcon 单例（供 QApplication / 窗口使用）。"""
    ensure_icon_files()
    from PyQt5.QtGui import QIcon
    return QIcon(str(ICON_PNG))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    ensure_icon_files()
    print(f"已生成图标：{ICON_PNG} / {ICON_ICO}")
