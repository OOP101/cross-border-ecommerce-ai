"""OpenAI 兼容接口 LLM：DeepSeek、小米 MiMo、通义千问(DashScope)、OpenAI、Moonshot 等均可接入。

支持故障转移：构造时传入 fallbacks（备用端点列表），主端点出现连接失败/超时/429/5xx 时
自动按序切换，流式与非流式均生效；流式一旦已产出片段则不再切换（避免内容重复）。
"""
import json
import logging
from typing import Iterator, List, Optional

import httpx

from .base import BaseLLM, LLMResult

logger = logging.getLogger(__name__)

# 视为「端点状态异常」、值得切换备用端点的 HTTP 状态码。
# 401/403 表示主端点密钥失效/无权限——切到密钥有效的备用端点可恢复服务；
# 若全部端点都失败，最终仍抛出最后一个异常。
_SWITCHABLE_STATUS = {401, 403, 408, 409, 425, 429, 500, 502, 503, 504}


class OpenAICompatibleLLM(BaseLLM):
    name = "openai_compatible"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.7,
        timeout: float = 60.0,
        fallbacks: Optional[List[dict]] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        # 备用端点：[{"base_url": ..., "api_key": ..., "model": ...}, ...]
        self.fallbacks = fallbacks or []

    # ---- 端点链与异常判定 ----
    def _endpoints(self):
        """按优先级产出全部端点：主端点在前，备用端点在后。"""
        yield (self.base_url, self.api_key, self.model)
        for fb in self.fallbacks:
            yield (fb["base_url"].rstrip("/"), fb["api_key"], fb["model"])

    @staticmethod
    def _is_switchable(exc: Exception) -> bool:
        """端点状态异常判定：网络连接类错误，或 401/403(密钥失效)/408/429/5xx 等服务端故障。
        400 等请求本身的问题不切换(换端点同样会失败)。"""
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in _SWITCHABLE_STATUS
        return isinstance(
            exc,
            (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout,
             httpx.WriteTimeout, httpx.PoolTimeout, httpx.RemoteProtocolError),
        )

    def _headers(self, api_key: str) -> dict:
        # 同时携带 Authorization 与 api-key：小米 MiMo 平台使用 api-key 头，
        # 其余 OpenAI 兼容厂商使用 Bearer，多发的头会被正常厂商忽略。
        return {"Authorization": f"Bearer {api_key}", "api-key": api_key}

    def _build_payload(self, prompt: str, system=None, model: str = None, **kwargs):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": model or self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
        }

    def _parse(self, data: dict) -> LLMResult:
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResult(content=content, raw=data, usage=usage)

    # ---- 非流式 ----
    def generate(self, prompt, system=None, **kwargs):
        last_exc: Optional[Exception] = None
        for idx, (base_url, api_key, model) in enumerate(self._endpoints()):
            try:
                url = f"{base_url}/chat/completions"
                payload = self._build_payload(prompt, system, model=model, **kwargs)
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload, headers=self._headers(api_key))
                    resp.raise_for_status()
                if idx > 0:
                    logger.info("已切换至备用端点 #%s(%s)", idx, model)
                return self._parse(resp.json())
            except Exception as e:  # noqa: BLE001
                if not self._is_switchable(e):
                    raise
                last_exc = e
                logger.warning("LLM 端点异常(%s: %s)，尝试备用端点 %s", type(e).__name__, e, model)
        raise last_exc

    # ---- 流式 ----
    def _stream_single_events(self, base_url, api_key, model, prompt, system, **kwargs):
        """单端点流式事件：逐段产出 (kind, text)。
        kind ∈ {"reasoning", "content"}：推理型模型（DeepSeek-R、小米 MiMo-V2.5-Pro 等）
        思考期 `delta.content` 为空、`delta.reasoning_content` 持续产出；
        两类都实时转发，客户端在思考期即可感知连接与进度，不会“假死”。
        """
        url = f"{base_url}/chat/completions"
        payload = self._build_payload(prompt, system, model=model, **kwargs)
        payload["stream"] = True
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, json=payload, headers=self._headers(api_key)) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if not data:
                        continue
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or [{}]
                    delta = choices[0].get("delta") or {}
                    reasoning = delta.get("reasoning_content")
                    if reasoning:
                        yield ("reasoning", reasoning)
                    piece = delta.get("content")
                    if piece:
                        yield ("content", piece)

    def _iter_events(self, prompt, system=None, **kwargs) -> Iterator[tuple]:
        """事件流主循环：首个事件前的异常可触发端点切换；
        已开始产出后发生异常则直接抛出（重开会重复内容）。"""
        last_exc: Optional[Exception] = None
        for idx, (base_url, api_key, model) in enumerate(self._endpoints()):
            try:
                stream = self._stream_single_events(base_url, api_key, model, prompt, system, **kwargs)
                first = next(stream)  # 连接 + 首事件阶段暴露端点异常
            except StopIteration:
                return
            except Exception as e:  # noqa: BLE001
                if not self._is_switchable(e):
                    raise
                last_exc = e
                logger.warning("LLM 流式端点异常(%s: %s)，尝试备用端点 %s", type(e).__name__, e, model)
                continue
            if idx > 0:
                logger.info("已切换至备用流式端点 #%s(%s)", idx, model)
            yield first
            yield from stream
            return
        if last_exc:
            raise last_exc

    def stream_events(self, prompt, system=None, **kwargs) -> Iterator[tuple]:
        """流式事件：(kind, text)，kind ∈ reasoning | content。"""
        return self._iter_events(prompt, system=system, **kwargs)

    def generate_stream(self, prompt, system=None, **kwargs) -> Iterator[str]:
        """仅取最终答案正文增量（不输出思考过程），向后兼容历史调用方。"""
        for kind, piece in self._iter_events(prompt, system=system, **kwargs):
            if kind == "content":
                yield piece
