"""
AURA Brain
Wraps calls to the local Ollama model.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Config"))
import settings  # noqa: E402

try:
    import ollama
except ImportError:
    print("The 'ollama' package isn't installed. Run: pip install ollama")
    sys.exit(1)


def ask_aura(messages: list):
    """
    Send a full message list (system + history + new user message)
    to the local model and return its reply as plain text.
    """
    try:
        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
            options={"num_ctx": settings.CONTEXT_WINDOW},
        )
        return response["message"]["content"]
    except Exception as e:
        return (
            f"[AURA could not reach the local model: {e}]\n"
            f"Make sure Ollama is running and you've pulled the model: "
            f"ollama pull {settings.OLLAMA_MODEL}"
        )
