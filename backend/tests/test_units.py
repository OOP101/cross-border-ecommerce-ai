"""单元测试：纯函数与核心组件，无外部服务依赖。运行方式同 test_smoke.py。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.llm.base import LLMResult, extract_usage  # noqa: E402
from app.core.llm.mock import MockLLM  # noqa: E402
from app.core.security import create_access_token, decode_access_token, pwd_hash, pwd_verify  # noqa: E402
from app.core.vector_store.memory import MemoryVectorStore  # noqa: E402
from app.services.rag.bm25 import BM25  # noqa: E402
from app.services.rag.rerank import rerank  # noqa: E402
from app.utils.chunking import chunk_text  # noqa: E402
from app.utils.text_utils import tokenize  # noqa: E402


# ---- 分块 ----
def test_chunk_size_and_overlap():
    text = "。".join(["这是一段测试句子内容较长一些"] * 50) + "。"
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert chunks, "应至少产出一个分块"
    assert all(len(c) <= 120 for c in chunks), "分块不应明显超过 chunk_size"


def test_chunk_empty():
    assert chunk_text("", 500, 128) == []
    assert chunk_text("   \n\n  ", 500, 128) == []


def test_chunk_short_single():
    assert chunk_text("短文本", 500, 128) == ["短文本"]


# ---- 分词 ----
def test_tokenize_mixed():
    tokens = tokenize("LED灯带 best seller 物流")
    assert "led" in tokens and "best" in tokens and "seller" in tokens
    assert any(t in tokens for t in ("物流",)), "孤立中文应保留"
    assert any("灯带" == t for t in tokens) or "灯" in tokens


# ---- BM25 ----
def test_bm25_ranking():
    corpus = [
        tokenize("订单发货时间是24小时"),
        tokenize("退货退款政策说明"),
        tokenize("订单发货与物流跟踪说明"),
    ]
    bm25 = BM25()
    bm25.fit(corpus)
    scores = bm25.get_scores(tokenize("订单 发货"))
    assert scores[0] > 0 and scores[2] > 0
    assert scores[1] == 0.0, "不含查询词的文档得分应为 0"


# ---- 重排序 ----
def test_rerank_no_internal_leak():
    items = [
        {"id": "1", "text": "完全无关的内容", "score": 0.9},
        {"id": "2", "text": "订单发货时间说明", "score": 0.1},
    ]
    out = rerank("订单发货", items)
    assert all("_rerank_score" not in item for item in out), "内部打分字段不应出现在结果中"
    assert all(set(item.keys()) == {"id", "text", "score"} for item in out)
    assert out[0]["id"] == "2", "关键词覆盖更高的候选应排前"


# ---- 密码与 JWT ----
def test_password_hash_verify():
    stored = pwd_hash("admin123")
    assert stored.startswith("pbkdf2_sha256$")
    assert pwd_verify("admin123", stored)
    assert not pwd_verify("wrong", stored)


def test_jwt_roundtrip_and_expiry():
    token = create_access_token("alice", expires_min=5)
    payload = decode_access_token(token)
    assert payload and payload["sub"] == "alice"
    assert decode_access_token(token + "x") is None, "篡改签名应解析失败"
    expired = create_access_token("bob", expires_min=-1)
    assert decode_access_token(expired) is None, "过期令牌应解析失败"


# ---- Token 用量提取 ----
def test_extract_usage_prefers_real():
    result = LLMResult(content="hi", usage={"prompt_tokens": 12, "completion_tokens": 34})
    assert extract_usage(result, "prompt", "hi") == (12, 34)


def test_extract_usage_falls_back_to_estimate():
    assert extract_usage(None, "x" * 40, "x" * 8) == (10, 2)
    assert extract_usage(LLMResult(content="x"), "", "") == (1, 1)


# ---- Mock LLM 流式 ----
def test_mock_llm_stream():
    llm = MockLLM()
    pieces = list(llm.generate_stream("介绍下产品", task="chat"))
    assert len(pieces) > 1, "mock 流式应产出多个片段"
    assert "".join(pieces) == llm.generate("介绍下产品", task="chat").content


# ---- 内存向量库 ----
def _fake_vec(seed: float, dim: int = 8):
    import numpy as np

    v = np.full(dim, seed, dtype=np.float32)
    v[0] = seed + 1.0
    return v


def test_vector_store_add_search_delete():
    store = MemoryVectorStore()
    store.add(
        ["a:0", "a:1", "b:0"],
        ["订单发货", "退货政策", "产品参数"],
        [_fake_vec(1.0), _fake_vec(2.0), _fake_vec(9.0)],
        [{"source": "a.md", "doc_id": "a"}, {"source": "a.md", "doc_id": "a"}, {"source": "b.md", "doc_id": "b"}],
    )
    assert store.count() == 3

    hits = store.search(_fake_vec(9.0), top_k=1)
    assert hits[0]["id"] == "b:0", "应命中与查询同向的向量"

    # 同 id 重复添加为覆盖
    store.add(["a:0"], ["订单发货（更新）"], [_fake_vec(1.0)], [{"source": "a.md", "doc_id": "a"}])
    assert store.count() == 3

    # 按 doc_id 精确删除
    store.delete(["a:0", "a:1"])
    assert store.count() == 1
    assert store.list_all()[0]["id"] == "b:0"


# ---- LLM 故障转移 ----
def test_llm_failover_switchable():
    import httpx

    from app.core.llm.openai_compatible import OpenAICompatibleLLM

    llm = OpenAICompatibleLLM(api_key="k", base_url="http://127.0.0.1:9/v1", model="m")
    assert llm._is_switchable(httpx.ConnectError("refused"))
    assert llm._is_switchable(httpx.ConnectTimeout("timeout"))
    req = httpx.Request("POST", "http://x")
    assert llm._is_switchable(httpx.HTTPStatusError("rate", request=req, response=httpx.Response(429, request=req)))
    assert llm._is_switchable(httpx.HTTPStatusError("srv", request=req, response=httpx.Response(502, request=req)))
    # 401/403 表示主端点密钥失效,应切换到有效备用端点;400 属请求本身问题,不切换
    assert llm._is_switchable(httpx.HTTPStatusError("auth", request=req, response=httpx.Response(401, request=req)))
    assert llm._is_switchable(httpx.HTTPStatusError("forbid", request=req, response=httpx.Response(403, request=req)))
    assert not llm._is_switchable(httpx.HTTPStatusError("bad", request=req, response=httpx.Response(400, request=req)))


def test_llm_endpoint_order():
    from app.core.llm.openai_compatible import OpenAICompatibleLLM

    llm = OpenAICompatibleLLM(
        api_key="k", base_url="http://a/v1", model="m1",
        fallbacks=[{"base_url": "http://b/v1", "api_key": "k2", "model": "m2"}],
    )
    eps = list(llm._endpoints())
    assert eps[0] == ("http://a/v1", "k", "m1")
    assert eps[1] == ("http://b/v1", "k2", "m2")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"✔ {fn.__name__}")
    print(f"单元测试全部通过（{len(tests)} 项）。")
