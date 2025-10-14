"""
Schema browser component for displaying database structure
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, Any, Callable, Optional

class SchemaBrowser(ctk.CTkFrame):
    """Tree view for browsing database schema"""
    
    def __init__(self, parent, on_table_select: Optional[Callable[[str], None]] = None):
        super().__init__(parent)
        
        self.on_table_select = on_table_select
        self.schema_data = {}
        
        # Create UI components
        self.create_widgets()
    
    def create_widgets(self):
        """Create schema browser widgets"""
        # Title
        title_label = ctk.CTkLabel(
            self, 
            text="Schema Browser", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        title_label.pack(pady=(12, 8))
        
        # Search frame
        search_frame = ctk.CTkFrame(self, fg_color="#E8DFD0")
        search_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        self.search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Search tables...",
            height=32,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(fill="x", padx=12, pady=12)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        # Tree frame
        tree_frame = ctk.CTkFrame(self, fg_color="#E8DFD0")
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # Create treeview with scrollbars
        self.tree = ttk.Treeview(tree_frame, show="tree")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Bind events
        self.tree.bind("<Double-1>", self.on_item_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)  # Right-click context menu
        
        # Info panel
        info_frame = ctk.CTkFrame(self, fg_color="#E8DFD0")
        info_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        self.info_label = ctk.CTkLabel(
            info_frame, 
            text="No database connected",
            font=ctk.CTkFont(size=12),
            wraplength=280,
            text_color="#3E2723"
        )
        self.info_label.pack(pady=12)
        
        # Configure tree styling
        self.configure_tree_style()
    
    def configure_tree_style(self):
        """Configure treeview styling"""
        style = ttk.Style()
        
        # Configure treeview colors to match warm beige theme
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="#F5EFE7",
                        foreground="#3E2723",
                        fieldbackground="#F5EFE7",
                        borderwidth=1,
                        font=("Segoe UI", 10),
                        rowheight=22)
        style.configure("Treeview.Heading",
                        background="#E8DFD0",
                        foreground="#3E2723",
                        borderwidth=1,
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview",
                  background=[('selected', '#9B8F5E')],
                  foreground=[('selected', 'white')])
        
        # Configure scrollbars
        style.configure("Vertical.TScrollbar", 
                        background="#E8DFD0", 
                        troughcolor="#F5EFE7", 
                        borderwidth=1,
                        arrowcolor="#3E2723")
        style.configure("Horizontal.TScrollbar", 
                        background="#E8DFD0", 
                        troughcolor="#F5EFE7", 
                        borderwidth=1,
                        arrowcolor="#3E2723")
    
    def update_schema(self, schema_data: Dict[str, Any]):
        """Update the schema browser with new data"""
        self.schema_data = schema_data
        self.populate_tree()
        self.update_info()
    
    def populate_tree(self):
        """Populate the tree with schema data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.schema_data:
            return
        
        # Add schemas
        schemas = set()
        for table_name in self.schema_data.get('tables', {}):
            schema_name = table_name.split('.')[0]
            schemas.add(schema_name)
        
        for schema_name in sorted(schemas):
            schema_id = self.tree.insert("", "end", text=f"📁 {schema_name}", 
                                       values=(schema_name, "schema"))
            
            # Add tables under schema
            tables_id = self.tree.insert(schema_id, "end", text="📋 Tables", 
                                       values=(f"{schema_name}.tables", "tables_folder"))
            
            # Add individual tables
            schema_tables = [name for name in self.schema_data.get('tables', {}) 
                           if name.startswith(f"{schema_name}.")]
            
            for table_name in sorted(schema_tables):
                table_display_name = table_name.split('.')[1]  # Remove schema prefix
                table_id = self.tree.insert(tables_id, "end", text=f"🔧 {table_display_name}", 
                                          values=(table_name, "table"))
                
                # Add columns under table
                table_info = self.schema_data['tables'][table_name]
                for column in table_info['columns']:
                    column_text = f"{column['name']} ({column['type']})"
                    if column.get('primary_key'):
                        column_text = f"🔑 {column_text}"
                    elif column.get('foreign_key'):
                        column_text = f"🔗 {column_text}"
                    else:
                        column_text = f"📄 {column_text}"
                    
                    self.tree.insert(table_id, "end", text=column_text,
                                   values=(f"{table_name}.{column['name']}", "column"))
            
            # Add views under schema if any
            schema_views = [name for name in self.schema_data.get('views', {}) 
                          if name.startswith(f"{schema_name}.")]
            
            if schema_views:
                views_id = self.tree.insert(schema_id, "end", text="👁️ Views", 
                                          values=(f"{schema_name}.views", "views_folder"))
                
                for view_name in sorted(schema_views):
                    view_display_name = view_name.split('.')[1]  # Remove schema prefix
                    self.tree.insert(views_id, "end", text=f"👁️ {view_display_name}", 
                                   values=(view_name, "view"))
        
        # Expand all schema nodes by default
        for item in self.tree.get_children():
            self.tree.item(item, open=True)
    
    def update_info(self):
        """Update the info panel"""
        if not self.schema_data:
            self.info_label.configure(text="No database connected")
            return
        
        table_count = len(self.schema_data.get('tables', {}))
        view_count = len(self.schema_data.get('views', {}))
        schema_count = len(self.schema_data.get('schemas', []))
        
        info_text = f"Schemas: {schema_count}\nTables: {table_count}\nViews: {view_count}"
        self.info_label.configure(text=info_text)
    
    def on_search(self, event):
        """Handle search input"""
        search_term = self.search_entry.get().lower()
        
        if not search_term:
            # Show all items
            self.show_all_items()
            return
        
        # Hide all items first
        self.hide_all_items()
        
        # Show matching items
        self.show_matching_items(search_term)
    
    def show_all_items(self):
        """Show all tree items"""
        def show_item(item):
            children = self.tree.get_children(item)
            for child in children:
                show_item(child)
            
            # Make item visible by ensuring parent is expanded
            parent = self.tree.parent(item)
            if parent:
                self.tree.item(parent, open=True)
        
        for item in self.tree.get_children():
            show_item(item)
    
    def hide_all_items(self):
        """Hide all tree items except top-level schemas"""
        def hide_children(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                hide_children(child)
        
        for item in self.tree.get_children():
            hide_children(item)
    
    def show_matching_items(self, search_term: str):
        """Show items that match the search term"""
        def check_and_show_item(item):
            item_text = self.tree.item(item, "text").lower()
            values = self.tree.item(item, "values")
            
            # Check if this item matches
            matches = search_term in item_text
            if values and len(values) > 0:
                matches = matches or search_term in values[0].lower()
            
            # Check children
            children = self.tree.get_children(item)
            child_matches = False
            for child in children:
                if check_and_show_item(child):
                    child_matches = True
            
            # Show this item if it matches or has matching children
            if matches or child_matches:
                parent = self.tree.parent(item)
                if parent:
                    self.tree.item(parent, open=True)
                self.tree.item(item, open=True)
                return True
            
            return False
        
        for item in self.tree.get_children():
            check_and_show_item(item)
    
    def on_item_double_click(self, event):
        """Handle double-click on tree item"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        
        values = self.tree.item(item, "values")
        if values and len(values) >= 2:
            item_type = values[1]
            item_name = values[0]
            
            if item_type == "table" and self.on_table_select:
                self.on_table_select(item_name)
            elif item_type == "view" and self.on_table_select:
                self.on_table_select(item_name)
    
    def on_right_click(self, event):
        """Handle right-click context menu"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        values = self.tree.item(item, "values")
        
        if values and len(values) >= 2:
            item_type = values[1]
            item_name = values[0]
            
            # Create context menu
            context_menu = tk.Menu(self, tearoff=0)
            
            if item_type == "table":
                context_menu.add_command(
                    label="Select from table", 
                    command=lambda: self.generate_select_query(item_name)
                )
                context_menu.add_command(
                    label="Describe table", 
                    command=lambda: self.describe_table(item_name)
                )
                context_menu.add_separator()
                context_menu.add_command(
                    label="Copy table name", 
                    command=lambda: self.copy_to_clipboard(item_name)
                )
            elif item_type == "view":
                context_menu.add_command(
                    label="Select from view", 
                    command=lambda: self.generate_select_query(item_name)
                )
                context_menu.add_command(
                    label="Copy view name", 
                    command=lambda: self.copy_to_clipboard(item_name)
                )
            elif item_type == "column":
                column_name = item_name.split('.')[-1]
                table_name = '.'.join(item_name.split('.')[:-1])
                context_menu.add_command(
                    label="Copy column name", 
                    command=lambda: self.copy_to_clipboard(column_name)
                )
                context_menu.add_command(
                    label="Filter by column", 
                    command=lambda: self.generate_filter_query(table_name, column_name)
                )
            
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def generate_select_query(self, table_name: str):
        """Generate a SELECT query for the table"""
        query = f"SELECT * FROM {table_name} LIMIT 100;"
        if self.on_table_select:
            # This is a bit of a hack - we're using the table select callback
            # to insert the query. In a real implementation, you'd have a proper
            # callback for inserting queries.
            self.master.master.query_panel.set_query(query)
    
    def describe_table(self, table_name: str):
        """Generate a query to describe the table structure"""
        query = f"""
-- Table structure for {table_name}
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = '{table_name.split('.')[-1]}'
  AND table_schema = '{table_name.split('.')[0]}'
ORDER BY ordinal_position;
"""
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query.strip())
    
    def generate_filter_query(self, table_name: str, column_name: str):
        """Generate a filtered SELECT query"""
        query = f"SELECT * FROM {table_name} WHERE {column_name} = ? LIMIT 100;"
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query)
    
    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(text)
        
        # Show feedback
        if hasattr(self.master.master, 'update_status'):
            self.master.master.update_status(f"Copied '{text}' to clipboard")
    
    def clear_schema(self):
        """Clear the schema browser"""
        self.schema_data = {}
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.info_label.configure(text="No database connected")
    
    def get_selected_item(self) -> Optional[str]:
        """Get the currently selected item"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        values = self.tree.item(selection[0], "values")
        return values[0] if values else None
    
    def expand_all(self):
        """Expand all tree nodes"""
        def expand_item(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand_item(child)
        
        for item in self.tree.get_children():
            expand_item(item)
    
    def collapse_all(self):
        """Collapse all tree nodes"""
        def collapse_item(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse_item(child)
        
        for item in self.tree.get_children():
            collapse_item(item)