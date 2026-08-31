"""RAG 检索质量离线评估：对评测集逐条检索，计算 Recall@K 与 MRR。

用法：
    python scripts/eval_rag.py                # 使用 data/eval/rag_eval.json
    python scripts/eval_rag.py --topk 5       # 指定评估的 K
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.rag.retriever import get_retriever  # noqa: E402

EVAL_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "rag_eval.json"


def is_hit(chunk_text: str, must_keywords: list) -> bool:
    text = chunk_text.lower()
    return all(kw.lower() in text for kw in must_keywords)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topk", type=int, default=5)
    args = parser.parse_args()
    k = args.topk

    cases = json.loads(EVAL_PATH.read_text(encoding="utf-8"))["cases"]
    retriever = get_retriever()

    recall_hits = 0
    rr_total = 0.0
    total_ms = 0
    details = []

    for case in cases:
        start = time.time()
        results = retriever.retrieve(case["query"], top_k=k)
        total_ms += int((time.time() - start) * 1000)

        rank = 0
        for i, item in enumerate(results, 1):
            if is_hit(item["text"], case["must"]):
                rank = i
                break

        hit = rank > 0
        recall_hits += hit
        rr_total += 1.0 / rank if rank else 0.0
        details.append({"query": case["query"], "hit_rank": rank})

    n = len(cases)
    print(f"评测集：{n} 条 | K={k}")
    print(f"Recall@{k} : {recall_hits}/{n} = {recall_hits / n:.1%}")
    print(f"MRR@{k}    : {rr_total / n:.3f}")
    print(f"平均检索耗时: {total_ms / n:.1f} ms")
    print("-" * 46)
    for d in details:
        mark = f"✔ rank={d['hit_rank']}" if d["hit_rank"] else "✘ 未命中"
        print(f"{mark:<12} {d['query']}")

    misses = [d["query"] for d in details if not d["hit_rank"]]
    if misses:
        print("-" * 46)
        print("未命中样例（用于优化召回）:")
        for q in misses:
            print(f"  - {q}")


if __name__ == "__main__":
    main()
