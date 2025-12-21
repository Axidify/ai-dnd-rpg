#!/usr/bin/env python3
"""
Terminal RPG Launcher
Runs the legacy terminal-based game with correct module paths.

Usage:
    python run_terminal.py
    
On Windows, for best emoji display, run in Windows Terminal or VS Code terminal.
"""

import sys
import os

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    # Enable UTF-8 mode on Windows
    import io
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        # Python < 3.7 fallback
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add src directory to Python path so imports work
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Now we can import and run the legacy game
if __name__ == "__main__":
    # Import the game module from legacy folder
    legacy_path = os.path.join(project_root, 'backup', 'legacy')
    sys.path.insert(0, legacy_path)
    
    try:
        from game import main
        main()
    except ImportError as e:
        print(f"Error importing game: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
        sys.exit(0)
