#!/bin/bash

# VS Code Theme Extractor
# Extracts VS Code theme JSON files and analyzes their structure

VSCODE_EXT_DIR="$HOME/.vscode/extensions"
OUTPUT_DIR="./vscode_themes_analysis"

echo "=== VS Code Theme Extractor ==="
echo "Extension Directory: $VSCODE_EXT_DIR"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Counter for themes
theme_count=0

# Find all package.json files in extensions directory
for package_json in "$VSCODE_EXT_DIR"/*/package.json; do
    if [[ -f "$package_json" ]]; then
        # Check if this extension contributes themes
        if grep -q '"themes"' "$package_json"; then
            # Extract extension info
            ext_name=$(dirname "$package_json" | xargs basename)
            display_name=$(grep -o '"displayName"[[:space:]]*:[[:space:]]*"[^"]*"' "$package_json" | sed 's/"displayName"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')
            publisher=$(grep -o '"publisher"[[:space:]]*:[[:space:]]*"[^"]*"' "$package_json" | sed 's/"publisher"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')
            
            echo "📦 Processing: $display_name ($publisher)"
            
            # Create extension directory in output
            ext_output_dir="$OUTPUT_DIR/$publisher-$ext_name"
            mkdir -p "$ext_output_dir"
            
            # Copy package.json for reference
            cp "$package_json" "$ext_output_dir/"
            
            # Find and copy theme files
            themes_dir=$(dirname "$package_json")/themes
            if [[ -d "$themes_dir" ]]; then
                for theme_file in "$themes_dir"/*.json; do
                    if [[ -f "$theme_file" ]]; then
                        theme_name=$(basename "$theme_file" .json)
                        
                        # Copy theme file
                        cp "$theme_file" "$ext_output_dir/"
                        
                        # Try to extract theme label from package.json
                        theme_label=$(grep -A 3 -B 1 "\"path\".*$theme_name.json" "$package_json" | grep -o '"label"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"label"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')
                        
                        if [[ -n "$theme_label" ]]; then
                            echo "   ✓ Extracted: $theme_label ($theme_name.json)"
                        else
                            echo "   ✓ Extracted: $theme_name.json"
                        fi
                        ((theme_count++))
                    fi
                done
            fi
        fi
    fi
done

echo ""
echo "=== Analyzing Theme Structure ==="

# Analyze a few popular themes to understand structure
analyze_theme() {
    local theme_file="$1"
    local theme_name="$2"
    
    if [[ -f "$theme_file" ]]; then
        echo ""
        echo "--- $theme_name ---"
        echo "File: $theme_file"
        
        # Check if it has 'colors' section
        if grep -q '"colors"' "$theme_file"; then
            echo "✓ Has 'colors' section"
            
            # Show some key color properties
            echo "Key colors found:"
            grep -o '"editor\.background"[[:space:]]*:[[:space:]]*"[^"]*"' "$theme_file" | head -1
            grep -o '"editor\.foreground"[[:space:]]*:[[:space:]]*"[^"]*"' "$theme_file" | head -1
            grep -o '"sideBar\.background"[[:space:]]*:[[:space:]]*"[^"]*"' "$theme_file" | head -1
            grep -o '"activityBar\.background"[[:space:]]*:[[:space:]]*"[^"]*"' "$theme_file" | head -1
        fi
        
        # Check if it has 'tokenColors' section
        if grep -q '"tokenColors"' "$theme_file"; then
            echo "✓ Has 'tokenColors' section (syntax highlighting)"
        fi
        
        # Get file size
        file_size=$(wc -c < "$theme_file")
        echo "File size: $file_size bytes"
    fi
}

# Find and analyze some popular themes
echo "Analyzing popular themes..."

# Look for Dark+ theme (default VS Code dark theme)
find "$OUTPUT_DIR" -name "*dark*plus*.json" -o -name "*default*dark*.json" | head -1 | while read theme_file; do
    analyze_theme "$theme_file" "Dark+ (default dark)"
done

# Look for Light+ theme (default VS Code light theme)
find "$OUTPUT_DIR" -name "*light*plus*.json" -o -name "*default*light*.json" | head -1 | while read theme_file; do
    analyze_theme "$theme_file" "Light+ (default light)"
done

# Look for Monokai theme
find "$OUTPUT_DIR" -name "*monokai*.json" | head -1 | while read theme_file; do
    analyze_theme "$theme_file" "Monokai"
done

# Look for Dracula theme
find "$OUTPUT_DIR" -name "*dracula*.json" | head -1 | while read theme_file; do
    analyze_theme "$theme_file" "Dracula"
done

echo ""
echo "=== Summary ==="
echo "Total themes extracted: $theme_count"
echo "Output directory: $OUTPUT_DIR"
echo ""
echo "To analyze theme structure:"
echo "find $OUTPUT_DIR -name '*.json' -exec jq '.colors | keys' {} \;"
echo ""
echo "To see all editor colors in a theme:"
echo "find $OUTPUT_DIR -name '*.json' -exec jq '.colors | to_entries | map(select(.key | startswith(\"editor\")))' {} \;"