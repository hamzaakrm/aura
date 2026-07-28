"""
AURA Config
Central place for all adjustable settings.
"""

import os

# Ollama model to use. Change to whatever you've pulled with `ollama pull <model>`
OLLAMA_MODEL = "qwen2.5:7b"

# Context window size (tokens) sent to the model per request
CONTEXT_WINDOW = 8192

# Generation temperature: lower = more careful/focused/consistent answers,
# higher = more varied/creative. 0.4 favors careful reasoning over flair.
TEMPERATURE = 0.4

# How many past messages to load from memory as conversation context
MEMORY_HISTORY_LIMIT = 20

# Once total stored messages exceed this, the oldest chunk gets summarized
SUMMARY_TRIGGER_COUNT = 40

# How many of the oldest messages to compress into one summary each time
SUMMARY_CHUNK_SIZE = 20

# --- Voice settings (Phase 3, multi-language) ---
# Each entry maps a short language code to the Vosk model folder name
# (placed inside AURA/Voice/) and keywords used to auto-match an
# installed system TTS voice for that language.
# Download models from https://alphacephei.com/vosk/models, unzip,
# and place the folder at AURA/Voice/<vosk_folder> exactly as named below.
VOICE_LANGUAGES = {
    "en": {"label": "English", "vosk_folder": "vosk-model-en",
           "tts_keywords": ["english", "en-", "en_"]},
    "ur": {"label": "Urdu", "vosk_folder": "vosk-model-ur",
           "tts_keywords": ["urdu", "ur-", "ur_"]},
    "ar": {"label": "Arabic", "vosk_folder": "vosk-model-ar",
           "tts_keywords": ["arabic", "ar-", "ar_"]},
    "hi": {"label": "Hindi", "vosk_folder": "vosk-model-hi",
           "tts_keywords": ["hindi", "hi-", "hi_"]},
    "es": {"label": "Spanish", "vosk_folder": "vosk-model-es",
           "tts_keywords": ["spanish", "es-", "es_"]},
    "fr": {"label": "French", "vosk_folder": "vosk-model-fr",
           "tts_keywords": ["french", "fr-", "fr_"]},
    "de": {"label": "German", "vosk_folder": "vosk-model-de",
           "tts_keywords": ["german", "de-", "de_"]},
    "zh": {"label": "Chinese", "vosk_folder": "vosk-model-zh",
           "tts_keywords": ["chinese", "mandarin", "zh-", "zh_"]},
}

# Language AURA listens/speaks in by default. Change anytime with: language: <code>
DEFAULT_VOICE_LANGUAGE = "en"

# Text-to-speech speaking rate (words per minute, roughly)
TTS_RATE = 175

# How many seconds of silence before AURA stops listening for your voice
VOICE_SILENCE_TIMEOUT = 8

# System prompt that defines AURA's personality/behavior
SYSTEM_PROMPT = (
    "You are AURA (Artificial Unified Responsive Assistant), a private, "
    "offline personal AI assistant. You run entirely on the user's own "
    "computer. You remember past conversations, help manage the user's "
    "work and business, and never send personal data anywhere online. "
    "Be direct, helpful, and concise. Always respond in English, unless "
    "the user is clearly writing in a different language or explicitly "
    "asks you to reply in one -- never switch languages mid-reply on "
    "your own."
)
