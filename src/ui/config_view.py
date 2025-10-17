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
        
        # Theme Settings Section
        self.create_section(main_container, "🎨 Theme Settings")
        
        theme_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        theme_frame.pack(fill="x", pady=(0, 20))
        
        self.create_theme_selector(theme_frame)
        
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
        separator = ctk.CTkFrame(section_frame, height=2, fg_color=theme_manager.get_color("accent.primary"), corner_radius=1)
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
            fg_color=theme_manager.get_color("inputs.bg"),
            text_color=theme_manager.get_color("inputs.text"),
            border_color=theme_manager.get_color("inputs.border")
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
                                        fg_color=theme_manager.get_color("inputs.bg"),
                                        text_color=theme_manager.get_color("inputs.text"),
                                        button_color=theme_manager.get_color("buttons.primary_bg"),
                                        button_hover_color=theme_manager.get_color("buttons.primary_hover")
                                    )
            except Exception as e:
                print(f"Error applying theme to config view: {e}")
                
    def refresh_theme_selector(self):
        """Refresh the theme selector to reflect current theme"""
        if hasattr(self, 'theme_var'):
            current_theme = theme_manager.get_current_theme()
            display_name = theme_manager.get_theme_display_name(current_theme)
            self.theme_var.set(display_name)
    
    def create_theme_selector(self, parent):
        """Create theme selection controls"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=15, pady=8)
        
        label = ctk.CTkLabel(
            row_frame,
            text="Default Theme:",
            font=ctk.CTkFont(size=12),
            text_color=theme_manager.get_color("text.primary"),
            width=200,
            anchor="w"
        )
        label.pack(side="left", padx=(0, 10))
        
        # Get available themes with display names
        theme_display_names = theme_manager.get_theme_display_names()
        theme_files = list(theme_display_names.keys())
        theme_labels = list(theme_display_names.values())
        
        current_theme = config_manager.get('default_theme', 'default')
        
        # Theme dropdown with display names
        self.theme_dropdown = ctk.CTkComboBox(
            row_frame,
            values=theme_labels,
            command=self.on_theme_change,
            width=200,
            font=ctk.CTkFont(size=12),
            dropdown_font=ctk.CTkFont(size=12),
            corner_radius=6,
            fg_color=theme_manager.get_color("background.secondary"),
            border_color=theme_manager.get_color("accent.main"),
            button_color=theme_manager.get_color("buttons.primary_bg"),
            button_hover_color=theme_manager.get_color("buttons.primary_hover")
        )
        
        # Set current theme by display name
        if current_theme in theme_display_names:
            current_display_name = theme_display_names[current_theme]
            self.theme_dropdown.set(current_display_name)
        else:
            self.theme_dropdown.set(theme_labels[0] if theme_labels else "Default")
        
        self.theme_dropdown.pack(side="left", padx=(0, 10))
        
        # Store mapping for lookup
        self.theme_file_map = {display_name: file_name for file_name, display_name in theme_display_names.items()}
        
        # Apply button
        apply_btn = ctk.CTkButton(
            row_frame,
            text="✓ Apply",
            command=self.apply_theme,
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=theme_manager.get_color("buttons.primary_bg"),
            hover_color=theme_manager.get_color("buttons.primary_hover"),
            corner_radius=6
        )
        apply_btn.pack(side="left", padx=(5, 0))
    
    def on_theme_change(self, selected_display_name):
        """Handle theme selection change (updates config but doesn't apply immediately)"""
        try:
            # Get the theme filename from display name
            theme_file = self.theme_file_map.get(selected_display_name)
            if theme_file:
                # Update config but don't save yet (wait for apply button)
                self.config.default_theme = theme_file
                print(f"Theme selection changed to: {selected_display_name} ({theme_file})")
        except Exception as e:
            print(f"Error handling theme change: {e}")
    
    def apply_theme(self):
        """Apply the selected theme immediately and save to config"""
        try:
            selected_display_name = self.theme_dropdown.get()
            theme_file = self.theme_file_map.get(selected_display_name)
            
            if theme_file:
                # Apply theme immediately
                if theme_manager.set_theme(theme_file):
                    # Update config and save
                    config_manager.set('default_theme', theme_file)
                    config_manager.save_config()
                    
                    # Apply theme to main window if available
                    if self.main_window and hasattr(self.main_window, 'apply_theme'):
                        self.main_window.apply_theme()
                    
                    # Refresh this config view
                    self.apply_theme_to_self()
                    
                    messagebox.showinfo("Theme Applied", f"Theme '{selected_display_name}' applied and saved as default!")
                else:
                    messagebox.showerror("Error", f"Failed to apply theme: {selected_display_name}")
            else:
                messagebox.showerror("Error", "Invalid theme selection")
                
        except Exception as e:
            print(f"Error applying theme: {e}")
            messagebox.showerror("Error", f"Error applying theme: {str(e)}")
    
    def apply_theme_to_self(self):
        """Apply current theme colors to this config view"""
        try:
            self.configure(fg_color=theme_manager.get_color("background.main"))
            
            # Update any child widgets that need theme updates
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkScrollableFrame):
                    widget.configure(fg_color=theme_manager.get_color("background.main"))
                    
        except Exception as e:
            print(f"Error applying theme to config view: {e}")
    
    def refresh_theme_selector(self):
        """Refresh the theme selector with current settings"""
        try:
            current_theme = config_manager.get('default_theme', 'default')
            theme_display_names = theme_manager.get_theme_display_names()
            
            if current_theme in theme_display_names:
                current_display_name = theme_display_names[current_theme]
                self.theme_dropdown.set(current_display_name)
                
        except Exception as e:
            print(f"Error refreshing theme selector: {e}")
    
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
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?\n\nThis will reset:\n• Theme preferences\n• Window settings\n• Database defaults\n• All other preferences"):
            try:
                config_manager.reset_to_defaults()
                
                # Refresh the UI with default values
                self.refresh_theme_selector()
                
                # Apply default theme
                theme_manager.initialize_with_fallback('default')
                if self.main_window and hasattr(self.main_window, 'apply_theme'):
                    self.main_window.apply_theme()
                
                self.apply_theme_to_self()
                messagebox.showinfo("Settings", "Settings reset to defaults!")
                
            except Exception as e:
                print(f"Error resetting settings: {e}")
                messagebox.showerror("Error", f"Error resetting settings: {str(e)}")
