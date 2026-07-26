"""
AURA Desktop App (GUI)
A proper chat-window interface for AURA, built with PySide6.
Toggle buttons in the toolbar control Automation, Learning, and
Business modes. Once a mode is on, its typed commands (open:, learn:,
describe:, etc.) still work in the chat box, same as the CLI version.

Setup:
    pip install PySide6
Run with:
    python gui.py
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

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QToolBar, QInputDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction

import settings          # noqa: E402
import db                 # noqa: E402
from chat_engine import ask_aura            # noqa: E402
from memory_manager import maybe_summarize  # noqa: E402
from gui_dialogs import PreferencesDialog, TasksDialog, GoalsDialog  # noqa: E402


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


class Worker(QThread):
    """Runs a slow function on a background thread so the window never freezes."""
    finished_with_result = Signal(object)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as e:
            result = f"[Error: {e}]"
        self.finished_with_result.emit(result)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        db.init_db()

        self.setWindowTitle("AURA - Your Personal AI Assistant")
        self.resize(760, 680)
        self.setStyleSheet(self._global_stylesheet())

        self.automation_on = False
        self.learning_on = False
        self.business_on = False
        self.voice_output_on = False
        self._workers = []  # keep references so background threads aren't garbage-collected

        self._build_toolbar()
        self._build_menu()
        self._build_chat_area()
        self._greet_user()

    @staticmethod
    def _global_stylesheet() -> str:
        """A clean, warm, Claude-inspired look for the whole app."""
        return """
            QMainWindow, QWidget {
                background-color: #F5F4EF;
                font-family: "Segoe UI", sans-serif;
                font-size: 14px;
                color: #2D2A26;
            }
            QScrollArea { border: none; }
            QToolBar {
                background-color: #F5F4EF;
                border: none;
                spacing: 8px;
                padding: 8px 12px;
            }
            QToolBar QToolButton {
                background-color: #EAE8E1;
                color: #5B5750;
                border: none;
                border-radius: 14px;
                padding: 6px 14px;
                font-size: 12px;
            }
            QToolBar QToolButton:checked {
                background-color: #D97757;
                color: white;
            }
            QMenuBar {
                background-color: #F5F4EF;
                border: none;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #E0DED6;
                border-radius: 18px;
                padding: 10px 16px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #D97757; }
            QPushButton {
                background-color: #D97757;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #C5673F; }
            QPushButton:pressed { background-color: #B15A35; }
        """

    # ---------- UI construction ----------

    def _build_toolbar(self):
        toolbar = QToolBar("Modes")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.automation_action = QAction("Automation: OFF", self)
        self.automation_action.setCheckable(True)
        self.automation_action.toggled.connect(self._toggle_automation)
        toolbar.addAction(self.automation_action)

        self.learning_action = QAction("Learning: OFF", self)
        self.learning_action.setCheckable(True)
        self.learning_action.toggled.connect(self._toggle_learning)
        toolbar.addAction(self.learning_action)

        self.business_action = QAction("Business: OFF", self)
        self.business_action.setCheckable(True)
        self.business_action.toggled.connect(self._toggle_business)
        toolbar.addAction(self.business_action)

        self.voice_action = QAction("Voice Output: OFF", self)
        self.voice_action.setCheckable(True)
        self.voice_action.toggled.connect(self._toggle_voice_output)
        toolbar.addAction(self.voice_action)

    def _build_menu(self):
        menu = self.menuBar().addMenu("Tools")

        prefs_action = QAction("Preferences...", self)
        prefs_action.triggered.connect(lambda: PreferencesDialog(self).exec())
        menu.addAction(prefs_action)

        tasks_action = QAction("Tasks...", self)
        tasks_action.triggered.connect(lambda: TasksDialog(self).exec())
        menu.addAction(tasks_action)

        goals_action = QAction("Goals...", self)
        goals_action.triggered.connect(self._open_goals_dialog)
        menu.addAction(goals_action)

    def _build_chat_area(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: #F5F4EF;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(24, 20, 24, 20)
        self.chat_layout.setSpacing(14)
        self.chat_layout.addStretch()
        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)

        input_wrapper = QWidget()
        input_wrapper.setStyleSheet("background-color: #F5F4EF; border-top: 1px solid #E5E4DD;")
        input_row = QHBoxLayout(input_wrapper)
        input_row.setContentsMargins(20, 14, 20, 14)
        input_row.setSpacing(10)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Message AURA...")
        self.input_box.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_box)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._on_send)
        input_row.addWidget(send_btn)

        mic_btn = QPushButton("Mic")
        mic_btn.setFixedWidth(48)
        mic_btn.clicked.connect(self._on_mic)
        input_row.addWidget(mic_btn)

        layout.addWidget(input_wrapper)

    # ---------- Helpers ----------

    def _add_bubble(self, text: str, sender: str):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if sender == "you":
            label.setStyleSheet(
                "background-color: white; border: 1px solid #E5E4DD; "
                "border-radius: 14px; padding: 10px 14px; margin-left: 100px; "
                "font-size: 14px; color: #2D2A26;"
            )
        else:
            label.setStyleSheet(
                "background-color: transparent; padding: 4px 6px 4px 0px; "
                "margin-right: 40px; font-size: 14px; color: #2D2A26; line-height: 150%;"
            )
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, label)
        QApplication.processEvents()
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _greet_user(self):
        name = db.get_preference("user_name")
        if name:
            self._add_bubble(f"Welcome back, {name}.", "aura")
        else:
            name, ok = QInputDialog.getText(self, "Welcome", "I don't think we've met. What's your name?")
            name = name.strip() if ok and name.strip() else "friend"
            db.set_preference("user_name", name)
            self._add_bubble(f"Nice to meet you, {name}. I'll remember that.", "aura")

    def _run_in_background(self, func, on_done, *args, **kwargs):
        worker = Worker(func, *args, **kwargs)
        worker.finished_with_result.connect(lambda result: self._finish_worker(worker, on_done, result))
        self._workers.append(worker)
        worker.start()

    def _finish_worker(self, worker, on_done, result):
        on_done(result)
        if worker in self._workers:
            self._workers.remove(worker)

    # ---------- Mode toggles ----------

    def _toggle_automation(self, checked):
        self.automation_on = checked
        self.automation_action.setText(f"Automation: {'ON' if checked else 'OFF'}")
        if checked:
            self._add_bubble(
                "Automation enabled. Try typed commands like: open: notepad, "
                "list: D:\\aura, mkdir: <path>, move:/copy:/delete:/search:. "
                "Every action gets logged to Logs/activity.log.",
                "aura"
            )

    def _toggle_learning(self, checked):
        if checked:
            try:
                try:
                    import ddgs  # noqa: F401
                except ImportError:
                    import duckduckgo_search  # noqa: F401
                import requests  # noqa: F401
                import bs4  # noqa: F401
            except ImportError as e:
                QMessageBox.warning(
                    self, "Missing packages",
                    f"Learning Mode packages aren't installed yet ({e}).\n"
                    f"Run: pip install ddgs requests beautifulsoup4"
                )
                self.learning_action.setChecked(False)
                return
        self.learning_on = checked
        self.learning_action.setText(f"Learning: {'ON' if checked else 'OFF'}")
        if checked:
            self._add_bubble(
                "Learning Mode on. Try: learn: <topic>, websearch: <question>, "
                "recall: <topic>, topics. I'll also automatically search the web "
                "mid-conversation if a normal question seems to need current info.",
                "aura"
            )

    def _toggle_business(self, checked):
        self.business_on = checked
        self.business_action.setText(f"Business: {'ON' if checked else 'OFF'}")
        if checked:
            self._add_bubble(
                "Business mode on. Try: describe: <product> | <details>, "
                "seo: <topic>, email: <purpose> | <key points>, "
                "content: <type> | <topic>.",
                "aura"
            )

    def _toggle_voice_output(self, checked):
        if checked:
            try:
                import pyttsx3  # noqa: F401
            except ImportError as e:
                QMessageBox.warning(
                    self, "Missing package",
                    f"Voice output isn't installed yet ({e}).\nRun: pip install pyttsx3"
                )
                self.voice_action.setChecked(False)
                return
        self.voice_output_on = checked
        self.voice_action.setText(f"Voice Output: {'ON' if checked else 'OFF'}")

    # ---------- Goals dialog ----------

    def _open_goals_dialog(self):
        def plan_callback(goal_text, on_done):
            def do_plan():
                import planning_engine
                steps = planning_engine.plan_goal(goal_text)
                db.create_goal(goal_text, steps)
                return None
            self._run_in_background(do_plan, lambda _: on_done())

        dialog = GoalsDialog(plan_callback, self)
        dialog.exec()

    # ---------- Sending messages ----------

    def _on_mic(self):
        try:
            import voice_engine
        except ImportError as e:
            QMessageBox.warning(self, "Missing packages", f"Voice input isn't installed yet ({e}).")
            return
        self._add_bubble("(listening... speak now)", "aura")
        self.input_box.setEnabled(False)

        def listen_task():
            return voice_engine.listen().strip()

        def on_done(text):
            self.input_box.setEnabled(True)
            if text:
                self.input_box.setText(text)
                self._on_send()

        self._run_in_background(listen_task, on_done)

    def _on_send(self):
        user_input = self.input_box.text().strip()
        if not user_input:
            return
        self.input_box.clear()
        self._add_bubble(user_input, "you")

        if self._handle_command(user_input):
            return

        db.save_message("user", user_input)
        self.input_box.setEnabled(False)

        learning_on = self.learning_on  # capture current toggle state for the background thread

        def chat_task():
            search_context = ""
            if learning_on:
                import learning_engine
                try:
                    if learning_engine.should_search(user_input):
                        search_context = learning_engine.gather_web_context(user_input)
                except Exception:
                    pass  # if the web check fails for any reason, just answer normally

            messages = build_message_list(user_input)
            if search_context:
                messages.insert(len(messages) - 1, {
                    "role": "system",
                    "content": f"Relevant web search results for the user's latest message:\n{search_context}"
                })
            reply = ask_aura(messages)
            return reply, bool(search_context)

        def on_done(result):
            reply, used_search = result
            self.input_box.setEnabled(True)
            if used_search:
                self._add_bubble("(checked the web for this reply)", "aura")
            self._add_bubble(reply, "aura")
            db.save_message("assistant", reply)
            if used_search:
                import learning_engine
                filename = learning_engine.save_knowledge(user_input, reply)
                self._add_bubble(f"(saved to Knowledge/{filename})", "aura")
            if self.voice_output_on:
                import voice_engine
                voice_engine.speak(reply)
            maybe_summarize()

        self._run_in_background(chat_task, on_done)
        # ---------- Text command routing (mirrors the CLI's command set) ----------

    def _handle_command(self, user_input: str) -> bool:
        lower = user_input.lower()

        if lower == "prefs":
            prefs = db.get_all_preferences()
            text = "\n".join(f"{k}: {v}" for k, v in prefs.items()) or "(nothing saved yet)"
            self._add_bubble(text, "aura")
            return True

        if lower.startswith("remember:"):
            body = user_input.split(":", 1)[1]
            if "=" not in body:
                self._add_bubble("Format: remember: key = value", "aura")
                return True
            key, value = body.split("=", 1)
            db.set_preference(key.strip(), value.strip())
            self._add_bubble(f"Got it. I'll remember {key.strip()} = {value.strip()}.", "aura")
            return True

        if lower.startswith("task add:"):
            desc = user_input.split(":", 1)[1].strip()
            task_id = db.add_task(desc)
            self._add_bubble(f"Added task #{task_id}: {desc}", "aura")
            return True

        if lower == "task list":
            tasks = db.list_tasks()
            text = "\n".join(f"#{t['id']}  {t['description']}" for t in tasks) or "No pending tasks."
            self._add_bubble(text, "aura")
            return True

        if lower.startswith("task done:"):
            raw_id = user_input.split(":", 1)[1].strip()
            if raw_id.isdigit() and db.complete_task(int(raw_id)):
                self._add_bubble(f"Task #{raw_id} marked done.", "aura")
            else:
                self._add_bubble("Couldn't find that pending task.", "aura")
            return True

        if self.automation_on and self._handle_automation(lower, user_input):
            return True

        if self._handle_learning(lower, user_input):
            return True

        if self.business_on and self._handle_business(lower, user_input):
            return True

        if lower.startswith("plan:"):
            goal_description = user_input.split(":", 1)[1].strip()
            self._add_bubble(f"Planning '{goal_description}'... this may take a moment.", "aura")

            def plan_task():
                import planning_engine
                steps = planning_engine.plan_goal(goal_description)
                goal_id = db.create_goal(goal_description, steps)
                lines = [f"Goal #{goal_id} created: {goal_description}"]
                lines += [f"  {i}. {s}" for i, s in enumerate(steps, start=1)]
                return "\n".join(lines)

            self._run_in_background(plan_task, lambda text: self._add_bubble(text, "aura"))
            return True

        if lower == "goals":
            goals = db.get_goals()
            text = "\n".join(
                f"Goal #{g['id']}: {g['description']} ({g['done_steps']}/{g['total_steps']} done)"
                for g in goals
            ) or "No active goals yet. Try: plan: <your goal>"
            self._add_bubble(text, "aura")
            return True

        return False

    def _handle_automation(self, lower, user_input) -> bool:
        import automation_engine

        if lower.startswith("open:"):
            app = user_input.split(":", 1)[1].strip()
            self._add_bubble(automation_engine.open_app(app), "aura")
            return True
        if lower.startswith("list:"):
            path = user_input.split(":", 1)[1].strip()
            self._add_bubble(automation_engine.list_files(path), "aura")
            return True
        if lower.startswith("mkdir:"):
            path = user_input.split(":", 1)[1].strip()
            self._add_bubble(automation_engine.create_folder(path), "aura")
            return True
        if lower.startswith("move:") and "->" in user_input:
            body = user_input.split(":", 1)[1]
            src, dst = [p.strip() for p in body.split("->", 1)]
            self._add_bubble(automation_engine.move_item(src, dst), "aura")
            return True
        if lower.startswith("copy:") and "->" in user_input:
            body = user_input.split(":", 1)[1]
            src, dst = [p.strip() for p in body.split("->", 1)]
            self._add_bubble(automation_engine.copy_item(src, dst), "aura")
            return True
        if lower.startswith("delete:"):
            path = user_input.split(":", 1)[1].strip()
            confirm = QMessageBox.question(self, "Confirm delete", f"Delete '{path}'?")
            if confirm == QMessageBox.Yes:
                self._add_bubble(automation_engine.delete_item(path), "aura")
            else:
                self._add_bubble("Cancelled, nothing was deleted.", "aura")
            return True
        if lower.startswith("search:") and " in " in user_input:
            body = user_input.split(":", 1)[1]
            query, root = body.split(" in ", 1)
            self._add_bubble(automation_engine.search_files(query.strip(), root.strip()), "aura")
            return True
        return False

    def _handle_learning(self, lower, user_input) -> bool:
        if lower == "topics":
            import learning_engine
            topics = learning_engine.list_known_topics()
            text = "\n".join(f"- {t.replace('_', ' ')}" for t in topics) or "I haven't learned anything yet."
            self._add_bubble(text, "aura")
            return True

        if lower.startswith("recall:"):
            import learning_engine
            topic = user_input.split(":", 1)[1].strip()
            self._add_bubble(learning_engine.smart_recall(topic), "aura")
            return True

        if self.learning_on and lower.startswith("learn:"):
            topic = user_input.split(":", 1)[1].strip()
            self._add_bubble(f"Researching '{topic}'... this may take a moment.", "aura")

            def task():
                import learning_engine
                return learning_engine.learn_topic(topic)

            self._run_in_background(task, lambda text: self._add_bubble(text, "aura"))
            return True

        if self.learning_on and lower.startswith("websearch:"):
            query = user_input.split(":", 1)[1].strip()
            self._add_bubble(f"Searching '{query}'... this may take a moment.", "aura")

            def task():
                import learning_engine
                return learning_engine.quick_search(query)

            self._run_in_background(task, lambda text: self._add_bubble(text, "aura"))
            return True

        if lower.startswith(("learn:", "websearch:")) and not self.learning_on:
            self._add_bubble("Learning Mode is off. Toggle it on in the toolbar first.", "aura")
            return True

        return False

    def _handle_business(self, lower, user_input) -> bool:
        if lower.startswith("describe:") and "|" in user_input:
            body = user_input.split(":", 1)[1]
            product, details = [p.strip() for p in body.split("|", 1)]

            def task():
                import business_engine
                return business_engine.write_product_description(product, details)

            self._run_in_background(task, lambda text: self._add_bubble(text, "aura"))
            return True

        if lower.startswith("seo:"):
            topic = user_input.split(":", 1)[1].strip()

            def task():
                import business_engine
                return business_engine.write_seo_keywords(topic)

            self._run_in_background(task, lambda text: self._add_bubble(text, "aura"))
            return True

        if lower.startswith("email:") and "|" in user_input:
            body = user_input.split(":", 1)[1]
            purpose, points = [p.strip() for p in body.split("|", 1)]

            def task():
                import business_engine
                return business_engine.draft_email(purpose, points)

            self._run_in_background(task, lambda text: self._add_bubble(text, "aura"))
            return True

        if lower.startswith("content:") and "|" in user_input:
            body = user_input.split(":", 1)[1]
            content_type, topic = [p.strip() for p in body.split("|", 1)]

            def task():
                import business_engine
                return business_engine.write_content(content_type, topic)

            self._run_in_background(task, lambda text: self._add_bubble(text, "aura"))
            return True

        return False


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()