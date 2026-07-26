"""
AURA Fact Extractor
After each normal conversation turn, asks the local model to notice any
durable personal facts/preferences worth remembering long-term, and
saves them automatically -- no "remember:" command needed.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Brain"))
from chat_engine import ask_aura  # noqa: E402

import db  # noqa: E402


def extract_and_save_facts(user_message: str, assistant_reply: str):
    """
    Look at the latest exchange and save any clear, durable facts about
    the user (preferences, goals, important details) to long-term memory.
    Returns a list of (key, value) tuples that were actually saved, so
    the caller can tell the user transparently what was remembered.
    """
    prompt = [
        {"role": "system", "content": (
            "Look at this single exchange between a user and their AI "
            "assistant. If the user revealed any durable personal fact, "
            "preference, or goal worth remembering long-term (e.g. their "
            "name, a preference, an allergy, a goal, their job, a "
            "recurring detail about their life or business), output it "
            "as one 'key: value' pair per line, using short snake_case "
            "keys. If nothing durable was mentioned, output exactly: NONE. "
            "Do not invent anything. Do not save one-off trivia, small "
            "talk, or anything not clearly meant to be remembered."
        )},
        {"role": "user", "content": f"User said: {user_message}\nAssistant replied: {assistant_reply}"},
    ]

    result = ask_aura(prompt).strip()

    if not result or result.upper() == "NONE":
        return []

    saved = []
    for line in result.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key and value and key.upper() != "NONE":
            db.set_preference(key, value)
            saved.append((key, value))

    return saved