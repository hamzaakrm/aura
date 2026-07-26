"""
AURA - Phase 1 through 7 Entry Point
Local AI chat with persistent + smarter memory (SQLite), optional
offline voice mode, computer automation, controlled web Learning Mode,
a business toolkit, and goal planning with step tracking.

Setup:
    1. Install Ollama: https://ollama.com
    2. Pull a model:   ollama pull qwen2.5:7b
    3. Install deps:   pip install -r requirements.txt
    4. (Optional, for voice) Download a Vosk model and place it at
       AURA/Voice/vosk-model  -- see Voice/voice_engine.py for details.

Run with:
    python main.py

Special commands:
    prefs                     -> show everything AURA has learned about you
    remember: key = value     -> explicitly teach AURA a fact (e.g. remember: goal = launch my Shopify store)
    voice on / voice off       -> talk instead of typing / go back to typing
    languages                       -> show voice languages available on your system
    language: <code>                -> switch voice language, e.g. language: ur

    automation on / automation off  -> allow/disallow AURA to touch your files & apps
    open: <app name>                -> e.g. open: notepad
    list: <folder path>             -> e.g. list: D:\\aura
    mkdir: <folder path>            -> create a folder
    move: <src> -> <dst>            -> move a file or folder
    copy: <src> -> <dst>            -> copy a file or folder
    delete: <path>                  -> delete a file or folder (asks to confirm)
    search: <query> in <folder path> -> find files/folders by name

    learning mode on / learning mode off  -> allow/disallow AURA to search the web
    learn: <topic>                        -> search the web, read a few pages, save notes
    websearch: <question>                 -> quick one-off search + answer, nothing saved
    recall: <topic>                       -> show previously saved notes on a topic
    topics                                -> list everything AURA has learned so far

    business mode on / business mode off  -> unlock the business toolkit below
    describe: <product> | <details>       -> write a product description
    seo: <topic>                          -> keyword ideas, title options, meta description
    email: <purpose> | <key points>       -> draft a professional email
    content: <type> | <topic>             -> write a blog post, caption, etc.
    task add: <description>               -> add a to-do item
    task list                             -> show pending tasks
    task done: <id>                       -> mark a task complete

    plan: <goal>                    -> break a goal into steps and track it
    goals                            -> list active goals with progress
    goal steps: <goal id>            -> show a goal's steps
    step done: <goal id> <step #>    -> mark a step complete

    backup now                       -> save a snapshot of your database & knowledge base
    backups                          -> list all saved snapshots
    restore: <backup name>           -> restore from a snapshot (asks to confirm)

    exit / quit                -> close AURA
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "Brain"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Memory"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Config"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Voice"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Automation"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Knowledge"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Skills"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Backup"))

import settings          # noqa: E402
import db                # noqa: E402
from chat_engine import ask_aura       # noqa: E402
from memory_manager import maybe_summarize  # noqa: E402
from fact_extractor import extract_and_save_facts  # noqa: E402


def build_message_list(user_input: str):
    """Assemble system prompt + long-term summaries + recent memory + new user message."""
    messages = [{"role": "system", "content": settings.SYSTEM_PROMPT}]

    summaries = db.get_all_summaries()
    if summaries:
        summary_block = "\n".join(f"- {s}" for s in summaries)
        messages.append({
            "role": "system",
            "content": f"Summary of earlier conversations with this user:\n{summary_block}"
        })

    messages += db.get_recent_history(settings.MEMORY_HISTORY_LIMIT)
    messages.append({"role": "user", "content": user_input})
    return messages


def main():
    db.init_db()
    voice_mode = False
    automation_enabled = False
    learning_enabled = False
    business_enabled = False
    current_voice_language = settings.DEFAULT_VOICE_LANGUAGE

    print("=" * 50)
    print(" AURA - Your Personal AI Assistant (Phase 1-7)")
    print(" Type 'exit' or 'quit' to end the session.")
    print(" Type 'voice on' to switch to talking instead of typing.")
    print(" Type 'automation on' to let me open apps and manage files.")
    print(" Type 'learning mode on' to let me search the web and learn.")
    print(" Type 'business mode on' for product/SEO/email/content tools.")
    print(" Type 'plan: <goal>' to break a goal into trackable steps.")
    print("=" * 50)

    # Greet using a remembered name if we have one
    name = db.get_preference("user_name")
    if name:
        print(f"\nAURA: Welcome back, {name}.")
    else:
        name = input("\nAURA: I don't think we've met. What's your name? ").strip()
        db.set_preference("user_name", name)
        print(f"AURA: Nice to meet you, {name}. I'll remember that.")

    while True:
        if voice_mode:
            print("\nAURA: (listening... speak now)")
            try:
                import voice_engine
                user_input = voice_engine.listen(current_voice_language).strip()
            except Exception as e:
                print(f"AURA: Voice input isn't working ({e}). Switching back to typing.")
                voice_mode = False
                continue
            if user_input:
                print(f"You (voice): {user_input}")
        else:
            try:
                user_input = input("\nYou: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nAURA: Shutting down. Everything we discussed is saved.")
                break

        if user_input.lower() in ("exit", "quit"):
            print("AURA: Goodbye. Everything we discussed is saved.")
            break

        if not user_input:
            continue

        if user_input.lower() == "voice on":
            try:
                import vosk          # noqa: F401
                import sounddevice   # noqa: F401
                import pyttsx3       # noqa: F401
            except ImportError as e:
                print(f"AURA: Voice packages aren't installed yet ({e}). "
                      f"Run: pip install vosk sounddevice pyttsx3")
                continue
            voice_mode = True
            print("AURA: Voice mode on. Say 'voice off' anytime to go back to typing.")
            continue

        if user_input.lower() == "voice off":
            voice_mode = False
            print("AURA: Voice mode off. Back to typing.")
            continue

        if user_input.lower() == "languages":
            try:
                import voice_engine
                found = voice_engine.available_languages()
                print("AURA: Voice languages with a downloaded speech model:")
                if not found:
                    print("  (none yet -- see Voice/voice_engine.py for setup instructions)")
                else:
                    for code in found:
                        label = settings.VOICE_LANGUAGES[code]["label"]
                        marker = " (current)" if code == current_voice_language else ""
                        print(f"  {code} - {label}{marker}")
                print("AURA: System voices installed for speaking:")
                for v in voice_engine.list_system_voices():
                    print(f"  {v['name']}")
            except ImportError as e:
                print(f"AURA: Voice packages aren't installed yet ({e}).")
            continue

        if user_input.lower().startswith("language:"):
            code = user_input.split(":", 1)[1].strip().lower()
            if code not in settings.VOICE_LANGUAGES:
                options = ", ".join(settings.VOICE_LANGUAGES.keys())
                print(f"AURA: Unknown language code '{code}'. Options: {options}")
                continue
            try:
                import voice_engine
                if code not in voice_engine.available_languages():
                    label = settings.VOICE_LANGUAGES[code]["label"]
                    print(f"AURA: No {label} speech model found yet. "
                          f"Download one from https://alphacephei.com/vosk/models and place it at "
                          f"Voice/{settings.VOICE_LANGUAGES[code]['vosk_folder']}. "
                          f"Switching anyway -- text-to-speech may still work if a system voice matches.")
            except ImportError:
                pass
            current_voice_language = code
            print(f"AURA: Voice language set to {settings.VOICE_LANGUAGES[code]['label']}.")
            continue

        if user_input.lower() == "prefs":
            prefs = db.get_all_preferences()
            if not prefs:
                print("AURA: I don't have any saved preferences yet.")
            else:
                for k, v in prefs.items():
                    print(f"  {k}: {v}")
            continue

        if user_input.lower().startswith("remember:"):
            body = user_input.split(":", 1)[1]
            if "=" not in body:
                print("AURA: Format: remember: key = value")
                continue
            key, value = body.split("=", 1)
            db.set_preference(key.strip(), value.strip())
            print(f"AURA: Got it. I'll remember {key.strip()} = {value.strip()}.")
            continue

        if user_input.lower() == "automation on":
            automation_enabled = True
            print("AURA: Automation enabled. I can now open apps and manage files when you ask "
                  "(open:, list:, mkdir:, move:, copy:, delete:, search:). "
                  "Every action gets logged to Logs/activity.log.")
            continue

        if user_input.lower() == "automation off":
            automation_enabled = False
            print("AURA: Automation disabled.")
            continue

        if automation_enabled:
            import automation_engine
            lower = user_input.lower()

            if lower.startswith("open:"):
                app = user_input.split(":", 1)[1].strip()
                print("AURA:", automation_engine.open_app(app))
                continue

            if lower.startswith("list:"):
                path = user_input.split(":", 1)[1].strip()
                print("AURA:\n" + automation_engine.list_files(path))
                continue

            if lower.startswith("mkdir:"):
                path = user_input.split(":", 1)[1].strip()
                print("AURA:", automation_engine.create_folder(path))
                continue

            if lower.startswith("move:") and "->" in user_input:
                body = user_input.split(":", 1)[1]
                src, dst = [p.strip() for p in body.split("->", 1)]
                print("AURA:", automation_engine.move_item(src, dst))
                continue

            if lower.startswith("copy:") and "->" in user_input:
                body = user_input.split(":", 1)[1]
                src, dst = [p.strip() for p in body.split("->", 1)]
                print("AURA:", automation_engine.copy_item(src, dst))
                continue

            if lower.startswith("delete:"):
                path = user_input.split(":", 1)[1].strip()
                confirm = input(f"AURA: Are you sure you want to delete '{path}'? (yes/no): ").strip().lower()
                if confirm == "yes":
                    print("AURA:", automation_engine.delete_item(path))
                else:
                    print("AURA: Cancelled, nothing was deleted.")
                continue

            if lower.startswith("search:") and " in " in user_input:
                body = user_input.split(":", 1)[1]
                query, root = body.split(" in ", 1)
                print("AURA:\n" + automation_engine.search_files(query.strip(), root.strip()))
                continue

        if user_input.lower() in ("learning mode on", "enter learning mode"):
            try:
                try:
                    import ddgs  # noqa: F401  (current package name)
                except ImportError:
                    import duckduckgo_search  # noqa: F401  (older package name)
                import requests           # noqa: F401
                import bs4                # noqa: F401
            except ImportError as e:
                print(f"AURA: Learning Mode packages aren't installed yet ({e}). "
                      f"Run: pip install ddgs requests beautifulsoup4")
                continue
            learning_enabled = True
            print("AURA: Learning Mode on. Only search queries and page fetches go online -- "
                  "your conversations and personal data stay local. "
                  "Try: learn: <topic>, websearch: <question>, recall: <topic>, topics. "
                  "I'll also automatically search the web mid-conversation if a normal "
                  "question of yours seems to need current info -- I'll always say when I do.")
            continue

        if user_input.lower() in ("learning mode off", "exit learning mode"):
            learning_enabled = False
            print("AURA: Learning Mode off. Back to fully offline.")
            continue

        if user_input.lower() == "topics":
            import learning_engine
            topics = learning_engine.list_known_topics()
            if not topics:
                print("AURA: I haven't learned anything yet. Try: learn: <topic>")
            else:
                for t in topics:
                    print(f"  - {t.replace('_', ' ')}")
            continue

        if user_input.lower().startswith("recall:"):
            import learning_engine
            topic = user_input.split(":", 1)[1].strip()
            print("AURA:\n" + learning_engine.recall_topic(topic))
            continue

        if learning_enabled and user_input.lower().startswith("learn:"):
            import learning_engine
            topic = user_input.split(":", 1)[1].strip()
            print(f"AURA: Researching '{topic}'... this may take a moment.")
            print("AURA:\n" + learning_engine.learn_topic(topic))
            continue

        if learning_enabled and user_input.lower().startswith("websearch:"):
            import learning_engine
            query = user_input.split(":", 1)[1].strip()
            print(f"AURA: Searching '{query}'... this may take a moment.")
            print("AURA:\n" + learning_engine.quick_search(query))
            continue

        if user_input.lower().startswith("learn:") and not learning_enabled:
            print("AURA: Learning Mode is off. Type 'learning mode on' first.")
            continue

        if user_input.lower().startswith("websearch:") and not learning_enabled:
            print("AURA: Learning Mode is off. Type 'learning mode on' first.")
            continue

        if user_input.lower() == "business mode on":
            business_enabled = True
            print("AURA: Business mode on. Try:\n"
                  "  describe: <product> | <details>\n"
                  "  seo: <topic>\n"
                  "  email: <purpose> | <key points>\n"
                  "  content: <type> | <topic>\n"
                  "  task add: <description>\n"
                  "  task list\n"
                  "  task done: <id>")
            continue

        if user_input.lower() == "business mode off":
            business_enabled = False
            print("AURA: Business mode off.")
            continue

        if user_input.lower().startswith("task add:"):
            desc = user_input.split(":", 1)[1].strip()
            task_id = db.add_task(desc)
            print(f"AURA: Added task #{task_id}: {desc}")
            continue

        if user_input.lower() == "task list":
            tasks = db.list_tasks()
            if not tasks:
                print("AURA: No pending tasks. Nice and clear!")
            else:
                for t in tasks:
                    print(f"  #{t['id']}  {t['description']}")
            continue

        if user_input.lower().startswith("task done:"):
            raw_id = user_input.split(":", 1)[1].strip()
            if not raw_id.isdigit():
                print("AURA: Format: task done: <id>")
                continue
            if db.complete_task(int(raw_id)):
                print(f"AURA: Task #{raw_id} marked done.")
            else:
                print(f"AURA: Couldn't find a pending task #{raw_id}.")
            continue

        if business_enabled:
            import business_engine
            lower = user_input.lower()

            if lower.startswith("describe:") and "|" in user_input:
                body = user_input.split(":", 1)[1]
                product, details = [p.strip() for p in body.split("|", 1)]
                print("AURA:\n" + business_engine.write_product_description(product, details))
                continue

            if lower.startswith("seo:"):
                topic = user_input.split(":", 1)[1].strip()
                print("AURA:\n" + business_engine.write_seo_keywords(topic))
                continue

            if lower.startswith("email:") and "|" in user_input:
                body = user_input.split(":", 1)[1]
                purpose, points = [p.strip() for p in body.split("|", 1)]
                print("AURA:\n" + business_engine.draft_email(purpose, points))
                continue

            if lower.startswith("content:") and "|" in user_input:
                body = user_input.split(":", 1)[1]
                content_type, topic = [p.strip() for p in body.split("|", 1)]
                print("AURA:\n" + business_engine.write_content(content_type, topic))
                continue

        if user_input.lower().startswith("plan:"):
            import planning_engine
            goal_description = user_input.split(":", 1)[1].strip()
            print(f"AURA: Planning '{goal_description}'... this may take a moment.")
            steps = planning_engine.plan_goal(goal_description)
            goal_id = db.create_goal(goal_description, steps)
            print(f"AURA: Goal #{goal_id} created: {goal_description}")
            for i, step in enumerate(steps, start=1):
                print(f"  {i}. {step}")
            continue

        if user_input.lower() == "goals":
            goals = db.get_goals()
            if not goals:
                print("AURA: No active goals yet. Try: plan: <your goal>")
            else:
                for g in goals:
                    print(f"  Goal #{g['id']}: {g['description']} "
                          f"({g['done_steps']}/{g['total_steps']} steps done)")
            continue

        if user_input.lower().startswith("goal steps:"):
            raw_id = user_input.split(":", 1)[1].strip()
            if not raw_id.isdigit():
                print("AURA: Format: goal steps: <goal id>")
                continue
            steps = db.get_goal_steps(int(raw_id))
            if not steps:
                print(f"AURA: No goal found with id {raw_id}.")
            else:
                for s in steps:
                    mark = "[x]" if s["status"] == "done" else "[ ]"
                    print(f"  {mark} {s['step_number']}. {s['description']}")
            continue

        if user_input.lower().startswith("step done:"):
            body = user_input.split(":", 1)[1].strip()
            parts = body.split()
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                print("AURA: Format: step done: <goal id> <step number>")
                continue
            goal_id, step_number = int(parts[0]), int(parts[1])
            if db.complete_step(goal_id, step_number):
                print(f"AURA: Step {step_number} on Goal #{goal_id} marked done.")
            else:
                print(f"AURA: Couldn't find a pending step {step_number} on Goal #{goal_id}.")
            continue

        if user_input.lower() == "backup now":
            import backup_engine
            name = backup_engine.create_backup()
            print(f"AURA: Backup created: Backup/{name}")
            continue

        if user_input.lower() == "backups":
            import backup_engine
            backups = backup_engine.list_backups()
            if not backups:
                print("AURA: No backups yet. Try: backup now")
            else:
                for b in backups:
                    print(f"  {b}")
            continue

        if user_input.lower().startswith("restore:"):
            import backup_engine
            name = user_input.split(":", 1)[1].strip()
            confirm = input(
                f"AURA: This will overwrite your current database and knowledge base "
                f"with '{name}'. Are you sure? (yes/no): "
            ).strip().lower()
            if confirm == "yes":
                if backup_engine.restore_backup(name):
                    print(f"AURA: Restored from {name}. Restart AURA for this to fully take effect.")
                else:
                    print(f"AURA: No backup found named '{name}'. Try: backups")
            else:
                print("AURA: Cancelled, nothing was restored.")
            continue

        search_context = ""
        if learning_enabled:
            import learning_engine
            try:
                if learning_engine.should_search(user_input):
                    print("AURA: (this needs current info -- checking the web...)")
                    search_context = learning_engine.gather_web_context(user_input)
            except Exception:
                pass  # if the web check fails for any reason, just answer normally

        db.save_message("user", user_input)

        messages = build_message_list(user_input)
        if search_context:
            messages.insert(len(messages) - 1, {
                "role": "system",
                "content": f"Relevant web search results for the user's latest message:\n{search_context}"
            })
        reply = ask_aura(messages)

        print(f"\nAURA: {reply}")
        db.save_message("assistant", reply)

        if search_context:
            import learning_engine
            filename = learning_engine.save_knowledge(user_input, reply)
            print(f"  (saved to Knowledge/{filename})")

        if voice_mode:
            import voice_engine
            voice_engine.speak(reply, current_voice_language)

        saved_facts = extract_and_save_facts(user_input, reply)
        for key, value in saved_facts:
            print(f"  (noted: {key} = {value})")

        # Keep long-term memory manageable: compress old history once it piles up
        maybe_summarize()


if __name__ == "__main__":
    main()