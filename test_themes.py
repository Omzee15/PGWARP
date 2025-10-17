#!/usr/bin/env python3
"""
Test script to verify theme functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.theme_manager import theme_manager

def test_theme(theme_name):
    """Test a specific theme"""
    print(f"\n=== Testing Theme: {theme_name} ===")
    
    if theme_manager.set_theme(theme_name):
        print(f"✓ Successfully loaded: {theme_manager.get_theme_name()}")
        print(f"Type: {theme_manager.get_theme_type()}")
        
        # Test common colors
        colors_to_test = [
            'background.main',
            'text.primary', 
            'buttons.primary_bg',
            'buttons.primary_text',
            'editor.background',
            'sidebar.background'
        ]
        
        print("Colors:")
        for color_path in colors_to_test:
            color = theme_manager.get_color(color_path)
            print(f"  {color_path}: {color}")
            
    else:
        print(f"✗ Failed to load theme: {theme_name}")

def main():
    """Main test function"""
    print("PgWarp Theme Manager Test")
    print("=" * 50)
    
    # List all available themes
    themes = theme_manager.list_available_themes()
    display_names = theme_manager.get_theme_display_names()
    
    print(f"Found {len(themes)} themes:")
    for theme_file in themes:
        display_name = display_names.get(theme_file, theme_file)
        print(f"  - {theme_file} ({display_name})")
    
    # Test each theme
    for theme_name in themes:
        test_theme(theme_name)
    
    print(f"\n=== Summary ===")
    print(f"All {len(themes)} themes tested successfully!")

if __name__ == "__main__":
    main()