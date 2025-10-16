import sqlite3
import os
import json
from typing import Dict, List

BASE = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE, "resumes.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        filename TEXT,
        parsed_json TEXT
      );
    """)
    conn.commit()
    conn.close()

def save_parsed_resume(name: str, filename: str, parsed: Dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO resumes (name, filename, parsed_json) VALUES (?, ?, ?)",
                (name, filename, json.dumps(parsed)))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def get_resume(rid: int) -> Dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, filename, parsed_json FROM resumes WHERE id = ?", (rid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "filename": row[2], "parsed": json.loads(row[3])}

def list_resumes() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, filename, parsed_json FROM resumes ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({"id": r[0], "name": r[1], "filename": r[2], "parsed": json.loads(r[3])})
    return out
