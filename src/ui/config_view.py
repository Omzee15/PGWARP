"""
Configuration View Component
Settings and preferences for PgWarp
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Optional, Dict, Any
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.theme_manager import theme_manager
from utils.config_manager import config_manager


class ConfigView(ctk.CTkFrame):
    """Configuration and Settings View"""
    
    def __init__(self, parent, main_window=None):
        super().__init__(parent, fg_color=theme_manager.get_color("background.main"))
        
        self.main_window = main_window  # Reference to main window for theme changes
        self.config = config_manager.config
        
        # Store original config for cancel functionality
        self.original_config = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the configuration UI"""
        # Main container with scrolling
        main_container = ctk.CTkScrollableFrame(self, fg_color=theme_manager.get_color("background.main"))
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        title_label = ctk.CTkLabel(
            main_container,
            text="⚙️ Configuration & Settings",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=theme_manager.get_color("text.primary")
        )
        title_label.pack(pady=(0, 20))
        
        # Database Settings Section
        self.create_section(main_container, "🗄️ Database Settings")
        
        db_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        db_frame.pack(fill="x", pady=(0, 20))
        
        # Default connection settings
        self.create_setting_row(db_frame, "Default Host:", "localhost")
        self.create_setting_row(db_frame, "Default Port:", "5432")
        self.create_setting_row(db_frame, "Default Database:", "postgres")
        self.create_setting_row(db_frame, "Connection Timeout (s):", "30")
        
        # AI Settings Section
        self.create_section(main_container, "🤖 AI Assistant Settings")
        
        ai_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        ai_frame.pack(fill="x", pady=(0, 20))
        
        self.create_setting_row(ai_frame, "API Key:", "••••••••••••", is_password=True)
        self.create_setting_row(ai_frame, "Model:", "gemini-pro")
        self.create_setting_row(ai_frame, "Temperature:", "0.7")
        self.create_setting_row(ai_frame, "Max Tokens:", "2000")
        
        # Editor Settings Section
        self.create_section(main_container, "📝 Editor Settings")
        
        editor_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        editor_frame.pack(fill="x", pady=(0, 20))
        
        self.create_setting_row(editor_frame, "Font Family:", "Consolas")
        self.create_setting_row(editor_frame, "Font Size:", "11")
        
        # Toggle settings
        self.create_toggle_row(editor_frame, "Line Numbers", True)
        self.create_toggle_row(editor_frame, "Auto-complete", True)
        self.create_toggle_row(editor_frame, "Syntax Highlighting", True)
        
        # Display Settings Section
        self.create_section(main_container, "🎨 Display Settings")
        
        display_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        display_frame.pack(fill="x", pady=(0, 20))
        
        self.create_setting_row(display_frame, "Max Result Rows:", "10000")
        self.create_toggle_row(display_frame, "Show Row Numbers", True)
        self.create_toggle_row(display_frame, "Alternating Row Colors", True)
        
        # Export Settings Section
        self.create_section(main_container, "📤 Export Settings")
        
        export_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
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
            fg_color=theme_manager.get_color("buttons.primary_bg"),
            hover_color=theme_manager.get_color("buttons.primary_hover"),
            text_color=theme_manager.get_color("buttons.primary_text"),
            corner_radius=6
        )
        save_btn.pack(side="left", padx=10)
        
        reset_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Reset to Defaults",
            command=self.reset_settings,
            fg_color=theme_manager.get_color("buttons.secondary_bg"),
            hover_color=theme_manager.get_color("buttons.secondary_hover"),
            text_color=theme_manager.get_color("buttons.secondary_text"),
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=6
        )
        reset_btn.pack(side="left", padx=10)
        
        # About Section
        self.create_section(main_container, "ℹ️ About NeuronDB")
        
        about_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
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
            text_color=theme_manager.get_color("text.primary"),
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
            text_color=theme_manager.get_color("text.secondary")
        )
        label.pack(side="left")
        
        # Separator line
        separator = ctk.CTkFrame(section_frame, height=2, fg_color=theme_manager.get_color("accent.main"), corner_radius=1)
        separator.pack(side="left", fill="x", expand=True, padx=(10, 0))
    
    def create_setting_row(self, parent, label_text: str, default_value: str, is_password: bool = False):
        """Create a setting row with label and entry"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=15, pady=8)
        
        label = ctk.CTkLabel(
            row_frame, 
            text=label_text, 
            font=("Arial", 13, "bold"),
            text_color=theme_manager.get_color("text.primary")
        )
        label.pack(side="left", padx=20, pady=10)
        
        entry = ctk.CTkEntry(
            row_frame,
            placeholder_text=default_value,
            width=200,
            fg_color=theme_manager.get_color("editor.background"),
            text_color=theme_manager.get_color("text.primary"),
            border_color=theme_manager.get_color("accent.main")
        )
    
    def create_toggle_row(self, parent, label_text: str, default_value: bool):
        """Create a toggle switch row"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=15, pady=8)
        
        label = ctk.CTkLabel(
            row_frame,
            text=label_text,
            font=ctk.CTkFont(size=12),
            text_color=theme_manager.get_color("text.primary"),
            width=200,
            anchor="w"
        )
        label.pack(side="left", padx=(0, 10))
        
        switch = ctk.CTkSwitch(
            row_frame,
            text="",
            width=50,
            fg_color=theme_manager.get_color("buttons.primary_bg"),
            progress_color=theme_manager.get_color("buttons.primary_text"),
            button_color=theme_manager.get_color("buttons.secondary_bg"),
            button_hover_color=theme_manager.get_color("buttons.secondary_hover")
        )
        if default_value:
            switch.select()
        switch.pack(side="left")
    
    def apply_theme(self):
        """Apply the current theme to all components"""
        if hasattr(self, 'main_container'):
            try:
                # Update main container
                self.main_container.configure(fg_color=theme_manager.get_color("background.main"))
                
                # Update all frames
                for widget in self.main_container.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        if "corner_radius" in str(widget.configure()):
                            widget.configure(fg_color=theme_manager.get_color("background.secondary"))
                    elif isinstance(widget, ctk.CTkLabel):
                        widget.configure(text_color=theme_manager.get_color("text.primary"))
                
                # Update theme selector specifically
                if hasattr(self, 'theme_var'):
                    for widget in self.theme_frame.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            for child in widget.winfo_children():
                                if isinstance(child, ctk.CTkOptionMenu):
                                    child.configure(
                                        fg_color=theme_manager.get_color("editor.background"),
                                        text_color=theme_manager.get_color("text.primary"),
                                        button_color=theme_manager.get_color("buttons.primary_bg"),
                                        button_hover_color=theme_manager.get_color("buttons.primary_hover")
                                    )
            except Exception as e:
                print(f"Error applying theme to config view: {e}")
    
    def save_settings(self):
        """Save all settings to configuration file"""
        try:
            # Save any pending changes
            config_manager.save_config()
            messagebox.showinfo("Settings", "All settings saved successfully!")
        except Exception as e:
            print(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Error saving settings: {str(e)}")
    
    def reset_settings(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?\n\nThis will reset:\n• Window settings\n• Database defaults\n• All other preferences"):
            try:
                config_manager.reset_to_defaults()
                messagebox.showinfo("Settings", "Settings reset to defaults!")
                
            except Exception as e:
                print(f"Error resetting settings: {e}")
                messagebox.showerror("Error", f"Error resetting settings: {str(e)}")
