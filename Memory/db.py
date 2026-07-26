"""
AURA Memory Engine
Handles all long-term storage of conversations in SQLite.
This is Phase 1/2 memory: simple conversation logging + recall.
Phase 6 adds tasks. Phase 7 adds goals with step tracking.
"""

import sqlite3
import os
from datetime import datetime

# DB lives in Database/ folder at the project root
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "Database", "aura.db")


def init_db():
    """Create the database and tables if they don't already exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goal_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (goal_id) REFERENCES goals(id)
        )
    """)

    conn.commit()
    conn.close()


def save_message(role: str, content: str):
    """Save a single message (user or assistant) to memory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (role, content, timestamp) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_recent_history(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()

    rows.reverse()
    return [{"role": role, "content": content} for role, content in rows]


def set_preference(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO preferences (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
    """, (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_preference(key: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_all_preferences():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM preferences")
    rows = cursor.fetchall()
    conn.close()
    return {k: v for k, v in rows}


def get_message_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversations")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_oldest_messages(limit: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, role, content FROM conversations ORDER BY id ASC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"id": i, "role": role, "content": content} for i, role, content in rows]


def delete_messages(ids: list):
    if not ids:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in ids)
    cursor.execute(f"DELETE FROM conversations WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()


def save_summary(content: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO summaries (content, created_at) VALUES (?, ?)",
        (content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_all_summaries():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM summaries ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def add_task(description: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (description, status, created_at) VALUES (?, 'pending', ?)",
        (description, datetime.now().isoformat())
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id


def list_tasks(include_done: bool = False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if include_done:
        cursor.execute("SELECT id, description, status FROM tasks ORDER BY id ASC")
    else:
        cursor.execute("SELECT id, description, status FROM tasks WHERE status='pending' ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": i, "description": d, "status": s} for i, d, s in rows]


def complete_task(task_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET status='done', completed_at=? WHERE id=? AND status='pending'",
        (datetime.now().isoformat(), task_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def create_goal(description: str, steps: list) -> int:
    """Create a new goal with an ordered list of step descriptions. Returns goal id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO goals (description, status, created_at) VALUES (?, 'active', ?)",
        (description, datetime.now().isoformat())
    )
    goal_id = cursor.lastrowid
    for i, step in enumerate(steps, start=1):
        cursor.execute(
            "INSERT INTO goal_steps (goal_id, step_number, description, status) "
            "VALUES (?, ?, ?, 'pending')",
            (goal_id, i, step)
        )
    conn.commit()
    conn.close()
    return goal_id


def get_goals(include_done: bool = False):
    """Return goals with their step-completion progress."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if include_done:
        cursor.execute("SELECT id, description, status FROM goals ORDER BY id ASC")
    else:
        cursor.execute("SELECT id, description, status FROM goals WHERE status='active' ORDER BY id ASC")
    goal_rows = cursor.fetchall()

    results = []
    for goal_id, description, status in goal_rows:
        cursor.execute("SELECT COUNT(*) FROM goal_steps WHERE goal_id=?", (goal_id,))
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM goal_steps WHERE goal_id=? AND status='done'", (goal_id,))
        done = cursor.fetchone()[0]
        results.append({
            "id": goal_id, "description": description, "status": status,
            "done_steps": done, "total_steps": total
        })
    conn.close()
    return results


def get_goal_steps(goal_id: int):
    """Return all steps for a goal, in order."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT step_number, description, status FROM goal_steps "
        "WHERE goal_id=? ORDER BY step_number ASC",
        (goal_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"step_number": n, "description": d, "status": s} for n, d, s in rows]


def complete_step(goal_id: int, step_number: int) -> bool:
    """
    Mark a specific step done. If that was the last remaining step,
    the parent goal is automatically marked done too.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE goal_steps SET status='done' WHERE goal_id=? AND step_number=? AND status='pending'",
        (goal_id, step_number)
    )
    updated = cursor.rowcount > 0

    if updated:
        cursor.execute(
            "SELECT COUNT(*) FROM goal_steps WHERE goal_id=? AND status='pending'",
            (goal_id,)
        )
        remaining = cursor.fetchone()[0]
        if remaining == 0:
            cursor.execute(
                "UPDATE goals SET status='done', completed_at=? WHERE id=?",
                (datetime.now().isoformat(), goal_id)
            )

    conn.commit()
    conn.close()
    return updated