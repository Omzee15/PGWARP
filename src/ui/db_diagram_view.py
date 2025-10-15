"""
Database Diagram View - DBML to ERD Generator
Converts DBML schema to visual entity-relationship diagrams
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import customtkinter as ctk
from typing import Dict, List, Tuple, Optional
import re


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
        super().__init__(parent, bg="#F5EFE7", highlightthickness=0, **kwargs)
        self.tables = {}
        self.relationships = []
        
        # Colors
        self.table_bg = "#E8DFD0"
        self.table_border = "#9B8F5E"
        self.header_bg = "#9B8F5E"
        self.header_fg = "#FFFFFF"
        self.text_color = "#3E2723"
        self.pk_color = "#87795A"
        self.fk_color = "#C4756C"
        self.line_color = "#9B8F5E"
        
        # Enable dragging
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        self.dragging_table = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
    
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
        
        x_spacing = 250
        y_spacing = 200
        x_start = 50
        y_start = 50
        
        for i, table in enumerate(tables_list):
            col = i % cols
            row = i // cols
            
            table.x = x_start + col * x_spacing
            table.y = y_start + row * y_spacing
            
            # Calculate table height based on number of columns
            table.height = 40 + len(table.columns) * 25
    
    def draw_table(self, table: Table):
        """Draw a single table"""
        x, y = table.x, table.y
        width, height = table.width, table.height
        
        # Draw table border
        self.create_rectangle(
            x, y, x + width, y + height,
            fill=self.table_bg,
            outline=self.table_border,
            width=2,
            tags=("table", f"table_{table.name}")
        )
        
        # Draw header
        header_height = 35
        self.create_rectangle(
            x, y, x + width, y + header_height,
            fill=self.header_bg,
            outline=self.table_border,
            width=2,
            tags=("table", f"table_{table.name}")
        )
        
        # Table name
        self.create_text(
            x + width / 2, y + header_height / 2,
            text=table.name,
            fill=self.header_fg,
            font=("Segoe UI", 12, "bold"),
            tags=("table", f"table_{table.name}")
        )
        
        # Draw columns
        y_offset = y + header_height + 5
        for col in table.columns:
            # Column icon
            if col.is_pk:
                icon = "🔑"
                color = self.pk_color
            elif any(fk.from_column == col.name for fk in table.foreign_keys):
                icon = "🔗"
                color = self.fk_color
            else:
                icon = "▪"
                color = self.text_color
            
            # Column text
            col_text = f"{icon} {col.name}: {col.data_type}"
            self.create_text(
                x + 10, y_offset,
                text=col_text,
                fill=color,
                font=("Consolas", 9),
                anchor="w",
                tags=("table", f"table_{table.name}")
            )
            
            y_offset += 25
    
    def draw_relationship(self, rel: ForeignKey):
        """Draw a relationship line between tables"""
        if rel.from_table not in self.tables or rel.to_table not in self.tables:
            return
        
        from_table = self.tables[rel.from_table]
        to_table = self.tables[rel.to_table]
        
        # Calculate connection points (center-right and center-left)
        from_x = from_table.x + from_table.width
        from_y = from_table.y + from_table.height / 2
        
        to_x = to_table.x
        to_y = to_table.y + to_table.height / 2
        
        # Draw line with arrow
        self.create_line(
            from_x, from_y, to_x, to_y,
            fill=self.line_color,
            width=2,
            arrow=tk.LAST,
            tags="relationship"
        )
        
        # Draw relationship label
        mid_x = (from_x + to_x) / 2
        mid_y = (from_y + to_y) / 2
        
        self.create_text(
            mid_x, mid_y - 10,
            text=f"{rel.from_column} → {rel.to_column}",
            fill=self.text_color,
            font=("Segoe UI", 8),
            tags="relationship"
        )
    
    def on_click(self, event):
        """Handle mouse click"""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        items = self.find_overlapping(x, y, x, y)
        
        for item in items:
            tags = self.gettags(item)
            for tag in tags:
                if tag.startswith("table_"):
                    table_name = tag[6:]
                    if table_name in self.tables:
                        self.dragging_table = self.tables[table_name]
                        self.drag_offset_x = x - self.dragging_table.x
                        self.drag_offset_y = y - self.dragging_table.y
                        return
    
    def on_drag(self, event):
        """Handle mouse drag"""
        if self.dragging_table:
            x, y = self.canvasx(event.x), self.canvasy(event.y)
            
            # Update table position
            self.dragging_table.x = x - self.drag_offset_x
            self.dragging_table.y = y - self.drag_offset_y
            
            # Redraw diagram
            self.draw_diagram(self.tables, self.relationships)
    
    def on_release(self, event):
        """Handle mouse release"""
        self.dragging_table = None
    
    def update_scroll_region(self):
        """Update the scroll region to fit all content"""
        bbox = self.bbox("all")
        if bbox:
            self.configure(scrollregion=(bbox[0] - 50, bbox[1] - 50, bbox[2] + 50, bbox[3] + 50))


class DBDiagramView(ctk.CTkFrame):
    """Database Diagram View Component"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F5EFE7")
        
        self.current_tables = {}
        self.current_relationships = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the diagram view UI"""
        # Split into two panels: DBML editor (left) and diagram (right)
        
        # Left panel - DBML Editor
        left_panel = ctk.CTkFrame(self, fg_color="#E8DFD0")
        left_panel.pack(side="left", fill="both", expand=False, padx=(10, 5), pady=10)
        left_panel.configure(width=400)
        
        # DBML Editor Title
        title_label = ctk.CTkLabel(
            left_panel,
            text="📝 DBML Schema",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3E2723"
        )
        title_label.pack(pady=(10, 5))
        
        # Help text
        help_text = ctk.CTkLabel(
            left_panel,
            text="Enter your database schema in DBML format",
            font=ctk.CTkFont(size=10),
            text_color="#8B7355"
        )
        help_text.pack(pady=(0, 10))
        
        # DBML Text Editor
        editor_frame = ctk.CTkFrame(left_panel, fg_color="#F5EFE7")
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
        button_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_frame.pack(pady=(0, 10))
        
        generate_btn = ctk.CTkButton(
            button_frame,
            text="Generate Diagram",
            command=self.generate_diagram,
            font=ctk.CTkFont(size=12, weight="bold"),
            width=150,
            height=35,
            fg_color="#9B8F5E",
            hover_color="#87795A"
        )
        generate_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            button_frame,
            text="Clear",
            command=self.clear_dbml,
            width=100,
            height=35,
            fg_color="#9B8F5E",
            hover_color="#87795A"
        )
        clear_btn.pack(side="left", padx=5)
        
        # Right panel - Diagram Canvas
        right_panel = ctk.CTkFrame(self, fg_color="#E8DFD0")
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        
        # Diagram Title
        diagram_title = ctk.CTkLabel(
            right_panel,
            text="🗺️ Entity Relationship Diagram",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3E2723"
        )
        diagram_title.pack(pady=(10, 5))
        
        # Canvas frame
        canvas_frame = ctk.CTkFrame(right_panel, fg_color="#F5EFE7")
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
            right_panel,
            text="💡 Drag tables to rearrange the diagram",
            font=ctk.CTkFont(size=10),
            text_color="#8B7355"
        )
        info_label.pack(pady=(0, 10))
    
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
