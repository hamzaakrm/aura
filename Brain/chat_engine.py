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


def ask_aura(messages: list, temperature: float = None):
    """
    Send a full message list (system + history + new user message)
    to the local model and return its reply as plain text.
    """
    try:
        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
            options={
                "num_ctx": settings.CONTEXT_WINDOW,
                "temperature": temperature if temperature is not None else settings.TEMPERATURE,
            },
        )
        return response["message"]["content"]
    except Exception as e:
        return (
            f"[AURA could not reach the local model: {e}]\n"
            f"Make sure Ollama is running and you've pulled the model: "
            f"ollama pull {settings.OLLAMA_MODEL}"
        )


def ask_aura_deep(messages: list) -> str:
    """
    A slower, two-pass 'think harder' mode for genuinely tough questions.
    First asks the model to reason through the problem step by step in
    a scratchpad (not shown to the user), then asks it to write a final,
    polished answer based on that reasoning -- closer to how dedicated
    reasoning models approach hard problems.
    """
    reasoning_prompt = messages + [{
        "role": "system",
        "content": (
            "Before answering, think through this carefully step by step: "
            "break down what's being asked, consider relevant facts or "
            "logic, weigh any tradeoffs or alternative angles, and work "
            "toward a conclusion. Write out this reasoning process now. "
            "Do not give a final answer yet -- just think it through."
        )
    }]
    reasoning = ask_aura(reasoning_prompt, temperature=0.3)

    final_prompt = messages + [{
        "role": "system",
        "content": (
            f"Here is your own careful reasoning about this:\n\n{reasoning}\n\n"
            "Now write your final, clear, well-organized answer for the "
            "user based on that reasoning. Do not repeat the raw "
            "reasoning steps -- just give the polished final response."
        )
    }]
    return ask_aura(final_prompt, temperature=0.4)