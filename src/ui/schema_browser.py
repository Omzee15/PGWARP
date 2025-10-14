"""
Schema browser component for displaying database structure
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import customtkinter as ctk
from typing import Dict, Any, Callable, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.saved_queries import SavedQueriesManager

class SchemaBrowser(ctk.CTkFrame):
    """Tree view for browsing database schema"""
    
    def __init__(self, parent, on_table_select: Optional[Callable[[str], None]] = None, 
                 on_query_select: Optional[Callable[[str], None]] = None,
                 ai_assistant: Optional[Any] = None):
        super().__init__(parent)
        
        self.on_table_select = on_table_select
        self.on_query_select = on_query_select
        self.ai_assistant = ai_assistant
        self.schema_data = {}
        self.saved_queries_manager = SavedQueriesManager()
        
        # Create UI components
        self.create_widgets()
    
    def create_widgets(self):
        """Create schema browser widgets"""
        # Title frame
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(12, 8), fill="x", padx=12)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Schema Browser", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        title_label.pack(side="left", expand=True)
        
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
        
        # Tree frame for database schema
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
        
        # Separator
        separator = ctk.CTkFrame(self, height=2, fg_color="#9B8F5E")
        separator.pack(fill="x", padx=12, pady=8)
        
        # Saved Queries Section
        self.create_saved_queries_section()
        
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
    
    def create_saved_queries_section(self):
        """Create the saved queries section below the schema browser"""
        # Saved queries title frame
        saved_queries_header = ctk.CTkFrame(self, fg_color="transparent")
        saved_queries_header.pack(fill="x", padx=12, pady=(0, 8))
        
        saved_queries_label = ctk.CTkLabel(
            saved_queries_header,
            text="⭐ Saved Queries",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        saved_queries_label.pack(side="left", expand=True)
        
        # Add query button
        add_query_btn = ctk.CTkButton(
            saved_queries_header,
            text="➕",
            width=30,
            height=30,
            command=self.show_add_query_dialog,
            font=ctk.CTkFont(size=16)
        )
        add_query_btn.pack(side="right")
        
        # Saved queries table frame
        queries_table_frame = ctk.CTkFrame(self, fg_color="#E8DFD0")
        queries_table_frame.pack(fill="both", expand=False, padx=12, pady=(0, 12))
        queries_table_frame.configure(height=200)  # Fixed height for saved queries section
        
        # Create treeview for saved queries (matching results table style)
        self.queries_tree = ttk.Treeview(
            queries_table_frame,
            columns=("title", "actions"),
            show="headings",
            selectmode="browse",
            height=8
        )
        
        # Configure columns
        self.queries_tree.heading("title", text="Query Title")
        self.queries_tree.heading("actions", text="")
        
        self.queries_tree.column("title", width=200, anchor="w")
        self.queries_tree.column("actions", width=50, anchor="center")
        
        # Scrollbars
        queries_v_scroll = ttk.Scrollbar(queries_table_frame, orient="vertical", command=self.queries_tree.yview)
        self.queries_tree.configure(yscrollcommand=queries_v_scroll.set)
        
        # Pack treeview and scrollbar
        self.queries_tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        queries_v_scroll.pack(side="right", fill="y", pady=2)
        
        # Bind events
        self.queries_tree.bind("<Double-1>", self.on_query_tree_double_click)
        self.queries_tree.bind("<Button-3>", self.on_query_tree_right_click)
        self.queries_tree.bind("<Button-1>", self.on_query_tree_click)
        
        # Load saved queries
        self.refresh_saved_queries()
    
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
    
    def refresh_saved_queries(self):
        """Refresh the saved queries list in table format"""
        # Reload queries from disk
        self.saved_queries_manager.load_queries()
        
        # Clear existing items
        for item in self.queries_tree.get_children():
            self.queries_tree.delete(item)
        
        # Get all saved queries
        queries = self.saved_queries_manager.get_all_queries()
        
        if not queries:
            # Show empty state message
            self.queries_tree.insert("", "end", values=("No saved queries yet - Click ➕ to add", ""), tags=("empty",))
            self.queries_tree.tag_configure("empty", foreground="#8B7355", font=("Segoe UI", 10, "italic"))
        else:
            # Add each saved query as a row with alternating colors
            for i, query in enumerate(queries):
                tag = "odd" if i % 2 == 1 else "even"
                # Store query id in the item
                item_id = self.queries_tree.insert("", "end", 
                                                   values=(f"💾 {query.title}", "🗑️"), 
                                                   tags=(tag, query.id))
            
            # Configure row tags for alternating colors (matching results table)
            self.queries_tree.tag_configure("odd", background="#F5EFE7")
            self.queries_tree.tag_configure("even", background="#EBE3D5")
    
    def on_query_tree_click(self, event):
        """Handle single click on queries tree"""
        # Check if delete button (🗑️) was clicked
        region = self.queries_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.queries_tree.identify_column(event.x)
            item = self.queries_tree.identify_row(event.y)
            
            if item and column == "#2":  # Actions column (delete button)
                # Get query id from tags
                tags = self.queries_tree.item(item, "tags")
                for tag in tags:
                    if tag not in ["odd", "even", "empty"]:
                        query_id = tag
                        saved_query = self.saved_queries_manager.get_query(query_id)
                        if saved_query:
                            self.confirm_delete_query(query_id, saved_query.title)
                        break
    
    def on_query_tree_double_click(self, event):
        """Handle double-click on saved query to load it"""
        item = self.queries_tree.selection()
        if not item:
            return
        
        # Get query id from tags
        tags = self.queries_tree.item(item[0], "tags")
        for tag in tags:
            if tag not in ["odd", "even", "empty"]:
                query_id = tag
                saved_query = self.saved_queries_manager.get_query(query_id)
                if saved_query and self.on_query_select:
                    self.on_query_select(saved_query.query)
                break
    
    def on_query_tree_right_click(self, event):
        """Handle right-click on saved query"""
        # Select the item under cursor
        item = self.queries_tree.identify_row(event.y)
        if not item:
            return
        
        self.queries_tree.selection_set(item)
        
        # Get query id from tags
        tags = self.queries_tree.item(item, "tags")
        query_id = None
        for tag in tags:
            if tag not in ["odd", "even", "empty"]:
                query_id = tag
                break
        
        if not query_id:
            return
        
        saved_query = self.saved_queries_manager.get_query(query_id)
        if not saved_query:
            return
        
        # Create context menu
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(
            label="Open Query",
            command=lambda: self.open_saved_query(query_id)
        )
        context_menu.add_command(
            label="Edit Title",
            command=lambda: self.edit_query_title(query_id)
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="Delete Query",
            command=lambda: self.delete_saved_query(query_id)
        )
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def confirm_delete_query(self, query_id: str, query_title: str):
        """Confirm and delete a saved query"""
        if messagebox.askyesno(
            "Delete Query",
            f"Are you sure you want to delete '{query_title}'?",
            parent=self
        ):
            self.saved_queries_manager.delete_query(query_id)
            self.refresh_saved_queries()
            
            if hasattr(self.master.master, 'update_status'):
                self.master.master.update_status(f"Deleted query: {query_title}")
    
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
    
    def show_add_query_dialog(self):
        """Show dialog to add a new saved query"""
        # Create a custom dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Saved Query")
        dialog.geometry("600x550")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (550 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Configure dialog grid
        dialog.grid_rowconfigure(2, weight=1)  # Query frame should expand
        dialog.grid_columnconfigure(0, weight=1)
        
        # Title label
        title_label = ctk.CTkLabel(
            dialog,
            text="Save New Query",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=20, padx=20, sticky="w")
        
        # Query title entry
        title_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        title_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="Query Title:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")
        
        title_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="Enter query title (leave blank for AI-generated title)",
            height=35,
            font=ctk.CTkFont(size=12)
        )
        title_entry.pack(fill="x", pady=5)
        
        # Query text area
        query_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        query_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        query_frame.grid_rowconfigure(1, weight=1)
        query_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            query_frame,
            text="SQL Query:",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Text widget frame
        text_widget_frame = ctk.CTkFrame(query_frame, fg_color="#F5EFE7", corner_radius=6)
        text_widget_frame.grid(row=1, column=0, sticky="nsew")
        
        query_text = tk.Text(
            text_widget_frame,
            font=("Consolas", 11),
            bg="#F5EFE7",
            fg="#3E2723",
            insertbackground="#9B8F5E",
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0,
            padx=8,
            pady=8,
            height=15
        )
        query_text.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Buttons frame - make sure it's visible and at bottom
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent", height=60)
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_frame.grid_propagate(False)  # Keep fixed height
        
        def save_query():
            query = query_text.get("1.0", "end-1c").strip()
            title = title_entry.get().strip()
            
            if not query:
                messagebox.showwarning("Empty Query", "Please enter a SQL query")
                return
            
            # Generate title using AI if not provided
            if not title:
                if self.ai_assistant:
                    try:
                        title = self.ai_assistant.generate_query_title(query)
                    except Exception as e:
                        title = "Saved Query"
                else:
                    title = "Saved Query"
            
            # Save the query
            self.saved_queries_manager.add_query(title, query)
            self.refresh_saved_queries()
            dialog.destroy()
            
            # Show success message
            if hasattr(self.master.master, 'update_status'):
                self.master.master.update_status(f"Saved query: {title}")
        
        # Cancel button (left side)
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=120,
            height=36,
            fg_color="#E8DFD0",
            hover_color="#D9CDBF",
            text_color="#3E2723"
        )
        cancel_btn.pack(side="left", padx=5, pady=10)
        
        # Save button (right side)
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Query",
            command=save_query,
            width=120,
            height=36
        )
        save_btn.pack(side="right", padx=5, pady=10)
    
    def open_saved_query(self, query_id: str):
        """Open a saved query in the query panel"""
        saved_query = self.saved_queries_manager.get_query(query_id)
        if saved_query and self.on_query_select:
            self.on_query_select(saved_query.query)
    
    def edit_query_title(self, query_id: str):
        """Edit the title of a saved query"""
        saved_query = self.saved_queries_manager.get_query(query_id)
        if not saved_query:
            return
        
        # Show input dialog
        new_title = simpledialog.askstring(
            "Edit Query Title",
            "Enter new title:",
            initialvalue=saved_query.title,
            parent=self
        )
        
        if new_title and new_title.strip():
            self.saved_queries_manager.update_query(query_id, title=new_title.strip())
            self.refresh_saved_queries()
            
            if hasattr(self.master.master, 'update_status'):
                self.master.master.update_status(f"Updated query title to: {new_title}")
    
    def delete_saved_query(self, query_id: str):
        """Delete a saved query"""
        saved_query = self.saved_queries_manager.get_query(query_id)
        if not saved_query:
            return
        
        # Confirm deletion
        if messagebox.askyesno(
            "Delete Query",
            f"Are you sure you want to delete '{saved_query.title}'?",
            parent=self
        ):
            self.saved_queries_manager.delete_query(query_id)
            self.refresh_saved_queries()
            
            if hasattr(self.master.master, 'update_status'):
                self.master.master.update_status(f"Deleted query: {saved_query.title}")
    
    def save_selected_query(self, query_text: str):
        """Save a query with optional AI-generated title"""
        if not query_text.strip():
            messagebox.showwarning("Empty Query", "Please select a query to save")
            return
        
        # Ask for title
        title = simpledialog.askstring(
            "Save Query",
            "Enter query title (leave blank for AI-generated title):",
            parent=self
        )
        
        # User cancelled
        if title is None:
            return
        
        # Generate title using AI if not provided
        if not title.strip():
            if self.ai_assistant:
                try:
                    title = self.ai_assistant.generate_query_title(query_text)
                except Exception as e:
                    title = "Saved Query"
            else:
                title = "Saved Query"
        
        # Save the query
        self.saved_queries_manager.add_query(title, query_text)
        self.refresh_saved_queries()
        
        if hasattr(self.master.master, 'update_status'):
            self.master.master.update_status(f"Saved query: {title}")