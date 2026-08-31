"""文本分块：按语义（段落/句子）切分，支持大小与重叠控制。"""
import re
from typing import List

_SENT_SPLIT = re.compile(r"(?<=[。！？!?；;\n])")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 128) -> List[str]:
    """将文本切分为不超过 chunk_size 字符的块，块间重叠 overlap 字符。

    优先按句子边界切分，避免在句中截断。
    """
    text = text.strip()
    if not text:
        return []

    # 先按段落拆分
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    chunks: List[str] = []
    buffer = ""
    for para in paragraphs:
        if len(para) <= chunk_size:
            if buffer and len(buffer) + len(para) + 1 > chunk_size:
                chunks.append(buffer)
                buffer = ""
            buffer = f"{buffer}\n{para}".strip() if buffer else para
        else:
            # 长段落按句子切分
            if buffer:
                chunks.append(buffer)
                buffer = ""
            for sent in _split_sentences(para):
                if len(sent) > chunk_size:
                    chunks.extend(_hard_split(sent, chunk_size, overlap))
                elif buffer and len(buffer) + len(sent) + 1 > chunk_size:
                    chunks.append(buffer)
                    buffer = sent
                else:
                    buffer = f"{buffer} {sent}".strip() if buffer else sent
    if buffer:
        chunks.append(buffer)

    # 应用重叠
    return _apply_overlap(chunks, overlap)


def _split_sentences(para: str) -> List[str]:
    parts = _SENT_SPLIT.split(para)
    return [p.strip() for p in parts if p.strip()]


def _hard_split(text: str, size: int, overlap: int) -> List[str]:
    step = max(size - overlap, 1)
    return [text[i : i + size] for i in range(0, len(text), step) if text[i : i + size].strip()]


def _apply_overlap(chunks: List[str], overlap: int) -> List[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    result = []
    prev_tail = ""
    for c in chunks:
        if prev_tail and prev_tail not in c:
            c = prev_tail + c
        result.append(c)
        prev_tail = c[-overlap:] if len(c) > overlap else ""
    return result
