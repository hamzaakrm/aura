"""
AURA Learning Engine (Phase 5)
Controlled web search + local knowledge base building.
Only search queries and page fetches go over the internet -- your
conversations, memory, and personal data are never sent anywhere.

Setup:
    pip install duckduckgo-search requests beautifulsoup4
"""

import os
import sys
import re
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Config"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Brain"))
import settings                   # noqa: E402
from chat_engine import ask_aura  # noqa: E402

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "Knowledge")
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "Logs", "activity.log")


def _log(action: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {action}\n")


def search_web(query: str, max_results: int = 5):
    """Search the web via DuckDuckGo (no API key needed). Returns a list of dicts."""
    try:
        from ddgs import DDGS  # current package name
    except ImportError:
        from duckduckgo_search import DDGS  # fallback for older installs
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    _log(f"Web search: {query} ({len(results)} results)")
    return results


def _fetch_page_text(url: str, max_chars: int = 3000) -> str:
    """Download a page and return a rough plain-text extraction."""
    import requests
    from bs4 import BeautifulSoup
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = " ".join(soup.stripped_strings)
        return text[:max_chars]
    except Exception:
        return ""


def _slugify(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")
    return slug or "topic"


def gather_web_context(query: str, max_pages: int = 3, deep: bool = False) -> str:
    """
    Search the web and return raw combined source text, or '' if
    nothing usable was found. When deep=True, searches several angles
    on the topic and reads more pages for broader, more thorough coverage
    -- used by learn_topic() for real research rather than quick lookups.
    """
    if deep:
        queries = [query, f"{query} explained", f"{query} overview", f"{query} latest developments"]
        max_pages = max(max_pages, 8)
        per_page_chars = 2000
    else:
        queries = [query]
        per_page_chars = 3000

    seen_urls = set()
    collected = []
    for q in queries:
        if len(collected) >= max_pages:
            break
        results = search_web(q, max_results=5)
        for r in results:
            if len(collected) >= max_pages:
                break
            url = r.get("href", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            page_text = _fetch_page_text(url, max_chars=per_page_chars)
            if page_text:
                collected.append(f"Source: {r.get('title', '')} ({url})\n{page_text}")

    return "\n\n---\n\n".join(collected)


def should_search(query: str) -> bool:
    """
    Ask the local model whether answering this well would benefit from
    current/external information it might not reliably know (e.g. recent
    events, prices, schedules, specific facts) versus general knowledge
    or personal conversation it can already handle on its own.
    """
    prompt = [
        {"role": "system", "content": (
            "Decide if answering the user's message well would require "
            "current, specific, or up-to-date factual information that "
            "you might not know or might have wrong (e.g. recent events, "
            "prices, schedules, specific product details, statistics, "
            "news). General knowledge, opinions, personal conversation, "
            "or requests unrelated to real-world facts do NOT need this. "
            "Reply with exactly one word: YES or NO."
        )},
        {"role": "user", "content": query},
    ]
    result = ask_aura(prompt).strip().upper()
    return result.startswith("Y")


def save_knowledge(topic: str, content: str) -> str:
    """
    Save any piece of learned content permanently under Knowledge/.
    Shared by learn_topic, quick_search, and the automatic in-chat
    search feature, so nothing AURA searches is ever thrown away.
    Returns the filename it was saved as.
    """
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    filename = f"{_slugify(topic)}.md"
    filepath = os.path.join(KNOWLEDGE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\nLearned on: {datetime.now().isoformat()}\n\n{content}\n")
    _log(f"Saved knowledge: {topic} -> {filename}")
    return filename


def learn_topic(topic: str) -> str:
    """
    Thoroughly research a topic: search from several angles, read up to
    8 unique pages, and ask the local model to write comprehensive,
    well-organized reference notes -- then save them to Knowledge/.
    """
    combined = gather_web_context(topic, deep=True)
    if not combined:
        return f"No usable search results found for '{topic}'."

    prompt = [
        {"role": "system", "content": (
            "You are AURA's learning module. Read the following source "
            "material, gathered from multiple pages and search angles, "
            "and write thorough, well-organized reference notes on the "
            "topic below. Structure it with clear markdown headers, "
            "using whichever of these actually apply based on the "
            "source material: Overview, Key Concepts, History/Background, "
            "Current Applications or Developments, Common Misconceptions, "
            "Related Topics. Be comprehensive and detailed, but only "
            "include facts actually supported by the sources -- never "
            "invent information."
        )},
        {"role": "user", "content": f"Topic: {topic}\n\nSource material from multiple pages:\n{combined}"},
    ]

    summary = ask_aura(prompt)
    filename = save_knowledge(topic, summary)
    return f"Learned about '{topic}' and saved notes to Knowledge/{filename}.\n\n{summary}"


def quick_search(query: str) -> str:
    """
    Search the web and read a couple of top results, then answer the
    query directly. The answer is also saved permanently to Knowledge/,
    just like learn_topic(), so nothing you ask about is forgotten.
    """
    combined = gather_web_context(query)
    if not combined:
        return f"No usable search results found for '{query}'."

    prompt = [
        {"role": "system", "content": (
            "Answer the user's question directly and concisely using the "
            "source material below. Mention the source briefly if relevant."
        )},
        {"role": "user", "content": f"Question: {query}\n\nSource material:\n{combined}"},
    ]

    answer = ask_aura(prompt)
    filename = save_knowledge(query, answer)
    return f"{answer}\n\n(Saved to Knowledge/{filename} for future reference.)"


def recall_topic(topic: str) -> str:
    """Return previously saved knowledge notes on a topic, if any exist."""
    filename = f"{_slugify(topic)}.md"
    filepath = os.path.join(KNOWLEDGE_DIR, filename)
    if not os.path.isfile(filepath):
        return f"No saved knowledge found for '{topic}'. Try: learn: {topic}"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def list_known_topics():
    if not os.path.isdir(KNOWLEDGE_DIR):
        return []
    return [f[:-3] for f in os.listdir(KNOWLEDGE_DIR) if f.endswith(".md")]