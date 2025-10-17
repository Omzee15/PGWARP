#!/usr/bin/env python3
"""
Test script to demonstrate the complete theme and configuration system
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.config_manager import config_manager
from utils.theme_manager import theme_manager


def demo_config_system():
    """Demonstrate the configuration system functionality"""
    print("🎨 PgWarp Theme & Configuration System Demo")
    print("=" * 60)
    
    # Show current configuration
    print("\n📋 Current Configuration:")
    print(f"  • Default Theme: {config_manager.get('default_theme')}")
    print(f"  • Theme Mode: {config_manager.get('theme_mode')}")
    print(f"  • Window Size: {config_manager.get('window_size')}")
    print(f"  • Database Host: {config_manager.get('default_host')}")
    print(f"  • Max Result Rows: {config_manager.get('max_result_rows')}")
    
    # Show available themes
    print(f"\n🎨 Available Themes ({len(theme_manager.list_available_themes())}):")
    theme_options = config_manager.get_theme_options()
    for i, (file_name, display_name) in enumerate(theme_options.items(), 1):
        current_marker = " ← Current" if file_name == config_manager.get('default_theme') else ""
        print(f"  {i}. {display_name} ({file_name}){current_marker}")
    
    # Test theme switching
    print(f"\n🔄 Testing Theme Changes:")
    original_theme = config_manager.get('default_theme')
    
    # Switch to a different theme
    new_theme = 'default' if original_theme != 'default' else 'dark'
    print(f"  Switching from '{original_theme}' to '{new_theme}'...")
    
    config_manager.set('default_theme', new_theme)
    config_manager.save_config()
    
    # Apply the new theme
    theme_manager.set_theme(new_theme)
    print(f"  ✓ Theme switched to: {theme_manager.get_theme_name()}")
    
    # Show theme colors
    print(f"\n🎨 Current Theme Colors:")
    color_samples = [
        'background.main',
        'text.primary',
        'buttons.primary_bg',
        'accent.main',
        'editor.background'
    ]
    
    for color_path in color_samples:
        color = theme_manager.get_color(color_path)
        print(f"  • {color_path}: {color}")
    
    # Restore original theme
    print(f"\n🔄 Restoring original theme: {original_theme}")
    config_manager.set('default_theme', original_theme)
    config_manager.save_config()
    theme_manager.set_theme(original_theme)
    
    print(f"\n💾 Configuration file location: {config_manager.config_file}")
    
    print(f"\n✅ Demo completed successfully!")
    print("\nTo test in the application:")
    print("1. Run 'python3 main.py' to start PgWarp")
    print("2. Go to the 'Config' tab")
    print("3. Change the 'Default Theme' setting")
    print("4. Click 'Apply' to see the change immediately")
    print("5. Restart the app to see it remembers your choice")


if __name__ == "__main__":
    demo_config_system()