"""
Main window for PgWarp application
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Dict, Any, Optional
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import DatabaseConnection, ConnectionManager
from ai.assistant import PgWarpAI
from utils.helpers import setup_logging
from ui.connection_dialog import ConnectionDialog
from ui.query_panel import QueryPanel
from ui.schema_browser import SchemaBrowser
from ui.psql_terminal import PSQLTerminal

# Set appearance mode and color theme
ctk.set_appearance_mode("light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# Configure CTk default colors to warm beige/tan theme with olive buttons
ctk.ThemeManager.theme["CTkFrame"]["fg_color"] = ["#F5EFE7", "#F5EFE7"]
ctk.ThemeManager.theme["CTk"]["fg_color"] = ["#F5EFE7", "#F5EFE7"]
ctk.ThemeManager.theme["CTkButton"]["fg_color"] = ["#9B8F5E", "#9B8F5E"]
ctk.ThemeManager.theme["CTkButton"]["hover_color"] = ["#87795A", "#87795A"]
ctk.ThemeManager.theme["CTkButton"]["text_color"] = ["white", "white"]

# Remove grey backgrounds from all components
ctk.ThemeManager.theme["CTkScrollableFrame"]["fg_color"] = ["#F5EFE7", "#F5EFE7"]
ctk.ThemeManager.theme["CTkEntry"]["fg_color"] = ["#F5EFE7", "#F5EFE7"]
ctk.ThemeManager.theme["CTkEntry"]["border_color"] = ["#E8DFD0", "#E8DFD0"]

class PgWarpApp(ctk.CTk):
    """Main application window for PgWarp"""
    
    def __init__(self):
        super().__init__()
        
        # Set up logging
        self.logger = setup_logging()
        
        # Initialize core components
        self.db_connection = DatabaseConnection()
        self.connection_manager = ConnectionManager()
        self.ai_assistant = None
        self.current_schema = {}
        
        # Configure main window
        self.title("PgWarp - AI-Powered PostgreSQL Client")
        self.geometry("1600x1100")
        self.minsize(1400, 950)
        
        # Configure window for better text display
        self.tk.call('tk', 'scaling', 1.0)  # Ensure consistent scaling
        
        # Set window icon (you can add an icon file later)
        # self.iconbitmap("assets/icon.ico")
        
        # Configure grid weights
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create UI components
        self.create_menu_bar()
        self.create_toolbar()
        self.create_main_interface()
        self.create_status_bar()
        
        # Initialize AI assistant
        self.init_ai_assistant()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.logger.info("PgWarp application initialized")
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Connection...", command=self.show_connection_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Connection menu
        connection_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Connection", menu=connection_menu)
        connection_menu.add_command(label="Connect...", command=self.show_connection_dialog)
        connection_menu.add_command(label="Disconnect", command=self.disconnect_database)
        connection_menu.add_separator()
        connection_menu.add_command(label="Refresh Schema", command=self.refresh_schema)
        
        # Query menu
        query_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Query", menu=query_menu)
        query_menu.add_command(label="Execute Query", command=self.execute_current_query)
        query_menu.add_command(label="Clear Query", command=self.clear_query)
        query_menu.add_separator()
        query_menu.add_command(label="Format Query", command=self.format_current_query)
        
        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_command(label="Generate Query...", command=self.show_ai_dialog)
        ai_menu.add_command(label="Explain Query", command=self.explain_current_query)
        ai_menu.add_separator()
        ai_menu.add_command(label="Clear Chat History", command=self.clear_ai_history)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_toolbar(self):
        """Create the main toolbar"""
        self.toolbar_frame = ctk.CTkFrame(self, height=45)
        self.toolbar_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.toolbar_frame.grid_columnconfigure(4, weight=1)  # Make connection info expandable
        
        # Connection buttons
        self.connect_btn = ctk.CTkButton(
            self.toolbar_frame, 
            text="Connect", 
            command=self.show_connection_dialog,
            width=120,
            height=28
        )
        self.connect_btn.grid(row=0, column=0, padx=(10, 8), pady=8)
        
        self.disconnect_btn = ctk.CTkButton(
            self.toolbar_frame, 
            text="Disconnect", 
            command=self.disconnect_database,
            width=120,
            height=28,
            state="disabled"
        )
        self.disconnect_btn.grid(row=0, column=1, padx=8, pady=8)
        
        # Separator
        separator = ctk.CTkFrame(self.toolbar_frame, width=2, height=28)
        separator.grid(row=0, column=2, padx=15, pady=8)
        
        # Execute button
        self.execute_btn = ctk.CTkButton(
            self.toolbar_frame, 
            text="Execute", 
            command=self.execute_current_query,
            width=120,
            height=28,
            state="disabled"
        )
        self.execute_btn.grid(row=0, column=3, padx=8, pady=8)
        
        # Connection info
        self.connection_info = ctk.CTkLabel(
            self.toolbar_frame, 
            text="Not connected",
            font=ctk.CTkFont(size=11)
        )
        self.connection_info.grid(row=0, column=4, padx=20, pady=8, sticky="w")
        
        # AI indicator
        self.ai_status = ctk.CTkLabel(
            self.toolbar_frame, 
            text="AI: Not configured",
            font=ctk.CTkFont(size=11),
            text_color="#FFFFFF"
        )
        self.ai_status.grid(row=0, column=5, padx=10, pady=8)
    
    def create_main_interface(self):
        """Create the main interface with panels"""
        # Create main paned window
        self.main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6)
        self.main_paned.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=8)
        
        # Left panel - Schema browser
        self.left_frame = ctk.CTkFrame(self.main_paned, width=350)
        self.main_paned.add(self.left_frame, width=350, minsize=280)
        
        # Schema browser
        self.schema_browser = SchemaBrowser(self.left_frame, self.on_table_select)
        self.schema_browser.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Right panel - Query and results
        self.right_paned = tk.PanedWindow(self.main_paned, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=6)
        self.main_paned.add(self.right_paned, minsize=500)
        
        # Query panel
        self.query_frame = ctk.CTkFrame(self.right_paned, height=400)
        self.right_paned.add(self.query_frame, height=400, minsize=250)
        
        # Create tabbed interface for query tools
        self.notebook = ctk.CTkTabview(self.query_frame, fg_color="#F5EFE7", 
                                       segmented_button_fg_color="#E8DFD0",
                                       segmented_button_selected_color="#9B8F5E",
                                       segmented_button_selected_hover_color="#87795A",
                                       segmented_button_unselected_color="#E8DFD0",
                                       segmented_button_unselected_hover_color="#D9CDBF")
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Query tool tab
        self.notebook.add("Query Tool")
        self.query_panel = QueryPanel(
            self.notebook.tab("Query Tool"), 
            self.execute_query_callback,
            self.ai_generate_callback,
            self.display_results_callback
        )
        self.query_panel.pack(fill="both", expand=True)
        
        # PSQL terminal tab
        self.notebook.add("PSQL Terminal")
        self.psql_terminal = PSQLTerminal(self.notebook.tab("PSQL Terminal"))
        self.psql_terminal.pack(fill="both", expand=True)
        
        # Results panel
        self.results_frame = ctk.CTkFrame(self.right_paned, height=400)
        self.right_paned.add(self.results_frame, height=400, minsize=200)
        
        # Create results display
        self.create_results_display()
    
    def create_results_display(self):
        """Create the results display area"""
        # Configure grid
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(1, weight=1)
        
        # Results header
        results_header = ctk.CTkFrame(self.results_frame, height=45)
        results_header.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        results_header.grid_columnconfigure(0, weight=1)
        
        self.results_label = ctk.CTkLabel(
            results_header, 
            text="Query results will appear here", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.results_label.grid(row=0, column=0, sticky="w", padx=15, pady=8)
        
        # Export buttons frame
        export_frame = ctk.CTkFrame(results_header, fg_color="transparent")
        export_frame.grid(row=0, column=1, padx=15, pady=8)
        
        # CSV Export button
        self.export_csv_btn = ctk.CTkButton(
            export_frame, 
            text="📄 CSV", 
            command=self.export_csv,
            width=80,
            height=32,
            state="disabled"
        )
        self.export_csv_btn.grid(row=0, column=0, padx=(0, 5))
        
        # Excel Export button
        self.export_excel_btn = ctk.CTkButton(
            export_frame, 
            text="📊 Excel", 
            command=self.export_excel,
            width=80,
            height=32,
            state="disabled",
            fg_color="#9B8F5E",
            hover_color="#87795A"
        )
        self.export_excel_btn.grid(row=0, column=1, padx=(5, 0))
        
        # Results table frame
        table_frame = ctk.CTkFrame(self.results_frame)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # Create treeview for results
        self.results_tree = ttk.Treeview(
            table_frame, 
            show="headings",
            selectmode="extended"
        )
        
        # Scrollbars for results
        results_v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.results_tree.yview)
        results_h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=results_v_scroll.set, xscrollcommand=results_h_scroll.set)
        
        # Pack results table and scrollbars
        self.results_tree.grid(row=0, column=0, sticky="nsew", padx=(1, 0), pady=(1, 0))
        results_v_scroll.grid(row=0, column=1, sticky="ns", pady=(1, 0))
        results_h_scroll.grid(row=1, column=0, sticky="ew", padx=(1, 0))
        
        # Configure results styling
        self.configure_results_style()
        
        # Current results data
        self.current_results = []
        self.current_columns = []
    
    def create_status_bar(self):
        """Create the status bar"""
        self.status_frame = ctk.CTkFrame(self, height=30)
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="Ready", 
            font=ctk.CTkFont(size=11)
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
    
    def configure_results_style(self):
        """Configure results table styling"""
        style = ttk.Style()
        
        # Configure treeview colors to match warm beige theme
        style.configure("Treeview", 
                        background="#F5EFE7",
                        foreground="#3E2723",
                        fieldbackground="#F5EFE7",
                        borderwidth=1,
                        font=("Consolas", 11),
                        rowheight=25)
        style.configure("Treeview.Heading",
                        background="#E8DFD0",
                        foreground="#3E2723",
                        borderwidth=1,
                        relief="raised",
                        font=("Consolas", 11, "bold"))
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
    
    def display_results_callback(self, results, columns):
        """Callback to display results from query panel"""
        self.display_results(results, columns)
    
    def display_results(self, results, columns):
        """Display query results in the main results area"""
        # Clear existing results
        self.clear_results()
        
        if not results or not columns:
            self.results_label.configure(text="Query results will appear here")
            return
        
        # Store current results
        self.current_results = results
        self.current_columns = columns
        
        # Configure columns
        self.results_tree["columns"] = columns
        
        # Set column headings and widths
        for col in columns:
            self.results_tree.heading(col, text=col, anchor="w")
            # Calculate column width based on content
            header_width = len(col) * 12
            max_width = max(120, header_width)
            
            if results:
                # Sample first few rows to estimate width
                sample_rows = results[:min(20, len(results))]
                for row in sample_rows:
                    if col in row and row[col] is not None:
                        content_length = len(str(row[col]))
                        if content_length <= 10:
                            content_width = content_length * 12
                        elif content_length <= 50:
                            content_width = content_length * 10
                        else:
                            content_width = 300
                        max_width = max(max_width, content_width)
            
            # Cap maximum and minimum widths
            max_width = min(max(max_width, 80), 400)
            self.results_tree.column(col, width=max_width, anchor="w", minwidth=80)
        
        # Insert data
        for i, row in enumerate(results):
            values = []
            for col in columns:
                value = row.get(col, "")
                # Handle None values
                if value is None:
                    value = "[NULL]"
                # Handle different data types
                elif isinstance(value, (list, dict)):
                    value = str(value)
                    if len(value) > 200:
                        value = value[:197] + "..."
                # Truncate very long text values for display
                elif isinstance(value, str):
                    if len(value) > 200:
                        value = value[:197] + "..."
                    # Replace newlines and tabs for better display
                    value = value.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
                # Handle other types
                else:
                    value = str(value)
                    if len(value) > 200:
                        value = value[:197] + "..."
                
                values.append(value)
            
            # Add alternating row colors by using tags
            tag = "odd" if i % 2 == 1 else "even"
            self.results_tree.insert("", "end", values=values, tags=(tag,))
        
        # Configure row tags for better readability
        self.results_tree.tag_configure("odd", background="#F5EFE7")
        self.results_tree.tag_configure("even", background="#EBE3D5")
        
        # Update results label
        self.results_label.configure(text=f"Results ({len(results)} rows)")
        
        # Enable export buttons
        self.export_csv_btn.configure(state="normal" if results else "disabled")
        self.export_excel_btn.configure(state="normal" if results else "disabled")
    
    def clear_results(self):
        """Clear the results table"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.results_tree["columns"] = ()
        self.results_label.configure(text="Query results will appear here")
        self.export_csv_btn.configure(state="disabled")
        self.export_excel_btn.configure(state="disabled")
        
        # Clear stored data
        self.current_results = []
        self.current_columns = []
    
    def export_csv(self):
        """Export query results to CSV"""
        if not self.current_results or not self.current_columns:
            messagebox.showwarning("No Results", "No query results to export")
            return
        
        from tkinter import filedialog
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Results"
        )
        
        if not filename:
            return
        
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.current_columns)
                writer.writeheader()
                
                for row in self.current_results:
                    # Handle None values and convert all to strings
                    clean_row = {}
                    for col in self.current_columns:
                        value = row.get(col)
                        clean_row[col] = "" if value is None else str(value)
                    writer.writerow(clean_row)
            
            messagebox.showinfo("Export Complete", f"Results exported to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{e}")
    
    def export_excel(self):
        """Export query results to Excel"""
        if not self.current_results or not self.current_columns:
            messagebox.showwarning("No Results", "No query results to export")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Export Results to Excel"
        )
        
        if not filename:
            return
        
        try:
            # Convert results to DataFrame
            data = []
            for row in self.current_results:
                clean_row = {}
                for col in self.current_columns:
                    value = row.get(col)
                    clean_row[col] = value  # Keep original types for Excel
                data.append(clean_row)
            
            df = pd.DataFrame(data, columns=self.current_columns)
            
            # Create Excel writer with formatting
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Write data to Excel
                df.to_excel(writer, sheet_name='Query Results', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Query Results']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)  # Max width of 50
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Style the header row
                from openpyxl.styles import Font, PatternFill, Alignment
                
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="0078D4", end_color="0078D4", fill_type="solid")
                center_alignment = Alignment(horizontal="center", vertical="center")
                
                for cell in worksheet[1]:  # Header row
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = center_alignment
            
            messagebox.showinfo("Export Complete", f"Results exported to Excel:\n{filename}")
            
        except ImportError:
            messagebox.showerror("Export Error", "Excel export requires 'openpyxl' package.\nPlease install it with: pip install openpyxl")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results to Excel:\n{e}")
    
    def init_ai_assistant(self):
        """Initialize the AI assistant"""
        try:
            self.ai_assistant = PgWarpAI()
            self.ai_status.configure(text="AI: Ready", text_color="#6B8E23")
            self.logger.info("AI assistant initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI assistant: {e}")
            self.ai_status.configure(text="AI: Error", text_color="#D2691E")
            messagebox.showwarning(
                "AI Assistant", 
                f"Failed to initialize AI assistant:\n{e}\n\n"
                "Please check your GOOGLE_API_KEY in .env file"
            )
    
    def show_connection_dialog(self):
        """Show connection dialog"""
        dialog = ConnectionDialog(self, self.connection_manager)
        self.wait_window(dialog)
        
        # Check if a connection was made
        if hasattr(dialog, 'selected_connection') and dialog.selected_connection:
            self.connect_to_database(dialog.selected_connection)
    
    def connect_to_database(self, connection_config: Dict[str, Any]):
        """Connect to database with given configuration"""
        try:
            self.update_status("Connecting to database...")
            
            # Attempt connection
            self.db_connection.connect(
                host=connection_config['host'],
                port=connection_config['port'],
                database=connection_config['database'],
                username=connection_config['username'],
                password=connection_config['password']
            )
            
            # Update UI
            conn_text = f"Connected to {connection_config['database']}@{connection_config['host']}:{connection_config['port']}"
            self.connection_info.configure(text=conn_text)
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.execute_btn.configure(state="normal")
            
            # Load schema
            self.refresh_schema()
            
            # Update PSQL terminal
            self.psql_terminal.set_connection(self.db_connection)
            
            self.update_status("Connected successfully")
            self.logger.info(f"Connected to database: {connection_config['database']}")
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect to database:\n{e}")
            self.update_status("Connection failed")
    
    def disconnect_database(self):
        """Disconnect from current database"""
        try:
            self.db_connection.disconnect()
            
            # Update UI
            self.connection_info.configure(text="Not connected")
            self.connect_btn.configure(state="normal")
            self.disconnect_btn.configure(state="disabled")
            self.execute_btn.configure(state="disabled")
            
            # Clear schema
            self.current_schema = {}
            self.schema_browser.clear_schema()
            
            # Clear AI schema context
            if self.ai_assistant:
                self.ai_assistant.set_database_schema({})
            
            # Update PSQL terminal
            self.psql_terminal.clear_connection()
            
            self.update_status("Disconnected")
            self.logger.info("Disconnected from database")
            
        except Exception as e:
            self.logger.error(f"Disconnect failed: {e}")
            messagebox.showerror("Disconnect Error", f"Failed to disconnect:\n{e}")
    
    def refresh_schema(self):
        """Refresh database schema"""
        if not self.db_connection.is_connected():
            messagebox.showwarning("Not Connected", "Please connect to a database first")
            return
        
        try:
            self.update_status("Loading database schema...")
            
            # Get schema from database
            self.current_schema = self.db_connection.get_database_schema()
            
            # Update schema browser
            self.schema_browser.update_schema(self.current_schema)
            
            # Update AI assistant with schema context
            if self.ai_assistant:
                self.ai_assistant.set_database_schema(self.current_schema)
            
            table_count = len(self.current_schema.get('tables', {}))
            view_count = len(self.current_schema.get('views', {}))
            self.update_status(f"Schema loaded: {table_count} tables, {view_count} views")
            
        except Exception as e:
            self.logger.error(f"Schema refresh failed: {e}")
            messagebox.showerror("Schema Error", f"Failed to load database schema:\n{e}")
            self.update_status("Schema load failed")
    
    def execute_current_query(self):
        """Execute the current query from query panel"""
        if hasattr(self.query_panel, 'execute_query'):
            self.query_panel.execute_query()
    
    def clear_query(self):
        """Clear the current query"""
        if hasattr(self.query_panel, 'clear_query'):
            self.query_panel.clear_query()
    
    def format_current_query(self):
        """Format the current query"""
        if hasattr(self.query_panel, 'format_query'):
            self.query_panel.format_query()
    
    def show_ai_dialog(self):
        """Show AI query generation dialog"""
        if not self.ai_assistant:
            messagebox.showwarning("AI Not Available", "AI assistant is not configured")
            return
        
        # This would open an AI chat dialog - simplified for now
        user_input = tk.simpledialog.askstring(
            "AI Query Generator",
            "Describe what you want to query:"
        )
        
        if user_input and hasattr(self.query_panel, 'generate_with_ai'):
            self.query_panel.generate_with_ai(user_input)
    
    def explain_current_query(self):
        """Explain the current query using AI"""
        if hasattr(self.query_panel, 'explain_query'):
            self.query_panel.explain_query()
    
    def clear_ai_history(self):
        """Clear AI conversation history"""
        if self.ai_assistant:
            self.ai_assistant.clear_conversation_history()
            messagebox.showinfo("AI History", "Conversation history cleared")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """PgWarp - AI-Powered PostgreSQL Client

Version: 1.0.0

A modern desktop application that brings AI assistance to PostgreSQL database management.

Features:
• AI-powered query generation
• Visual schema browser
• Advanced query editor
• Built-in PSQL terminal
• Connection management

Built with Python, CustomTkinter, and LangChain.
"""
        messagebox.showinfo("About PgWarp", about_text)
    
    def execute_query_callback(self, query: str):
        """Callback for executing queries from query panel"""
        if not self.db_connection.is_connected():
            return None, "Not connected to database"
        
        try:
            results, columns = self.db_connection.execute_query(query)
            return results, columns
        except Exception as e:
            return None, str(e)
    
    def ai_generate_callback(self, user_input: str):
        """Callback for AI query generation"""
        if not self.ai_assistant:
            return None, "AI assistant not available"
        
        try:
            result = self.ai_assistant.generate_sql_query(user_input)
            if result['success']:
                return result['query'], None
            else:
                return None, result['error']
        except Exception as e:
            return None, str(e)
    
    def on_table_select(self, table_name: str):
        """Handle table selection from schema browser"""
        if hasattr(self.query_panel, 'insert_table_name'):
            self.query_panel.insert_table_name(table_name)
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.configure(text=message)
        self.update_idletasks()
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Disconnect from database
            if self.db_connection.is_connected():
                self.db_connection.disconnect()
            
            self.logger.info("PgWarp application closing")
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            self.destroy()

if __name__ == "__main__":
    app = PgWarpApp()
    app.mainloop()