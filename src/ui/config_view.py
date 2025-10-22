"""
Configuration View Component
Settings and preferences for PgWarp
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Optional, Dict, Any
import os
import json
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
        self.default_host_entry = self.create_setting_row(db_frame, "Default Host:", self.config.default_host)
        self.default_port_entry = self.create_setting_row(db_frame, "Default Port:", str(self.config.default_port))
        self.default_database_entry = self.create_setting_row(db_frame, "Default Database:", self.config.default_database)
        self.connection_timeout_entry = self.create_setting_row(db_frame, "Connection Timeout (s):", "30")
        
        # AI Settings Section
        self.create_section(main_container, "🤖 AI Assistant Settings")
        
        ai_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        ai_frame.pack(fill="x", pady=(0, 20))
        
        self.api_key_entry = self.create_setting_row(ai_frame, "API Key:", "••••••••••••", is_password=True)
        self.ai_model_entry = self.create_setting_row(ai_frame, "Model:", self.config.ai_model)
        self.temperature_entry = self.create_setting_row(ai_frame, "Temperature:", "0.7")
        self.max_tokens_entry = self.create_setting_row(ai_frame, "Max Tokens:", str(self.config.ai_max_history * 100))
        
        # Editor Settings Section
        self.create_section(main_container, "📝 Editor Settings")
        
        editor_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        editor_frame.pack(fill="x", pady=(0, 20))
        
        self.font_family_entry = self.create_setting_row(editor_frame, "Font Family:", self.config.terminal_font_family)
        self.font_size_entry = self.create_setting_row(editor_frame, "Font Size:", str(self.config.terminal_font_size))
        
        # Toggle settings
        self.line_numbers_switch = self.create_toggle_row(editor_frame, "Line Numbers", self.config.show_line_numbers)
        self.auto_complete_switch = self.create_toggle_row(editor_frame, "Auto-complete", True)
        self.syntax_highlighting_switch = self.create_toggle_row(editor_frame, "Syntax Highlighting", True)
        
        # Display Settings Section
        self.create_section(main_container, "🎨 Display Settings")
        
        display_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        display_frame.pack(fill="x", pady=(0, 20))
        
        self.max_rows_entry = self.create_setting_row(display_frame, "Max Result Rows:", str(self.config.max_result_rows))
        self.show_row_numbers_switch = self.create_toggle_row(display_frame, "Show Row Numbers", True)
        self.alternating_colors_switch = self.create_toggle_row(display_frame, "Alternating Row Colors", True)
        
        # Theme Settings Section
        self.create_section(main_container, "🎨 Theme Settings")
        
        theme_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        theme_frame.pack(fill="x", pady=(0, 20))
        
        self.create_theme_selector(theme_frame)
        
        # Export Settings Section
        self.create_section(main_container, "📤 Export Settings")
        
        export_frame = ctk.CTkFrame(main_container, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        export_frame.pack(fill="x", pady=(0, 20))
        
        # Create export format dropdown instead of text entry
        export_format_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_format_frame.pack(fill="x", padx=15, pady=8)
        
        export_format_label = ctk.CTkLabel(
            export_format_frame,
            text="Default Export Format:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme_manager.get_color("text.primary"),
            width=200,
            anchor="w"
        )
        export_format_label.pack(side="left", padx=(20, 10), pady=10)
        
        self.export_format_menu = ctk.CTkOptionMenu(
            export_format_frame,
            values=["CSV", "Excel", "JSON", "SQL"],
            width=250,
            height=32,
            fg_color=theme_manager.get_color("editor.background"),
            text_color=theme_manager.get_color("text.primary"),
            button_color=theme_manager.get_color("buttons.primary_bg"),
            button_hover_color=theme_manager.get_color("buttons.primary_hover"),
            corner_radius=6
        )
        self.export_format_menu.pack(side="left", padx=(0, 20), pady=10)
        self.export_format_menu.set("CSV")
        
        # Create export directory row with browse button
        export_dir_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_dir_frame.pack(fill="x", padx=15, pady=8)
        
        export_dir_label = ctk.CTkLabel(
            export_dir_frame,
            text="Export Directory:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme_manager.get_color("text.primary"),
            width=200,
            anchor="w"
        )
        export_dir_label.pack(side="left", padx=(20, 10), pady=10)
        
        self.export_directory_entry = ctk.CTkEntry(
            export_dir_frame,
            width=200,
            height=32,
            fg_color=theme_manager.get_color("editor.background"),
            text_color=theme_manager.get_color("text.primary"),
            border_color=theme_manager.get_color("accent.main"),
            corner_radius=6
        )
        self.export_directory_entry.pack(side="left", padx=(0, 10), pady=10)
        self.export_directory_entry.insert(0, str(Path.home() / "Downloads"))
        
        browse_btn = ctk.CTkButton(
            export_dir_frame,
            text="Browse",
            command=self.browse_export_directory,
            width=80,
            height=32,
            fg_color=theme_manager.get_color("buttons.secondary_bg"),
            hover_color=theme_manager.get_color("buttons.secondary_hover"),
            text_color=theme_manager.get_color("buttons.secondary_text"),
            font=ctk.CTkFont(size=12),
            corner_radius=6
        )
        browse_btn.pack(side="left", padx=(0, 20), pady=10)
        
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
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme_manager.get_color("text.primary"),
            width=200,
            anchor="w"
        )
        label.pack(side="left", padx=(20, 10), pady=10)
        
        entry = ctk.CTkEntry(
            row_frame,
            placeholder_text=default_value,
            width=250,
            height=32,
            fg_color=theme_manager.get_color("editor.background"),
            text_color=theme_manager.get_color("text.primary"),
            border_color=theme_manager.get_color("accent.main"),
            corner_radius=6,
            show="*" if is_password else None
        )
        entry.pack(side="left", padx=(0, 20), pady=10)
        entry.insert(0, default_value)
        return entry
    
    def create_toggle_row(self, parent, label_text: str, default_value: bool):
        """Create a toggle switch row"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=15, pady=8)
        
        label = ctk.CTkLabel(
            row_frame,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme_manager.get_color("text.primary"),
            width=200,
            anchor="w"
        )
        label.pack(side="left", padx=(20, 10))
        
        switch = ctk.CTkSwitch(
            row_frame,
            text="",
            width=50,
            height=24,
            fg_color=theme_manager.get_color("buttons.primary_bg"),
            progress_color=theme_manager.get_color("buttons.primary_text"),
            button_color=theme_manager.get_color("buttons.secondary_bg"),
            button_hover_color=theme_manager.get_color("buttons.secondary_hover")
        )
        if default_value:
            switch.select()
        switch.pack(side="left", padx=(0, 20))
        return switch
    
    def apply_theme(self):
        """Apply the current theme to all components"""
        try:
            # Update main frame
            self.configure(fg_color=theme_manager.get_color("background.main"))
            
            # Update all child widgets recursively
            for widget in self.winfo_children():
                self._update_widget_theme(widget)
        except Exception as e:
            print(f"Error applying theme to config view: {e}")
    
    def _update_widget_theme(self, widget):
        """Recursively update widget themes"""
        try:
            if isinstance(widget, ctk.CTkFrame):
                if hasattr(widget, 'cget') and widget.cget('fg_color') != "transparent":
                    widget.configure(fg_color=theme_manager.get_color("background.secondary"))
            elif isinstance(widget, ctk.CTkLabel):
                widget.configure(text_color=theme_manager.get_color("text.primary"))
            elif isinstance(widget, ctk.CTkEntry):
                widget.configure(
                    fg_color=theme_manager.get_color("editor.background"),
                    text_color=theme_manager.get_color("text.primary"),
                    border_color=theme_manager.get_color("accent.main")
                )
            elif isinstance(widget, ctk.CTkOptionMenu):
                widget.configure(
                    fg_color=theme_manager.get_color("editor.background"),
                    text_color=theme_manager.get_color("text.primary"),
                    button_color=theme_manager.get_color("buttons.primary_bg"),
                    button_hover_color=theme_manager.get_color("buttons.primary_hover")
                )
            elif isinstance(widget, ctk.CTkButton):
                if "primary" in str(widget.cget('fg_color')):
                    widget.configure(
                        fg_color=theme_manager.get_color("buttons.primary_bg"),
                        hover_color=theme_manager.get_color("buttons.primary_hover"),
                        text_color=theme_manager.get_color("buttons.primary_text")
                    )
                else:
                    widget.configure(
                        fg_color=theme_manager.get_color("buttons.secondary_bg"),
                        hover_color=theme_manager.get_color("buttons.secondary_hover"),
                        text_color=theme_manager.get_color("buttons.secondary_text")
                    )
            elif isinstance(widget, ctk.CTkSwitch):
                widget.configure(
                    fg_color=theme_manager.get_color("buttons.primary_bg"),
                    progress_color=theme_manager.get_color("buttons.primary_text"),
                    button_color=theme_manager.get_color("buttons.secondary_bg"),
                    button_hover_color=theme_manager.get_color("buttons.secondary_hover")
                )
            
            # Recursively update children
            for child in widget.winfo_children():
                self._update_widget_theme(child)
        except Exception:
            pass
    
    def create_theme_selector(self, parent):
        """Create theme selection controls"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=15, pady=8)
        
        label = ctk.CTkLabel(
            row_frame,
            text="Application Theme:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme_manager.get_color("text.primary"),
            width=200,
            anchor="w"
        )
        label.pack(side="left", padx=(20, 10), pady=10)
        
        # Get available themes
        available_themes = theme_manager.list_available_themes()
        theme_display_names = []
        self.theme_file_mapping = {}
        
        for theme_file in available_themes:
            # Load theme to get display name
            theme_path = theme_manager.themes_dir / f"{theme_file}.json"
            try:
                with open(theme_path, 'r') as f:
                    theme_data = json.load(f)
                display_name = theme_data.get('name', theme_file)
                theme_display_names.append(display_name)
                self.theme_file_mapping[display_name] = theme_file
            except Exception as e:
                print(f"Error loading theme {theme_file}: {e}")
                theme_display_names.append(theme_file)
                self.theme_file_mapping[theme_file] = theme_file
        
        self.theme_selector = ctk.CTkOptionMenu(
            row_frame,
            values=theme_display_names if theme_display_names else ["Default"],
            command=self.on_theme_change,
            width=250,
            height=32,
            fg_color=theme_manager.get_color("input"),
            text_color=theme_manager.get_color("foreground"),
            button_color=theme_manager.get_color("primary"),
            button_hover_color=theme_manager.get_color("accent"),
            corner_radius=6
        )
        self.theme_selector.pack(side="left", padx=(0, 20), pady=10)
        
        # Set current theme
        current_theme_file = getattr(self.config, 'selected_theme', 'solarized-light')
        for display_name, file_name in self.theme_file_mapping.items():
            if file_name == current_theme_file:
                self.theme_selector.set(display_name)
                break
    
    def on_theme_change(self, selected_display_name):
        """Handle theme selection change"""
        try:
            theme_file = self.theme_file_mapping.get(selected_display_name, 'solarized-light')
            
            # Update config
            self.config.selected_theme = theme_file
            
            # Apply theme immediately
            if theme_manager.set_theme(theme_file):
                # Refresh the entire UI
                if self.main_window:
                    self.main_window.apply_theme()
                self.apply_theme()
                print(f"✓ Applied theme: {selected_display_name}")
            else:
                print(f"✗ Failed to apply theme: {selected_display_name}")
                
        except Exception as e:
            print(f"Error changing theme: {e}")
            messagebox.showerror("Theme Error", f"Failed to change theme: {str(e)}")
    
    def browse_export_directory(self):
        """Open directory browser for export directory"""
        try:
            current_dir = self.export_directory_entry.get() or str(Path.home() / "Downloads")
            directory = filedialog.askdirectory(
                title="Select Export Directory",
                initialdir=current_dir
            )
            if directory:
                self.export_directory_entry.delete(0, 'end')
                self.export_directory_entry.insert(0, directory)
        except Exception as e:
            print(f"Error browsing directory: {e}")
    
    def validate_numeric_input(self, value: str, field_name: str, default: int, min_val: int = 1, max_val: int = None) -> int:
        """Validate numeric input with proper error handling"""
        try:
            num_value = int(value)
            if num_value < min_val:
                messagebox.showwarning("Invalid Input", f"{field_name} must be at least {min_val}")
                return default
            if max_val and num_value > max_val:
                messagebox.showwarning("Invalid Input", f"{field_name} must be at most {max_val}")
                return default
            return num_value
        except ValueError:
            messagebox.showwarning("Invalid Input", f"{field_name} must be a valid number")
            return default
    
    def save_settings(self):
        """Save all settings to configuration file"""
        try:
            # Update config with values from UI
            if hasattr(self, 'default_host_entry'):
                host_value = self.default_host_entry.get().strip()
                self.config.default_host = host_value if host_value else "localhost"
            
            if hasattr(self, 'default_port_entry'):
                self.config.default_port = self.validate_numeric_input(
                    self.default_port_entry.get(), "Port", 5432, 1, 65535
                )
            
            if hasattr(self, 'default_database_entry'):
                db_value = self.default_database_entry.get().strip()
                self.config.default_database = db_value if db_value else "postgres"
            
            # AI settings
            if hasattr(self, 'ai_model_entry'):
                model_value = self.ai_model_entry.get().strip()
                self.config.ai_model = model_value if model_value else "gemini-2.0-flash-exp"
            
            # Editor settings
            if hasattr(self, 'font_family_entry'):
                font_value = self.font_family_entry.get().strip()
                self.config.terminal_font_family = font_value if font_value else "Consolas"
            
            if hasattr(self, 'font_size_entry'):
                self.config.terminal_font_size = self.validate_numeric_input(
                    self.font_size_entry.get(), "Font Size", 11, 8, 72
                )
            
            if hasattr(self, 'line_numbers_switch'):
                self.config.show_line_numbers = bool(self.line_numbers_switch.get())
            
            # Display settings
            if hasattr(self, 'max_rows_entry'):
                self.config.max_result_rows = self.validate_numeric_input(
                    self.max_rows_entry.get(), "Max Result Rows", 10000, 100, 1000000
                )
            
            # Theme settings - already saved in on_theme_change, but ensure it's saved
            if hasattr(self, 'theme_selector'):
                selected_display_name = self.theme_selector.get()
                if hasattr(self, 'theme_file_mapping'):
                    theme_file = self.theme_file_mapping.get(selected_display_name, 'solarized-light')
                    self.config.selected_theme = theme_file
            
            # Export settings (these would need to be added to config if needed)
            export_format = getattr(self, 'export_format_menu', None)
            export_dir = getattr(self, 'export_directory_entry', None)
            if export_format and export_dir:
                print(f"Export format: {export_format.get()}")
                print(f"Export directory: {export_dir.get()}")
            
            # Save configuration
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
                
                # Refresh UI with default values
                self.refresh_ui_values()
                
                messagebox.showinfo("Settings", "Settings reset to defaults!")
                
            except Exception as e:
                print(f"Error resetting settings: {e}")
                messagebox.showerror("Error", f"Error resetting settings: {str(e)}")
    
    def refresh_ui_values(self):
        """Refresh UI controls with current config values"""
        try:
            # Database settings
            if hasattr(self, 'default_host_entry'):
                self.default_host_entry.delete(0, 'end')
                self.default_host_entry.insert(0, self.config.default_host)
            if hasattr(self, 'default_port_entry'):
                self.default_port_entry.delete(0, 'end')
                self.default_port_entry.insert(0, str(self.config.default_port))
            if hasattr(self, 'default_database_entry'):
                self.default_database_entry.delete(0, 'end')
                self.default_database_entry.insert(0, self.config.default_database)
            
            # AI settings
            if hasattr(self, 'ai_model_entry'):
                self.ai_model_entry.delete(0, 'end')
                self.ai_model_entry.insert(0, self.config.ai_model)
            
            # Editor settings
            if hasattr(self, 'font_family_entry'):
                self.font_family_entry.delete(0, 'end')
                self.font_family_entry.insert(0, self.config.terminal_font_family)
            if hasattr(self, 'font_size_entry'):
                self.font_size_entry.delete(0, 'end')
                self.font_size_entry.insert(0, str(self.config.terminal_font_size))
            
            # Toggle switches
            if hasattr(self, 'line_numbers_switch'):
                if self.config.show_line_numbers:
                    self.line_numbers_switch.select()
                else:
                    self.line_numbers_switch.deselect()
            
            # Display settings
            if hasattr(self, 'max_rows_entry'):
                self.max_rows_entry.delete(0, 'end')
                self.max_rows_entry.insert(0, str(self.config.max_result_rows))
            
            # Export settings
            if hasattr(self, 'export_format_menu'):
                self.export_format_menu.set("CSV")  # Default export format
            if hasattr(self, 'export_directory_entry'):
                self.export_directory_entry.delete(0, 'end')
                self.export_directory_entry.insert(0, str(Path.home() / "Downloads"))
                
        except Exception as e:
            print(f"Error refreshing UI values: {e}")
