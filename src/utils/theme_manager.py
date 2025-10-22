"""
Theme manager for PgWarp application
Handles loading and applying themes from JSON files
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class ThemeManager:
    """Manages application themes and color schemes"""
    
    def __init__(self):
        self.current_theme: Dict[str, Any] = {}
        self.theme_name: str = ""
        self.available_themes: Dict[str, Dict] = {}
        
        # Look for themes directory at src/themes level
        self.themes_dir = Path(__file__).parent.parent / "themes"
        self.themes_dir.mkdir(exist_ok=True)
        
        # Load available themes and set default
        self.load_available_themes()
        # Try to load from config first, fallback to projectnest-default
        from utils.config_manager import config_manager
        selected_theme = getattr(config_manager.config, 'selected_theme', 'projectnest-default')
        self.initialize_with_fallback(selected_theme)
    
    def load_available_themes(self):
        """Load all available theme files"""
        if not self.themes_dir.exists():
            print(f"Themes directory not found: {self.themes_dir}")
            return
        
        self.available_themes = {}
        
        for theme_file in self.themes_dir.glob("*.json"):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                
                theme_name = theme_data.get('name', theme_file.stem)
                file_name = theme_file.stem
                
                self.available_themes[file_name] = {
                    'file': theme_file,
                    'data': theme_data,
                    'display_name': theme_name
                }
                
                print(f"Loaded theme: {theme_name} ({file_name})")
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading theme {theme_file}: {e}")
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme by filename (without .json)"""
        print(f"Trying to set theme: '{theme_name}'")
        print(f"Available themes: {list(self.available_themes.keys())}")
        
        # Try exact match first
        if theme_name in self.available_themes:
            self.current_theme = self.available_themes[theme_name]['data']
            self.theme_name = theme_name
            print(f"✓ Set theme to: {self.available_themes[theme_name]['display_name']} ({theme_name})")
            return True
        
        # Try case-insensitive match
        for available_name in self.available_themes:
            if available_name.lower() == theme_name.lower():
                self.current_theme = self.available_themes[available_name]['data']
                self.theme_name = available_name
                print(f"✓ Set theme to: {self.available_themes[available_name]['display_name']} ({available_name})")
                return True
        
        print(f"✗ Theme not found: {theme_name}")
        return False
    
    def get_color(self, color_path: str, fallback: str = "#000000") -> str:
        """
        Get color from current theme using simple color paths.
        
        Args:
            color_path: Simple color path (e.g., "background", "primary", "foreground")
            fallback: Fallback color if not found
            
        Returns:
            Color string (hex, hsl, or css color)
        """
        if not self.current_theme:
            return self._get_fallback_color(color_path, fallback)
        
        colors = self.current_theme.get('colors', {})
        
        # Try direct color lookup first
        if color_path in colors:
            color = colors[color_path]
            return self._normalize_color(color)
        
        # Try mapping common paths to new format
        color_mapping = {
            # Background colors
            "background.main": "background",
            "background.secondary": "card",
            
            # Text colors
            "text.primary": "foreground", 
            "text.secondary": "mutedForeground",
            
            # Button colors
            "buttons.primary_bg": "primary",
            "buttons.primary_text": "primaryForeground", 
            "buttons.primary_hover": "primaryHover",
            "buttons.secondary_bg": "secondary",
            "buttons.secondary_text": "secondaryForeground",
            "buttons.secondary_hover": "secondaryHover",
            "buttons.danger_bg": "destructive",
            "buttons.danger_text": "destructiveForeground",
            "buttons.danger_hover": "destructive",
            
            # Accent colors
            "accent.main": "primary",
            "accent.primary": "primary",
            
            # Editor colors
            "editor.background": "background",
            
            # Sidebar colors  
            "sidebar.background": "sidebarBackground",
            "sidebar.header": "card",
            "sidebar.text": "sidebarForeground",
            
            # Table colors (legacy support)
            "table.background": "background",
            "table.text": "foreground", 
            "table.header": "card",
            "table.selected": "primary",
            
            # Scrollbar colors (legacy support)
            "scrollbar.thumb": "muted",
            "scrollbar.track": "background",
            
            # Schema browser specific colors
            "schema.title_bg": "primary",
            "schema.title_text": "primaryForeground",
            "schema.button_bg": "secondary",
            "schema.button_hover": "secondaryHover",
            "schema.button_text": "secondaryForeground",
            "schema.delete_bg": "destructive",
            "schema.delete_hover": "destructive",
            "schema.export_bg": "muted",
            "schema.export_hover": "accent",
            "schema.export_text": "foreground",
            "schema.table_frame": "card",
            "schema.table_odd": "cardHover",
            "schema.empty_text": "mutedForeground",
            
            # Terminal specific colors
            "terminal.background": "card",
            "terminal.foreground": "foreground",
            "terminal.cursor": "accent",
            "terminal.selection": "accent",
            "terminal.highlight": "accent",
            "terminal.scrollbar_bg": "cardHover",
            "terminal.scrollbar_trough": "card",
            "terminal.scrollbar_arrow": "accent",
            "terminal.error": "destructive",
            "terminal.command": "mutedForeground",
            
            # Diagram specific colors
            "diagram.canvas_bg": "card",
            "diagram.table_bg": "background",
            "diagram.table_border": "primary",
            "diagram.header_bg": "primary",
            "diagram.header_fg": "primaryForeground",
            "diagram.text": "foreground",
            "diagram.pk": "primary",
            "diagram.fk": "secondary",
            "diagram.line": "primary",
            "diagram.null_indicator": "destructive",
            "diagram.column_type": "mutedForeground",
            "diagram.minimap_bg": "cardHover",
            "diagram.minimap_viewport": "accent",
            "diagram.minimap_outline": "border",
            "diagram.panel_bg": "card",
            "diagram.separator": "primary",
            "diagram.separator_hover": "primaryHover",
            "scrollbar.arrow": "foreground",
            
            # Additional mappings for better coverage
            "statusbar.background": "card",
            "statusbar.foreground": "foreground",
            "results.background": "background",
            "results.foreground": "foreground",
            "results.header": "card",
        }
        
        # Try mapped lookup
        if color_path in color_mapping:
            mapped_color = color_mapping[color_path]
            if mapped_color in colors:
                color = colors[mapped_color]
                return self._normalize_color(color)
        
        # Return fallback
        return self._get_fallback_color(color_path, fallback)
    
    def _normalize_color(self, color: str) -> str:
        """Normalize different color formats to usable CSS color"""
        if not color:
            return "#000000"
        
        color = color.strip()
        
        # If it's already a hex color, return as is
        if color.startswith("#"):
            return color
        
        # If it's an HSL value without hsl(), add it
        if not color.startswith("hsl(") and not color.startswith("rgb("):
            # Try to parse as HSL values (e.g., "222.2 84% 4.9%")
            if "%" in color:
                try:
                    parts = color.split()
                    if len(parts) == 3:
                        return f"hsl({parts[0]}, {parts[1]}, {parts[2]})"
                except:
                    pass
        
        return color
    
    def _get_fallback_color(self, color_path: str, fallback: str = "#000000") -> str:
        """Get fallback colors when theme is not available or color not found"""
        fallback_colors = {
            # Background colors
            "background": "#F5EFE7",
            "background.main": "#F5EFE7",
            "background.secondary": "#E8DFD0",
            "card": "#E8DFD0", 
            
            # Text colors
            "foreground": "#3E2723",
            "text.primary": "#3E2723",
            "text.secondary": "#8B7355",
            "mutedForeground": "#8B7355",
            
            # Button colors
            "primary": "#9B8F5E",
            "primaryForeground": "#FFFFFF",
            "buttons.primary_bg": "#9B8F5E",
            "buttons.primary_text": "#FFFFFF",
            "buttons.primary_hover": "#87795A",
            "secondary": "#E8DFD0",
            "secondaryForeground": "#3E2723", 
            "buttons.secondary_bg": "#E8DFD0",
            "buttons.secondary_text": "#3E2723",
            "buttons.secondary_hover": "#D9CDBF",
            "destructive": "#C4756C",
            "destructiveForeground": "#FFFFFF",
            "buttons.danger_bg": "#C4756C",
            "buttons.danger_text": "#FFFFFF",
            "buttons.danger_hover": "#A85E56",
            
            # Accent colors
            "accent": "#9B8F5E",
            "accent.main": "#9B8F5E", 
            "accent.primary": "#9B8F5E",
            
            # Editor colors
            "editor.background": "#F5EFE7",
            
            # Borders
            "border": "#D9CDBF",
            "input": "#E8DFD0",
            
            # Sidebar colors
            "sidebar.background": "#E8DFD0",
            "sidebar.header": "#D9CDBF",
        }
        
        return fallback_colors.get(color_path, fallback)
    
    def _get_fallback_color(self, color_path: str, fallback: str = "#000000") -> str:
        """Get fallback colors when theme is not available or color not found"""
        fallback_colors = {
            # Editor colors (dot notation)
            'editor.background': '#F5EFE7',
            'editor.text': '#3E2723',
            'primary.main': '#F5EFE7',
            'primary.light': '#FFFFFF',
            'primary.dark': '#E8DFD0',
            'secondary.main': '#E8DFD0',
            'accent.main': '#9B8F5E',
            'text.primary': '#3E2723',
            'text.secondary': '#8B7355',
            'background.main': '#F5EFE7',
            'background.secondary': '#E8DFD0',
            'buttons.primary_bg': '#9B8F5E',
            'buttons.primary_text': '#FFFFFF',
            'buttons.primary_hover': '#87795A',
            'buttons.secondary_bg': '#E8DFD0',
            'buttons.secondary_hover': '#D9CDBF',
            'buttons.secondary_text': '#3E2723',
            'buttons.danger_bg': '#C4756C',
            'buttons.danger_hover': '#A85E56',
            'buttons.danger_text': '#FFFFFF',
        }
        
        return fallback_colors.get(color_path, fallback)
    
    def get_colors(self, color_group: str) -> Dict[str, str]:
        """Get all colors from a color group"""
        try:
            return self.current_theme.get('colors', {}).get(color_group, {})
        except Exception:
            return {}
    
    def list_available_themes(self) -> List[str]:
        """Get list of available theme files (without .json extension)"""
        return list(self.available_themes.keys())
    
    def get_available_themes(self) -> List[str]:
        """Get available themes (alias for list_available_themes)"""
        return self.list_available_themes()
    
    def get_theme_display_names(self) -> Dict[str, str]:
        """Get mapping of theme filenames to display names"""
        return {
            filename: info['display_name'] 
            for filename, info in self.available_themes.items()
        }
    
    def get_theme_type(self) -> str:
        """Get the current theme type (light/dark)"""
        if not self.current_theme:
            return 'light'
        return self.current_theme.get('type', 'light')
    
    def get_theme_name(self) -> str:
        """Get the current theme display name"""
        if not self.current_theme:
            return 'Default'
        return self.current_theme.get('name', 'Unknown')
    
    @property
    def current_theme_name(self) -> str:
        """Get the current theme filename"""
        return self.theme_name
    
    def save_theme(self, theme_name: str, theme_data: Dict[str, Any]) -> bool:
        """Save a theme to JSON file"""
        try:
            theme_file = self.themes_dir / f"{theme_name}.json"
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            # Reload available themes to include the new one
            self.load_available_themes()
            return True
        except Exception as e:
            print(f"Error saving theme {theme_name}: {e}")
            return False
    
    def create_custom_theme(self, name: str, description: str, base_theme: str = "default") -> Dict[str, Any]:
        """Create a new custom theme based on an existing theme"""
        try:
            if base_theme != self.theme_name:
                self.set_theme(base_theme)
            
            custom_theme = self.current_theme.copy()
            custom_theme["name"] = name
            custom_theme["description"] = description
            
            return custom_theme
        except Exception as e:
            print(f"Error creating custom theme: {e}")
            return {}
    
    def initialize_with_fallback(self, preferred_theme: str = "default") -> bool:
        """Initialize theme manager with preferred theme or fallback to default"""
        try:
            # Try preferred theme first
            if self.set_theme(preferred_theme):
                return True
            
            # Fallback to default
            if preferred_theme != "default" and self.set_theme("default"):
                print(f"Preferred theme '{preferred_theme}' not found, using default")
                return True
            
            # If default doesn't exist, use first available theme
            available = self.list_available_themes()
            if available:
                first_theme = available[0]
                if self.set_theme(first_theme):
                    print(f"Default theme not found, using '{first_theme}'")
                    return True
            
            print("No themes available!")
            return False
            
        except Exception as e:
            print(f"Error initializing theme: {e}")
            return False


# Global theme manager instance
theme_manager = ThemeManager()


def get_color(color_path: str, fallback: str = "#000000") -> str:
    """Convenience function to get colors from the global theme manager"""
    return theme_manager.get_color(color_path, fallback)


def get_colors(color_group: str) -> Dict[str, str]:
    """Convenience function to get color groups from the global theme manager"""
    return theme_manager.get_colors(color_group)


def set_theme(theme_name: str) -> bool:
    """Convenience function to set a theme"""
    return theme_manager.set_theme(theme_name)


def list_themes() -> List[str]:
    """Convenience function to list available themes"""
    return theme_manager.list_available_themes()