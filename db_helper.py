import sqlite3
import json
from datetime import datetime

DB_PATH = "data/bio_pipeline.db"


def init_db():
    """初始化数据库，创建表（如果不存在）"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proteins (
            uniprot_id TEXT PRIMARY KEY,
            gene_name TEXT,
            function_summary TEXT,
            ai_json TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成：{DB_PATH}")


def get_cached_result(uniprot_id):
    """
    查询缓存。如果存在，返回已解析的 AI 结果字典；否则返回 None。
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT ai_json FROM proteins WHERE uniprot_id = ?", (uniprot_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row[0])
    return None


def save_result(uniprot_id, ai_data):
    """把 AI 分析结果保存到数据库"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT OR REPLACE INTO proteins 
        (uniprot_id, gene_name, function_summary, ai_json, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        uniprot_id,
        ai_data.get("gene_name", "Unknown"),
        ai_data.get("function_summary", ""),
        json.dumps(ai_data, ensure_ascii=False),
        now
    ))
    conn.commit()
    conn.close()

def get_all_ids():
    """
    返回数据库中所有已经分析过的 uniprot_id 列表。
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT uniprot_id FROM proteins ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_cached_result_with_time(uniprot_id):
    """
    查询缓存，返回 (ai_data, created_at)。
    如果不存在，返回 (None, None)。
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ai_json, created_at FROM proteins WHERE uniprot_id = ?",
        (uniprot_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row[0]), row[1]
    return None, None