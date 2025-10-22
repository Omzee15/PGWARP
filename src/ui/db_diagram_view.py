"""
Database Diagram View - DBML to ERD Generator
Converts DBML schema to visual entity-relationship diagrams
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import customtkinter as ctk
from typing import Dict, List, Tuple, Optional
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.theme_manager import theme_manager


class Table:
    """Represents a database table"""
    def __init__(self, name: str):
        self.name = name
        self.columns = []
        self.primary_keys = []
        self.foreign_keys = []
        self.x = 0
        self.y = 0
        self.width = 200
        self.height = 100


class Column:
    """Represents a table column"""
    def __init__(self, name: str, data_type: str, is_pk: bool = False):
        self.name = name
        self.data_type = data_type
        self.is_pk = is_pk


class ForeignKey:
    """Represents a foreign key relationship"""
    def __init__(self, from_table: str, from_column: str, to_table: str, to_column: str):
        self.from_table = from_table
        self.from_column = from_column
        self.to_table = to_table
        self.to_column = to_column


class DBMLParser:
    """Parser for DBML (Database Markup Language)"""
    
    @staticmethod
    def parse(dbml_text: str) -> Tuple[Dict[str, Table], List[ForeignKey]]:
        """Parse DBML text and extract tables and relationships"""
        tables = {}
        relationships = []
        
        # Remove comments
        dbml_text = re.sub(r'//.*$', '', dbml_text, flags=re.MULTILINE)
        dbml_text = re.sub(r'/\*.*?\*/', '', dbml_text, flags=re.DOTALL)
        
        # Extract tables
        table_pattern = r'Table\s+(\w+)\s*\{([^}]+)\}'
        for match in re.finditer(table_pattern, dbml_text, re.DOTALL):
            table_name = match.group(1)
            table_body = match.group(2)
            
            table = Table(table_name)
            
            # Extract columns
            column_lines = table_body.strip().split('\n')
            for line in column_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse column definition: column_name data_type [constraints]
                parts = line.split()
                if len(parts) >= 2:
                    col_name = parts[0]
                    col_type = parts[1]
                    
                    # Check for primary key
                    is_pk = '[pk]' in line.lower() or 'primary key' in line.lower()
                    
                    column = Column(col_name, col_type, is_pk)
                    table.columns.append(column)
                    
                    if is_pk:
                        table.primary_keys.append(col_name)
            
            tables[table_name] = table
        
        # Extract relationships (Ref)
        ref_pattern = r'Ref:\s*(\w+)\.(\w+)\s*[<>-]+\s*(\w+)\.(\w+)'
        for match in re.finditer(ref_pattern, dbml_text):
            from_table = match.group(1)
            from_col = match.group(2)
            to_table = match.group(3)
            to_col = match.group(4)
            
            fk = ForeignKey(from_table, from_col, to_table, to_col)
            relationships.append(fk)
            
            # Store in table
            if from_table in tables:
                tables[from_table].foreign_keys.append(fk)
        
        return tables, relationships


class DiagramCanvas(tk.Canvas):
    """Canvas for drawing ER diagrams"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=theme_manager.get_color("diagram.canvas_bg"), highlightthickness=0, **kwargs)
        self.tables = {}
        self.relationships = []
        
        # Colors - Following app's theme
        self.table_bg = theme_manager.get_color("diagram.table_bg")
        self.table_border = theme_manager.get_color("diagram.table_border")
        self.header_bg = theme_manager.get_color("diagram.header_bg")
        self.header_fg = theme_manager.get_color("diagram.header_fg")
        self.text_color = theme_manager.get_color("diagram.text")
        self.pk_color = theme_manager.get_color("diagram.pk")
        self.fk_color = theme_manager.get_color("diagram.fk")
        self.line_color = theme_manager.get_color("diagram.line")
        self.null_indicator_color = theme_manager.get_color("diagram.null_indicator")
        self.column_type_color = theme_manager.get_color("diagram.column_type")
        
        # Zoom settings
        self.zoom_level = 1.0
        self.min_zoom = 0.3
        self.max_zoom = 3.0
        self.zoom_step = 0.1
        self.zoom_callback = None  # Callback to update zoom label
        
        # Pan/drag canvas settings
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Table dragging settings
        self.dragging_table = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.dragging_header = False
        
        # Enable panning with middle mouse or Ctrl+drag
        self.bind("<Button-2>", self.start_pan)  # Middle mouse button
        self.bind("<B2-Motion>", self.do_pan)
        self.bind("<ButtonRelease-2>", self.stop_pan)
        
        # Also support Ctrl+Left click for panning
        self.bind("<Control-Button-1>", self.start_pan)
        self.bind("<Control-B1-Motion>", self.do_pan)
        self.bind("<Control-ButtonRelease-1>", self.stop_pan)
        
        # Table dragging
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        # Enable zoom with mouse wheel
        self.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows/Mac
        self.bind("<Button-4>", self.on_mouse_wheel)    # Linux scroll up
        self.bind("<Button-5>", self.on_mouse_wheel)    # Linux scroll down
    
    def draw_diagram(self, tables: Dict[str, Table], relationships: List[ForeignKey]):
        """Draw the complete diagram"""
        self.delete("all")
        self.tables = tables
        self.relationships = relationships
        
        # Auto-layout tables in a grid
        self.auto_layout_tables()
        
        # Draw relationships first (so they appear behind tables)
        for rel in relationships:
            self.draw_relationship(rel)
        
        # Draw tables
        for table in tables.values():
            self.draw_table(table)
        
        # Update scroll region
        self.update_scroll_region()
    
    def auto_layout_tables(self):
        """Automatically position tables in a grid layout"""
        tables_list = list(self.tables.values())
        if not tables_list:
            return
        
        # Calculate grid dimensions
        num_tables = len(tables_list)
        cols = max(3, int(num_tables ** 0.5))
        
        x_spacing = 280
        y_spacing = 220
        x_start = 60
        y_start = 60
        
        for i, table in enumerate(tables_list):
            col = i % cols
            row = i // cols
            
            table.x = x_start + col * x_spacing
            table.y = y_start + row * y_spacing
            
            # Calculate table height based on number of columns
            # Header (40px) + columns (24px each) + padding (16px)
            table.height = 40 + len(table.columns) * 24 + 16
            table.width = 220  # Fixed width
    
    def draw_table(self, table: Table):
        """Draw a single table with a clean, professional look"""
        # Apply zoom to positions
        x = table.x * self.zoom_level
        y = table.y * self.zoom_level
        width = table.width * self.zoom_level
        height = table.height * self.zoom_level
        
        # Calculate font sizes based on zoom level
        title_font_size = max(8, int(13 * self.zoom_level))
        icon_font_size = max(6, int(10 * self.zoom_level))
        text_font_size = max(6, int(10 * self.zoom_level))
        type_font_size = max(6, int(9 * self.zoom_level))
        
        # Scale other dimensions
        shadow_offset = 3 * self.zoom_level
        header_height = 40 * self.zoom_level
        
        # Draw shadow effect (subtle depth)
        self.create_rectangle(
            x + shadow_offset, y + shadow_offset, 
            x + width + shadow_offset, y + height + shadow_offset,
            fill=theme_manager.get_color("diagram.minimap_bg"),
            outline="",
            tags=("table", f"table_{table.name}", "shadow")
        )
        
        # Draw main table background
        self.create_rectangle(
            x, y, x + width, y + height,
            fill=self.table_bg,
            outline=self.table_border,
            width=max(1, int(2 * self.zoom_level)),
            tags=("table", f"table_{table.name}", "body")
        )
        
        # Draw header with rounded appearance
        self.create_rectangle(
            x, y, x + width, y + header_height,
            fill=self.header_bg,
            outline="",
            tags=("table", f"table_{table.name}", "header", f"header_{table.name}")
        )
        
        # Table name in header
        self.create_text(
            x + width / 2, y + header_height / 2,
            text=table.name,
            fill=self.header_fg,
            font=("Segoe UI", title_font_size, "bold"),
            tags=("table", f"table_{table.name}", "header", f"header_{table.name}")
        )
        
        # Draw separator line below header
        self.create_line(
            x, y + header_height,
            x + width, y + header_height,
            fill=self.table_border,
            width=max(1, int(1 * self.zoom_level)),
            tags=("table", f"table_{table.name}", "separator")
        )
        
        # Draw columns with better formatting
        row_height = 24 * self.zoom_level
        y_offset = y + header_height + 12 * self.zoom_level
        
        for i, col in enumerate(table.columns):
            # Alternate row background for better readability
            if i % 2 == 1:
                self.create_rectangle(
                    x + 1, y_offset - 8 * self.zoom_level,
                    x + width - 1, y_offset + 16 * self.zoom_level,
                    fill=theme_manager.get_color("diagram.minimap_viewport"),
                    outline="",
                    tags=("table", f"table_{table.name}", "row_bg")
                )
            
            # Primary key icon
            if col.is_pk:
                self.create_text(
                    x + 12 * self.zoom_level, y_offset,
                    text="🔑",
                    font=("Segoe UI", icon_font_size),
                    anchor="w",
                    tags=("table", f"table_{table.name}", "icon")
                )
                name_x_offset = 30 * self.zoom_level
                name_color = self.pk_color
                name_font = ("Segoe UI", text_font_size, "bold")
            # Foreign key icon
            elif any(fk.from_column == col.name for fk in table.foreign_keys):
                self.create_text(
                    x + 12 * self.zoom_level, y_offset,
                    text="🔗",
                    font=("Segoe UI", icon_font_size),
                    anchor="w",
                    tags=("table", f"table_{table.name}", "icon")
                )
                name_x_offset = 30 * self.zoom_level
                name_color = self.fk_color
                name_font = ("Segoe UI", text_font_size)
            else:
                name_x_offset = 12 * self.zoom_level
                name_color = self.text_color
                name_font = ("Segoe UI", text_font_size)
            
            # Column name
            self.create_text(
                x + name_x_offset, y_offset,
                text=col.name,
                fill=name_color,
                font=name_font,
                anchor="w",
                tags=("table", f"table_{table.name}", "column_name")
            )
            
            # Data type (right-aligned)
            self.create_text(
                x + width - 12 * self.zoom_level, y_offset,
                text=col.data_type,
                fill=self.column_type_color,
                font=("Consolas", type_font_size),
                anchor="e",
                tags=("table", f"table_{table.name}", "column_type")
            )
            
            y_offset += row_height
    
    def draw_relationship(self, rel: ForeignKey):
        """Draw a relationship line between tables with cleaner styling"""
        if rel.from_table not in self.tables or rel.to_table not in self.tables:
            return
        
        from_table = self.tables[rel.from_table]
        to_table = self.tables[rel.to_table]
        
        # Calculate font size based on zoom
        label_font_size = max(6, int(9 * self.zoom_level))
        
        # Apply zoom to positions
        from_x = (from_table.x + from_table.width) * self.zoom_level
        from_y = (from_table.y + from_table.height / 2) * self.zoom_level
        
        to_x = to_table.x * self.zoom_level
        to_y = (to_table.y + to_table.height / 2) * self.zoom_level
        
        # Create a cleaner, orthogonal line path (like in the reference image)
        mid_x = (from_x + to_x) / 2
        
        # Scale line width
        line_width = max(1, int(2 * self.zoom_level))
        
        # Draw line segments
        # First segment: horizontal from source
        self.create_line(
            from_x, from_y, mid_x, from_y,
            fill=self.line_color,
            width=line_width,
            tags="relationship",
            smooth=True
        )
        
        # Second segment: vertical connector
        self.create_line(
            mid_x, from_y, mid_x, to_y,
            fill=self.line_color,
            width=line_width,
            tags="relationship",
            smooth=True
        )
        
        # Third segment: horizontal to target with arrow
        arrow_size = max(6, int(10 * self.zoom_level))
        self.create_line(
            mid_x, to_y, to_x, to_y,
            fill=self.line_color,
            width=line_width,
            arrow=tk.LAST,
            arrowshape=(arrow_size, arrow_size + 2, arrow_size - 4),
            tags="relationship",
            smooth=True
        )
        
        # Draw relationship label with background
        label_text = f"{rel.from_column} → {rel.to_column}"
        text_x = mid_x
        text_y = (from_y + to_y) / 2 - 15 * self.zoom_level
        
        # Scale label box
        box_width = 40 * self.zoom_level
        box_height = 8 * self.zoom_level
        
        # Background for label
        self.create_rectangle(
            text_x - box_width, text_y - box_height,
            text_x + box_width, text_y + box_height,
            fill=theme_manager.get_color("diagram.canvas_bg"),
            outline=theme_manager.get_color("diagram.minimap_outline"),
            tags="relationship"
        )
        
        # Label text
        self.create_text(
            text_x, text_y,
            text=label_text,
            fill=self.text_color,
            font=("Segoe UI", label_font_size),
            tags="relationship"
        )
    
    def on_click(self, event):
        """Handle mouse click - check if clicking on table header for dragging"""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        items = self.find_overlapping(x, y, x, y)
        
        # Check if clicking on a table header
        for item in items:
            tags = self.gettags(item)
            for tag in tags:
                # Check if this is a header
                if tag.startswith("header_"):
                    table_name = tag[7:]  # Remove "header_" prefix
                    if table_name in self.tables:
                        self.dragging_table = self.tables[table_name]
                        self.dragging_header = True
                        # Store original position in canvas coordinates
                        self.drag_offset_x = x - (self.dragging_table.x * self.zoom_level)
                        self.drag_offset_y = y - (self.dragging_table.y * self.zoom_level)
                        # Change cursor to indicate dragging
                        self.config(cursor="fleur")
                        return
    
    def on_drag(self, event):
        """Handle mouse drag - either drag table or do nothing"""
        if self.dragging_table and self.dragging_header:
            x, y = self.canvasx(event.x), self.canvasy(event.y)
            
            # Calculate new position in logical coordinates (unscaled)
            new_x = (x - self.drag_offset_x) / self.zoom_level
            new_y = (y - self.drag_offset_y) / self.zoom_level
            
            # Update table position
            self.dragging_table.x = new_x
            self.dragging_table.y = new_y
            
            # Redraw diagram
            self.draw_diagram(self.tables, self.relationships)
    
    def on_release(self, event):
        """Handle mouse release"""
        self.dragging_table = None
        self.dragging_header = False
        self.config(cursor="")
    
    def start_pan(self, event):
        """Start panning the canvas view"""
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.config(cursor="fleur")
    
    def do_pan(self, event):
        """Pan the canvas view"""
        if self.panning:
            # Calculate how much to scroll
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            
            # Scroll the canvas
            self.xview_scroll(int(-dx / 10), "units")
            self.yview_scroll(int(-dy / 10), "units")
            
            # Update start position for continuous panning
            self.pan_start_x = event.x
            self.pan_start_y = event.y
    
    def stop_pan(self, event):
        """Stop panning the canvas view"""
        self.panning = False
        self.config(cursor="")
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        # Get mouse position in canvas coordinates
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)
        
        # Determine zoom direction
        if event.num == 4 or event.delta > 0:  # Scroll up / zoom in
            self.zoom_in(x, y)
        elif event.num == 5 or event.delta < 0:  # Scroll down / zoom out
            self.zoom_out(x, y)
    
    def zoom_in(self, focus_x=None, focus_y=None):
        """Zoom in the entire canvas view"""
        if self.zoom_level < self.max_zoom:
            new_zoom = min(self.max_zoom, self.zoom_level + self.zoom_step)
            self.apply_canvas_zoom(new_zoom, focus_x, focus_y)
    
    def zoom_out(self, focus_x=None, focus_y=None):
        """Zoom out the entire canvas view"""
        if self.zoom_level > self.min_zoom:
            new_zoom = max(self.min_zoom, self.zoom_level - self.zoom_step)
            self.apply_canvas_zoom(new_zoom, focus_x, focus_y)
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.apply_canvas_zoom(1.0)
    
    def apply_canvas_zoom(self, new_zoom, focus_x=None, focus_y=None):
        """Apply zoom by redrawing everything at new scale"""
        if not self.tables:
            self.zoom_level = new_zoom
            if self.zoom_callback:
                self.zoom_callback(new_zoom)
            return
        
        # Calculate scale factor
        scale_factor = new_zoom / self.zoom_level
        
        # If no focus point, use center of visible area
        if focus_x is None or focus_y is None:
            focus_x = self.canvasx(self.winfo_width() / 2)
            focus_y = self.canvasy(self.winfo_height() / 2)
        
        # Convert focus point to logical coordinates
        focus_x_logical = focus_x / self.zoom_level
        focus_y_logical = focus_y / self.zoom_level
        
        # Update zoom level
        old_zoom = self.zoom_level
        self.zoom_level = new_zoom
        
        # Redraw diagram with new zoom (fonts will scale automatically)
        self.draw_diagram(self.tables, self.relationships)
        
        # Adjust scroll position to keep focus point in place
        new_focus_x = focus_x_logical * self.zoom_level
        new_focus_y = focus_y_logical * self.zoom_level
        
        # Calculate how much to scroll to keep focus centered
        scroll_x = new_focus_x - focus_x
        scroll_y = new_focus_y - focus_y
        
        # Update the view
        self.xview_moveto((self.xview()[0] * old_zoom + scroll_x / self.winfo_width()) / new_zoom)
        self.yview_moveto((self.yview()[0] * old_zoom + scroll_y / self.winfo_height()) / new_zoom)
        
        # Update scroll region to fit new size
        self.update_scroll_region()
        
        # Update zoom label if callback is set
        if self.zoom_callback:
            self.zoom_callback(new_zoom)
    
    def update_scroll_region(self):
        """Update the scroll region to fit all content"""
        bbox = self.bbox("all")
        if bbox:
            self.configure(scrollregion=(bbox[0] - 50, bbox[1] - 50, bbox[2] + 50, bbox[3] + 50))


