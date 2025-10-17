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
from utils.saved_variables import SavedVariablesManager
from utils.theme_manager import theme_manager


class QueryTooltip:
    """Tooltip widget for showing query preview on hover"""
    
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.text = ""
        
    def show_tooltip(self, text: str, x: int, y: int):
        """Display tooltip with query text"""
        if self.tip_window or not text:
            return
        
        # Create tooltip window
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Create frame with border
        frame = tk.Frame(tw, background=theme_manager.get_color("accent.primary"), borderwidth=1, relief="solid")
        frame.pack()
        
        # Create text widget for query preview
        text_widget = tk.Text(
            frame,
            background=theme_manager.get_color("background.main"),
            foreground=theme_manager.get_color("text.primary"),
            font=("Consolas", 10),
            wrap="word",
            borderwidth=8,
            relief="flat",
            padx=8,
            pady=8,
            width=50,
            height=min(10, len(text.split('\n')) + 1)
        )
        text_widget.pack()
        
        # Insert query text
        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")
        
    def hide_tooltip(self):
        """Hide the tooltip"""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class SchemaBrowser(ctk.CTkFrame):
    """Tree view for browsing database schema"""
    
    def __init__(self, parent, on_table_select: Optional[Callable[[str], None]] = None, 
                 on_query_select: Optional[Callable[[str], None]] = None,
                 ai_assistant: Optional[Any] = None,
                 on_connect: Optional[Callable[[], None]] = None,
                 on_disconnect: Optional[Callable[[], None]] = None,
                 db_connection: Optional[Any] = None):
        super().__init__(parent)
        
        self.on_table_select = on_table_select
        self.on_query_select = on_query_select
        self.ai_assistant = ai_assistant
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.db_connection = db_connection
        self.schema_data = {}
        self.saved_queries_manager = SavedQueriesManager()
        self.saved_variables_manager = SavedVariablesManager()
        
        # Tooltip for query preview
        self.query_tooltip = None
        self.hover_after_id = None
        
        # Collapsible section states
        self.schema_collapsed = False
        self.queries_collapsed = False
        self.variables_collapsed = False
        
        # Create UI components
        self.create_widgets()
    
    def create_widgets(self):
        """Create schema browser widgets"""
        # ===== HEADER: Connection Controls =====
        header_frame = ctk.CTkFrame(self, fg_color=theme_manager.get_color("accent.primary"), corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        # Title and controls container
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=12, pady=8)
        
        # Left side - title
        title_label = ctk.CTkLabel(
            header_content,
            text="🗄️ Database",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF"
        )
        title_label.pack(side="left")
        
        # Right side - connection buttons
        self.button_container = ctk.CTkFrame(header_content, fg_color="transparent")
        self.button_container.pack(side="right")
        
        self.connect_btn = ctk.CTkButton(
            self.button_container,
            text="🔌 Connect",
            command=self.on_connect if self.on_connect else None,
            width=100,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#87795A",
            hover_color="#6B5E45",
            corner_radius=6
        )
        self.connect_btn.pack(side="left", padx=2)
        
        self.disconnect_btn = ctk.CTkButton(
            self.button_container,
            text="🔌 Disconnect",
            command=self.on_disconnect if self.on_disconnect else None,
            width=100,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#C4756C",
            hover_color="#A85E56",
            corner_radius=6
        )
        # Initially hide disconnect button
        self.disconnect_btn.pack_forget()
        
        # Connection info label (below header)
        connection_info_frame = ctk.CTkFrame(self, fg_color=theme_manager.get_color("background.main"), corner_radius=8)
        connection_info_frame.pack(fill="x", padx=0, pady=0)
        
        self.connection_label = ctk.CTkLabel(
            connection_info_frame,
            text="Not connected",
            font=ctk.CTkFont(size=9),
            text_color="#8B7355",
            wraplength=280,
            anchor="center"
        )
        self.connection_label.pack(pady=6, padx=10)
        
        # ===== SCHEMA BROWSER SECTION (Collapsible) =====
        # Schema browser header
        self.schema_header = ctk.CTkFrame(self, fg_color=theme_manager.get_color("background.secondary"), corner_radius=6)
        self.schema_header.pack(fill="x", padx=8, pady=(8, 0))
        
        schema_header_btn = ctk.CTkButton(
            self.schema_header,
            text="▼ Schema Browser",
            command=self.toggle_schema_section,
            fg_color="transparent",
            hover_color="#C9BDB0",
            text_color="#3E2723",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            height=32
        )
        schema_header_btn.pack(fill="x", padx=8, pady=4)
        self.schema_header_btn = schema_header_btn
        
        # Schema browser content frame
        self.schema_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.schema_content_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        # Tree frame for database schema
        tree_frame = ctk.CTkFrame(self.schema_content_frame, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        tree_frame.pack(fill="both", expand=True)
        
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
        info_frame = ctk.CTkFrame(self.schema_content_frame, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        info_frame.pack(fill="x", pady=(8, 0))
        
        self.info_label = ctk.CTkLabel(
            info_frame, 
            text="No database connected",
            font=ctk.CTkFont(size=11),
            wraplength=280,
            text_color="#3E2723"
        )
        self.info_label.pack(pady=8)
        
        # Configure tree styling
        self.configure_tree_style()
        
        # ===== SAVED QUERIES SECTION (Collapsible) =====
        # Saved queries header (separate from content)
        self.queries_header = ctk.CTkFrame(self, fg_color=theme_manager.get_color("background.secondary"), corner_radius=6)
        self.queries_header.pack(fill="x", padx=8, pady=(8, 0))
        
        queries_header_container = ctk.CTkFrame(self.queries_header, fg_color="transparent")
        queries_header_container.pack(fill="x", padx=4, pady=4)
        
        queries_header_btn = ctk.CTkButton(
            queries_header_container,
            text="▼ Saved Queries",
            command=self.toggle_queries_section,
            fg_color="transparent",
            hover_color="#C9BDB0",
            text_color="#3E2723",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            height=32
        )
        queries_header_btn.pack(side="left", fill="x", expand=True)
        self.queries_header_btn = queries_header_btn
        
        # Add query button
        add_query_btn = ctk.CTkButton(
            queries_header_container,
            text="➕",
            width=30,
            height=28,
            command=self.show_add_query_dialog,
            fg_color="#9B8F5E",
            hover_color="#87795A",
            font=ctk.CTkFont(size=14),
            corner_radius=6
        )
        add_query_btn.pack(side="right", padx=4)
        
        # Saved queries content frame (this will be shown/hidden)
        self.queries_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.queries_content_frame.pack(fill="x", expand=False, padx=8, pady=(0, 8))
        
        # Saved Queries Section
        self.create_saved_queries_section()
        
        # ===== SAVED VARIABLES SECTION (Collapsible) =====
        # Variables header
        self.variables_header = ctk.CTkFrame(self, fg_color=theme_manager.get_color("background.secondary"), corner_radius=6)
        self.variables_header.pack(fill="x", padx=8, pady=(8, 0))
        
        variables_header_container = ctk.CTkFrame(self.variables_header, fg_color="transparent")
        variables_header_container.pack(fill="x", padx=4, pady=4)
        
        variables_header_btn = ctk.CTkButton(
            variables_header_container,
            text="▼ Variables",
            command=self.toggle_variables_section,
            fg_color="transparent",
            hover_color="#C9BDB0",
            text_color="#3E2723",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            height=32
        )
        variables_header_btn.pack(side="left", fill="x", expand=True)
        self.variables_header_btn = variables_header_btn
        
        # Add variable button
        add_variable_btn = ctk.CTkButton(
            variables_header_container,
            text="➕",
            width=30,
            height=28,
            command=self.show_add_variable_dialog,
            fg_color="#9B8F5E",
            hover_color="#87795A",
            font=ctk.CTkFont(size=14),
            corner_radius=6
        )
        add_variable_btn.pack(side="right", padx=4)
        
        # Variables content frame (this will be shown/hidden)
        self.variables_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.variables_content_frame.pack(fill="x", expand=False, padx=8, pady=(0, 8))
        
        # Saved Variables Section
        self.create_saved_variables_section()
    
    def create_saved_queries_section(self):
        """Create the saved queries section below the schema browser"""
        # Saved queries table frame (removed duplicate header and button)
        queries_table_frame = ctk.CTkFrame(self.queries_content_frame, fg_color="#E8DFD0", corner_radius=8)
        queries_table_frame.pack(fill="both", expand=False, padx=12, pady=(0, 12))
        queries_table_frame.configure(height=200)  # Fixed height for saved queries section
        
        # Create treeview for saved queries (matching results table style)
        self.queries_tree = ttk.Treeview(
            queries_table_frame,
            columns=("title", "shortcut", "copy", "delete"),
            show="headings",
            selectmode="browse",
            height=8
        )
        
        # Configure columns
        self.queries_tree.heading("title", text="Query Title")
        self.queries_tree.heading("shortcut", text="Shortcut")
        self.queries_tree.heading("copy", text="")
        self.queries_tree.heading("delete", text="")
        
        self.queries_tree.column("title", width=140, anchor="w")
        self.queries_tree.column("shortcut", width=80, anchor="w")
        self.queries_tree.column("copy", width=40, anchor="center")
        self.queries_tree.column("delete", width=40, anchor="center")
        
        # Scrollbars
        queries_v_scroll = ttk.Scrollbar(queries_table_frame, orient="vertical", command=self.queries_tree.yview)
        self.queries_tree.configure(yscrollcommand=queries_v_scroll.set)
        
        # Pack treeview and scrollbar
        self.queries_tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        queries_v_scroll.pack(side="right", fill="y", pady=2)
        
        # Create tooltip for query preview
        self.query_tooltip = QueryTooltip(self.queries_tree)
        
        # Bind events
        self.queries_tree.bind("<Double-1>", self.on_query_tree_double_click)
        self.queries_tree.bind("<Button-3>", self.on_query_tree_right_click)
        self.queries_tree.bind("<Button-1>", self.on_query_tree_click)
        self.queries_tree.bind("<Motion>", self.on_query_tree_motion)
        self.queries_tree.bind("<Leave>", self.on_query_tree_leave)
        
        # Load saved queries
        self.refresh_saved_queries()
    
    def create_saved_variables_section(self):
        """Create the saved variables section"""
        # Variables table frame
        variables_table_frame = ctk.CTkFrame(self.variables_content_frame, fg_color="#E8DFD0", corner_radius=8)
        variables_table_frame.pack(fill="both", expand=False, padx=12, pady=(0, 12))
        variables_table_frame.configure(height=180)  # Fixed height for saved variables section
        
        # Create treeview for saved variables (without value column in display)
        self.variables_tree = ttk.Treeview(
            variables_table_frame,
            columns=("name", "copy", "delete"),
            show="headings",
            selectmode="browse",
            height=7
        )
        
        # Configure columns (no value column shown)
        self.variables_tree.heading("name", text="Variable Name")
        self.variables_tree.heading("copy", text="")
        self.variables_tree.heading("delete", text="")
        
        self.variables_tree.column("name", width=220, anchor="w")
        self.variables_tree.column("copy", width=30, anchor="center")
        self.variables_tree.column("delete", width=30, anchor="center")
        
        # Scrollbars
        variables_v_scroll = ttk.Scrollbar(variables_table_frame, orient="vertical", command=self.variables_tree.yview)
        self.variables_tree.configure(yscrollcommand=variables_v_scroll.set)
        
        # Pack treeview and scrollbar
        self.variables_tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        variables_v_scroll.pack(side="right", fill="y", pady=2)
        
        # Create tooltip for variable value preview
        self.variable_tooltip = None
        self.variable_tooltip_window = None
        
        # Bind events
        self.variables_tree.bind("<Button-1>", self.on_variable_tree_click)
        self.variables_tree.bind("<Double-1>", self.on_variable_tree_double_click)
        self.variables_tree.bind("<Button-3>", self.on_variable_tree_right_click)
        self.variables_tree.bind("<Motion>", self.on_variable_tree_motion)
        self.variables_tree.bind("<Leave>", self.on_variable_tree_leave)
        
        # Load saved variables
        self.refresh_saved_variables()
    
    def configure_tree_style(self):
        """Configure treeview styling"""
        style = ttk.Style()
        
        # Configure treeview colors to match current theme
        style.theme_use("clam")
        style.configure("Treeview", 
                        background=theme_manager.get_color("background.main"),
                        foreground=theme_manager.get_color("text.primary"),
                        fieldbackground=theme_manager.get_color("background.main"),
                        borderwidth=1,
                        font=("Segoe UI", 10),
                        rowheight=22)
        style.configure("Treeview.Heading",
                        background=theme_manager.get_color("background.secondary"),
                        foreground=theme_manager.get_color("text.primary"),
                        borderwidth=1,
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview",
                  background=[('selected', theme_manager.get_color("accent.primary"))],
                  foreground=[('selected', theme_manager.get_color("buttons.primary_text"))])
        
        # Configure scrollbars
        style.configure("Vertical.TScrollbar", 
                        background=theme_manager.get_color("background.secondary"), 
                        troughcolor=theme_manager.get_color("background.main"), 
                        borderwidth=1,
                        arrowcolor=theme_manager.get_color("text.primary"))
        style.configure("Horizontal.TScrollbar", 
                        background=theme_manager.get_color("background.secondary"), 
                        troughcolor=theme_manager.get_color("background.main"), 
                        borderwidth=1,
                        arrowcolor=theme_manager.get_color("text.primary"))
    
    def toggle_schema_section(self):
        """Toggle the schema browser section visibility"""
        if self.schema_collapsed:
            # Expand - pack after the schema header
            self.schema_content_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8), after=self.schema_header)
            self.schema_header_btn.configure(text="▼ Schema Browser")
            self.schema_collapsed = False
        else:
            # Collapse
            self.schema_content_frame.pack_forget()
            self.schema_header_btn.configure(text="▶ Schema Browser")
            self.schema_collapsed = True
    
    def toggle_queries_section(self):
        """Toggle the saved queries section visibility"""
        if self.queries_collapsed:
            # Expand - pack after the queries header
            self.queries_content_frame.pack(fill="x", expand=False, padx=8, pady=(0, 8), after=self.queries_header)
            self.queries_header_btn.configure(text="▼ Saved Queries")
            self.queries_collapsed = False
        else:
            # Collapse
            self.queries_content_frame.pack_forget()
            self.queries_header_btn.configure(text="▶ Saved Queries")
            self.queries_collapsed = True
    
    def toggle_variables_section(self):
        """Toggle the saved variables section visibility"""
        if self.variables_collapsed:
            # Expand - pack after the variables header
            self.variables_content_frame.pack(fill="x", expand=False, padx=8, pady=(0, 8), after=self.variables_header)
            self.variables_header_btn.configure(text="▼ Variables")
            self.variables_collapsed = False
        else:
            # Collapse
            self.variables_content_frame.pack_forget()
            self.variables_header_btn.configure(text="▶ Variables")
            self.variables_collapsed = True
    
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
            self.queries_tree.insert("", "end", values=("No saved queries yet - Click ➕ to add", "", "", ""), tags=("empty",))
            self.queries_tree.tag_configure("empty", foreground="#8B7355", font=("Segoe UI", 10, "italic"))
        else:
            # Add each saved query as a row with alternating colors
            for i, query in enumerate(queries):
                tag = "odd" if i % 2 == 1 else "even"
                
                # Display shortcut with {{}} formatting if it exists
                shortcut_display = f"{{{{{query.shortcut}}}}}" if query.shortcut else ""
                
                # Store query id in the item - now with shortcut column
                item_id = self.queries_tree.insert("", "end", 
                                                   values=(f"💾 {query.title}", shortcut_display, "📋", "🗑️"), 
                                                   tags=(tag, query.id))
            
            # Configure row tags for alternating colors (matching results table)
            self.queries_tree.tag_configure("odd", background="#F5EFE7")
            self.queries_tree.tag_configure("even", background="#EBE3D5")
    
    def on_query_tree_click(self, event):
        """Handle single click on queries tree"""
        # Check if copy or delete button was clicked
        region = self.queries_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.queries_tree.identify_column(event.x)
            item = self.queries_tree.identify_row(event.y)
            
            if item:
                # Get query id from tags
                tags = self.queries_tree.item(item, "tags")
                query_id = None
                for tag in tags:
                    if tag not in ["odd", "even", "empty"]:
                        query_id = tag
                        break
                
                if query_id:
                    saved_query = self.saved_queries_manager.get_query(query_id)
                    if saved_query:
                        # Column #3 is copy button (📋) - updated from #2
                        if column == "#3":
                            self.copy_query_to_clipboard(query_id)
                            self.flash_row(item)
                        # Column #4 is delete button (🗑️) - updated from #3
                        elif column == "#4":
                            self.confirm_delete_query(query_id, saved_query.title)
    
    def on_query_tree_double_click(self, event):
        """Handle double-click on saved query to copy it to clipboard"""
        item = self.queries_tree.selection()
        if not item:
            return
        
        # Get query id from tags
        tags = self.queries_tree.item(item[0], "tags")
        for tag in tags:
            if tag not in ["odd", "even", "empty"]:
                query_id = tag
                saved_query = self.saved_queries_manager.get_query(query_id)
                if saved_query:
                    # Copy to clipboard
                    self.clipboard_clear()
                    self.clipboard_append(saved_query.query)
                    self.update()  # Make clipboard change persistent
                    
                    # Visual feedback - flash the row
                    self.flash_row(item[0])
                    
                    # Update status if available
                    if hasattr(self.master.master, 'update_status'):
                        self.master.master.update_status(f"'{saved_query.title}' copied to clipboard")
                break
    
    def flash_row(self, item_id):
        """Flash a row to provide visual feedback"""
        # Store original tags
        original_tags = self.queries_tree.item(item_id, "tags")
        
        # Flash with selection color
        self.queries_tree.item(item_id, tags=("flash",))
        self.queries_tree.tag_configure("flash", background="#9B8F5E", foreground="white")
        
        # Restore original tags after 300ms
        def restore_tags():
            self.queries_tree.item(item_id, tags=original_tags)
        
        self.after(300, restore_tags)
    
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
            label="📋 Copy to Clipboard",
            command=lambda: self.copy_query_to_clipboard(query_id)
        )
        context_menu.add_command(
            label="➕ Append to Editor",
            command=lambda: self.append_query_to_editor(query_id)
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="✏️ Edit Title",
            command=lambda: self.edit_query_title(query_id)
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="🗑️ Delete Query",
            command=lambda: self.delete_saved_query(query_id)
        )
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def on_query_tree_motion(self, event):
        """Handle mouse motion over queries tree - show tooltip"""
        # Cancel any pending tooltip
        if self.hover_after_id:
            self.after_cancel(self.hover_after_id)
            self.hover_after_id = None
        
        # Hide existing tooltip
        if self.query_tooltip:
            self.query_tooltip.hide_tooltip()
        
        # Get item under cursor
        item = self.queries_tree.identify_row(event.y)
        if not item:
            return
        
        # Get query id from tags
        tags = self.queries_tree.item(item, "tags")
        query_id = None
        for tag in tags:
            if tag not in ["odd", "even", "empty"]:
                query_id = tag
                break
        
        if not query_id:
            return
        
        # Get the saved query
        saved_query = self.saved_queries_manager.get_query(query_id)
        if not saved_query:
            return
        
        # Schedule tooltip to show after 500ms (prevents flickering)
        def show_delayed_tooltip():
            if self.query_tooltip:
                # Calculate tooltip position (offset from cursor)
                x = event.x_root + 15
                y = event.y_root + 10
                self.query_tooltip.show_tooltip(saved_query.query, x, y)
        
        self.hover_after_id = self.after(500, show_delayed_tooltip)
    
    def on_query_tree_leave(self, event):
        """Handle mouse leaving the queries tree - hide tooltip"""
        # Cancel any pending tooltip
        if self.hover_after_id:
            self.after_cancel(self.hover_after_id)
            self.hover_after_id = None
        
        # Hide tooltip
        if self.query_tooltip:
            self.query_tooltip.hide_tooltip()
    
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
    
    def copy_query_to_clipboard(self, query_id: str):
        """Copy saved query to clipboard"""
        saved_query = self.saved_queries_manager.get_query(query_id)
        if saved_query:
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(saved_query.query)
            self.update()  # Make clipboard change persistent
            
            # Update status
            if hasattr(self.master.master, 'update_status'):
                self.master.master.update_status(f"'{saved_query.title}' copied to clipboard")
    
    def append_query_to_editor(self, query_id: str):
        """Append saved query to the query editor"""
        saved_query = self.saved_queries_manager.get_query(query_id)
        if saved_query and self.on_query_select:
            self.on_query_select(saved_query.query)
            
            # Update status
            if hasattr(self.master.master, 'update_status'):
                self.master.master.update_status(f"'{saved_query.title}' appended to editor")
    
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
    
    def set_connected(self, connected: bool, db_info: str = None):
        """Update connection button states and connection info"""
        if connected:
            # Hide connect button, show disconnect button
            self.connect_btn.pack_forget()
            self.disconnect_btn.pack(side="left", padx=2)
            if db_info:
                self.connection_label.configure(text=db_info, text_color="#3E2723")
        else:
            # Hide disconnect button, show connect button
            self.disconnect_btn.pack_forget()
            self.connect_btn.pack(side="left", padx=2)
            self.connection_label.configure(text="Not connected", text_color="#8B7355")
    
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
                # Basic queries
                context_menu.add_command(
                    label="📊 Show First 100 Rows", 
                    command=lambda: self.show_table_rows(item_name, 100)
                )
                context_menu.add_command(
                    label="🔢 Count All Entries", 
                    command=lambda: self.count_table_entries(item_name)
                )
                context_menu.add_separator()
                
                # Table structure and info
                context_menu.add_command(
                    label="📋 Describe Table Structure", 
                    command=lambda: self.describe_table(item_name)
                )
                context_menu.add_command(
                    label="🔍 Show Table Indexes", 
                    command=lambda: self.show_table_indexes(item_name)
                )
                context_menu.add_command(
                    label="🔗 Show Foreign Keys", 
                    command=lambda: self.show_foreign_keys(item_name)
                )
                context_menu.add_separator()
                
                # Data analysis
                context_menu.add_command(
                    label="📈 Analyze Table Statistics", 
                    command=lambda: self.analyze_table_stats(item_name)
                )
                context_menu.add_command(
                    label="🔍 Find Duplicate Rows", 
                    command=lambda: self.find_duplicate_rows(item_name)
                )
                context_menu.add_separator()
                
                # Quick actions
                context_menu.add_command(
                    label="📝 Generate SELECT Query", 
                    command=lambda: self.generate_select_query(item_name)
                )
                context_menu.add_command(
                    label="📥 Generate INSERT Template", 
                    command=lambda: self.generate_insert_template(item_name)
                )
                context_menu.add_command(
                    label="🔄 Generate UPDATE Template", 
                    command=lambda: self.generate_update_template(item_name)
                )
                context_menu.add_separator()
                
                # Utility
                context_menu.add_command(
                    label="📋 Copy Table Name", 
                    command=lambda: self.copy_to_clipboard(item_name)
                )
                
            elif item_type == "view":
                context_menu.add_command(
                    label="📊 Show First 100 Rows", 
                    command=lambda: self.show_table_rows(item_name, 100)
                )
                context_menu.add_command(
                    label="🔢 Count All Entries", 
                    command=lambda: self.count_table_entries(item_name)
                )
                context_menu.add_separator()
                context_menu.add_command(
                    label="📋 Show View Definition", 
                    command=lambda: self.show_view_definition(item_name)
                )
                context_menu.add_command(
                    label="📝 Generate SELECT Query", 
                    command=lambda: self.generate_select_query(item_name)
                )
                context_menu.add_separator()
                context_menu.add_command(
                    label="📋 Copy View Name", 
                    command=lambda: self.copy_to_clipboard(item_name)
                )
            elif item_type == "column":
                column_name = item_name.split('.')[-1]
                table_name = '.'.join(item_name.split('.')[:-1])
                context_menu.add_command(
                    label="📋 Copy Column Name", 
                    command=lambda: self.copy_to_clipboard(column_name)
                )
                context_menu.add_command(
                    label="🔍 Filter by Column", 
                    command=lambda: self.generate_filter_query(table_name, column_name)
                )
                context_menu.add_command(
                    label="📊 Analyze Column Values", 
                    command=lambda: self.analyze_column_values(table_name, column_name)
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
    
    def show_table_rows(self, table_name: str, limit: int = 100):
        """Show first N rows from a table"""
        query = f"SELECT * FROM {table_name} LIMIT {limit};"
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query)
            # Optionally auto-execute the query
            if hasattr(self.master.master, 'execute_query'):
                self.master.master.execute_query()
    
    def count_table_entries(self, table_name: str):
        """Count total entries in a table"""
        query = f"SELECT COUNT(*) as total_rows FROM {table_name};"
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query)
            # Optionally auto-execute the query
            if hasattr(self.master.master, 'execute_query'):
                self.master.master.execute_query()
    
    def show_table_indexes(self, table_name: str):
        """Show indexes for a table"""
        schema_name, table_only = table_name.split('.') if '.' in table_name else ('public', table_name)
        query = f"""
-- Indexes for table {table_name}
SELECT 
    indexname,
    indexdef,
    tablespace
FROM pg_indexes 
WHERE tablename = '{table_only}'
  AND schemaname = '{schema_name}'
ORDER BY indexname;
"""
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query.strip())
    
    def show_foreign_keys(self, table_name: str):
        """Show foreign key constraints for a table"""
        schema_name, table_only = table_name.split('.') if '.' in table_name else ('public', table_name)
        query = f"""
-- Foreign key constraints for table {table_name}
SELECT 
    conname AS constraint_name,
    a.attname AS column_name,
    cl.relname AS foreign_table_name,
    af.attname AS foreign_column_name
FROM pg_constraint AS c
JOIN pg_class AS l ON l.oid = c.conrelid
JOIN pg_attribute AS a ON a.attrelid = c.conrelid
JOIN pg_class AS f ON f.oid = c.confrelid
JOIN pg_attribute AS af ON af.attrelid = c.confrelid
JOIN pg_class AS cl ON cl.oid = c.confrelid
JOIN pg_namespace AS n ON n.oid = l.relnamespace
WHERE c.contype = 'f'
  AND l.relname = '{table_only}'
  AND n.nspname = '{schema_name}'
  AND a.attnum = ANY(c.conkey)
  AND af.attnum = ANY(c.confkey)
ORDER BY conname, a.attnum;
"""
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query.strip())
    
    def analyze_table_stats(self, table_name: str):
        """Analyze table statistics and show useful information"""
        schema_name, table_only = table_name.split('.') if '.' in table_name else ('public', table_name)
        query = f"""
-- Table statistics for {table_name}
SELECT 
    schemaname,
    tablename,
    attname as column_name,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs
FROM pg_stats 
WHERE tablename = '{table_only}'
  AND schemaname = '{schema_name}'
ORDER BY attname;
"""
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query.strip())
    
    def find_duplicate_rows(self, table_name: str):
        """Generate query to find duplicate rows in a table"""
        query = f"""
-- Find duplicate rows in {table_name}
-- Note: Modify the GROUP BY clause to include the columns you want to check for duplicates
SELECT 
    *,
    COUNT(*) as duplicate_count
FROM {table_name}
GROUP BY 
    -- Add column names here for duplicate detection
    -- Example: column1, column2, column3
    *  -- This groups by all columns (exact duplicates only)
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
"""
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query.strip())
    
    def generate_insert_template(self, table_name: str):
        """Generate an INSERT template for a table"""
        schema_name, table_only = table_name.split('.') if '.' in table_name else ('public', table_name)
        
        # First get the columns for the table
        column_query = f"""
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = '{table_only}'
  AND table_schema = '{schema_name}'
ORDER BY ordinal_position;
"""
        
        # For now, generate a basic template
        query = f"""
-- INSERT template for {table_name}
-- Replace ? with actual values
INSERT INTO {table_name} (
    -- column1,
    -- column2,
    -- column3
) VALUES (
    -- value1,
    -- value2,
    -- value3
);

-- To see the table structure, run:
-- {column_query.strip()}
"""
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query.strip())
    
    def generate_update_template(self, table_name: str):
        """Generate an UPDATE template for a table"""
        query = f"""
-- UPDATE template for {table_name}
-- Replace ? with actual values and conditions
UPDATE {table_name}
SET 
    -- column1 = ?,
    -- column2 = ?,
    -- column3 = ?
WHERE 
    -- Add WHERE conditions here
    -- Example: id = ?
    -- AND status = ?
;

-- Always test with SELECT first:
-- SELECT * FROM {table_name} WHERE your_conditions_here;
"""
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query.strip())
    
    def show_view_definition(self, view_name: str):
        """Show the definition of a view"""
        schema_name, view_only = view_name.split('.') if '.' in view_name else ('public', view_name)
        query = f"""
-- View definition for {view_name}
SELECT definition 
FROM pg_views 
WHERE viewname = '{view_only}'
  AND schemaname = '{schema_name}';
"""
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query.strip())
    
    def analyze_column_values(self, table_name: str, column_name: str):
        """Analyze values in a specific column"""
        query = f"""
-- Column analysis for {table_name}.{column_name}
SELECT 
    '{column_name}' as column_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT {column_name}) as unique_values,
    COUNT({column_name}) as non_null_values,
    COUNT(*) - COUNT({column_name}) as null_values,
    MIN({column_name}) as min_value,
    MAX({column_name}) as max_value
FROM {table_name}

UNION ALL

-- Top 10 most frequent values
SELECT 
    'Top Values:' as column_name,
    NULL, NULL, NULL, NULL,
    {column_name}::text as min_value,
    COUNT(*)::text as max_value
FROM {table_name}
WHERE {column_name} IS NOT NULL
GROUP BY {column_name}
ORDER BY COUNT(*) DESC
LIMIT 10;
"""
        if hasattr(self.master.master, 'query_panel'):
            self.master.master.query_panel.set_query(query.strip())
    
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
        dialog.grid_rowconfigure(3, weight=1)  # Query frame should expand (updated from row 2)
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
            font=ctk.CTkFont(size=12),
            corner_radius=6
        )
        title_entry.pack(fill="x", pady=5)
        
        # Shortcut entry
        shortcut_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        shortcut_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            shortcut_frame,
            text="Shortcut (optional):",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")
        
        shortcut_entry = ctk.CTkEntry(
            shortcut_frame,
            placeholder_text="e.g., top_users (use {{top_users}} in queries)",
            height=35,
            font=ctk.CTkFont(size=12),
            corner_radius=6
        )
        shortcut_entry.pack(fill="x", pady=5)
        
        # Help text for shortcuts
        help_label = ctk.CTkLabel(
            shortcut_frame,
            text="💡 Shortcuts let you use {{shortcut}} in queries to insert this saved query",
            font=ctk.CTkFont(size=10),
            text_color="#6B5E45"
        )
        help_label.pack(anchor="w", pady=(2, 0))
        
        # Query text area
        query_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        query_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
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
        button_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(10, 20))  # Updated from row 3
        button_frame.grid_propagate(False)  # Keep fixed height
        
        def save_query():
            query = query_text.get("1.0", "end-1c").strip()
            title = title_entry.get().strip()
            shortcut = shortcut_entry.get().strip()
            
            if not query:
                messagebox.showwarning("Empty Query", "Please enter a SQL query")
                return
            
            # Validate shortcut if provided
            if shortcut:
                if not self.saved_queries_manager.is_shortcut_valid(shortcut):
                    messagebox.showwarning(
                        "Invalid Shortcut", 
                        "Shortcut can only contain letters, numbers, and underscores.\n" +
                        "It must start with a letter or underscore.\n\n" +
                        "Examples: top_users, daily_report, stats"
                    )
                    return
                
                # Check if shortcut already exists
                if self.saved_queries_manager.get_query_by_shortcut(shortcut):
                    messagebox.showwarning(
                        "Shortcut Exists", 
                        f"The shortcut '{shortcut}' is already used by another query.\n" +
                        "Please choose a different shortcut."
                    )
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
            
            # Save the query with shortcut
            try:
                self.saved_queries_manager.add_query(title, query, shortcut)
                self.refresh_saved_queries()
                dialog.destroy()
                
                # Show success message
                if hasattr(self.master.master, 'update_status'):
                    shortcut_msg = f" (shortcut: {shortcut})" if shortcut else ""
                    self.master.master.update_status(f"Saved query: {title}{shortcut_msg}")
            except ValueError as e:
                messagebox.showerror("Save Error", str(e))
        
        # Cancel button (left side)
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=120,
            height=36,
            fg_color="#E8DFD0",
            hover_color="#D9CDBF",
            text_color="#3E2723",
            corner_radius=6
        )
        cancel_btn.pack(side="left", padx=5, pady=10)
        
        # Save button (right side)
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Query",
            command=save_query,
            width=120,
            height=36,
            corner_radius=6
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
    
    # ===== VARIABLES METHODS =====
    
    def refresh_saved_variables(self):
        """Refresh the saved variables list in table format"""
        # Reload variables from disk
        self.saved_variables_manager.load_variables()
        
        # Clear existing items
        for item in self.variables_tree.get_children():
            self.variables_tree.delete(item)
        
        # Get all saved variables
        variables = self.saved_variables_manager.get_all_variables()
        
        if not variables:
            # Show empty state message
            self.variables_tree.insert("", "end", values=("No saved variables yet - Click ➕ to add", "", ""), tags=("empty",))
            self.variables_tree.tag_configure("empty", foreground="#8B7355", font=("Segoe UI", 10, "italic"))
        else:
            # Add each saved variable as a row with alternating colors
            for i, (var_name, var_value) in enumerate(sorted(variables.items())):
                tag = "odd" if i % 2 == 1 else "even"
                
                # Store variable name and value in tags (value not displayed in column)
                item_id = self.variables_tree.insert("", "end", 
                                                     values=(f"💾 {var_name}", "📋", "🗑️"), 
                                                     tags=(tag, f"var_{var_name}"))
            
            # Configure row tags for alternating colors
            self.variables_tree.tag_configure("odd", background="#F5EFE7")
            self.variables_tree.tag_configure("even", background="#EBE3D5")
    
    def on_variable_tree_click(self, event):
        """Handle single click on variables tree"""
        region = self.variables_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.variables_tree.identify_column(event.x)
            item = self.variables_tree.identify_row(event.y)
            
            if item:
                # Get variable name from tags
                tags = self.variables_tree.item(item, "tags")
                var_name = None
                for tag in tags:
                    if tag.startswith("var_"):
                        var_name = tag[4:]  # Remove "var_" prefix
                        break
                
                if var_name:
                    # Column #2 is copy button (📋)
                    if column == "#2":
                        self.copy_variable_to_clipboard(var_name)
                        self.flash_variable_row(item)
                    # Column #3 is delete button (🗑️)
                    elif column == "#3":
                        self.confirm_delete_variable(var_name)
    
    def on_variable_tree_double_click(self, event):
        """Handle double-click on variable to copy as {{variable_name}}"""
        item = self.variables_tree.selection()
        if not item:
            return
        
        # Get variable name from tags
        tags = self.variables_tree.item(item[0], "tags")
        for tag in tags:
            if tag.startswith("var_"):
                var_name = tag[4:]  # Remove "var_" prefix
                
                # Copy as {{variable_name}} for use in queries
                variable_placeholder = f"{{{{{var_name}}}}}"
                self.clipboard_clear()
                self.clipboard_append(variable_placeholder)
                self.update()
                
                # Visual feedback
                self.flash_variable_row(item[0])
                
                if hasattr(self.master.master, 'update_status'):
                    self.master.master.update_status(f"'{variable_placeholder}' copied to clipboard")
                break
    
    def on_variable_tree_right_click(self, event):
        """Handle right-click on variable"""
        item = self.variables_tree.identify_row(event.y)
        if not item:
            return
        
        self.variables_tree.selection_set(item)
        
        # Get variable name from tags
        tags = self.variables_tree.item(item, "tags")
        var_name = None
        for tag in tags:
            if tag.startswith("var_"):
                var_name = tag[4:]
                break
        
        if not var_name:
            return
        
        # Create context menu
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.configure(
            background="#F5EFE7",
            foreground="#3E2723",
            activebackground="#9B8F5E",
            activeforeground="white"
        )
        
        context_menu.add_command(
            label="📋 Copy Value",
            command=lambda: self.copy_variable_to_clipboard(var_name)
        )
        
        context_menu.add_command(
            label="🔤 Copy as {{variable}}",
            command=lambda: self.copy_variable_placeholder(var_name)
        )
        
        context_menu.add_separator()
        
        context_menu.add_command(
            label="✏️ Edit Variable",
            command=lambda: self.edit_variable(var_name)
        )
        
        context_menu.add_command(
            label="🗑️ Delete Variable",
            command=lambda: self.confirm_delete_variable(var_name)
        )
        
        # Show menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def flash_variable_row(self, item_id):
        """Flash a variable row to provide visual feedback"""
        original_tags = self.variables_tree.item(item_id, "tags")
        self.variables_tree.item(item_id, tags=("flash",))
        self.variables_tree.tag_configure("flash", background="#9B8F5E", foreground="white")
        
        def restore_tags():
            self.variables_tree.item(item_id, tags=original_tags)
        
        self.after(300, restore_tags)
    
    def copy_variable_to_clipboard(self, var_name: str):
        """Copy variable value to clipboard"""
        var_value = self.saved_variables_manager.get_variable(var_name)
        if var_value is not None:
            self.clipboard_clear()
            self.clipboard_append(var_value)
            self.update()
            
            if hasattr(self.master.master, 'update_status'):
                self.master.master.update_status(f"Variable '{var_name}' value copied to clipboard")
    
    def copy_variable_placeholder(self, var_name: str):
        """Copy variable as {{variable_name}} for use in queries"""
        placeholder = f"{{{{{var_name}}}}}"
        self.clipboard_clear()
        self.clipboard_append(placeholder)
        self.update()
        
        if hasattr(self.master.master, 'update_status'):
            self.master.master.update_status(f"'{placeholder}' copied to clipboard")
    
    def confirm_delete_variable(self, var_name: str):
        """Confirm and delete a variable"""
        if messagebox.askyesno(
            "Delete Variable",
            f"Are you sure you want to delete variable '{var_name}'?",
            parent=self
        ):
            self.delete_variable(var_name)
    
    def delete_variable(self, var_name: str):
        """Delete a saved variable"""
        if self.saved_variables_manager.delete_variable(var_name):
            self.refresh_saved_variables()
            
            if hasattr(self.master.master, 'update_status'):
                self.master.master.update_status(f"Deleted variable: {var_name}")
    
    def show_add_variable_dialog(self):
        """Show dialog to add a new variable"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Variable")
        dialog.geometry("500x350")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (175)
        dialog.geometry(f"+{x}+{y}")
        
        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text="Add New Variable",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=20, padx=20, anchor="w")
        
        # Variable name
        name_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        name_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            name_frame,
            text="Variable Name:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")
        
        name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="e.g., start_date, user_id, limit",
            height=35,
            font=ctk.CTkFont(size=12),
            corner_radius=6
        )
        name_entry.pack(fill="x", pady=5)
        
        # Variable value
        value_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        value_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            value_frame,
            text="Variable Value:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")
        
        value_entry = ctk.CTkEntry(
            value_frame,
            placeholder_text="e.g., 2024-01-01, 12345, 100",
            height=35,
            font=ctk.CTkFont(size=12),
            corner_radius=6
        )
        value_entry.pack(fill="x", pady=5)
        
        # Info label
        info_label = ctk.CTkLabel(
            dialog,
            text="Use in queries as: {{variable_name}}",
            font=ctk.CTkFont(size=10),
            text_color="#8B7355"
        )
        info_label.pack(pady=10)
        
        # Spacer to push buttons to bottom
        spacer = ctk.CTkFrame(dialog, fg_color="transparent", height=20)
        spacer.pack(fill="both", expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20), side="bottom")
        
        def save_variable():
            var_name = name_entry.get().strip()
            var_value = value_entry.get().strip()
            
            if not var_name:
                messagebox.showwarning("Missing Name", "Please enter a variable name")
                return
            
            if not var_value:
                messagebox.showwarning("Missing Value", "Please enter a variable value")
                return
            
            # Validate variable name (only letters, numbers, underscore)
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                messagebox.showwarning(
                    "Invalid Variable Name", 
                    "Variable name can only contain letters, numbers, and underscores.\n" +
                    "It must start with a letter or underscore.\n\n" +
                    "Examples: start_date, user_id, limit_value"
                )
                return
            
            # Save the variable
            if self.saved_variables_manager.add_variable(var_name, var_value):
                self.refresh_saved_variables()
                dialog.destroy()
                
                if hasattr(self.master.master, 'update_status'):
                    self.master.master.update_status(f"Added variable: {var_name}")
            else:
                messagebox.showerror("Error", "Failed to save variable")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=120,
            height=36,
            fg_color="#E8DFD0",
            hover_color="#D9CDBF",
            text_color="#3E2723",
            corner_radius=6
        )
        cancel_btn.pack(side="left", padx=5)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Add Variable",
            command=save_variable,
            width=120,
            height=36,
            corner_radius=6
        )
        save_btn.pack(side="right", padx=5)
        
        # Focus on name entry
        name_entry.focus()
    
    def edit_variable(self, var_name: str):
        """Edit an existing variable"""
        current_value = self.saved_variables_manager.get_variable(var_name)
        if current_value is None:
            return
        
        # Show input dialog
        new_value = simpledialog.askstring(
            "Edit Variable",
            f"Edit value for '{var_name}':",
            initialvalue=current_value,
            parent=self
        )
        
        if new_value is not None:
            new_value = new_value.strip()
            if not new_value:
                messagebox.showwarning("Missing Value", "Please enter a variable value")
                return
                
            if self.saved_variables_manager.add_variable(var_name, new_value):
                self.refresh_saved_variables()
                
                if hasattr(self.master.master, 'update_status'):
                    self.master.master.update_status(f"Updated variable: {var_name}")
    
    def get_all_variables(self):
        """Get all saved variables for autocomplete"""
        return self.saved_variables_manager.get_all_variables()
    
    def substitute_variables_in_query(self, query: str):
        """Substitute variables in query before execution"""
        return self.saved_variables_manager.substitute_variables(query)
    
    def get_all_query_shortcuts(self):
        """Get all saved query shortcuts for autocomplete"""
        return self.saved_queries_manager.get_all_shortcuts()
    
    def get_query_by_shortcut(self, shortcut: str):
        """Get saved query by shortcut"""
        return self.saved_queries_manager.get_query_by_shortcut(shortcut)
    
    def substitute_query_shortcuts_in_query(self, query: str):
        """Substitute query shortcuts in query before execution"""
        return self.saved_queries_manager.substitute_query_shortcuts(query)
    
    def on_variable_tree_motion(self, event):
        """Show tooltip with variable value on hover"""
        item = self.variables_tree.identify_row(event.y)
        
        if item:
            # Get variable name from tags
            tags = self.variables_tree.item(item, "tags")
            var_name = None
            for tag in tags:
                if tag.startswith("var_"):
                    var_name = tag[4:]
                    break
            
            if var_name:
                var_value = self.saved_variables_manager.get_variable(var_name)
                if var_value is not None:
                    self.show_variable_tooltip(var_name, var_value, event.x_root, event.y_root)
                    return
        
        # No item under cursor, hide tooltip
        self.hide_variable_tooltip()
    
    def on_variable_tree_leave(self, event):
        """Hide tooltip when mouse leaves the tree"""
        self.hide_variable_tooltip()
    
    def show_variable_tooltip(self, var_name: str, var_value: str, x: int, y: int):
        """Show tooltip with variable value"""
        # Hide existing tooltip if any
        self.hide_variable_tooltip()
        
        # Create tooltip window
        self.variable_tooltip_window = tk.Toplevel(self)
        self.variable_tooltip_window.wm_overrideredirect(True)
        self.variable_tooltip_window.wm_geometry(f"+{x + 10}+{y + 10}")
        
        # Create frame with border
        frame = tk.Frame(
            self.variable_tooltip_window,
            background="#3E2723",
            borderwidth=1,
            relief="solid"
        )
        frame.pack()
        
        # Create label with value
        label = tk.Label(
            frame,
            text=f"{var_name} = {var_value}",
            background="#F5EFE7",
            foreground="#3E2723",
            font=("Segoe UI", 10),
            padx=10,
            pady=6,
            justify=tk.LEFT
        )
        label.pack()
    
    def hide_variable_tooltip(self):
        """Hide the variable tooltip"""
        if self.variable_tooltip_window:
            self.variable_tooltip_window.destroy()
            self.variable_tooltip_window = None
    
    def apply_theme(self):
        """Apply current theme to schema browser components"""
        try:
            # Update main frame
            self.configure(fg_color=theme_manager.get_color("background.main"))
            
            # Reconfigure tree styling with new theme colors
            self.configure_tree_style()
            
            # Update header frames if they exist
            if hasattr(self, 'queries_header'):
                self.queries_header.configure(fg_color=theme_manager.get_color("background.secondary"))
            
            if hasattr(self, 'variables_header'):
                self.variables_header.configure(fg_color=theme_manager.get_color("background.secondary"))
            
            if hasattr(self, 'schema_header'):
                self.schema_header.configure(fg_color=theme_manager.get_color("background.secondary"))
                
            # Update all frames and child components
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    widget.configure(fg_color=theme_manager.get_color("background.secondary"))
                    
                    # Update child widgets
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkLabel):
                            child.configure(text_color=theme_manager.get_color("text.primary"))
                        elif isinstance(child, ctk.CTkButton):
                            child.configure(
                                fg_color=theme_manager.get_color("buttons.primary_bg"),
                                hover_color=theme_manager.get_color("buttons.primary_hover"),
                                text_color=theme_manager.get_color("buttons.primary_text")
                            )
                        elif isinstance(child, ctk.CTkFrame):
                            child.configure(fg_color=theme_manager.get_color("background.secondary"))
                            
            # Update content frames specifically
            if hasattr(self, 'schema_content_frame'):
                for child in self.schema_content_frame.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        child.configure(fg_color=theme_manager.get_color("background.secondary"))
                        
        except Exception as e:
            print(f"Error applying theme to schema browser: {e}")