import json
import os
from datetime import datetime

DATA_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def add_task(title, priority="medium", deadline=None):
    tasks = load_tasks()
    task = {
        "id": len(tasks) + 1,
        "title": title,
        "priority": priority,
        "deadline": deadline,
        "done": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"✅ Task added: {title}")

def list_tasks(filter_done=None):
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return
    for task in tasks:
        if filter_done is not None and task["done"] != filter_done:
            continue
        status = "✅" if task["done"] else "⏳"
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task["priority"], "⚪")
        deadline = task["deadline"] or "No deadline"
        print(f"{status} [{task['id']}] {priority_icon} {task['title']} | Due: {deadline}")

def complete_task(task_id):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks)
            print(f"✅ Task {task_id} marked as done!")
            return
    print(f"Task {task_id} not found.")

def delete_task(task_id):
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        print(f"Task {task_id} not found.")
        return
    save_tasks(new_tasks)
    print(f"🗑️ Task {task_id} deleted.")

def show_stats():
    tasks = load_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    pending = total - done
    high = sum(1 for t in tasks if t["priority"] == "high" and not t["done"])
    print(f"\n📊 Stats:")
    print(f"  Total: {total} | Done: {done} | Pending: {pending}")
    print(f"  High priority pending: {high}")

def main():
    print("🗂️ Smart Task Manager")
    print("Commands: add, list, done, delete, stats, quit\n")
    while True:
        cmd = input(">> ").strip().lower()
        if cmd == "quit":
            print("Goodbye!")
            break
        elif cmd == "add":
            title = input("Task title: ")
            priority = input("Priority (high/medium/low): ").lower()
            deadline = input("Deadline (YYYY-MM-DD or leave empty): ")
            add_task(title, priority, deadline or None)
        elif cmd == "list":
            list_tasks()
        elif cmd == "done":
            task_id = int(input("Task ID: "))
            complete_task(task_id)
        elif cmd == "delete":
            task_id = int(input("Task ID: "))
            delete_task(task_id)
        elif cmd == "stats":
            show_stats()
        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()
