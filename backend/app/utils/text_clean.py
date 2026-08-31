"""文本清洗与 PII 脱敏。"""
import re
from typing import List

# 噪声清理规则
_NOISE_PATTERNS: List[re.Pattern] = [
    re.compile(r"<[^>]+>"),            # HTML 标签
    re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]"),  # 控制字符
    re.compile(r"[\u200b-\u200d\ufeff]"),  # 零宽字符 / BOM
]

# PII 脱敏规则
_PII_PATTERNS: List[tuple] = [
    (re.compile(r"\b\d{13,19}\b"), "[银行卡]"),                       # 银行卡
    (re.compile(r"\b1[3-9]\d{9}\b"), "[手机号]"),                      # 大陆手机号
    (re.compile(r"\b\d{17}[\dXx]\b"), "[身份证]"),                     # 身份证
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[邮箱]"),  # 邮箱
]


def clean_text(text: str) -> str:
    """去除噪声：HTML、控制字符、零宽字符，合并多余空白。"""
    for p in _NOISE_PATTERNS:
        text = p.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def mask_pii(text: str) -> str:
    """对敏感信息脱敏。"""
    for pattern, repl in _PII_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def sanitize(text: str) -> str:
    """清洗 + 脱敏。"""
    return mask_pii(clean_text(text))
