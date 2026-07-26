"""
AURA Planning Engine (Phase 7)
Breaks a high-level goal into a clear, ordered list of concrete steps
using your local model. AURA tracks progress on these steps, but you
stay in control -- it doesn't execute file/automation actions on its
own without you triggering each one yourself.
"""

import os
import sys
import re

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Config"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Brain"))
import settings                   # noqa: E402
from chat_engine import ask_aura  # noqa: E402


def plan_goal(goal_description: str) -> list:
    """
    Ask the local model to break a goal into ordered, actionable steps.
    Returns a list of step description strings.
    """
    prompt = [
        {"role": "system", "content": (
            "Break the user's goal into a clear, ordered list of concrete, "
            "actionable steps. Return ONLY a numbered list, one step per "
            "line, no extra commentary, no headers. Keep each step "
            "specific and doable. Aim for 4 to 8 steps."
        )},
        {"role": "user", "content": f"Goal: {goal_description}"},
    ]
    raw = ask_aura(prompt)

    steps = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^\d+[\.\)]\s*(.*)", line)
        if match:
            steps.append(match.group(1).strip())
        elif line.startswith(("-", "*")):
            steps.append(line[1:].strip())
        else:
            steps.append(line)

    return steps if steps else [raw.strip()]