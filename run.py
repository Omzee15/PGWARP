#!/usr/bin/env python3
"""
Quick launcher for PgWarp application
"""

import sys
import os
from pathlib import Path

def main():
    """Launch PgWarp application"""
    # Check if we're in the right directory
    current_dir = Path.cwd()
    main_py = current_dir / "main.py"
    
    if not main_py.exists():
        print("Error: main.py not found in current directory")
        print("Please run this script from the PgWarp root directory")
        sys.exit(1)
    
    # Check if virtual environment exists
    venv_dir = current_dir / "venv"
    if venv_dir.exists():
        print("Virtual environment found. Please activate it first:")
        if os.name == 'nt':  # Windows
            print("  venv\\Scripts\\activate.bat")
        else:  # Unix/Linux/macOS
            print("  source venv/bin/activate")
        print("  python main.py")
        print()
        print("Or run directly with:")
        if os.name == 'nt':
            print("  venv\\Scripts\\python.exe main.py")
        else:
            print("  venv/bin/python main.py")
    else:
        print("Virtual environment not found. Please run setup first:")
        if os.name == 'nt':
            print("  setup.bat")
        else:
            print("  ./setup.sh")
    
    # Try to run anyway
    try:
        import main
        main.main()
    except ImportError as e:
        print(f"Error importing dependencies: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()