"""
AURA Voice Engine (Phase 3, multi-language)
Offline speech-to-text (Vosk) and text-to-speech (pyttsx3), with
support for multiple languages. No audio ever leaves your computer.

Setup:
    pip install vosk sounddevice pyttsx3
    For each language you want, download its model from
    https://alphacephei.com/vosk/models, unzip it, and place the
    unzipped folder inside AURA/Voice/ using the folder name listed
    in Config/settings.py's VOICE_LANGUAGES (e.g. vosk-model-en,
    vosk-model-ur, vosk-model-ar, etc.)
"""

import sys
import os
import json
import queue

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Config"))
import settings  # noqa: E402

_vosk_models = {}  # cache: lang_code -> loaded vosk.Model


def _model_path_for(lang_code: str) -> str:
    info = settings.VOICE_LANGUAGES.get(lang_code)
    if not info:
        raise ValueError(f"Unknown language code '{lang_code}'.")
    folder = os.path.join(os.path.dirname(__file__), info["vosk_folder"])
    # Backward-compat: earlier single-language setup used a folder just
    # named "vosk-model" for English -- keep honoring that if present.
    legacy_folder = os.path.join(os.path.dirname(__file__), "vosk-model")
    if lang_code == "en" and not os.path.isdir(folder) and os.path.isdir(legacy_folder):
        return legacy_folder
    return folder


def available_languages() -> list:
    """Return language codes for which a Vosk model folder actually exists on disk."""
    return [code for code in settings.VOICE_LANGUAGES if os.path.isdir(_model_path_for(code))]


def _get_vosk_model(lang_code: str):
    if lang_code in _vosk_models:
        return _vosk_models[lang_code]

    import vosk
    path = _model_path_for(lang_code)
    if not os.path.isdir(path):
        label = settings.VOICE_LANGUAGES.get(lang_code, {}).get("label", lang_code)
        raise FileNotFoundError(
            f"No Vosk model found for {label} at {path}. Download one from "
            f"https://alphacephei.com/vosk/models, unzip it, and place the "
            f"folder at that exact path."
        )
    vosk.SetLogLevel(-1)  # quiet Vosk's own console spam
    model = vosk.Model(path)
    _vosk_models[lang_code] = model
    return model


def listen(lang_code: str = None) -> str:
    """
    Record from the default microphone until a pause in speech (or
    timeout), then return the transcribed text using the offline model
    for the given language (defaults to settings.DEFAULT_VOICE_LANGUAGE).
    """
    import sounddevice as sd
    import vosk

    lang_code = lang_code or settings.DEFAULT_VOICE_LANGUAGE
    model = _get_vosk_model(lang_code)
    samplerate = 16000
    audio_queue = queue.Queue()

    def _callback(indata, frames, time_info, status):
        audio_queue.put(bytes(indata))

    recognizer = vosk.KaldiRecognizer(model, samplerate)
    empty_reads = 0
    max_empty_reads = settings.VOICE_SILENCE_TIMEOUT

    with sd.RawInputStream(samplerate=samplerate, blocksize=8000,
                            dtype="int16", channels=1, callback=_callback):
        while True:
            try:
                data = audio_queue.get(timeout=1)
            except queue.Empty:
                empty_reads += 1
                if empty_reads >= max_empty_reads:
                    break
                continue

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    return text
                empty_reads = 0  # reset timeout while actively hearing speech

    final = json.loads(recognizer.FinalResult())
    return final.get("text", "").strip()


def list_system_voices():
    """
    Return the TTS voices installed on this system (via pyttsx3), each
    as a dict with id/name -- useful for figuring out what Windows
    calls its Urdu/Arabic/etc. voice once you've installed a language pack.
    """
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    result = [{"id": v.id, "name": v.name} for v in voices]
    engine.stop()
    return result


def _find_voice_id_for(lang_code: str):
    """Try to match an installed system voice to the requested language."""
    keywords = settings.VOICE_LANGUAGES.get(lang_code, {}).get("tts_keywords", [])
    if not keywords:
        return None
    for voice in list_system_voices():
        name_lower = voice["name"].lower()
        id_lower = voice["id"].lower()
        if any(k in name_lower or k in id_lower for k in keywords):
            return voice["id"]
    return None


def speak(text: str, lang_code: str = None):
    """
    Speak text out loud using the local offline TTS engine, using a
    system voice matching lang_code if one is installed. Falls back to
    the default voice and prints a note if that language isn't found.
    A fresh engine instance is created each call -- pyttsx3's Windows
    SAPI5 backend is known to go silent on repeat use of a cached
    engine within the same process, so this avoids that entirely.
    """
    lang_code = lang_code or settings.DEFAULT_VOICE_LANGUAGE
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", settings.TTS_RATE)

        voice_id = _find_voice_id_for(lang_code)
        if voice_id:
            engine.setProperty("voice", voice_id)
        elif lang_code != "en":
            label = settings.VOICE_LANGUAGES.get(lang_code, {}).get("label", lang_code)
            print(f"[Voice: no {label} system voice found -- speaking with the default voice. "
                  f"Add a {label} language pack in Windows Settings > Time & Language > "
                  f"Language & region for a native-sounding voice.]")

        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[Voice: could not speak reply: {e}]")