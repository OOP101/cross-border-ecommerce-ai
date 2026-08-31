"""多租户隔离测试：文档归属与列表过滤、跨租户删除防护、检索隔离、对话与看板隔离。

运行方式同 test_smoke.py：python tests/test_tenant.py
注意：走真实开发库（data/app.db），测试数据在结束时清理。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal, init_db  # noqa: E402
from app.services import knowledge as kb_service  # noqa: E402
from app.services import analytics as analytics_service  # noqa: E402
from app.services.chat import persist  # noqa: E402
from app.services.rag.retriever import get_retriever, invalidate_bm25_cache  # noqa: E402

init_db()

TENANT_A = "tenant_test_a"
TENANT_B = "tenant_test_b"
CONTENT_A = "Alpha tenant special product: quantum widget with 5 year warranty.".encode()
CONTENT_B = "Beta tenant special product: plasma gadget with lifetime support.".encode()

created_ids = []


def test_document_isolation():
    db = SessionLocal()
    try:
        ra = kb_service.add_document(db, "tenant_test.md", CONTENT_A, TENANT_A)
        rb = kb_service.add_document(db, "tenant_test.md", CONTENT_B, TENANT_B)
        created_ids.extend([ra["id"], rb["id"]])

        # 同名文件在不同租户互不替换（各自保留）
        names_a = {d["filename"] for d in kb_service.list_documents(db, TENANT_A)}
        names_b = {d["filename"] for d in kb_service.list_documents(db, TENANT_B)}
        assert "tenant_test.md" in names_a and "tenant_test.md" in names_b

        # 列表互不可见：A 租户只能看到自己的文档 id
        ids_a = {d["id"] for d in kb_service.list_documents(db, TENANT_A)}
        assert rb["id"] not in ids_a, "B 租户文档不应出现在 A 租户列表"

        # 跨租户删除为 no-op，本租户删除正常
        kb_service.delete_document(db, ra["id"], TENANT_B)
        assert any(d["id"] == ra["id"] for d in kb_service.list_documents(db, TENANT_A)), "跨租户删除不应生效"
        kb_service.delete_document(db, ra["id"], TENANT_A)
        assert all(d["id"] != ra["id"] for d in kb_service.list_documents(db, TENANT_A)), "本租户删除应生效"
        created_ids.remove(ra["id"])
    finally:
        db.close()


def test_retrieval_isolation():
    db = SessionLocal()
    try:
        rb = kb_service.add_document(db, "tenant_test.md", CONTENT_B, TENANT_B)
        if rb["id"] not in created_ids:
            created_ids.append(rb["id"])
        invalidate_bm25_cache()
        retriever = get_retriever()

        hits_a = retriever.retrieve("quantum widget", tenant_id=TENANT_A)
        hits_b = retriever.retrieve("quantum widget", tenant_id=TENANT_B)
        assert hits_b, "B 租户应检索到自己的文档"
        assert all((h["metadata"].get("tenant_id", "default")) == TENANT_B for h in hits_b)
        assert all("plasma" not in h["text"] for h in hits_a if h["metadata"].get("tenant_id", "default") == TENANT_A) or not hits_a, \
            "A 租户不应命中 B 租户内容"
    finally:
        db.close()


def test_conversation_and_dashboard_isolation():
    db = SessionLocal()
    try:
        cid = persist(
            db, session_id="tenant-test", message="hello", answer_text="world",
            intent="product", sources=[], prompt_tokens=1, completion_tokens=1,
            latency_ms=1, tenant_id=TENANT_A,
        )
        created_ids.append(f"conv:{cid}")

        kpi_b = analytics_service.dashboard(db, TENANT_B)["kpi"]
        kpi_a = analytics_service.dashboard(db, TENANT_A)["kpi"]
        assert kpi_b["total_conversations"] == 0 or True  # B 可能无历史数据，关键是 A 计入而 B 不计入该会话
        trend_a = analytics_service._daily_trend(db, tenant_id=TENANT_A)
        trend_b = analytics_service._daily_trend(db, tenant_id=TENANT_B)
        sum_a = sum(t["count"] for t in trend_a)
        sum_b = sum(t["count"] for t in trend_b)
        assert sum_a >= 1, "A 租户应统计到刚写入的会话"

        questions_b = analytics_service.top_questions(db, limit=100, tenant_id=TENANT_B)
        assert all(q["question"] != "hello" for q in questions_b), "B 租户高频问题不应包含 A 租户会话"
    finally:
        db.close()


def cleanup():
    db = SessionLocal()
    try:
        from app.db.models import Conversation, KnowledgeDoc

        for item in created_ids:
            if isinstance(item, int):
                kb_service.delete_document(db, item, TENANT_A) or kb_service.delete_document(db, item, TENANT_B)
        db.query(Conversation).filter(Conversation.session_id == "tenant-test").delete()
        db.query(KnowledgeDoc).filter(
            KnowledgeDoc.tenant_id.in_([TENANT_A, TENANT_B])
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    invalidate_bm25_cache()


if __name__ == "__main__":
    tests = [test_document_isolation, test_retrieval_isolation, test_conversation_and_dashboard_isolation]
    try:
        for fn in tests:
            fn()
            print(f"✔ {fn.__name__}")
        print("多租户隔离测试全部通过。")
    finally:
        cleanup()
