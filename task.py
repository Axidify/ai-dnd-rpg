#!/usr/bin/env python3
"""
TaskSync V6 - Task Input Helper

Simplifies the task input command from:
  python -c "task = input('Task: '); print(f'Received: {task}')"
To:
  python task.py

Supports prefixes:
  - (none)     : Normal task execution
  - discuss:   : Conversation mode - get agent's input/opinions
  - urgent:    : High priority - interrupt current work
  - blocked:   : Log a blocker

Special commands:
  - pause      : Stop task request loop
  - resume     : Continue task request loop  
  - status     : Show task history
  - stop/quit  : End session
"""

def main():
    task = input("Task: ").strip()
    
    if not task:
        print("⚠️ No task provided")
        return
    
    # Parse prefix
    prefix = None
    content = task
    
    if task.startswith("discuss:"):
        prefix = "💬 DISCUSS"
        content = task[8:].strip()
    elif task.startswith("urgent:"):
        prefix = "🚨 URGENT"
        content = task[7:].strip()
    elif task.startswith("blocked:"):
        prefix = "🚫 BLOCKED"
        content = task[8:].strip()
    elif task.lower() == "pause":
        print("⏸️ Session paused")
        return
    elif task.lower() == "resume":
        print("▶️ Session resumed")
        return
    elif task.lower() == "status":
        print("📊 Status requested")
        return
    elif task.lower() in ["stop", "quit", "end", "terminate"]:
        print("🛑 Session terminated")
        return
    
    # Output
    if prefix:
        print(f"{prefix}: {content}")
    else:
        print(f"Received: {task}")

if __name__ == "__main__":
    main()
