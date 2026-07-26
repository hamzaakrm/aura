"""
AURA GUI Dialogs
Small popup windows for tasks, goals, and preferences -- used by gui.py.
"""

import sys
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt

sys.path.append(os.path.join(os.path.dirname(__file__), "Memory"))
import db  # noqa: E402


class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(400, 350)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("What AURA remembers about you:"))
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.refresh()

        layout.addWidget(QLabel("Teach AURA a new fact:"))
        form = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("key (e.g. goal)")
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("value (e.g. launch my store)")
        add_btn = QPushButton("Save")
        add_btn.clicked.connect(self.add_pref)
        form.addWidget(self.key_input)
        form.addWidget(self.value_input)
        form.addWidget(add_btn)
        layout.addLayout(form)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def refresh(self):
        self.list_widget.clear()
        prefs = db.get_all_preferences()
        if not prefs:
            self.list_widget.addItem("(nothing saved yet)")
        for k, v in prefs.items():
            self.list_widget.addItem(f"{k}: {v}")

    def add_pref(self):
        key = self.key_input.text().strip()
        value = self.value_input.text().strip()
        if not key or not value:
            QMessageBox.warning(self, "Missing info", "Please fill in both fields.")
            return
        db.set_preference(key, value)
        self.key_input.clear()
        self.value_input.clear()
        self.refresh()


class TasksDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tasks")
        self.resize(420, 400)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Pending tasks (check the box to mark done):"))
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.refresh()

        form = QHBoxLayout()
        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("New task description")
        add_btn = QPushButton("Add Task")
        add_btn.clicked.connect(self.add_task)
        form.addWidget(self.new_task_input)
        form.addWidget(add_btn)
        layout.addLayout(form)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def refresh(self):
        self.list_widget.clear()
        tasks = db.list_tasks()
        if not tasks:
            self.list_widget.addItem("(no pending tasks)")
            return
        for t in tasks:
            item = QListWidgetItem(f"#{t['id']}  {t['description']}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, t["id"])
            self.list_widget.addItem(item)
        try:
            self.list_widget.itemChanged.disconnect(self.on_item_changed)
        except (TypeError, RuntimeError):
            pass
        self.list_widget.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item):
        if item.checkState() == Qt.Checked:
            task_id = item.data(Qt.UserRole)
            if task_id is not None:
                db.complete_task(task_id)
                self.refresh()

    def add_task(self):
        desc = self.new_task_input.text().strip()
        if not desc:
            return
        db.add_task(desc)
        self.new_task_input.clear()
        self.refresh()


class GoalsDialog(QDialog):
    """
    plan_callback(goal_text, on_done) is supplied by gui.py so goal
    planning (which calls the local AI model) runs on a background
    thread instead of freezing this dialog.
    """
    def __init__(self, plan_callback, parent=None):
        super().__init__(parent)
        self.plan_callback = plan_callback
        self.current_goal_id = None
        self._goal_ids = []

        self.setWindowTitle("Goals")
        self.resize(480, 450)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Active goals:"))
        self.goals_list = QListWidget()
        self.goals_list.itemClicked.connect(self.on_goal_selected)
        layout.addWidget(self.goals_list)
        self.refresh()

        layout.addWidget(QLabel("Steps for selected goal (double-click a step to mark done):"))
        self.steps_list = QListWidget()
        self.steps_list.itemDoubleClicked.connect(self.on_step_double_clicked)
        layout.addWidget(self.steps_list)

        form = QHBoxLayout()
        self.new_goal_input = QLineEdit()
        self.new_goal_input.setPlaceholderText("New goal, e.g. launch my Shopify store")
        self.plan_btn = QPushButton("Plan It")
        self.plan_btn.clicked.connect(self.on_plan_clicked)
        form.addWidget(self.new_goal_input)
        form.addWidget(self.plan_btn)
        layout.addLayout(form)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def refresh(self):
        self.goals_list.clear()
        self._goal_ids = []
        goals = db.get_goals()
        if not goals:
            self.goals_list.addItem("(no active goals yet)")
            return
        for g in goals:
            self.goals_list.addItem(
                f"#{g['id']}  {g['description']}  ({g['done_steps']}/{g['total_steps']} done)"
            )
            self._goal_ids.append(g["id"])

    def on_goal_selected(self, item):
        row = self.goals_list.row(item)
        if row < 0 or row >= len(self._goal_ids):
            return
        self.current_goal_id = self._goal_ids[row]
        self.steps_list.clear()
        for s in db.get_goal_steps(self.current_goal_id):
            mark = "[x]" if s["status"] == "done" else "[ ]"
            self.steps_list.addItem(f"{mark} {s['step_number']}. {s['description']}")

    def on_step_double_clicked(self, item):
        if self.current_goal_id is None:
            return
        text = item.text()
        try:
            step_number = int(text.split(".")[0].split()[-1])
        except (ValueError, IndexError):
            return
        db.complete_step(self.current_goal_id, step_number)
        goal_id = self.current_goal_id
        self.refresh()
        for i, gid in enumerate(self._goal_ids):
            if gid == goal_id:
                self.on_goal_selected(self.goals_list.item(i))
                break

    def on_plan_clicked(self):
        goal_text = self.new_goal_input.text().strip()
        if not goal_text:
            return
        self.new_goal_input.clear()
        self.plan_btn.setEnabled(False)
        self.plan_btn.setText("Planning...")
        self.plan_callback(goal_text, self._on_plan_done)

    def _on_plan_done(self):
        self.plan_btn.setEnabled(True)
        self.plan_btn.setText("Plan It")
        self.refresh()