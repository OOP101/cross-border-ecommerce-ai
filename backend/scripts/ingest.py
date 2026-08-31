"""知识库导入脚本：将 data/knowledge 下的文档批量向量化入库。

用法：python scripts/ingest.py
"""
import sys
from pathlib import Path

# 允许以脚本方式运行时导入 app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal, init_db  # noqa: E402
from app.services import knowledge as kb_service  # noqa: E402

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"


def main():
    init_db()
    db = SessionLocal()
    files = sorted(KNOWLEDGE_DIR.glob("*")) if KNOWLEDGE_DIR.exists() else []
    supported = [f for f in files if f.suffix.lower() in kb_service.SUPPORTED_EXT]

    if not supported:
        print(f"未在 {KNOWLEDGE_DIR} 找到可导入文档，请放入 txt/md/csv/pdf/docx 文件。")
        return

    print(f"开始导入 {len(supported)} 个文档...")
    for f in supported:
        try:
            content = f.read_bytes()
            result = kb_service.add_document(db, f.name, content)
            print(f"  ✔ {f.name} -> {result['chunk_count']} 个分块")
        except Exception as e:  # noqa: BLE001
            print(f"  ✘ {f.name} 导入失败：{e}")

    print("导入完成。")


if __name__ == "__main__":
    main()
