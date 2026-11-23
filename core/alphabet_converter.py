"""字母转换模块。

按照图片底部的字母数字对应规则，将英文字母转换为数字：
A=1, B=2, ..., Z=26。字母不区分大小写。

例如：
    ABC  -> 123
    MILK -> 139112
    GTA  -> 7201
"""

from __future__ import annotations

import re

# A-Z -> 1-26 的映射表（同时包含大写和小写键）
LETTER_TO_NUMBER: dict[str, str] = {
    chr(ord("A") + i): str(i + 1) for i in range(26)
}
LETTER_TO_NUMBER.update({k.lower(): v for k, v in LETTER_TO_NUMBER.copy().items()})

# 允许输入的字符：数字 0-9 与英文字母 A-Z / a-z
VALID_INPUT_PATTERN = re.compile(r"^[0-9A-Za-z]*$")


def is_valid_char(ch: str) -> bool:
    """判断单个字符是否为允许输入的字符（数字或英文字母）。"""
    return len(ch) == 1 and (ch.isdigit() or ch.isalpha() and ch.isascii())


def filter_invalid_chars(text: str) -> str:
    """过滤掉所有非法字符，只保留数字与英文字母。"""
    return "".join(ch for ch in text if is_valid_char(ch))


def is_valid_input(text: str) -> bool:
    """校验整串输入是否合法（只允许数字与英文字母）。"""
    return bool(VALID_INPUT_PATTERN.match(text))


def letters_to_digits(text: str) -> str:
    """将英文字母转换为对应数字，数字保持不变。

    字母不区分大小写。转换按字符逐个进行，每个字母最多产生两位数字。
    """
    result: list[str] = []
    for ch in text:
        if ch.isdigit():
            result.append(ch)
        elif ch in LETTER_TO_NUMBER:
            result.append(LETTER_TO_NUMBER[ch])
        # 非法字符被忽略（调用方应先做校验）
    return "".join(result)


def convert(raw_input: str) -> tuple[str, str, str]:
    """执行完整转换。

    返回 (原始输入, 过滤后的有效输入, 转换后的数字字符串)。
    """
    cleaned = filter_invalid_chars(raw_input)
    digits = letters_to_digits(cleaned)
    return raw_input, cleaned, digits
