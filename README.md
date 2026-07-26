# AURA — Artificial Unified Responsive Assistant

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Offline First](https://img.shields.io/badge/offline--first-yes-brightgreen)

A fully offline, privacy-first personal AI assistant that runs entirely on your own computer. No cloud, no subscriptions, no data ever leaves your machine except deliberate, controlled web searches you explicitly enable.

## Why AURA

Most AI assistants (ChatGPT, Alexa, Siri, Google Assistant) send everything you say to a company's servers. AURA doesn't. Your conversations, memory, and personal data live only on your own disk. You own it completely — no account, no subscription, no company that can shut it down or change the rules.

## Screenshots

<!--
Add real screenshots here once you have them. In your repo:
1. Create a folder called "docs/images" (or "screenshots")
2. Upload a screenshot of the terminal chat and/or the desktop GUI window
3. Reference them like this:

![Terminal chat](docs/images/terminal-chat.png)
![Desktop GUI](docs/images/gui-window.png)
-->

*(Screenshots coming soon)*

## Features

- **Offline AI chat** — powered by a local LLM via [Ollama](https://ollama.com), no internet required
- **Persistent long-term memory** — remembers conversations, preferences, and facts across sessions, with automatic summarization so context never gets lost
- **Automatic fact learning** — notices and remembers durable facts from normal conversation, no special command needed
- **Offline voice** — speech-to-text and text-to-speech, with multi-language support (English, Urdu*, Arabic, Hindi, Spanish, French, German, Chinese)
- **Computer automation** — open apps, manage files and folders, all with activity logging
- **Controlled web research (Learning Mode)** — deep multi-source research on any topic, quick one-off lookups, and automatic mid-conversation search when a question needs current information — everything it learns is saved permanently and fuzzy-searchable later
- **Business toolkit** — product descriptions, SEO keyword research, email drafting, content writing, task management
- **Goal planning** — breaks any goal into concrete, trackable steps
- **Backup & restore** — snapshot and recover your database and knowledge base anytime
- **Desktop GUI** — a proper chat window (PySide6) alongside the terminal version, with clickable mode toggles

*Urdu speech recognition isn't available in the underlying speech engine; Hindi is used as a practical substitute.

## Requirements

- Windows 10/11 (64-bit)
- Python 3.11 or 3.12
- 8GB RAM minimum, 16GB+ recommended
- [Ollama](https://ollama.com) installed, with a model pulled (e.g. `qwen2.5:7b`)

## Setup

```bash
git clone https://github.com/hamzaakrm/aura.git
cd aura
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
ollama pull qwen2.5:7b
python main.py                 # terminal version
python gui.py                  # desktop window version
```

Voice features additionally require downloading a [Vosk](https://alphacephei.com/vosk/models) speech model per language you want, placed under `Voice/vosk-model-<lang>/`.

## Usage

On first run, AURA asks your name and remembers it going forward. From there, just talk to it normally. Special commands unlock additional capabilities:

| Command | What it does |
|---|---|
| `remember: key = value` | Explicitly teach it a fact |
| `prefs` | Show everything it knows about you |
| `voice on` / `voice off` | Toggle voice conversation |
| `automation on` | Unlock file/app commands (`open:`, `mkdir:`, `move:`, etc.) |
| `learning mode on` | Unlock web research (`learn:`, `websearch:`, `recall:`) |
| `business mode on` | Unlock business tools (`describe:`, `seo:`, `email:`, `content:`) |
| `plan: <goal>` | Break a goal into trackable steps |
| `backup now` | Snapshot your database and knowledge base |

Run `python main.py` and type any command with no arguments to see the full in-app command reference.

## Project structure
## Privacy

Everything is stored locally in `Database/aura.db` and `Knowledge/*.md`. The only network activity is Ollama's local API calls (never leaves your machine) and, when explicitly enabled, Learning Mode's web searches — which send only the search query and page-fetch requests, never your conversation history or personal data.

## License

MIT — see [LICENSE](LICENSE) for details.