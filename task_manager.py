import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
import hashlib


DATA_FILE = "tasks.json"
USERS_FILE = "users.json"


class Task:
    def __init__(self, task_id: int, title: str, description: str = "",
                 priority: str = "medium", deadline: Optional[str] = None,
                 tags: List[str] = None, owner: str = "default"):
        self.id = task_id
        self.title = title
        self.description = description
        self.priority = priority
        self.deadline = deadline
        self.tags = tags or []
        self.owner = owner
        self.done = False
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.completed_at = None
        self.subtasks = []

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data: dict):
        t = cls(data["id"], data["title"])
        t.__dict__.update(data)
        return t

    def is_overdue(self) -> bool:
        if not self.deadline or self.done:
            return False
        try:
            dl = datetime.strptime(self.deadline, "%Y-%m-%d")
            return datetime.now() > dl
        except ValueError:
            return False

    def days_until_deadline(self) -> Optional[int]:
        if not self.deadline:
            return None
        try:
            dl = datetime.strptime(self.deadline, "%Y-%m-%d")
            return (dl - datetime.now()).days
        except ValueError:
            return None


class TaskManager:
    def __init__(self):
        self.tasks: List[Task] = []
        self.current_user = "default"
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(d) for d in data]
            except (json.JSONDecodeError, KeyError):
                self.tasks = []

    def save(self):
        with open(DATA_FILE, "w") as f:
            json.dump([t.to_dict() for t in self.tasks], f, indent=2)

    def add_task(self, title: str, description: str = "", priority: str = "medium",
                 deadline: Optional[str] = None, tags: List[str] = None) -> Task:
        if not title.strip():
            raise ValueError("Title cannot be empty.")
        valid_priorities = ["low", "medium", "high", "critical"]
        if priority not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        if deadline:
            try:
                datetime.strptime(deadline, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Deadline must be in YYYY-MM-DD format.")
        task_id = max((t.id for t in self.tasks), default=0) + 1
        task = Task(task_id, title.strip(), description, priority, deadline,
                    tags or [], self.current_user)
        self.tasks.append(task)
        self.save()
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def complete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        task.done = True
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.save()
        return True

    def delete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        self.tasks.remove(task)
        self.save()
        return True

    def add_subtask(self, task_id: int, subtask_title: str) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        task.subtasks.append({"title": subtask_title, "done": False})
        self.save()
        return True

    def filter_tasks(self, priority=None, tag=None, overdue=False,
                     done=None, owner=None) -> List[Task]:
        result = self.tasks
        if priority:
            result = [t for t in result if t.priority == priority]
        if tag:
            result = [t for t in result if tag in t.tags]
        if overdue:
            result = [t for t in result if t.is_overdue()]
        if done is not None:
            result = [t for t in result if t.done == done]
        if owner:
            result = [t for t in result if t.owner == owner]
        return result

    def sort_tasks(self, by="priority") -> List[Task]:
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        if by == "priority":
            return sorted(self.tasks, key=lambda t: priority_order.get(t.priority, 99))
        elif by == "deadline":
            return sorted(self.tasks, key=lambda t: t.deadline or "9999-99-99")
        elif by == "created":
            return sorted(self.tasks, key=lambda t: t.created_at)
        return self.tasks

    def get_stats(self) -> dict:
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.done)
        overdue = sum(1 for t in self.tasks if t.is_overdue())
        by_priority = {}
        for p in ["critical", "high", "medium", "low"]:
            by_priority[p] = sum(1 for t in self.tasks if t.priority == p and not t.done)
        return {
            "total": total, "done": done,
            "pending": total - done, "overdue": overdue,
            "by_priority": by_priority
        }


