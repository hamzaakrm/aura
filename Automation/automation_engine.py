"""
AURA Automation Engine (Phase 4)
Lets AURA open applications and manage files on your computer.
Only runs when automation mode is explicitly turned on in the chat,
and every action gets written to Logs/activity.log for your own record.
"""

import os
import subprocess
import shutil
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Config"))
import settings  # noqa: E402

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "Logs", "activity.log")


def _log(action: str):
    """Append a timestamped line describing what AURA just did."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {action}\n")


def open_app(app_name: str) -> str:
    """Open an application by name (e.g. 'notepad', 'chrome') or a full path."""
    try:
        os.startfile(app_name)
        _log(f"Opened app: {app_name}")
        return f"Opened {app_name}."
    except FileNotFoundError:
        try:
            subprocess.Popen(["start", "", app_name], shell=True)
            _log(f"Opened app via shell: {app_name}")
            return f"Opened {app_name}."
        except Exception as e:
            return f"Couldn't open '{app_name}': {e}"
    except Exception as e:
        return f"Couldn't open '{app_name}': {e}"


def list_files(path: str) -> str:
    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        return f"'{path}' is not a valid folder."
    entries = os.listdir(path)
    _log(f"Listed folder: {path}")
    if not entries:
        return f"'{path}' is empty."
    lines = []
    for e in sorted(entries):
        full = os.path.join(path, e)
        tag = "[DIR] " if os.path.isdir(full) else "      "
        lines.append(f"{tag}{e}")
    return "\n".join(lines)


def create_folder(path: str) -> str:
    path = os.path.expanduser(path)
    try:
        os.makedirs(path, exist_ok=True)
        _log(f"Created folder: {path}")
        return f"Folder ready: {path}"
    except Exception as e:
        return f"Couldn't create folder: {e}"


def move_item(src: str, dst: str) -> str:
    src, dst = os.path.expanduser(src), os.path.expanduser(dst)
    if not os.path.exists(src):
        return f"Source not found: {src}"
    try:
        shutil.move(src, dst)
        _log(f"Moved: {src} -> {dst}")
        return f"Moved {src} -> {dst}"
    except Exception as e:
        return f"Couldn't move: {e}"


def copy_item(src: str, dst: str) -> str:
    src, dst = os.path.expanduser(src), os.path.expanduser(dst)
    if not os.path.exists(src):
        return f"Source not found: {src}"
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        _log(f"Copied: {src} -> {dst}")
        return f"Copied {src} -> {dst}"
    except Exception as e:
        return f"Couldn't copy: {e}"


def delete_item(path: str) -> str:
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return f"Not found: {path}"
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        _log(f"Deleted: {path}")
        return f"Deleted: {path}"
    except Exception as e:
        return f"Couldn't delete: {e}"


def search_files(query: str, root: str) -> str:
    root = os.path.expanduser(root)
    if not os.path.isdir(root):
        return f"'{root}' is not a valid folder."
    matches = []
    query_lower = query.lower()
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames + dirnames:
            if query_lower in name.lower():
                matches.append(os.path.join(dirpath, name))
        if len(matches) >= 50:
            break
    _log(f"Searched for '{query}' in {root} ({len(matches)} matches)")
    if not matches:
        return f"No matches for '{query}' under {root}."
    return "\n".join(matches[:50])