"""LLM 抽象层：可插拔，支持 mock / OpenAI 兼容接口。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional


@dataclass
class LLMResult:
    """统一的 LLM 返回结构。"""
    content: str
    raw: Any = None
    usage: dict = field(default_factory=dict)


def extract_usage(result: Optional[LLMResult], prompt: str = "", completion: str = "") -> tuple:
    """从 LLM 返回中提取真实 token 用量；缺失时按 len//4 降级估算。"""
    usage = getattr(result, "usage", None) or {}
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    p = int(prompt_tokens) if prompt_tokens else max(1, len(prompt) // 4)
    c = int(completion_tokens) if completion_tokens else max(1, len(completion) // 4)
    return p, c


class BaseLLM(ABC):
    """LLM 接口基类。所有提供商需实现 generate。"""

    name: str = "base"

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        task: Optional[str] = None,
        **kwargs,
    ) -> LLMResult:
        """同步生成。task 用于提示 mock/特定提供商采用对应策略。"""

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        task: Optional[str] = None,
        **kwargs,
    ) -> Iterator[str]:
        """流式生成，逐段产出文本。默认退化为一次性生成。"""
        yield self.generate(prompt, system=system, task=task, **kwargs).content

    async def agenerate(
        self,
        prompt: str,
        system: Optional[str] = None,
        task: Optional[str] = None,
        **kwargs,
    ) -> LLMResult:
        """默认退化为同步调用，异步提供商可覆盖。"""
        return self.generate(prompt, system=system, task=task, **kwargs)
