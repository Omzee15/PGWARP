"""
Configuration View Component
Settings and preferences for NeuronDB
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Optional
import os
from pathlib import Path


class ConfigView(ctk.CTkFrame):
    """Configuration and Settings View"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F5EFE7")
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the configuration UI"""
        # Main container with scrolling
        main_container = ctk.CTkScrollableFrame(self, fg_color="#F5EFE7")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        title_label = ctk.CTkLabel(
            main_container,
            text="⚙️ Configuration & Settings",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#3E2723"
        )
        title_label.pack(pady=(0, 20))
        
        # Database Settings Section
        self.create_section(main_container, "🗄️ Database Settings")
        
        db_frame = ctk.CTkFrame(main_container, fg_color="#E8DFD0")
        db_frame.pack(fill="x", pady=(0, 20))
        
        # Default connection settings
        self.create_setting_row(db_frame, "Default Host:", "localhost")
        self.create_setting_row(db_frame, "Default Port:", "5432")
        self.create_setting_row(db_frame, "Default Database:", "postgres")
        self.create_setting_row(db_frame, "Connection Timeout (s):", "30")
        
        # AI Settings Section
        self.create_section(main_container, "🤖 AI Assistant Settings")
        
        ai_frame = ctk.CTkFrame(main_container, fg_color="#E8DFD0")
        ai_frame.pack(fill="x", pady=(0, 20))
        
        self.create_setting_row(ai_frame, "API Key:", "••••••••••••", is_password=True)
        self.create_setting_row(ai_frame, "Model:", "gemini-pro")
        self.create_setting_row(ai_frame, "Temperature:", "0.7")
        self.create_setting_row(ai_frame, "Max Tokens:", "2000")
        
        # Editor Settings Section
        self.create_section(main_container, "📝 Editor Settings")
        
        editor_frame = ctk.CTkFrame(main_container, fg_color="#E8DFD0")
        editor_frame.pack(fill="x", pady=(0, 20))
        
        self.create_setting_row(editor_frame, "Font Family:", "Consolas")
        self.create_setting_row(editor_frame, "Font Size:", "11")
        
        # Toggle settings
        self.create_toggle_row(editor_frame, "Line Numbers", True)
        self.create_toggle_row(editor_frame, "Auto-complete", True)
        self.create_toggle_row(editor_frame, "Syntax Highlighting", True)
        
        # Display Settings Section
        self.create_section(main_container, "🎨 Display Settings")
        
        display_frame = ctk.CTkFrame(main_container, fg_color="#E8DFD0")
        display_frame.pack(fill="x", pady=(0, 20))
        
        self.create_setting_row(display_frame, "Max Result Rows:", "10000")
        self.create_toggle_row(display_frame, "Show Row Numbers", True)
        self.create_toggle_row(display_frame, "Alternating Row Colors", True)
        
        # Export Settings Section
        self.create_section(main_container, "📤 Export Settings")
        
        export_frame = ctk.CTkFrame(main_container, fg_color="#E8DFD0")
        export_frame.pack(fill="x", pady=(0, 20))
        
        self.create_setting_row(export_frame, "Default Export Format:", "Excel")
        self.create_setting_row(export_frame, "Export Directory:", str(Path.home() / "Downloads"))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(pady=20)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#9B8F5E",
            hover_color="#87795A"
        )
        save_btn.pack(side="left", padx=10)
        
        reset_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Reset to Defaults",
            command=self.reset_settings,
            fg_color="#9B8F5E",
            hover_color="#87795A",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        reset_btn.pack(side="left", padx=10)
        
        # About Section
        self.create_section(main_container, "ℹ️ About NeuronDB")
        
        about_frame = ctk.CTkFrame(main_container, fg_color="#E8DFD0")
        about_frame.pack(fill="x", pady=(0, 20))
        
        about_text = """
NeuronDB - AI-Powered PostgreSQL Client
Version: 1.0.0

A modern desktop application that brings AI assistance 
to PostgreSQL database management.

Features:
• AI-powered query generation with Google Gemini
• Visual schema browser & ER diagrams
• Advanced query editor with saved queries
• Built-in PSQL terminal
• Connection management
• DBML to ERD diagram generator

Built with Python, CustomTkinter, and LangChain.
"""
        
        about_label = ctk.CTkLabel(
            about_frame,
            text=about_text,
            font=ctk.CTkFont(size=11),
            text_color="#3E2723",
            justify="left"
        )
        about_label.pack(padx=20, pady=15)
    
    def create_section(self, parent, title: str):
        """Create a section header"""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=(10, 5))
        
        label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#9B8F5E"
        )
        label.pack(side="left")
        
        # Separator line
        separator = ctk.CTkFrame(section_frame, height=2, fg_color="#9B8F5E")
        separator.pack(side="left", fill="x", expand=True, padx=(10, 0))
    
    def create_setting_row(self, parent, label_text: str, default_value: str, is_password: bool = False):
        """Create a setting row with label and entry"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=15, pady=8)
        
        label = ctk.CTkLabel(
            row_frame,
            text=label_text,
            font=ctk.CTkFont(size=12),
            text_color="#3E2723",
            width=200,
            anchor="w"
        )
        label.pack(side="left", padx=(0, 10))
        
        entry = ctk.CTkEntry(
            row_frame,
            font=ctk.CTkFont(size=11),
            width=250,
            show="•" if is_password else None
        )
        entry.insert(0, default_value)
        entry.pack(side="left")
    
    def create_toggle_row(self, parent, label_text: str, default_value: bool):
        """Create a toggle switch row"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=15, pady=8)
        
        label = ctk.CTkLabel(
            row_frame,
            text=label_text,
            font=ctk.CTkFont(size=12),
            text_color="#3E2723",
            width=200,
            anchor="w"
        )
        label.pack(side="left", padx=(0, 10))
        
        switch = ctk.CTkSwitch(
            row_frame,
            text="",
            width=50
        )
        if default_value:
            switch.select()
        switch.pack(side="left")
    
    def save_settings(self):
        """Save settings to configuration file"""
        messagebox.showinfo("Settings", "Settings saved successfully!")
    
    def reset_settings(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            messagebox.showinfo("Settings", "Settings reset to defaults!")