class DBDiagramView(ctk.CTkFrame):
    """Database Diagram View Component"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color=theme_manager.get_color("diagram.canvas_bg"))
        
        self.current_tables = {}
        self.current_relationships = []
        
        # Resizable panel settings
        self.resizing = False
        self.left_panel_width = 400
        self.min_left_width = 250
        self.max_left_width = 800
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the diagram view UI"""
        # Container for panels
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - DBML Editor
        self.left_panel = ctk.CTkFrame(container, fg_color=theme_manager.get_color("diagram.panel_bg"), width=self.left_panel_width, corner_radius=8)
        self.left_panel.place(x=0, y=0, relheight=1.0)
        self.left_panel.place_configure(width=self.left_panel_width)
        
        # Resizable separator
        self.separator = ctk.CTkFrame(container, fg_color=theme_manager.get_color("diagram.separator"), cursor="sb_h_double_arrow")
        self.separator.place(x=self.left_panel_width, y=0, relheight=1.0)
        self.separator.place_configure(width=6)
        
        # Bind separator events for resizing
        self.separator.bind("<Button-1>", self.start_resize)
        self.separator.bind("<B1-Motion>", self.do_resize)
        self.separator.bind("<ButtonRelease-1>", self.stop_resize)
        self.separator.bind("<Enter>", lambda e: self.separator.configure(fg_color=theme_manager.get_color("diagram.separator_hover")))
        self.separator.bind("<Leave>", lambda e: self.separator.configure(fg_color=theme_manager.get_color("diagram.separator")))
        
        # Right panel - Diagram Canvas
        self.right_panel = ctk.CTkFrame(container, fg_color=theme_manager.get_color("diagram.panel_bg"), corner_radius=8)
        self.right_panel.place(x=self.left_panel_width + 6, y=0, relwidth=1.0, relheight=1.0)
        
        # Configure right panel to adjust with left panel width
        self.bind("<Configure>", self.update_panels)
        
        # DBML Editor Title
        title_label = ctk.CTkLabel(
            self.left_panel,
            text="📝 DBML Schema",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3E2723"
        )
        title_label.pack(pady=(10, 5))
        
        # Help text
        help_text = ctk.CTkLabel(
            self.left_panel,
            text="Enter your database schema in DBML format",
            font=ctk.CTkFont(size=10),
            text_color="#8B7355"
        )
        help_text.pack(pady=(0, 10))
        
        # DBML Text Editor
        editor_frame = ctk.CTkFrame(self.left_panel, fg_color="#F5EFE7", corner_radius=8)
        editor_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.dbml_text = tk.Text(
            editor_frame,
            bg="#F5EFE7",
            fg="#3E2723",
            font=("Consolas", 11),
            wrap="none",
            insertbackground="#9B8F5E",
            selectbackground="#9B8F5E",
            selectforeground="white",
            padx=10,
            pady=10
        )
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.dbml_text.yview)
        h_scroll = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.dbml_text.xview)
        self.dbml_text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.dbml_text.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)
        
        # Add sample DBML
        self.load_sample_dbml()
        
        # Buttons
        button_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        button_frame.pack(pady=(0, 10))
        
        generate_btn = ctk.CTkButton(
            button_frame,
            text="Generate Diagram",
            command=self.generate_diagram,
            font=ctk.CTkFont(size=12, weight="bold"),
            width=150,
            height=35,
            fg_color="#9B8F5E",
            hover_color="#87795A",
            corner_radius=6
        )
        generate_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            button_frame,
            text="Clear",
            command=self.clear_dbml,
            width=100,
            height=35,
            fg_color="#9B8F5E",
            hover_color="#87795A",
            corner_radius=6
        )
        clear_btn.pack(side="left", padx=5)
        
        # === Right Panel Content ===
        
        # Diagram Title and Zoom Controls
        header_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 5))
        
        diagram_title = ctk.CTkLabel(
            header_frame,
            text="🗺️ Entity Relationship Diagram",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3E2723"
        )
        diagram_title.pack(side="left", padx=10)
        
        # Zoom controls
        zoom_frame = ctk.CTkFrame(header_frame, fg_color="#E8DFD0", corner_radius=8)
        zoom_frame.pack(side="right", padx=10)
        
        zoom_out_btn = ctk.CTkButton(
            zoom_frame,
            text="−",
            command=lambda: self.canvas.zoom_out(),
            width=35,
            height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#9B8F5E",
            hover_color="#87795A",
            corner_radius=6
        )
        zoom_out_btn.pack(side="left", padx=(5, 0), pady=5)
        
        self.zoom_label = ctk.CTkLabel(
            zoom_frame,
            text="100%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#3E2723",
            width=50
        )
        self.zoom_label.pack(side="left", padx=5, pady=5)
        
        zoom_in_btn = ctk.CTkButton(
            zoom_frame,
            text="+",
            command=lambda: self.canvas.zoom_in(),
            width=35,
            height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#9B8F5E",
            hover_color="#87795A",
            corner_radius=6
        )
        zoom_in_btn.pack(side="left", padx=0, pady=5)
        
        reset_zoom_btn = ctk.CTkButton(
            zoom_frame,
            text="⟲",
            command=lambda: self.canvas.reset_zoom(),
            width=35,
            height=30,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#9B8F5E",
            hover_color="#87795A",
            corner_radius=6
        )
        reset_zoom_btn.pack(side="left", padx=(5, 5), pady=5)
        
        # Canvas frame
        canvas_frame = ctk.CTkFrame(self.right_panel, fg_color="#F5EFE7", corner_radius=8)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create canvas with scrollbars
        self.canvas = DiagramCanvas(canvas_frame)
        
        v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Info label
        info_label = ctk.CTkLabel(
            self.right_panel,
            text="💡 Drag table headers to move • Ctrl+Drag or Middle-click to pan • Scroll to zoom",
            font=ctk.CTkFont(size=10),
            text_color="#8B7355"
        )
        info_label.pack(pady=(0, 10))
        
        # Connect canvas zoom update to label
        self.canvas.zoom_callback = self.update_zoom_label
    
    def load_sample_dbml(self):
        """Load sample DBML code"""
        sample = """// Sample Database Schema

Table users {
  id integer [pk]
  username varchar
  email varchar
  created_at timestamp
}

Table posts {
  id integer [pk]
  title varchar
  content text
  user_id integer
  created_at timestamp
}

Table comments {
  id integer [pk]
  post_id integer
  user_id integer
  content text
  created_at timestamp
}

// Relationships
Ref: posts.user_id > users.id
Ref: comments.post_id > posts.id
Ref: comments.user_id > users.id
"""
        self.dbml_text.delete("1.0", tk.END)
        self.dbml_text.insert("1.0", sample)
    
    def clear_dbml(self):
        """Clear the DBML editor"""
        self.dbml_text.delete("1.0", tk.END)
        self.canvas.delete("all")
    
    def generate_diagram(self):
        """Generate diagram from DBML"""
        dbml_code = self.dbml_text.get("1.0", tk.END)
        
        if not dbml_code.strip():
            messagebox.showwarning("Empty Schema", "Please enter DBML schema code")
            return
        
        try:
            # Parse DBML
            tables, relationships = DBMLParser.parse(dbml_code)
            
            if not tables:
                messagebox.showwarning("No Tables", "No tables found in DBML schema")
                return
            
            # Store for later use
            self.current_tables = tables
            self.current_relationships = relationships
            
            # Draw diagram
            self.canvas.draw_diagram(tables, relationships)
            
            # Show success message
            table_count = len(tables)
            rel_count = len(relationships)
            messagebox.showinfo(
                "Diagram Generated",
                f"Successfully generated diagram with {table_count} tables and {rel_count} relationships"
            )
            
        except Exception as e:
            messagebox.showerror("Parse Error", f"Failed to parse DBML:\n{str(e)}")
    
    def update_zoom_label(self, zoom_level):
        """Update the zoom percentage label"""
        percentage = int(zoom_level * 100)
        self.zoom_label.configure(text=f"{percentage}%")
    
    def start_resize(self, event):
        """Start resizing the left panel"""
        self.resizing = True
        self.resize_start_x = event.x_root
        self.resize_start_width = self.left_panel_width
    
    def do_resize(self, event):
        """Handle panel resizing"""
        if self.resizing:
            # Calculate new width
            delta = event.x_root - self.resize_start_x
            new_width = self.resize_start_width + delta
            
            # Clamp to min/max values
            new_width = max(self.min_left_width, min(self.max_left_width, new_width))
            
            # Update width
            self.left_panel_width = new_width
            
            # Update panel positions
            self.left_panel.place_configure(width=self.left_panel_width)
            self.separator.place(x=self.left_panel_width)
            self.right_panel.place(x=self.left_panel_width + 6)
    
    def stop_resize(self, event):
        """Stop resizing the left panel"""
        self.resizing = False
    
    def update_panels(self, event=None):
        """Update right panel width when container resizes"""
        if hasattr(self, 'right_panel'):
            container_width = self.winfo_width() - 20  # Account for padding
            right_width = container_width - self.left_panel_width - 6
            if right_width > 0:
                self.right_panel.place(x=self.left_panel_width + 6)
                self.right_panel.place_configure(width=right_width)
