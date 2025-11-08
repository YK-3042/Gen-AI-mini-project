import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "db.sqlite")


def get_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()

    # Admin table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            must_change_password BOOLEAN DEFAULT 0
        )
    """)

    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'processing',
            chunks_count INTEGER DEFAULT 0
        )
    """)

    # History table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            sources_json TEXT,
            used_documents BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Vector metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vector_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vector_id INTEGER NOT NULL,
            doc_id INTEGER,
            chunk_id INTEGER,
            text_snippet TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents(id)
        )
    """)

    conn.commit()
    conn.close()


def create_admin_user(username: str,
                      password_hash: str,
                      must_change: bool = False) -> bool:
    """Create admin user, return True if created, False if exists"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO admin (username, password_hash, must_change_password) VALUES (?, ?, ?)",
            (username, password_hash, 1 if must_change else 0))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_admin_user(username: str) -> Optional[Dict]:
    """Get admin user by username"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE username = ?", (username, ))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_admin_password(username: str, new_password_hash: str):
    """Update admin password"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE admin SET password_hash = ?, must_change_password = 0 WHERE username = ?",
        (new_password_hash, username))
    conn.commit()
    conn.close()


def add_document(filename: str) -> int:
    """Add document record, return document ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (filename, status) VALUES (?, 'processing')",
        (filename, ))
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def update_document_status(doc_id: int, status: str, chunks_count: int = 0):
    """Update document processing status"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET status = ?, chunks_count = ? WHERE id = ?",
        (status, chunks_count, doc_id))
    conn.commit()
    conn.close()


def get_documents() -> List[Dict]:
    """Get all documents"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_history(query: str, response: str, sources: List[Dict],
                used_documents: bool):
    """Add query to history"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (query, response, sources_json, used_documents) VALUES (?, ?, ?, ?)",
        (query, response, json.dumps(sources), 1 if used_documents else 0))
    conn.commit()
    conn.close()


def get_history(limit: int = 20) -> List[Dict]:
    """Get recent history"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?",
                   (limit, ))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        item = dict(row)
        if item.get('sources_json'):
            try:
                item['sources'] = json.loads(item['sources_json'])
            except:
                item['sources'] = []
        else:
            item['sources'] = []
        history.append(item)

    return history


def clear_history():
    """Delete all chat history"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history")
    conn.commit()
    conn.close()


def delete_history_item(history_id: int) -> bool:
    """Delete a specific history entry"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history WHERE id = ?", (history_id, ))
        conn.commit()
        deleted_rows = cursor.rowcount
        conn.close()
        return deleted_rows > 0
    except Exception as e:
        print(f"DB delete error: {e}")
        return False


def add_vector_metadata(vector_id: int, doc_id: int, chunk_id: int,
                        text_snippet: str):
    """Add vector metadata"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vector_metadata (vector_id, doc_id, chunk_id, text_snippet) VALUES (?, ?, ?, ?)",
        (vector_id, doc_id, chunk_id, text_snippet))
    conn.commit()
    conn.close()


def get_vector_metadata(vector_ids: List[int]) -> List[Dict]:
    """Get metadata for vector IDs"""
    if not vector_ids:
        return []

    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(vector_ids))
    cursor.execute(
        f"""
        SELECT vm.*, d.filename
        FROM vector_metadata vm
        LEFT JOIN documents d ON vm.doc_id = d.id
        WHERE vm.vector_id IN ({placeholders})
    """, vector_ids)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_vector_metadata() -> List[Tuple[int, str, int, int, str]]:
    """Get all vector metadata for rebuilding index"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vm.vector_id, d.filename, vm.chunk_id, vm.doc_id, vm.text_snippet
        FROM vector_metadata vm
        LEFT JOIN documents d ON vm.doc_id = d.id
        ORDER BY vm.vector_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows]


def health_check() -> bool:
    """Check database health"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True
    except:
        return False


def clear_history():
    """Delete all chat history records"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        print("✅ Chat history cleared successfully.")
        return True
    except Exception as e:
        print(f"❌ Error clearing history: {e}")
        return False
