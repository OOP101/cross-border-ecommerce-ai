"""配置自检：无需 API Key，报告当前 LLM / Embedding / 鉴权 / 向量库 实际生效状态。

用法：
    cd backend
    .venv/Scripts/python.exe scripts/check_config.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.core.embeddings.factory import get_embedding
from app.core.llm.factory import get_llm


def _status(impl_name: str) -> str:
    return "真实模型" if impl_name != "mock" else "离线 Mock"


def main() -> None:
    llm = get_llm()
    emb = get_embedding()
    print("=" * 56)
    print("  国际贸易智能服务平台 · 配置自检")
    print("=" * 56)
    print(f"  LLM 提供方        : {settings.LLM_PROVIDER}")
    print(f"  LLM 模型          : {settings.LLM_MODEL}")
    print(f"  LLM 实际实现      : {llm.name}  ->  {_status(llm.name)}")
    print(f"  Embedding 实际实现: {emb.name}  ->  {_status(emb.name)}")
    print(f"  向量库            : {settings.VECTOR_STORE}")
    print(f"  RAG 重排序        : {'开启' if settings.ENABLE_RERANK else '关闭(启发式)'}")
    print(f"  鉴权开关          : {'开启' if settings.AUTH_REQUIRED else '关闭(演示免登录)'}")
    print("=" * 56)

    if llm.name == "mock":
        print("\n[提示] 未配置 LLM_API_KEY，当前为离线演示模式（文案/客服/翻译返回占位文本）。")
        print("       接入真实模型只需在 backend/.env 设置：")
        print("         LLM_PROVIDER=openai_compatible")
        print("         LLM_API_KEY=sk-xxx")
        print("         LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  # 通义千问")
        print("         LLM_MODEL=qwen-plus")
    else:
        print("\n[OK] 已加载真实 LLM 实现，文案/客服/翻译将基于企业知识库生成真实内容。")

    if emb.name == "mock":
        print("\n[提示] Embedding 为离线哈希向量，向量检索仅具可运行骨架；")
        print("       接入真实嵌入（EMBEDDING_PROVIDER=openai_compatible）后 RAG 才具备语义检索能力。")

    if not settings.AUTH_REQUIRED:
        print("\n[提示] 鉴权当前关闭。生产环境请在 .env 设置 AUTH_REQUIRED=true 并更换 JWT_SECRET_KEY。")
    print()


if __name__ == "__main__":
    main()
