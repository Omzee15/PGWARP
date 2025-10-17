#!/bin/bash

# VS Code Themes Lister
# Lists all installed themes in VS Code extensions directory

VSCODE_EXT_DIR="$HOME/.vscode/extensions"

echo "=== VS Code Themes Installed ==="
echo "Extension Directory: $VSCODE_EXT_DIR"
echo ""

# Counter for themes
theme_count=0

# Find all package.json files in extensions directory
for package_json in "$VSCODE_EXT_DIR"/*/package.json; do
    if [[ -f "$package_json" ]]; then
        # Check if this extension contributes themes
        if grep -q '"themes"' "$package_json"; then
            # Extract extension name and display name
            ext_name=$(dirname "$package_json" | xargs basename)
            display_name=$(grep -o '"displayName"[[:space:]]*:[[:space:]]*"[^"]*"' "$package_json" | sed 's/"displayName"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')
            publisher=$(grep -o '"publisher"[[:space:]]*:[[:space:]]*"[^"]*"' "$package_json" | sed 's/"publisher"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')
            version=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$package_json" | sed 's/"version"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')
            
            echo "📦 Extension: $display_name"
            echo "   Publisher: $publisher"
            echo "   Version: $version"
            echo "   Folder: $ext_name"
            
            # Find and list theme files
            themes_dir=$(dirname "$package_json")/themes
            if [[ -d "$themes_dir" ]]; then
                echo "   Themes:"
                for theme_file in "$themes_dir"/*.json; do
                    if [[ -f "$theme_file" ]]; then
                        theme_name=$(basename "$theme_file" .json)
                        # Try to extract theme label from package.json
                        theme_label=$(grep -A 3 -B 1 "\"path\".*$theme_name.json" "$package_json" | grep -o '"label"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"label"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')
                        
                        if [[ -n "$theme_label" ]]; then
                            echo "     • $theme_label ($theme_name.json)"
                        else
                            echo "     • $theme_name.json"
                        fi
                        ((theme_count++))
                    fi
                done
            else
                echo "   Themes: No themes directory found"
            fi
            echo ""
        fi
    fi
done

echo "=== Summary ==="
echo "Total themes found: $theme_count"
echo ""
echo "To view a specific theme file:"
echo "cat ~/.vscode/extensions/EXTENSION_FOLDER/themes/THEME_FILE.json"