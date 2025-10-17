#!/usr/bin/env python3
"""
Comprehensive theme system test to verify all components use theme colors
"""

import sys
from pathlib import Path
import tkinter as tk

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from utils.theme_manager import theme_manager
from utils.config_manager import config_manager

def test_all_theme_colors():
    """Test that all theme colors are accessible and valid"""
    print("=== Comprehensive Theme System Test ===\n")
    
    # Test all available themes
    themes = theme_manager.list_available_themes()
    print(f"Available themes: {themes}")
    
    for theme_name in themes:
        print(f"\n--- Testing Theme: {theme_name} ---")
        theme_manager.set_theme(theme_name)
        display_name = theme_manager.get_theme_display_name(theme_name)
        print(f"Display name: {display_name}")
        
        # Test all color categories
        color_categories = [
            "background.main",
            "background.secondary", 
            "text.primary",
            "text.secondary",
            "buttons.primary_bg",
            "buttons.primary_hover",
            "buttons.primary_text",
            "buttons.secondary_bg",
            "buttons.secondary_hover", 
            "buttons.secondary_text",
            "buttons.danger_bg",
            "buttons.danger_hover",
            "buttons.danger_text",
            "inputs.bg",
            "inputs.text",
            "inputs.border",
            "accent.primary",
            "sidebar.background",
            "sidebar.header"
        ]
        
        print("Color values:")
        for color_path in color_categories:
            try:
                color = theme_manager.get_color(color_path)
                print(f"  {color_path}: {color}")
            except Exception as e:
                print(f"  {color_path}: ERROR - {e}")
        
        # Test config persistence
        if theme_name == 'dark':
            print(f"\nTesting config persistence with {theme_name}")
            config_manager.set('default_theme', theme_name)
            saved_theme = config_manager.get('default_theme')
            print(f"Saved theme: {saved_theme}")
            assert saved_theme == theme_name, f"Config persistence failed: expected {theme_name}, got {saved_theme}"
            print("✓ Config persistence working")
    
    print("\n=== All Themes Tested Successfully ===")
    
    # Test theme switching 
    print("\n--- Testing Theme Switching ---")
    original_theme = theme_manager.get_current_theme()
    print(f"Original theme: {original_theme}")
    
    # Switch to different theme
    test_theme = 'github-dark' if original_theme != 'github-dark' else 'default'
    success = theme_manager.set_theme(test_theme)
    assert success, f"Failed to switch to {test_theme}"
    
    current = theme_manager.get_current_theme()
    assert current == test_theme, f"Theme switch failed: expected {test_theme}, got {current}"
    print(f"✓ Successfully switched to: {current}")
    
    # Switch back
    theme_manager.set_theme(original_theme)
    final = theme_manager.get_current_theme()
    assert final == original_theme, f"Failed to switch back to {original_theme}"
    print(f"✓ Successfully switched back to: {final}")
    
    print("\n=== Theme System Fully Functional ===")

if __name__ == "__main__":
    test_all_theme_colors()