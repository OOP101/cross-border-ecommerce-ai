"""文本工具：中英混合分词。"""
import re
from typing import List

_CJK = re.compile(r"[\u4e00-\u9fff]")
_WORD = re.compile(r"[a-zA-Z0-9]+")


def tokenize(text: str) -> List[str]:
    """将文本切分为 token：英文按单词，中文按相邻二字 bigram。"""
    text = text.lower()
    tokens = _WORD.findall(text)
    cjk = _CJK.findall(text)
    tokens.extend(cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1))
    if len(cjk) == 1:
        tokens.append(cjk[0])
    return tokens
