#!/usr/bin/env python3
"""
Quick test to demonstrate the improved popover with visible buttons
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from src.ui.main_window import NeuronDBApp

def create_test_data():
    """Create some test data to populate the results table"""
    test_results = [
        {"id": 1, "name": "John Doe", "email": "john.doe@example.com", "description": "This is a very long description that should show the benefits of having a popover to view the full content instead of just copying it to clipboard. The buttons should now be clearly visible at the bottom."},
        {"id": 2, "name": "Jane Smith", "email": "jane.smith@example.com", "description": "Another long description with lots of text that would be truncated in the table view. The popover will allow users to see all the content in a nice, readable format with working Copy and View Full buttons."},
        {"id": 3, "name": "Bob Johnson", "email": "bob.johnson@example.com", "description": "JSON data: {'label': 'd6477452-f595-491d-89b5-0d6ac27980a3', 'language': 'afe98819-1e2c-4386-a6eb-33d2ca2e042e', 'reference_phrase': 'post', 'identified_phrase': 'post'}"},
        {"id": 4, "name": "Alice Brown", "email": "alice.brown@example.com", "description": "Multi-line content\nwith newlines\nand various formatting\nthat should be displayed properly in the popover window with visible buttons."},
    ]
    
    columns = ["id", "name", "email", "description"]
    
    return test_results, columns

def main():
    """Main function to test the improved popover functionality"""
    # Create the main application
    app = NeuronDBApp()
    
    # Get test data
    test_results, columns = create_test_data()
    
    # Populate the results table with test data
    app.display_results(test_results, columns)
    
    # Update the status to indicate test mode
    app.status_label.configure(text="✨ IMPROVED POPOVER TEST: Double-click any cell to see the enhanced popover with visible buttons!")
    
    # Start the application
    app.mainloop()

if __name__ == "__main__":
    main()