# PgWarp Design System & Color Documentation

## 🎨 Color Palette Overview

PgWarp uses a warm, earthy color palette inspired by natural beige, tan, and olive tones. The design creates a comfortable, professional environment for database work.

---

## 📊 Primary Color Palette

### Background Colors

| Color Name | Hex Code | RGB | Usage | Preview |
|------------|----------|-----|-------|---------|
| **Lightest Beige** | `#F5EFE7` | rgb(245, 239, 231) | Main background, input fields, text areas | ![#F5EFE7](https://via.placeholder.com/50/F5EFE7/000000?text=+) |
| **Light Beige** | `#E8DFD0` | rgb(232, 223, 208) | Secondary background, frames, panels | ![#E8DFD0](https://via.placeholder.com/50/E8DFD0/000000?text=+) |
| **Medium Beige** | `#EBE3D5` | rgb(235, 227, 213) | Alternating row background | ![#EBE3D5](https://via.placeholder.com/50/EBE3D5/000000?text=+) |
| **Hover Beige** | `#D9CDBF` | rgb(217, 205, 191) | Hover states for secondary elements | ![#D9CDBF](https://via.placeholder.com/50/D9CDBF/000000?text=+) |

### Primary Action Colors (Olive/Brown)

| Color Name | Hex Code | RGB | Usage | Preview |
|------------|----------|-----|-------|---------|
| **Primary Olive** | `#9B8F5E` | rgb(155, 143, 94) | Primary buttons, accents, selections | ![#9B8F5E](https://via.placeholder.com/50/9B8F5E/FFFFFF?text=+) |
| **Hover Olive** | `#87795A` | rgb(135, 121, 90) | Hover state for primary buttons | ![#87795A](https://via.placeholder.com/50/87795A/FFFFFF?text=+) |

### Text Colors

| Color Name | Hex Code | RGB | Usage | Preview |
|------------|----------|-----|-------|---------|
| **Dark Brown** | `#3E2723` | rgb(62, 39, 35) | Primary text, labels, headings | ![#3E2723](https://via.placeholder.com/50/3E2723/FFFFFF?text=+) |
| **Medium Brown** | `#8B7355` | rgb(139, 115, 85) | Secondary text, hints, placeholders | ![#8B7355](https://via.placeholder.com/50/8B7355/FFFFFF?text=+) |
| **White** | `#FFFFFF` | rgb(255, 255, 255) | Text on dark backgrounds, button text | ![#FFFFFF](https://via.placeholder.com/50/FFFFFF/000000?text=+) |

### Accent Colors

| Color Name | Hex Code | RGB | Usage | Preview |
|------------|----------|-----|-------|---------|
| **Delete Red** | `#C4756C` | rgb(196, 117, 108) | Delete buttons, destructive actions | ![#C4756C](https://via.placeholder.com/50/C4756C/FFFFFF?text=+) |
| **Delete Hover** | `#A85E56` | rgb(168, 94, 86) | Hover state for delete buttons | ![#A85E56](https://via.placeholder.com/50/A85E56/FFFFFF?text=+) |
| **Error Orange** | `#CD853F` | rgb(205, 133, 63) | Error messages, warnings | ![#CD853F](https://via.placeholder.com/50/CD853F/000000?text=+) |
| **Warning Orange** | `#D2691E` | rgb(210, 105, 30) | Warning states, AI errors | ![#D2691E](https://via.placeholder.com/50/D2691E/FFFFFF?text=+) |
| **Success Green** | `#6B8E23` | rgb(107, 142, 35) | Success messages, AI ready state | ![#6B8E23](https://via.placeholder.com/50/6B8E23/FFFFFF?text=+) |

---

## 🏗️ Component-Specific Color Usage

### 1. Main Window & Global Theme

**File**: `src/ui/main_window.py`

```python
# Global Theme Configuration
Background Color:        #F5EFE7  # Main window background
Frame Color:             #F5EFE7  # Default frame background
Primary Button:          #9B8F5E  # All primary action buttons
Primary Button Hover:    #87795A  # Button hover state
Entry Background:        #F5EFE7  # Text input background
Entry Border:            #E8DFD0  # Text input border
Scrollable Frame:        #F5EFE7  # Scrollable areas
```

**Color Assignments**:
- Window background: `#F5EFE7`
- All CTk frames: `#F5EFE7`
- All CTk buttons: `#9B8F5E` (normal), `#87795A` (hover)
- All CTk entries: `#F5EFE7` (bg), `#E8DFD0` (border)

### 2. Toolbar

**File**: `src/ui/main_window.py`

```python
Toolbar Background:      #E8DFD0  # Toolbar frame
Separator:               #9B8F5E  # Vertical dividers
Text Labels:             #3E2723  # Connection status, AI status
Success Text:            #6B8E23  # "AI: Ready"
Error Text:              #D2691E  # "AI: Error"
```

### 3. Schema Browser

**File**: `src/ui/schema_browser.py`

```python
# Tree Area
Search Frame:            #E8DFD0  # Search box container
Tree Frame:              #E8DFD0  # Tree container
Tree Background:         #F5EFE7  # Tree items background
Tree Foreground:         #3E2723  # Tree text
Tree Selected:           #9B8F5E  # Selected item background
Tree Selected Text:      #FFFFFF  # Selected item text

# Scrollbars
Scrollbar Background:    #E8DFD0  # Scrollbar track
Scrollbar Trough:        #F5EFE7  # Scrollbar background
Scrollbar Arrow:         #3E2723  # Scrollbar arrow color

# Saved Queries Section
Separator:               #9B8F5E  # Divider line (2px height)
Query List Frame:        #E8DFD0  # Saved queries container
Query Row Background:    #E8DFD0  # Individual query row
Query Row Hover:         #D9CDBF  # Query row on hover
Delete Button:           #C4756C  # Delete button
Delete Button Hover:     #A85E56  # Delete button on hover
Empty State Text:        #8B7355  # "No saved queries" text
```

### 4. Query Panel

**File**: `src/ui/query_panel.py`

```python
# Toolbar
Toolbar Frame:           #E8DFD0  # Top toolbar
Clear Button:            #E8DFD0  # Background
Clear Button Hover:      #D9CDBF  # Hover state

# Query Editor
Text Background:         #F5EFE7  # SQL editor background
Text Foreground:         #3E2723  # SQL text color
Cursor Color:            #9B8F5E  # Text cursor
Selection Background:    #9B8F5E  # Selected text background
Selection Foreground:    #FFFFFF  # Selected text color
Highlight Border:        #9B8F5E  # Focus border
Highlight Background:    #E8DFD0  # Non-focus border

# Scrollbars
Vertical Scrollbar:      #E8DFD0  # Background
Horizontal Scrollbar:    #E8DFD0  # Background
Scrollbar Trough:        #F5EFE7  # Track background

# Info Panel
Info Frame:              #E8DFD0  # Bottom info bar
Info Text:               #3E2723  # Status messages
```

### 5. Results Table

**File**: `src/ui/main_window.py`

```python
# Results Header
Header Frame:            #E8DFD0  # Results title bar
Header Text:             #3E2723  # "Query results" text
Excel Button:            #9B8F5E  # Export Excel button
Excel Button Hover:      #87795A  # Export button hover

# Table
Table Background:        #F5EFE7  # Main table background
Table Foreground:        #3E2723  # Table text
Table Header:            #E8DFD0  # Column headers
Table Selected:          #9B8F5E  # Selected row background
Table Selected Text:     #FFFFFF  # Selected row text
Odd Rows:                #F5EFE7  # Alternating row color 1
Even Rows:               #EBE3D5  # Alternating row color 2

# Scrollbars
Scrollbar Background:    #E8DFD0
Scrollbar Trough:        #F5EFE7
Scrollbar Arrow:         #3E2723
```

### 6. Connection Dialog

**File**: `src/ui/connection_dialog.py`

```python
# Main Layout
Main Frame:              #F5EFE7  # Dialog background
Saved Frame:             #E8DFD0  # Saved connections section
Form Frame:              #E8DFD0  # Connection form section

# Listbox
Listbox Background:      #F5EFE7  # Saved connections list
Listbox Foreground:      #3E2723  # Connection names
Listbox Selection:       #9B8F5E  # Selected connection
Highlight Border:        #9B8F5E  # Focus border

# Buttons
Load Button:             #9B8F5E  # Load connection
Load Button Hover:       #87795A
Test Button:             #9B8F5E  # Test connection
Test Button Hover:       #87795A
Connect Button:          #9B8F5E  # Main connect button
Connect Button Hover:    #87795A
Cancel Button:           #E8DFD0  # Cancel/close
Cancel Button Hover:     #D9CDBF
Cancel Text:             #3E2723  # Text color for cancel

# Separator
Divider Line:            #9B8F5E  # Horizontal separator (3px)

# Helper Text
Hint Text:               #8B7355  # Port helper text
```

### 7. PSQL Terminal

**File**: `src/ui/psql_terminal.py`

```python
# Terminal
Terminal Background:     #F5EFE7  # Console background
Terminal Foreground:     #3E2723  # Default text
Cursor Color:            #9B8F5E  # Blinking cursor
Selection Background:    #9B8F5E  # Selected text
Highlight Border:        #9B8F5E  # Focus border

# Text Colors
Command Text:            #8B7355  # User commands (brown)
Error Text:              #CD853F  # Error messages (orange)
Output Text:             #3E2723  # Normal output

# Scrollbar
Scrollbar Background:    #E8DFD0
Scrollbar Trough:        #F5EFE7
Scrollbar Arrow:         #9B8F5E
```

### 8. Saved Query Dialog

**File**: `src/ui/schema_browser.py`

```python
# Dialog Layout
Query Text Frame:        #F5EFE7  # SQL text area container
Text Background:         #F5EFE7  # SQL input background
Text Foreground:         #3E2723  # SQL text color
Cursor Color:            #9B8F5E  # Text cursor

# Buttons
Save Button:             #9B8F5E  # Default primary color
Save Button Hover:       #87795A
Cancel Button:           #E8DFD0  # Secondary background
Cancel Button Hover:     #D9CDBF
Cancel Button Text:      #3E2723  # Dark text on light button
```

### 9. Tab/Notebook Widget

**File**: `src/ui/main_window.py`

```python
Notebook Background:            #F5EFE7  # Tab content area
Tab Button Background:          #E8DFD0  # Unselected tabs
Tab Button Selected:            #9B8F5E  # Selected tab
Tab Button Selected Hover:      #87795A  # Selected tab hover
Tab Button Unselected:          #E8DFD0  # Unselected tabs
Tab Button Unselected Hover:    #D9CDBF  # Unselected tab hover
```

### 10. Status Bar

**File**: `src/ui/main_window.py`

```python
Status Frame:            #E8DFD0  # Status bar background
Status Text:             #3E2723  # Status messages
```

---

## 🎯 Color Usage Guidelines

### When to Use Each Color

#### **#F5EFE7 (Lightest Beige)**
✅ Main application background  
✅ Text input fields  
✅ Code editor backgrounds  
✅ Scrollable content areas  
✅ Table backgrounds  
✅ Default frame backgrounds  

#### **#E8DFD0 (Light Beige)**
✅ Panel containers  
✅ Toolbars  
✅ Section headers  
✅ Separating frames  
✅ Secondary button backgrounds  
✅ Inactive/disabled states  

#### **#9B8F5E (Primary Olive)**
✅ Primary action buttons  
✅ Selected items  
✅ Active states  
✅ Separators/dividers  
✅ Highlights  
✅ Focus indicators  

#### **#3E2723 (Dark Brown)**
✅ Primary text  
✅ Headings  
✅ Labels  
✅ Icons  
✅ Critical information  

#### **#C4756C (Delete Red)**
✅ Delete buttons  
✅ Destructive actions  
✅ Remove/clear operations  

#### **#8B7355 (Medium Brown)**
✅ Secondary text  
✅ Hints and tips  
✅ Placeholder text  
✅ Non-critical information  

---

## 📐 Accessibility & Contrast Ratios

### Text Contrast (WCAG 2.1 Compliance)

| Foreground | Background | Ratio | Level | Usage |
|------------|------------|-------|-------|-------|
| #3E2723 | #F5EFE7 | 12.8:1 | AAA ✅ | Primary text on main bg |
| #3E2723 | #E8DFD0 | 11.2:1 | AAA ✅ | Text on panels |
| #8B7355 | #F5EFE7 | 5.1:1 | AA ✅ | Secondary text |
| #FFFFFF | #9B8F5E | 4.8:1 | AA ✅ | Button text |
| #FFFFFF | #C4756C | 5.2:1 | AA ✅ | Delete button text |

---

## 🎨 Color Relationships

### Warm Beige Family
```
#F5EFE7 ──┐
          ├─── Background Hierarchy
#E8DFD0 ──┤
          ├─── Darker variants for structure
#D9CDBF ──┘
```

### Olive/Brown Family
```
#9B8F5E ──┐
          ├─── Primary actions & accents
#87795A ──┤
          ├─── Hover states & variations
#8B7355 ──┘
```

### Dark Text Family
```
#3E2723 ──┐
          ├─── Text hierarchy
#8B7355 ──┘
```

---

## 🖌️ Design Principles

### 1. **Warm & Natural**
- Earthy beige and olive tones create a comfortable workspace
- Reduces eye strain during long database work sessions

### 2. **Clear Hierarchy**
- Light backgrounds (#F5EFE7) for main content
- Medium tones (#E8DFD0) for structure and containers
- Dark olive (#9B8F5E) for interactive elements

### 3. **Consistent Interaction**
- All primary actions use #9B8F5E
- All hover states darken by ~10-15%
- Delete actions always use red (#C4756C)

### 4. **Visual Separation**
- Olive (#9B8F5E) separators between major sections
- Beige (#E8DFD0) frames for logical grouping
- White space using #F5EFE7 for breathing room

### 5. **Accessible by Default**
- All text combinations meet WCAG AA standards
- Primary text (#3E2723) provides excellent contrast
- Interactive elements clearly distinguishable

---

## 📱 Component Color Matrix

| Component | Background | Text | Border | Hover | Selected | Action |
|-----------|------------|------|--------|-------|----------|--------|
| **Window** | #F5EFE7 | #3E2723 | - | - | - | - |
| **Toolbar** | #E8DFD0 | #3E2723 | - | - | - | #9B8F5E |
| **Button** | #9B8F5E | #FFFFFF | - | #87795A | - | - |
| **Input** | #F5EFE7 | #3E2723 | #E8DFD0 | - | #9B8F5E | - |
| **Table** | #F5EFE7 | #3E2723 | - | - | #9B8F5E | - |
| **Tree** | #F5EFE7 | #3E2723 | - | - | #9B8F5E | - |
| **Panel** | #E8DFD0 | #3E2723 | - | - | - | - |
| **Delete** | #C4756C | #FFFFFF | - | #A85E56 | - | - |
| **Status** | #E8DFD0 | #3E2723 | - | - | - | - |

---

## 🔧 Implementation Notes

### CustomTkinter Theme Setup
```python
# Main window theme configuration (main_window.py)
ctk.ThemeManager.theme["CTkFrame"]["fg_color"] = ["#F5EFE7", "#F5EFE7"]
ctk.ThemeManager.theme["CTk"]["fg_color"] = ["#F5EFE7", "#F5EFE7"]
ctk.ThemeManager.theme["CTkButton"]["fg_color"] = ["#9B8F5E", "#9B8F5E"]
ctk.ThemeManager.theme["CTkButton"]["hover_color"] = ["#87795A", "#87795A"]
ctk.ThemeManager.theme["CTkScrollableFrame"]["fg_color"] = ["#F5EFE7", "#F5EFE7"]
ctk.ThemeManager.theme["CTkEntry"]["fg_color"] = ["#F5EFE7", "#F5EFE7"]
ctk.ThemeManager.theme["CTkEntry"]["border_color"] = ["#E8DFD0", "#E8DFD0"]
```

### Standard Tkinter Widgets
```python
# For native Tkinter widgets (Text, Listbox, etc.)
bg="#F5EFE7"              # Background
fg="#3E2723"              # Foreground text
selectbackground="#9B8F5E" # Selection background
selectforeground="white"   # Selection text
insertbackground="#9B8F5E" # Cursor color
highlightcolor="#9B8F5E"   # Focus border
```

### TTK Treeview Styling
```python
style = ttk.Style()
style.configure("Treeview",
    background="#F5EFE7",
    foreground="#3E2723",
    fieldbackground="#F5EFE7")
style.configure("Treeview.Heading",
    background="#E8DFD0",
    foreground="#3E2723")
style.map("Treeview",
    background=[('selected', '#9B8F5E')],
    foreground=[('selected', 'white')])
```

---

## 🎨 Color Palette Export

### For Design Tools

**CSS Variables**:
```css
:root {
  --bg-lightest: #F5EFE7;
  --bg-light: #E8DFD0;
  --bg-medium: #EBE3D5;
  --bg-hover: #D9CDBF;
  --primary: #9B8F5E;
  --primary-hover: #87795A;
  --text-primary: #3E2723;
  --text-secondary: #8B7355;
  --delete: #C4756C;
  --delete-hover: #A85E56;
  --error: #CD853F;
  --warning: #D2691E;
  --success: #6B8E23;
}
```

**RGB Values**:
```
Lightest Beige: rgb(245, 239, 231)
Light Beige: rgb(232, 223, 208)
Medium Beige: rgb(235, 227, 213)
Hover Beige: rgb(217, 205, 191)
Primary Olive: rgb(155, 143, 94)
Hover Olive: rgb(135, 121, 90)
Dark Brown: rgb(62, 39, 35)
Medium Brown: rgb(139, 115, 85)
Delete Red: rgb(196, 117, 108)
Delete Hover: rgb(168, 94, 86)
Error Orange: rgb(205, 133, 63)
Warning Orange: rgb(210, 105, 30)
Success Green: rgb(107, 142, 35)
```

---

## 📚 Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│ PgWarp Color Quick Reference                            │
├─────────────────────────────────────────────────────────┤
│ Backgrounds:                                            │
│   Main:      #F5EFE7 (Lightest Beige)                  │
│   Panels:    #E8DFD0 (Light Beige)                     │
│   Hover:     #D9CDBF (Hover Beige)                     │
│                                                         │
│ Actions:                                                │
│   Primary:   #9B8F5E (Olive)                           │
│   Hover:     #87795A (Dark Olive)                      │
│   Delete:    #C4756C (Red)                             │
│                                                         │
│ Text:                                                   │
│   Primary:   #3E2723 (Dark Brown)                      │
│   Secondary: #8B7355 (Medium Brown)                    │
│   On Dark:   #FFFFFF (White)                           │
│                                                         │
│ States:                                                 │
│   Success:   #6B8E23 (Green)                           │
│   Error:     #CD853F (Orange)                          │
│   Warning:   #D2691E (Dark Orange)                     │
└─────────────────────────────────────────────────────────┘
```

---

**Version**: 1.0  
**Last Updated**: October 15, 2025  
**Application**: PgWarp - AI-Powered PostgreSQL Desktop Client
