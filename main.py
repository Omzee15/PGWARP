#!/usr/bin/env python3
"""
NeuronDB - AI-Powered PostgreSQL Desktop Client
Main entry point for the application
"""

import os
import sys
import tkinter as tk
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from ui.main_window import NeuronDBApp

def main():
    """Main entry point for NeuronDB application"""
    try:
        # Set up the application
        app = NeuronDBApp()
        
        # Start the main event loop
        app.mainloop()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting NeuronDB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()