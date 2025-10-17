#!/usr/bin/env python3
"""
Theme system demonstr    # Switch back to default
    print("\nSwitching back to default theme...")
    theme_manager.set_theme("default")on script
Shows how the theme manager works and how themes can be switched
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.theme_manager import theme_manager, get_color

def demonstrate_theme_system():
    """Demonstrate the theme system functionality"""
    
    print("=== PgWarp Theme System Demo ===\n")
    
    # Show available themes
    print("Available themes:")
    themes = theme_manager.list_available_themes()
    for theme in themes:
        print(f"  - {theme}")
    print()
    
    # Show current theme colors
    print("Current theme colors (default):")
    print(f"  Primary background: {get_color('primary.main')}")
    print(f"  Secondary background: {get_color('secondary.main')}")
    print(f"  Accent color: {get_color('accent.main')}")
    print(f"  Text primary: {get_color('text.primary')}")
    print(f"  Button background: {get_color('buttons.primary_bg')}")
    print(f"  Button hover: {get_color('buttons.primary_hover')}")
    print()
    
    # Switch to dark theme
    print("Switching to dark theme...")
    theme_manager.set_theme("dark")
    print("Dark theme colors:")
    print(f"  Primary background: {get_color('primary.main')}")
    print(f"  Secondary background: {get_color('secondary.main')}")
    print(f"  Accent color: {get_color('accent.main')}")
    print(f"  Text primary: {get_color('text.primary')}")
    print(f"  Button background: {get_color('buttons.primary_bg')}")
    print(f"  Button hover: {get_color('buttons.primary_hover')}")
    print()
    
    # Switch back to default
    print("Switching back to default theme...")
    theme_manager.set_theme("default")
    print(f"Primary background: {get_color('primary.main')}")
    print()
    
    # Test color groups
    print("Button colors group:")
    button_colors = theme_manager.get_colors("buttons")
    for key, value in button_colors.items():
        print(f"  {key}: {value}")
    print()
    
    # Test fallback colors
    print("Testing fallback for non-existent color:")
    fallback_color = get_color("non.existent.color", "#FF0000")
    print(f"  Result: {fallback_color}")
    print()
    
    print("=== Demo Complete ===")


if __name__ == "__main__":
    demonstrate_theme_system()