def display_task(task: Task):
    status = "✅" if task.done else ("🔴" if task.is_overdue() else "⏳")
    icons = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}
    icon = icons.get(task.priority, "⚪")
    days = task.days_until_deadline()
    deadline_str = ""
    if days is not None:
        if days < 0:
            deadline_str = f" (⚠️ {abs(days)}d overdue)"
        elif days == 0:
            deadline_str = " (⚠️ Due today!)"
        else:
            deadline_str = f" (📅 {days}d left)"
    tags_str = f" #{' #'.join(task.tags)}" if task.tags else ""
    print(f"{status} [{task.id}] {icon} {task.title}{deadline_str}{tags_str}")
    if task.description:
        print(f"      📝 {task.description}")
    if task.subtasks:
        for i, st in enumerate(task.subtasks):
            s = "✅" if st["done"] else "◻️"
            print(f"      {s} subtask {i+1}: {st['title']}")


def main():
    manager = TaskManager()
    print("🗂️  Smart Task Manager Pro")
    print("Type 'help' for commands.\n")

    while True:
        try:
            cmd = input(f"[{manager.current_user}] >> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if cmd == "quit":
            print("Goodbye!")
            break

        elif cmd == "help":
            print("""
Commands:
  add       - Add a new task
  list      - List all tasks
  sort      - Sort tasks (priority/deadline/created)
  filter    - Filter tasks
  done      - Mark task as complete
  delete    - Delete a task
  subtask   - Add subtask
  stats     - Show statistics
  user      - Switch user
  quit      - Exit
""")

        elif cmd == "add":
            try:
                title = input("Title: ")
                desc = input("Description (optional): ")
                priority = input("Priority (low/medium/high/critical) [medium]: ") or "medium"
                deadline = input("Deadline YYYY-MM-DD (optional): ") or None
                tags_input = input("Tags (comma-separated, optional): ")
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                task = manager.add_task(title, desc, priority, deadline, tags)
                print(f"✅ Task #{task.id} added!")
            except ValueError as e:
                print(f"❌ Error: {e}")

        elif cmd == "list":
            tasks = manager.tasks
            if not tasks:
                print("No tasks found.")
            else:
                for t in tasks:
                    display_task(t)

        elif cmd == "sort":
            by = input("Sort by (priority/deadline/created): ") or "priority"
            for t in manager.sort_tasks(by):
                display_task(t)

        elif cmd == "filter":
            priority = input("Priority filter (or leave empty): ") or None
            tag = input("Tag filter (or leave empty): ") or None
            overdue = input("Only overdue? (y/n): ").lower() == "y"
            results = manager.filter_tasks(priority=priority, tag=tag, overdue=overdue)
            if not results:
                print("No matching tasks.")
            else:
                for t in results:
                    display_task(t)

        elif cmd == "done":
            try:
                task_id = int(input("Task ID: "))
                if manager.complete_task(task_id):
                    print(f"✅ Task #{task_id} completed!")
                else:
                    print("❌ Task not found.")
            except ValueError:
                print("❌ Invalid ID.")

        elif cmd == "delete":
            try:
                task_id = int(input("Task ID: "))
                if manager.delete_task(task_id):
                    print(f"🗑️ Task #{task_id} deleted.")
                else:
                    print("❌ Task not found.")
            except ValueError:
                print("❌ Invalid ID.")

        elif cmd == "subtask":
            try:
                task_id = int(input("Task ID: "))
                subtask = input("Subtask title: ")
                if manager.add_subtask(task_id, subtask):
                    print("✅ Subtask added!")
                else:
                    print("❌ Task not found.")
            except ValueError:
                print("❌ Invalid ID.")

        elif cmd == "stats":
            s = manager.get_stats()
            print(f"\n📊 Statistics:")
            print(f"  Total: {s['total']} | Done: {s['done']} | Pending: {s['pending']} | Overdue: {s['overdue']}")
            print(f"  By priority (pending): {s['by_priority']}")

        elif cmd == "user":
            name = input("Enter username: ").strip()
            if name:
                manager.current_user = name
                print(f"👤 Switched to user: {name}")

        else:
            print("Unknown command. Type 'help' for commands.")


if __name__ == "__main__":
    main()
