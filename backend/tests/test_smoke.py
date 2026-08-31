"""冒烟测试：验证核心接口可正常响应。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import init_db  # noqa: E402
from app.main import app  # noqa: E402

init_db()  # 确保数据表已创建（TestClient 需手动触发）

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_copywriting():
    r = client.post("/api/v1/copywriting/generate", json={
        "copy_type": "product",
        "product_name": "智能LED灯带",
        "selling_points": "RGB变色、App控制",
        "target_market": "欧美",
        "target_language": "en",
    })
    assert r.status_code == 200
    assert "title" in r.json()


def test_translation():
    r = client.post("/api/v1/translation/translate", json={
        "text": "你好，欢迎咨询。",
        "source_language": "zh",
        "target_language": "en",
    })
    assert r.status_code == 200
    assert "translation" in r.json()


def test_chat():
    r = client.post("/api/v1/chat", json={"message": "订单什么时候发货？", "session_id": "test"})
    assert r.status_code == 200
    assert "answer" in r.json()


def test_knowledge_list():
    r = client.get("/api/v1/knowledge")
    assert r.status_code == 200
    assert "documents" in r.json()


def test_admin_status():
    r = client.get("/api/v1/admin/status")
    assert r.status_code == 200
    assert "llm_provider" in r.json()


def test_terminology_persistent():
    # 默认播种的术语应可读
    r = client.get("/api/v1/translation/terminology")
    assert r.status_code == 200
    terms = r.json()["terminology"]
    assert "FOB" in terms and "CIF" in terms

    # 新增术语并再次读取，验证落库
    client.post("/api/v1/translation/terminology", json={
        "term": "DDP", "translations": {"zh": "完税后交货", "en": "Delivered Duty Paid"}, "category": "trade",
    })
    r2 = client.get("/api/v1/translation/terminology")
    assert "DDP" in r2.json()["terminology"]


def test_auth_login_and_me():
    # 演示模式默认播种 admin/admin123
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token

    r_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 200
    assert r_me.json()["sub"] == "admin"

    # 错误密码应 401
    bad = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert bad.status_code == 401


if __name__ == "__main__":
    for name in ("test_health", "test_copywriting", "test_translation", "test_chat",
                 "test_knowledge_list", "test_admin_status",
                 "test_terminology_persistent", "test_auth_login_and_me"):
        fn = globals()[name]
        fn()
        print(f"✔ {name}")
    print("冒烟测试全部通过。")
