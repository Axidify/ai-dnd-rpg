#!/usr/bin/env python
"""TaskSync Input Loop - Maintains focus and waits for user input"""

import sys

def main():
    print("[TaskSync Input Ready]")
    while True:
        try:
            task = input("> ")
            if task.lower() in ['stop', 'end', 'terminate', 'quit']:
                print("Session ended.")
                break
            elif task.strip():
                print(f"[Task: {task}]")
                # The task is printed so the AI can read it from terminal output
        except KeyboardInterrupt:
            print("\n[Interrupted - Enter task:]")
        except EOFError:
            break

if __name__ == "__main__":
    main()
