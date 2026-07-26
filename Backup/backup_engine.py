"""
AURA Backup System
Snapshots your database and knowledge base into timestamped folders
under Backup/, and lets you restore from any snapshot if something
ever goes wrong. Purely local -- nothing leaves your computer.
"""

import os
import shutil
from datetime import datetime

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "Backup")
DATABASE_DIR = os.path.join(os.path.dirname(__file__), "..", "Database")
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "Knowledge")


def create_backup() -> str:
    """Create a timestamped snapshot of the database and knowledge base. Returns its name."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"backup_{timestamp}"
    dest = os.path.join(BACKUP_DIR, name)
    os.makedirs(dest, exist_ok=True)

    db_path = os.path.join(DATABASE_DIR, "aura.db")
    if os.path.isfile(db_path):
        shutil.copy2(db_path, os.path.join(dest, "aura.db"))

    if os.path.isdir(KNOWLEDGE_DIR):
        shutil.copytree(KNOWLEDGE_DIR, os.path.join(dest, "Knowledge"), dirs_exist_ok=True)

    return name


def list_backups() -> list:
    """Return backup names, most recent first."""
    if not os.path.isdir(BACKUP_DIR):
        return []
    names = [
        d for d in os.listdir(BACKUP_DIR)
        if d.startswith("backup_") and os.path.isdir(os.path.join(BACKUP_DIR, d))
    ]
    return sorted(names, reverse=True)


def restore_backup(name: str) -> bool:
    """
    Restore the database and knowledge base from a named backup,
    overwriting the current ones. Returns True if the backup existed
    and was restored.
    """
    src = os.path.join(BACKUP_DIR, name)
    if not os.path.isdir(src):
        return False

    db_src = os.path.join(src, "aura.db")
    if os.path.isfile(db_src):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        shutil.copy2(db_src, os.path.join(DATABASE_DIR, "aura.db"))

    knowledge_src = os.path.join(src, "Knowledge")
    if os.path.isdir(knowledge_src):
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        shutil.copytree(knowledge_src, KNOWLEDGE_DIR, dirs_exist_ok=True)

    return True