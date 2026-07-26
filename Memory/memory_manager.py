"""
AURA Memory Manager
Handles turning old raw conversation history into compact summaries,
so long-term memory stays useful without the context window growing forever.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Config"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Brain"))
import settings          # noqa: E402
import db                # noqa: E402
from chat_engine import ask_aura  # noqa: E402


def maybe_summarize():
    """
    Check if enough raw messages have piled up. If so, take the oldest
    chunk, ask the local model to summarize it, save that summary,
    and delete the raw messages it covered.
    Safe to call after every turn — it does nothing until the threshold is hit.
    """
    total = db.get_message_count()
    if total <= settings.SUMMARY_TRIGGER_COUNT:
        return

    chunk = db.get_oldest_messages(settings.SUMMARY_CHUNK_SIZE)
    if not chunk:
        return

    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in chunk)

    summarize_prompt = [
        {"role": "system", "content": (
            "Summarize the following conversation snippet in 3-5 short "
            "sentences. Capture key facts, decisions, preferences, and "
            "goals mentioned. Be concise and factual, no filler."
        )},
        {"role": "user", "content": transcript},
    ]

    summary_text = ask_aura(summarize_prompt)

    db.save_summary(summary_text)
    db.delete_messages([m["id"] for m in chunk])
