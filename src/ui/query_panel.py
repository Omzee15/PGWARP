"""
Query panel component for SQL editing and execution
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import customtkinter as ctk
from typing import Dict, Any, Callable, Optional, List, Tuple
import threading
import time
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.theme_manager import theme_manager
from utils.config_manager import config_manager

class QueryPanel(ctk.CTkFrame):
    """Query panel with SQL editor and AI assistant"""
    
    def __init__(self, parent, execute_callback, ai_callback, results_callback=None, schema_browser=None):
        super().__init__(parent)
        
        # Callbacks
        self.execute_callback = execute_callback
        self.ai_callback = ai_callback  
        self.results_callback = results_callback  # Callback to display results in main window
        self.schema_browser = schema_browser  # Reference to schema browser for saved queries
        
        # Current state
        self.current_results = []
        self.current_columns = []
        
        # Autocomplete state
        self.autocomplete_popup = None
        self.autocomplete_listbox = None
        self.table_names_cache = []
        self.is_fetching_tables = False
        
        # Keyword autocomplete state
        self.current_suggestion = ""
        self.suggestion_start_pos = None
        
        # SQL Keywords for autocomplete
        self.sql_keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET',
            'DELETE', 'CREATE', 'TABLE', 'DROP', 'ALTER', 'ADD', 'COLUMN',
            'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'CONSTRAINT', 'INDEX',
            'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER', 'CROSS', 'ON',
            'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'DISTINCT',
            'AS', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'IN', 'LIKE', 'BETWEEN',
            'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'EXISTS', 'ANY', 'ALL',
            'UNION', 'INTERSECT', 'EXCEPT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
            'CAST', 'COALESCE', 'NULLIF', 'SUBSTRING', 'TRIM', 'LOWER', 'UPPER',
            'CONCAT', 'LENGTH', 'REPLACE', 'ROUND', 'FLOOR', 'CEIL', 'ABS',
            'NOW', 'CURRENT_DATE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP',
            'DATE', 'TIME', 'TIMESTAMP', 'INTERVAL', 'EXTRACT', 'DATE_PART',
            'VARCHAR', 'INTEGER', 'BIGINT', 'SMALLINT', 'DECIMAL', 'NUMERIC',
            'REAL', 'DOUBLE', 'PRECISION', 'BOOLEAN', 'TEXT', 'CHAR', 'SERIAL',
            'RETURNING', 'DEFAULT', 'CHECK', 'UNIQUE', 'NOT NULL', 'AUTO_INCREMENT',
            'CASCADE', 'RESTRICT', 'NO ACTION', 'SET NULL', 'SET DEFAULT',
            'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'TRANSACTION',
            'BEGIN', 'START', 'WORK', 'TRUNCATE', 'DESCRIBE', 'EXPLAIN', 'ANALYZE'
        ]
        
        # Create UI components
        self.create_widgets()
    
    def create_widgets(self):
        """Create query panel widgets"""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Query editor
        
        # Top toolbar
        toolbar_frame = ctk.CTkFrame(self, height=60, fg_color=theme_manager.get_color("card"), corner_radius=8)
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        toolbar_frame.grid_columnconfigure(3, weight=1)
        
        # Execute All button (Play symbol)
        self.execute_all_btn = ctk.CTkButton(
            toolbar_frame, 
            text="▶", 
            command=self.execute_all_query,
            width=45,
            height=36,
            fg_color=theme_manager.get_color("primary"),
            hover_color=theme_manager.get_color("primary"),
            text_color=theme_manager.get_color("primaryForeground"),
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=6
        )
        self.execute_all_btn.grid(row=0, column=0, padx=(10, 4), pady=12)
        
        # Execute Selected button (Play in circle)
        self.execute_selected_btn = ctk.CTkButton(
            toolbar_frame, 
            text="◉▶", 
            command=self.execute_selected_query,
            width=50,
            height=36,
            fg_color=theme_manager.get_color("buttons.primary_bg"),
            hover_color=theme_manager.get_color("buttons.primary_hover"),
            text_color=theme_manager.get_color("buttons.primary_text"),
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=6
        )
        self.execute_selected_btn.grid(row=0, column=1, padx=4, pady=12)
        
        # Clear button
        self.clear_btn = ctk.CTkButton(
            toolbar_frame, 
            text="🗑 Clear", 
            command=self.clear_query,
            width=100,
            height=36,
            fg_color=theme_manager.get_color("buttons.secondary_bg"),
            hover_color=theme_manager.get_color("buttons.secondary_hover"),
            text_color=theme_manager.get_color("buttons.secondary_text"),
            corner_radius=6
        )
        self.clear_btn.grid(row=0, column=2, padx=8, pady=12)
        
        # AI chat frame
        ai_frame = ctk.CTkFrame(toolbar_frame, fg_color=theme_manager.get_color("background"), corner_radius=8)
        ai_frame.grid(row=0, column=3, sticky="ew", padx=15, pady=8)
        ai_frame.grid_columnconfigure(0, weight=1)
        
        # AI input
        self.ai_entry = ctk.CTkEntry(
            ai_frame, 
            placeholder_text="Ask AI to generate a query...",
            height=36,
            font=ctk.CTkFont(size=12),
            fg_color=theme_manager.get_color("input"),
            text_color=theme_manager.get_color("foreground"),
            placeholder_text_color=theme_manager.get_color("mutedForeground"),
            border_color=theme_manager.get_color("border"),
            corner_radius=6
        )
        self.ai_entry.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.ai_entry.bind("<Return>", self.on_ai_enter)
        
        # AI generate button
        self.ai_btn = ctk.CTkButton(
            ai_frame, 
            text="🤖 Generate", 
            command=self.generate_with_ai,
            width=120,
            height=36,
            fg_color=theme_manager.get_color("buttons.primary_bg"),
            hover_color=theme_manager.get_color("buttons.primary_hover"),
            text_color=theme_manager.get_color("buttons.primary_text"),
            corner_radius=6
        )
        self.ai_btn.grid(row=0, column=1, padx=8, pady=8)
        
        # Format button
        self.format_btn = ctk.CTkButton(
            toolbar_frame, 
            text="📐 Format", 
            command=self.format_query,
            width=100,
            height=36,
            fg_color=theme_manager.get_color("buttons.secondary_bg"),
            hover_color=theme_manager.get_color("buttons.secondary_hover"),
            text_color=theme_manager.get_color("buttons.secondary_text"),
            corner_radius=6
        )
        self.format_btn.grid(row=0, column=4, padx=(8, 10), pady=12)
        
        # Query editor
        editor_frame = ctk.CTkFrame(self, corner_radius=8)
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        editor_frame.grid_columnconfigure(1, weight=1)
        editor_frame.grid_rowconfigure(0, weight=1)
        
        # Line numbers widget
        self.line_numbers = tk.Text(
            editor_frame,
            font=(config_manager.config.terminal_font_family, config_manager.config.terminal_font_size),
            bg=theme_manager.get_color("card"),
            fg=theme_manager.get_color("mutedForeground"),
            width=4,
            state="disabled",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=5,
            pady=8,
            takefocus=0,
            cursor="arrow"
        )
        
        # Query text area
        self.query_text = tk.Text(
            editor_frame,
            font=(config_manager.config.terminal_font_family, config_manager.config.terminal_font_size),
            bg=theme_manager.get_color("background"),
            fg=theme_manager.get_color("foreground"),
            insertbackground=theme_manager.get_color("primary"),
            selectbackground=theme_manager.get_color("primary"),
            selectforeground=theme_manager.get_color("primaryForeground"),
            wrap=tk.NONE,
            undo=True,
            maxundo=50,
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightcolor=theme_manager.get_color("border"),
            highlightbackground=theme_manager.get_color("border"),
            padx=12,
            pady=8
        )
        
        # Scrollbars for query editor
        query_v_scroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.query_text.yview)
        query_h_scroll = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.query_text.xview)
        self.query_text.configure(yscrollcommand=query_v_scroll.set, xscrollcommand=query_h_scroll.set)
        
        # Configure scrollbar styles using theme colors
        style = ttk.Style()
        style.configure("Vertical.TScrollbar", background=theme_manager.get_color("background.secondary"), troughcolor=theme_manager.get_color("background.main"), borderwidth=1)
        style.configure("Horizontal.TScrollbar", background=theme_manager.get_color("background.secondary"), troughcolor=theme_manager.get_color("background.main"), borderwidth=1)
        
        # Pack line numbers and query editor
        self.line_numbers.grid(row=0, column=0, sticky="ns", pady=(2, 0))
        self.query_text.grid(row=0, column=1, sticky="nsew", pady=(2, 0))
        query_v_scroll.grid(row=0, column=2, sticky="ns", pady=(2, 0))
        query_h_scroll.grid(row=1, column=1, sticky="ew")
        
        # Bind events to update line numbers
        self.query_text.bind("<MouseWheel>", self.update_line_numbers)
        self.query_text.bind("<Configure>", self.update_line_numbers)
        
        # Sync scrolling between line numbers and text
        def on_text_scroll(*args):
            self.line_numbers.yview_moveto(args[0])
            query_v_scroll.set(*args)
        
        self.query_text.configure(yscrollcommand=on_text_scroll)
        
        # Initialize line numbers
        self.update_line_numbers()
        
        # Query info frame
        info_frame = ctk.CTkFrame(self, height=35, fg_color=theme_manager.get_color("background.secondary"), corner_radius=8)
        info_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        
        self.query_info = ctk.CTkLabel(
            info_frame, 
            text="Ready to execute queries",
            font=ctk.CTkFont(size=12),
            text_color=theme_manager.get_color("text.primary")
        )
        self.query_info.pack(side="left", padx=15, pady=8)
        
        self.execution_time = ctk.CTkLabel(
            info_frame, 
            text="", 
            font=ctk.CTkFont(size=12),
            text_color=theme_manager.get_color("text.primary")
        )
        self.execution_time.pack(side="right", padx=15, pady=8)
        
        # Bind events
        self.query_text.bind("<Control-Return>", lambda e: self.execute_all_query())
        self.query_text.bind("<Command-Return>", lambda e: self.execute_all_query())
        
        # Bind for executing selected text
        self.query_text.bind("<Control-Shift-Return>", lambda e: self.execute_selected_query())
        self.query_text.bind("<Command-Shift-Return>", lambda e: self.execute_selected_query())
        
        # Bind autocomplete events
        self.query_text.bind("<KeyPress>", self.on_key_press)
        self.query_text.bind("<KeyRelease>", self.on_key_release)
        
        # Bind Tab key for accepting suggestions (unified handler for both keyword and table autocomplete)
        self.query_text.bind("<Tab>", self.on_tab_key)
        
        # Configure tag for inline suggestions using theme colors
        self.query_text.tag_configure("suggestion", foreground=theme_manager.get_color("text.secondary"), font=("Consolas", 13, "italic"))
        
        # Configure tags for reference highlighting using theme colors
        self.query_text.tag_configure("reference", foreground=theme_manager.get_color("text.secondary"))
        self.query_text.tag_configure("reference_valid", foreground=theme_manager.get_color("text.secondary"))
        self.query_text.tag_configure("reference_invalid", foreground=theme_manager.get_color("buttons.danger_bg"))
        
        # Tooltip for reference hover
        self.reference_tooltip = None
        self.tooltip_after_id = None
        
        # Bind events for reference highlighting and tooltips
        self.query_text.bind("<Motion>", self.on_mouse_motion)
        self.query_text.bind("<Leave>", self.hide_reference_tooltip)
        self.query_text.bind("<Button-1>", self.hide_reference_tooltip)
        
        # Store initial content
        self.insert_welcome_text()
    
    def update_line_numbers(self, event=None):
        """Update line numbers in the line number widget"""
        # Get the number of lines in the text widget
        line_count = self.query_text.get("1.0", "end-1c").count('\n') + 1
        
        # Generate line numbers
        line_numbers_text = "\n".join(str(i) for i in range(1, line_count + 1))
        
        # Update line numbers widget
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", line_numbers_text)
        self.line_numbers.configure(state="disabled")
    
    def insert_welcome_text(self):
        """Insert welcome text into the query editor"""
        # Add some sample placeholder text
        sample_query = """-- Welcome to PgWarp Query Tool
-- Write your SQL queries here
-- Press ▶ button or Ctrl+Enter to execute all
-- Press ◉▶ button or Ctrl+Shift+Enter to execute selected text
-- Use the AI assistant above to generate queries

SELECT version();"""
        self.query_text.insert("1.0", sample_query)
        self.update_line_numbers()
        self.highlight_references()
    
    def execute_query(self):
        """Execute the current query"""
        # Clear any autocomplete suggestion first
        if self.current_suggestion:
            self.clear_keyword_suggestion()
        
        query = self.get_current_query()
        if not query.strip():
            messagebox.showwarning("Empty Query", "Please enter a SQL query to execute")
            return
        
        # Substitute variables and query shortcuts if schema browser is available
        substituted_query = query
        missing_vars = []
        if self.schema_browser:
            # First substitute query shortcuts
            substituted_query = self.schema_browser.substitute_query_shortcuts_in_query(substituted_query)
            
            # Then substitute variables
            substituted_query, missing_vars = self.schema_browser.substitute_variables_in_query(substituted_query)
            
            # Warn about missing variables
            if missing_vars:
                if not messagebox.askyesno(
                    "Missing Variables",
                    f"The following variables are not defined:\n{', '.join(missing_vars)}\n\n" +
                    "Do you want to execute the query anyway?",
                    icon='warning'
                ):
                    return
        
        # Update UI to show execution in progress
        self.query_info.configure(text="Executing query...")
        self.execute_all_btn.configure(text="⏳", state="disabled")
        self.execution_time.configure(text="")
        
        # Execute in background thread to prevent UI freezing
        def execute_in_background():
            start_time = time.time()
            
            try:
                # Execute query using callback with substituted query
                results, columns_or_error = self.execute_callback(substituted_query)
                execution_time = time.time() - start_time
                
                # Update UI on main thread
                self.after(0, lambda: self.handle_query_result(results, columns_or_error, execution_time, substituted_query))
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.after(0, lambda: self.handle_query_error(str(e), execution_time))
        
        # Start background execution
        thread = threading.Thread(target=execute_in_background, daemon=True)
        thread.start()
    
    def execute_all_query(self):
        """Execute all text in the query editor (Play button ▶)"""
        # This is the same as execute_query, just with a clearer name
        self.execute_query()
    
    def execute_selected_query(self):
        """Execute only the selected text (Play in circle button ⊙▶)"""
        # Clear any autocomplete suggestion first
        if self.current_suggestion:
            self.clear_keyword_suggestion()
        
        selected_text = self.get_selected_text().strip()
        if not selected_text:
            messagebox.showwarning("No Selection", "Please select the SQL text you want to execute")
            return
        
        # Substitute variables and query shortcuts if schema browser is available
        substituted_query = selected_text
        missing_vars = []
        if self.schema_browser:
            # First substitute query shortcuts
            substituted_query = self.schema_browser.substitute_query_shortcuts_in_query(substituted_query)
            
            # Then substitute variables
            substituted_query, missing_vars = self.schema_browser.substitute_variables_in_query(substituted_query)
            
            # Warn about missing variables
            if missing_vars:
                if not messagebox.askyesno(
                    "Missing Variables",
                    f"The following variables are not defined:\n{', '.join(missing_vars)}\n\n" +
                    "Do you want to execute the query anyway?",
                    icon='warning'
                ):
                    return
        
        # Update UI to show execution in progress
        self.query_info.configure(text="Executing selected query...")
        self.execute_selected_btn.configure(text="◉⏳", state="disabled")
        self.execution_time.configure(text="")
        
        # Execute in background thread to prevent UI freezing
        def execute_in_background():
            start_time = time.time()
            
            try:
                # Execute query using callback with substituted query
                results, columns_or_error = self.execute_callback(substituted_query)
                execution_time = time.time() - start_time
                
                # Update UI on main thread
                self.after(0, lambda: self.handle_selected_query_result(results, columns_or_error, execution_time, substituted_query))
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.after(0, lambda: self.handle_selected_query_error(str(e), execution_time))
        
        # Start background execution
        thread = threading.Thread(target=execute_in_background, daemon=True)
        thread.start()
    
    def handle_selected_query_result(self, results: Optional[List[Dict]], columns_or_error, execution_time: float, query: str):
        """Handle successful selected query execution result"""
        # Restore execute button
        self.execute_selected_btn.configure(text="◉▶", state="normal")
        
        if results is None:
            # Error occurred
            self.handle_selected_query_error(columns_or_error, execution_time)
            return
        
        # Store results
        self.current_results = results
        self.current_columns = columns_or_error if isinstance(columns_or_error, list) else []
        
        # Send results to main window via callback
        if self.results_callback:
            self.results_callback(results, self.current_columns)
        
        # Update info
        row_count = len(results)
        self.query_info.configure(text=f"Selected query executed successfully - {row_count} rows returned")
        self.execution_time.configure(text=f"Execution time: {execution_time:.3f}s")
    
    def handle_selected_query_error(self, error_message: str, execution_time: float):
        """Handle selected query execution error"""
        # Restore execute button
        self.execute_selected_btn.configure(text="◉▶", state="normal")
        
        # Update info
        self.query_info.configure(text=f"Selected query failed: {error_message}")
        self.execution_time.configure(text=f"Execution time: {execution_time:.3f}s")
        
        # Clear results in main window
        if self.results_callback:
            self.results_callback([], [])
        
        # Show error dialog
        messagebox.showerror("Query Error", f"Selected query execution failed:\n\n{error_message}")
    
    def handle_query_result(self, results: Optional[List[Dict]], columns_or_error, execution_time: float, query: str):
        """Handle successful query execution result"""
        # Restore execute button
        self.execute_all_btn.configure(text="▶", state="normal")
        
        if results is None:
            # Error occurred
            self.handle_query_error(columns_or_error, execution_time)
            return
        
        # Store results
        self.current_results = results
        self.current_columns = columns_or_error if isinstance(columns_or_error, list) else []
        
        # Send results to main window via callback
        if self.results_callback:
            self.results_callback(results, self.current_columns)
        
        # Update info
        row_count = len(results)
        self.query_info.configure(text=f"Query executed successfully - {row_count} rows returned")
        self.execution_time.configure(text=f"Execution time: {execution_time:.3f}s")
        
        # Save to recent queries (if you have this utility)
        try:
            from utils.helpers import save_recent_query
            save_recent_query(query)
        except ImportError:
            pass
    
    def handle_query_error(self, error_message: str, execution_time: float):
        """Handle query execution error"""
        # Restore execute button
        self.execute_all_btn.configure(text="▶", state="normal")
        
        # Update info
        self.query_info.configure(text=f"Query failed: {error_message}")
        self.execution_time.configure(text=f"Execution time: {execution_time:.3f}s")
        
        # Clear results in main window
        if self.results_callback:
            self.results_callback([], [])
        
        # Show error dialog
        messagebox.showerror("Query Error", f"Query execution failed:\n\n{error_message}")
    
    def get_current_query(self) -> str:
        """Get the current query text (excluding suggestion text)"""
        # Temporarily clear any suggestion to get the real query
        had_suggestion = bool(self.current_suggestion)
        if had_suggestion:
            self.clear_keyword_suggestion()
        
        # Get the actual query text
        query = self.query_text.get("1.0", tk.END).strip()
        
        # Note: We don't restore the suggestion here as it will be regenerated on next key press
        
        return query
    
    def set_query(self, query: str):
        """Set the query text"""
        self.query_text.delete("1.0", tk.END)
        self.query_text.insert("1.0", query)
        self.update_line_numbers()
        self.highlight_references()
    
    def append_query(self, query: str):
        """Append query text to the current query"""
        # Get current content
        current_content = self.query_text.get("1.0", tk.END).strip()
        
        # Add newlines if there's existing content
        if current_content:
            self.query_text.insert(tk.END, "\n\n")
        
        # Append the new query
        self.query_text.insert(tk.END, query)
        
        # Update info
        self.query_info.configure(text="Saved query appended")
    
    def clear_query(self):
        """Clear the query text"""
        self.query_text.delete("1.0", tk.END)
        self.query_info.configure(text="Query cleared")
    
    def format_query(self):
        """Format the current query"""
        query = self.get_current_query()
        if not query:
            return
        
        try:
            from utils.helpers import format_sql_query
            formatted_query = format_sql_query(query)
            self.set_query(formatted_query)
            self.query_info.configure(text="Query formatted")
        except ImportError:
            messagebox.showwarning("Format Error", "SQL formatting not available")
        except Exception as e:
            messagebox.showerror("Format Error", f"Failed to format query:\n{e}")
    
    def on_ai_enter(self, event):
        """Handle Enter key in AI input field"""
        self.generate_with_ai()
    
    def generate_with_ai(self, user_input: Optional[str] = None):
        """Generate query using AI"""
        if not self.ai_callback:
            messagebox.showwarning("AI Not Available", "AI assistant is not configured")
            return
        
        # Get user input
        if user_input is None:
            user_input = self.ai_entry.get().strip()
        
        if not user_input:
            messagebox.showwarning("Empty Request", "Please describe what you want to query")
            return
        
        # Update UI
        self.ai_btn.configure(text="🤖 Generating...", state="disabled")
        self.query_info.configure(text="AI is generating query...")
        
        # Generate in background
        def generate_in_background():
            try:
                query, error = self.ai_callback(user_input)
                self.after(0, lambda: self.handle_ai_result(query, error, user_input))
            except Exception as e:
                self.after(0, lambda: self.handle_ai_error(str(e)))
        
        thread = threading.Thread(target=generate_in_background, daemon=True)
        thread.start()
    
    def handle_ai_result(self, query: Optional[str], error: Optional[str], user_input: str):
        """Handle AI generation result"""
        # Restore AI button
        self.ai_btn.configure(text="🤖 Generate", state="normal")
        
        if error:
            self.query_info.configure(text=f"AI error: {error}")
            messagebox.showerror("AI Error", f"Failed to generate query:\n\n{error}")
            return
        
        if query:
            # Insert generated query
            current_query = self.get_current_query().strip()
            if current_query and not messagebox.askyesno(
                "Replace Query", 
                "Replace the current query with the AI-generated one?"
            ):
                return
            
            self.set_query(query)
            self.query_info.configure(text=f"AI generated query for: {user_input}")
            
            # Clear AI input
            self.ai_entry.delete(0, tk.END)
            
            # Ask if user wants to execute immediately
            if messagebox.askyesno("Execute Query", "Would you like to execute the generated query?"):
                self.execute_query()
        else:
            self.query_info.configure(text="AI could not generate a query")
    
    def handle_ai_error(self, error_message: str):
        """Handle AI generation error"""
        self.ai_btn.configure(text="🤖 Generate", state="normal")
        self.query_info.configure(text=f"AI error: {error_message}")
        messagebox.showerror("AI Error", f"AI generation failed:\n\n{error_message}")
    
    def explain_query(self):
        """Explain the current query using AI"""
        query = self.get_current_query()
        if not query.strip():
            messagebox.showwarning("Empty Query", "Please enter a SQL query to explain")
            return
        
        if not self.ai_callback:
            messagebox.showwarning("AI Not Available", "AI assistant is not configured for explanations")
            return
        
        # This would need an additional AI callback for explanations
        # For now, show a simple info dialog
        messagebox.showinfo("Query Explanation", "Query explanation feature will be implemented with AI assistant")
    
    def insert_table_name(self, table_name: str):
        """Insert table name at cursor position"""
        cursor_pos = self.query_text.index(tk.INSERT)
        self.query_text.insert(cursor_pos, table_name)
        self.query_text.mark_set(tk.INSERT, f"{cursor_pos} + {len(table_name)}c")
        self.query_text.focus()
    
    def get_selected_text(self) -> str:
        """Get currently selected text in query editor"""
        try:
            # Clear any autocomplete suggestion first to avoid including it
            had_suggestion = bool(self.current_suggestion)
            if had_suggestion:
                self.clear_keyword_suggestion()
            
            # Get the selected text
            selected = self.query_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            return selected
        except tk.TclError:
            return ""
    
    def execute_selected(self):
        """Execute only the selected text"""
        selected_text = self.get_selected_text().strip()
        if not selected_text:
            messagebox.showwarning("No Selection", "Please select the SQL text to execute")
            return
        
        # Temporarily replace query text with selection
        original_query = self.get_current_query()
        self.set_query(selected_text)
        
        # Execute
        self.execute_query()
        
        # Optionally restore original query after execution
        # (you might want to ask user about this)
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Create context menu
        context_menu = tk.Menu(self, tearoff=0)
        
        # Check if there's a selection
        selected_text = self.get_selected_text()
        
        if selected_text:
            context_menu.add_command(
                label="Execute Selected",
                command=self.execute_selected
            )
            context_menu.add_command(
                label="Save Selected as Saved Query",
                command=lambda: self.save_selection_as_query()
            )
            context_menu.add_separator()
        
        context_menu.add_command(label="Execute All", command=self.execute_query)
        context_menu.add_command(label="Format Query", command=self.format_query)
        context_menu.add_separator()
        context_menu.add_command(label="Clear", command=self.clear_query)
        context_menu.add_separator()
        context_menu.add_command(label="Cut", command=lambda: self.query_text.event_generate("<<Cut>>"))
        context_menu.add_command(label="Copy", command=lambda: self.query_text.event_generate("<<Copy>>"))
        context_menu.add_command(label="Paste", command=lambda: self.query_text.event_generate("<<Paste>>"))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def save_selection_as_query(self):
        """Save selected text as a saved query"""
        selected_text = self.get_selected_text().strip()
        if not selected_text:
            messagebox.showwarning("No Selection", "Please select the SQL text to save")
            return
        
        if self.schema_browser:
            self.schema_browser.save_selected_query(selected_text)
        else:
            messagebox.showwarning("Feature Not Available", "Saved queries feature is not available")
    
    def set_schema_browser(self, schema_browser):
        """Set reference to schema browser"""
        self.schema_browser = schema_browser
    
    # ====== AUTOCOMPLETE METHODS ======
    
    def on_tab_key(self, event):
        """Unified Tab key handler for both keyword and table autocomplete"""
        # Priority 1: If table autocomplete popup is showing, use it
        if self.autocomplete_popup and self.autocomplete_popup.winfo_ismapped():
            self.on_autocomplete_select()
            return "break"
        
        # Priority 2: If there's a keyword suggestion, accept it
        if self.current_suggestion and self.suggestion_start_pos:
            return self.accept_keyword_suggestion(event)
        
        # Otherwise: Insert 4 spaces (standard tab behavior for code editors)
        self.query_text.insert(tk.INSERT, "    ")
        return "break"
    
    def on_key_press(self, event):
        """Handle key press events - clear suggestions when typing"""
        # Ignore special keys that don't change content
        if event.keysym in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 
                            'Alt_L', 'Alt_R', 'Meta_L', 'Meta_R', 'Super_L', 
                            'Super_R', 'Caps_Lock', 'Up', 'Down', 'Left', 'Right',
                            'Home', 'End', 'Page_Up', 'Page_Down', 'Escape']:
            return
        
        # If Tab is pressed and we have a suggestion, let the Tab handler deal with it
        if event.keysym == 'Tab' and self.current_suggestion:
            return
        
        # For any other key that could change content, clear the suggestion
        # This includes letters, numbers, space, backspace, delete, etc.
        if event.keysym not in ['Tab']:
            self.clear_keyword_suggestion()
    
    def on_key_release(self, event):
        """Handle key release events for autocomplete"""
        # Update line numbers
        self.update_line_numbers(event)
        
        # Ignore special keys
        if event.keysym in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 
                            'Alt_L', 'Alt_R', 'Meta_L', 'Meta_R', 'Super_L', 
                            'Super_R', 'Caps_Lock', 'Up', 'Down', 'Left', 'Right',
                            'Home', 'End', 'Page_Up', 'Page_Down', 'Tab']:
            return
        
        # Close popup on Escape
        if event.keysym == 'Escape':
            self.close_autocomplete_popup()
            self.clear_keyword_suggestion()
            return
        
        # Update reference highlighting
        self.highlight_references()
        
        # Check if we should show variable autocomplete (for {{variables}})
        # This takes priority over table autocomplete
        showing_variable_autocomplete = self.check_for_variable_autocomplete()
        
        # Only check for table autocomplete if we're not showing variable autocomplete
        if not showing_variable_autocomplete:
            self.check_for_table_autocomplete()
        
        # Check for keyword autocomplete (inline) - do this after table autocomplete
        # so we don't suggest keywords when table popup is showing
        if not (self.autocomplete_popup and self.autocomplete_popup.winfo_ismapped()):
            self.check_for_keyword_autocomplete()
    
    def check_for_table_autocomplete(self):
        """Check if we should show table autocomplete popup"""
        try:
            # Don't show table autocomplete if variable autocomplete is active
            if (self.autocomplete_popup and 
                hasattr(self, 'autocomplete_type') and 
                self.autocomplete_type == 'variable'):
                return
            
            # Get current cursor position
            cursor_pos = self.query_text.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            
            # Get the current line text up to cursor
            line_text = self.query_text.get(f"{line}.0", cursor_pos)
            
            # Keywords that precede table names (case-insensitive)
            # FROM, JOIN, INTO, UPDATE, TABLE (for CREATE/DROP/ALTER)
            table_keywords = [
                r'\bFROM\s+(\w*\.?\w*)$',           # SELECT ... FROM table
                r'\bJOIN\s+(\w*\.?\w*)$',           # ... JOIN table
                r'\bINTO\s+(\w*\.?\w*)$',           # INSERT INTO table
                r'\bUPDATE\s+(\w*\.?\w*)$',         # UPDATE table
                r'\bTABLE\s+(\w*\.?\w*)$',          # CREATE/DROP/ALTER TABLE table
                r'\bINNER\s+JOIN\s+(\w*\.?\w*)$',   # INNER JOIN table
                r'\bLEFT\s+JOIN\s+(\w*\.?\w*)$',    # LEFT JOIN table
                r'\bRIGHT\s+JOIN\s+(\w*\.?\w*)$',   # RIGHT JOIN table
                r'\bFULL\s+JOIN\s+(\w*\.?\w*)$',    # FULL JOIN table
                r'\bCROSS\s+JOIN\s+(\w*\.?\w*)$',   # CROSS JOIN table
                r'\bLEFT\s+OUTER\s+JOIN\s+(\w*\.?\w*)$',   # LEFT OUTER JOIN table
                r'\bRIGHT\s+OUTER\s+JOIN\s+(\w*\.?\w*)$',  # RIGHT OUTER JOIN table
                r'\bFULL\s+OUTER\s+JOIN\s+(\w*\.?\w*)$',   # FULL OUTER JOIN table
            ]
            
            # Check each pattern
            for pattern in table_keywords:
                match = re.search(pattern, line_text, re.IGNORECASE)
                if match:
                    # We're typing after a table keyword
                    current_word = match.group(1)
                    self.show_table_autocomplete_popup(current_word)
                    return
            
            # Close popup if open and we're not in the right context
            self.close_autocomplete_popup()
                
        except Exception as e:
            # Silently handle errors to not interrupt typing
            pass
    
    def show_table_autocomplete_popup(self, filter_text: str = ""):
        """Show autocomplete popup with table names"""
        # Fetch tables if not already cached or if cache is empty
        if not self.table_names_cache and not self.is_fetching_tables:
            self.fetch_table_names()
            # Don't show popup yet, wait for fetch to complete
            return
        
        # Filter table names based on current input
        filtered_tables = self.filter_table_names(filter_text)
        
        if not filtered_tables:
            self.close_autocomplete_popup()
            return
        
        # Create or update popup
        if self.autocomplete_popup is None:
            self.create_autocomplete_popup()
        
        # Update listbox with filtered tables
        self.autocomplete_listbox.delete(0, tk.END)
        for table_name in filtered_tables:
            self.autocomplete_listbox.insert(tk.END, table_name)
        
        # Select first item
        if self.autocomplete_listbox.size() > 0:
            self.autocomplete_listbox.selection_clear(0, tk.END)
            self.autocomplete_listbox.selection_set(0)
            self.autocomplete_listbox.see(0)
        
        # Position popup at cursor
        self.position_autocomplete_popup()
        
        # Show popup
        if self.autocomplete_popup:
            self.autocomplete_popup.deiconify()
    
    def create_autocomplete_popup(self):
        """Create the autocomplete popup window"""
        # Always destroy existing popup to avoid styling issues
        if self.autocomplete_popup:
            try:
                self.autocomplete_popup.destroy()
            except:
                pass
            self.autocomplete_popup = None
            self.autocomplete_listbox = None
        
        # Create toplevel window with explicit styling
        self.autocomplete_popup = tk.Toplevel(self)
        self.autocomplete_popup.withdraw()  # Hide initially
        self.autocomplete_popup.overrideredirect(True)  # Remove window decorations
        self.autocomplete_popup.wm_attributes("-topmost", True)  # Keep on top
        
        # Force background color on the toplevel itself using theme
        self.autocomplete_popup.configure(bg=theme_manager.get_color("background.main"))
        
        # Create main container frame with explicit styling using theme
        main_frame = tk.Frame(
            self.autocomplete_popup, 
            bg=theme_manager.get_color("background.main"), 
            bd=0,
            relief=tk.FLAT
        )
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create border frame for better visual appearance using theme
        border_frame = tk.Frame(
            main_frame,
            bg=theme_manager.get_color("accent.main"),
            bd=1,
            relief=tk.SOLID
        )
        border_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Create content frame using theme
        content_frame = tk.Frame(
            border_frame, 
            bg=theme_manager.get_color("background.main"), 
            bd=0
        )
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar with proper styling using theme
        scrollbar = tk.Scrollbar(
            content_frame, 
            orient=tk.VERTICAL,
            bg=theme_manager.get_color("background.secondary"),
            troughcolor=theme_manager.get_color("background.main"),
            activebackground=theme_manager.get_color("accent.main"),
            borderwidth=0
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create listbox using theme colors
        self.autocomplete_listbox = tk.Listbox(
            content_frame,
            font=("Consolas", 11),
            bg=theme_manager.get_color("background.main"),
            fg=theme_manager.get_color("text.primary"),
            selectbackground=theme_manager.get_color("buttons.primary_bg"),
            selectforeground=theme_manager.get_color("buttons.primary_text"),
            highlightthickness=0,
            borderwidth=0,
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            height=10,
            width=40
        )
        self.autocomplete_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.autocomplete_listbox.yview)
        
        # Bind events
        self.autocomplete_listbox.bind("<Double-Button-1>", self.on_autocomplete_select)
        self.autocomplete_listbox.bind("<Return>", self.on_autocomplete_select)
        self.autocomplete_listbox.bind("<Escape>", lambda e: self.close_autocomplete_popup())
        
        # Bind to query text widget to handle navigation
        self.query_text.bind("<Down>", self.on_autocomplete_down)
        self.query_text.bind("<Up>", self.on_autocomplete_up)
        self.query_text.bind("<Return>", self.on_autocomplete_return)
        # Note: Tab is already bound in __init__, don't rebind it here
        
        # Close popup when clicking outside
        self.autocomplete_popup.bind("<FocusOut>", lambda e: self.close_autocomplete_popup())
    
    def position_autocomplete_popup(self):
        """Position the autocomplete popup at the cursor"""
        if not self.autocomplete_popup:
            return
        
        try:
            # Get cursor position in text widget
            cursor_pos = self.query_text.index(tk.INSERT)
            bbox = self.query_text.bbox(cursor_pos)
            
            if bbox:
                x, y, width, height = bbox
                
                # Get absolute position of query text widget
                text_x = self.query_text.winfo_rootx()
                text_y = self.query_text.winfo_rooty()
                
                # Calculate popup position
                popup_x = text_x + x
                popup_y = text_y + y + height + 2
                
                # Position popup
                self.autocomplete_popup.geometry(f"+{popup_x}+{popup_y}")
        except:
            pass
    
    def close_autocomplete_popup(self):
        """Close the autocomplete popup"""
        if self.autocomplete_popup:
            try:
                self.autocomplete_popup.destroy()
            except:
                pass
            self.autocomplete_popup = None
            self.autocomplete_listbox = None
    
    def on_autocomplete_select(self, event=None):
        """Handle selection from autocomplete popup"""
        if not self.autocomplete_listbox:
            return
        
        selection = self.autocomplete_listbox.curselection()
        if selection:
            selected_item = self.autocomplete_listbox.get(selection[0])
            
            # Check if this is variable autocomplete
            if hasattr(self, 'autocomplete_type') and self.autocomplete_type == 'variable':
                self.insert_autocomplete_variable(selected_item)
            else:
                # Table autocomplete
                self.insert_autocomplete_table(selected_item)
            
            self.close_autocomplete_popup()
    
    def on_autocomplete_down(self, event):
        """Handle down arrow key when autocomplete is open"""
        if self.autocomplete_popup and self.autocomplete_popup.winfo_ismapped():
            if self.autocomplete_listbox.size() > 0:
                current = self.autocomplete_listbox.curselection()
                if current:
                    next_index = min(current[0] + 1, self.autocomplete_listbox.size() - 1)
                else:
                    next_index = 0
                self.autocomplete_listbox.selection_clear(0, tk.END)
                self.autocomplete_listbox.selection_set(next_index)
                self.autocomplete_listbox.see(next_index)
            return "break"  # Prevent default behavior
        return None
    
    def on_autocomplete_up(self, event):
        """Handle up arrow key when autocomplete is open"""
        if self.autocomplete_popup and self.autocomplete_popup.winfo_ismapped():
            if self.autocomplete_listbox.size() > 0:
                current = self.autocomplete_listbox.curselection()
                if current:
                    prev_index = max(current[0] - 1, 0)
                else:
                    prev_index = 0
                self.autocomplete_listbox.selection_clear(0, tk.END)
                self.autocomplete_listbox.selection_set(prev_index)
                self.autocomplete_listbox.see(prev_index)
            return "break"  # Prevent default behavior
        return None
    
    def on_autocomplete_return(self, event):
        """Handle Return key when autocomplete is open"""
        if self.autocomplete_popup and self.autocomplete_popup.winfo_ismapped():
            self.on_autocomplete_select()
            return "break"  # Prevent default behavior
        return None
    
    def insert_autocomplete_table(self, table_name: str):
        """Insert selected table name at cursor, replacing any partial text"""
        try:
            # Get current cursor position
            cursor_pos = self.query_text.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            
            # Get the current line text up to cursor
            line_text = self.query_text.get(f"{line}.0", cursor_pos)
            
            # Find the start of the current word being typed
            pattern = r'\bFROM\s+(\w*\.?\w*)$'
            match = re.search(pattern, line_text, re.IGNORECASE)
            
            if match:
                # Calculate positions
                word_start = len(line_text) - len(match.group(1))
                start_pos = f"{line}.{word_start}"
                
                # Delete the partial word
                self.query_text.delete(start_pos, cursor_pos)
                
                # Insert the selected table name
                self.query_text.insert(start_pos, table_name)
                
                # Add a space after the table name for convenience
                new_cursor_pos = f"{line}.{word_start + len(table_name)}"
                self.query_text.insert(new_cursor_pos, " ")
                
                # Set cursor after the space
                self.query_text.mark_set(tk.INSERT, f"{line}.{word_start + len(table_name) + 1}")
            
            # Focus back to text widget
            self.query_text.focus_set()
            
        except Exception as e:
            # If something goes wrong, just insert the table name at cursor
            self.query_text.insert(tk.INSERT, table_name + " ")
            self.query_text.focus_set()
    
    def insert_autocomplete_variable(self, item_display: str):
        """Insert selected variable or query shortcut at cursor, replacing any partial text"""
        try:
            # Determine if this is a variable (💾) or query shortcut (🔗)
            if item_display.startswith("💾"):
                # Extract variable name from display text (format: "💾 var_name = value")
                item_name = item_display.split()[1]
            elif item_display.startswith("🔗"):
                # Extract shortcut name from display text (format: "🔗 shortcut → title")
                item_name = item_display.split()[1]
            else:
                return
            
            # Get current cursor position
            cursor_pos = self.query_text.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            
            # Get the current line text up to cursor
            line_text = self.query_text.get(f"{line}.0", cursor_pos)
            
            # Find the start of {{ pattern
            match = re.search(r'\{\{(\w*)$', line_text)
            
            if match:
                # Calculate positions
                word_start = len(line_text) - len(match.group(0))
                start_pos = f"{line}.{word_start}"
                
                # Delete the partial text (including {{)
                self.query_text.delete(start_pos, cursor_pos)
                
                # Insert the complete placeholder
                placeholder = f"{{{{{item_name}}}}}"
                self.query_text.insert(start_pos, placeholder)
                
                # Set cursor after the }}
                new_pos = word_start + len(placeholder)
                self.query_text.mark_set(tk.INSERT, f"{line}.{new_pos}")
            
            # Focus back to text widget
            self.query_text.focus_set()
            
        except Exception as e:
            # If something goes wrong, just insert the item at cursor
            try:
                if item_display.startswith("💾"):
                    item_name = item_display.split()[1]
                elif item_display.startswith("🔗"):
                    item_name = item_display.split()[1]
                else:
                    return
                self.query_text.insert(tk.INSERT, f"{{{{{item_name}}}}}")
            except:
                pass
            self.query_text.focus_set()
    
    def filter_table_names(self, filter_text: str) -> List[str]:
        """Filter table names based on input text"""
        if not filter_text:
            return self.table_names_cache[:20]  # Return first 20 if no filter
        
        filter_lower = filter_text.lower()
        filtered = [
            name for name in self.table_names_cache 
            if filter_lower in name.lower()
        ]
        return filtered[:20]  # Limit to 20 results
    
    def fetch_table_names(self):
        """Fetch table names from database"""
        if self.is_fetching_tables:
            return
        
        self.is_fetching_tables = True
        
        def fetch_in_background():
            try:
                # Execute query to get table names
                # Using information_schema to get both tables and views
                query = """
                    SELECT table_schema || '.' || table_name as full_name
                    FROM information_schema.tables
                    WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    AND table_type IN ('BASE TABLE', 'VIEW')
                    ORDER BY table_schema, table_name
                """
                
                results, columns = self.execute_callback(query)
                
                if results is not None:
                    # Extract table names from results
                    table_names = [row['full_name'] for row in results if 'full_name' in row]
                    
                    # Update cache on main thread
                    self.after(0, lambda: self.update_table_cache(table_names))
                
            except Exception as e:
                # Silently handle errors
                pass
            finally:
                self.is_fetching_tables = False
        
        # Start background fetch
        thread = threading.Thread(target=fetch_in_background, daemon=True)
        thread.start()
    
    def update_table_cache(self, table_names: List[str]):
        """Update table names cache and show popup if needed"""
        self.table_names_cache = table_names
        # Note: We don't auto-show popup here, it will show on next key press
    
    # ====== VARIABLE AUTOCOMPLETE METHODS ======
    
    def check_for_variable_autocomplete(self):
        """Check if we should show variable autocomplete popup for {{variables}}"""
        try:
            # Get current cursor position
            cursor_pos = self.query_text.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            
            # Get the current line text up to cursor
            line_text = self.query_text.get(f"{line}.0", cursor_pos)
            
            # Check if we're inside {{ }}
            # Pattern: {{variable_name with cursor here
            match = re.search(r'\{\{(\w*)$', line_text)
            
            if match and self.schema_browser:
                # We're typing a variable after {{
                current_word = match.group(1)
                self.show_variable_autocomplete_popup(current_word)
                return True  # Indicate we showed variable autocomplete
            else:
                # Only close if this was actually showing variable autocomplete
                if (self.autocomplete_popup and 
                    hasattr(self, 'autocomplete_type') and 
                    self.autocomplete_type == 'variable'):
                    self.close_autocomplete_popup()
                return False  # Indicate no variable autocomplete
                    
        except Exception as e:
            return False  # Ignore errors in autocomplete
    
    def show_variable_autocomplete_popup(self, current_word: str):
        """Show autocomplete popup with matching variables and query shortcuts"""
        if not self.schema_browser:
            return
        
        # Get all variables and query shortcuts
        all_variables = self.schema_browser.get_all_variables()
        all_shortcuts = self.schema_browser.get_all_query_shortcuts()
        
        matching_items = []
        
        # Add matching variables
        if all_variables:
            if current_word:
                matching_vars = [(name, value, 'variable') for name, value in all_variables.items() 
                               if name.lower().startswith(current_word.lower())]
            else:
                matching_vars = [(name, value, 'variable') for name, value in all_variables.items()]
            matching_items.extend(matching_vars)
        
        # Add matching query shortcuts
        if all_shortcuts:
            if current_word:
                matching_shortcuts = [(shortcut, title, 'query') for shortcut, title in all_shortcuts.items() 
                                    if shortcut.lower().startswith(current_word.lower())]
            else:
                matching_shortcuts = [(shortcut, title, 'query') for shortcut, title in all_shortcuts.items()]
            matching_items.extend(matching_shortcuts)
        
        if not matching_items:
            self.close_autocomplete_popup()
            return
        
        # Create popup if it doesn't exist
        self.create_autocomplete_popup()
        
        # Mark this as variable autocomplete (handles both variables and query shortcuts)
        self.autocomplete_type = 'variable'
        
        # Clear and populate listbox
        self.autocomplete_listbox.delete(0, tk.END)
        
        # Sort by type (variables first, then queries) and then by name
        matching_items.sort(key=lambda x: (x[2], x[0].lower()))
        
        for name, description, item_type in matching_items:
            if item_type == 'variable':
                # Show variable name and truncated value
                display_value = str(description)
                if len(display_value) > 25:
                    display_value = display_value[:22] + "..."
                display_text = f"💾 {name} = {display_value}"
            else:  # query shortcut
                # Show query shortcut and title
                display_title = str(description)
                if len(display_title) > 25:
                    display_title = display_title[:22] + "..."
                display_text = f"🔗 {name} → {display_title}"
            
            self.autocomplete_listbox.insert(tk.END, display_text)
        
        # Select first item
        if self.autocomplete_listbox.size() > 0:
            self.autocomplete_listbox.selection_set(0)
            self.autocomplete_listbox.activate(0)
        
        # Position and show popup
        self.position_autocomplete_popup()
        self.autocomplete_popup.deiconify()
    
    # ====== KEYWORD AUTOCOMPLETE METHODS ======
    
    def check_for_keyword_autocomplete(self):
        """Check if we should show inline keyword suggestion"""
        try:
            # Get current cursor position
            cursor_pos = self.query_text.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            
            # Get the current word being typed
            line_text = self.query_text.get(f"{line}.0", cursor_pos)
            
            # Find the current word (last word before cursor)
            # Match word characters (letters, numbers, underscore)
            word_match = re.search(r'(\w+)$', line_text)
            
            if not word_match:
                return
            
            current_word = word_match.group(1)
            
            # Don't suggest for very short words or if the word is all lowercase (likely a table/column name)
            if len(current_word) < 2:
                return
            
            # Check if the current word starts with uppercase (likely a keyword)
            if not current_word[0].isupper():
                # User is typing lowercase, convert to uppercase for matching
                current_word_upper = current_word.upper()
            else:
                current_word_upper = current_word
            
            # Find matching keywords
            matches = [
                keyword for keyword in self.sql_keywords
                if keyword.startswith(current_word_upper) and keyword != current_word_upper
            ]
            
            if matches:
                # Take the first match
                suggestion = matches[0]
                
                # Get the part of the suggestion that should be shown
                remaining = suggestion[len(current_word_upper):]
                
                # If user is typing lowercase, show suggestion in lowercase
                if not current_word[0].isupper():
                    remaining = remaining.lower()
                
                # Show the suggestion
                self.show_keyword_suggestion(remaining, cursor_pos)
            
        except Exception as e:
            # Silently handle errors to not interrupt typing
            pass
    
    def show_keyword_suggestion(self, suggestion: str, position: str):
        """Show inline keyword suggestion at cursor position"""
        if not suggestion:
            return
        
        try:
            # Store the suggestion and position
            self.current_suggestion = suggestion
            self.suggestion_start_pos = position
            
            # Insert the suggestion text with special tag (this is visual only)
            self.query_text.insert(position, suggestion, "suggestion")
            
            # Move cursor back to the original position (before the suggestion)
            self.query_text.mark_set(tk.INSERT, position)
            
            # Prevent the suggestion from being part of the actual text by marking it
            # We'll handle this properly in get_current_query()
            
        except Exception as e:
            # Silently handle errors
            self.current_suggestion = ""
            self.suggestion_start_pos = None
    
    def clear_keyword_suggestion(self):
        """Clear any existing keyword suggestion"""
        if not self.current_suggestion or not self.suggestion_start_pos:
            return
        
        try:
            # Calculate end position of suggestion
            line, col = map(int, self.suggestion_start_pos.split('.'))
            end_col = col + len(self.current_suggestion)
            end_pos = f"{line}.{end_col}"
            
            # Check if the suggestion text is still there
            try:
                text_at_pos = self.query_text.get(self.suggestion_start_pos, end_pos)
                
                # Only delete if it matches our suggestion (to avoid deleting user text)
                if text_at_pos == self.current_suggestion:
                    self.query_text.delete(self.suggestion_start_pos, end_pos)
            except tk.TclError:
                # Position might be invalid, just clear the state
                pass
            
        except Exception:
            # If anything goes wrong, just clear the state
            pass
        finally:
            # Always clear the state
            self.current_suggestion = ""
            self.suggestion_start_pos = None
    
    def accept_keyword_suggestion(self, event=None):
        """Accept the current keyword suggestion (Tab key handler)"""
        if self.current_suggestion and self.suggestion_start_pos:
            try:
                # Calculate end position
                line, col = map(int, self.suggestion_start_pos.split('.'))
                end_col = col + len(self.current_suggestion)
                end_pos = f"{line}.{end_col}"
                
                # Remove the suggestion tag
                self.query_text.tag_remove("suggestion", self.suggestion_start_pos, end_pos)
                
                # Move cursor to the end of the suggestion
                self.query_text.mark_set(tk.INSERT, end_pos)
                
                # Clear suggestion state
                self.current_suggestion = ""
                self.suggestion_start_pos = None
                
                # Prevent default Tab behavior
                return "break"
            except Exception:
                pass
        
        # If no suggestion, allow default Tab behavior
        return None

    def highlight_references(self):
        """Highlight {{variable}} and {{query}} references in the text"""
        try:
            # Clear existing reference tags
            self.query_text.tag_remove("reference", "1.0", "end")
            self.query_text.tag_remove("reference_valid", "1.0", "end")
            self.query_text.tag_remove("reference_invalid", "1.0", "end")
            
            # Get all text
            text = self.query_text.get("1.0", "end-1c")
            
            # Find all {{...}} patterns
            import re
            pattern = r'\{\{([^}]+)\}\}'
            
            for match in re.finditer(pattern, text):
                start_idx = match.start()
                end_idx = match.end()
                reference_name = match.group(1).strip()
                
                # Convert string indices to tkinter positions
                start_pos = self.index_to_position(text, start_idx)
                end_pos = self.index_to_position(text, end_idx)
                
                # Check if it's a valid reference
                is_valid = self.is_valid_reference(reference_name)
                
                # Apply appropriate tag
                if is_valid:
                    self.query_text.tag_add("reference_valid", start_pos, end_pos)
                else:
                    self.query_text.tag_add("reference_invalid", start_pos, end_pos)
                    
        except Exception as e:
            # Silently handle errors to avoid disrupting user experience
            pass
    
    def index_to_position(self, text: str, index: int) -> str:
        """Convert string index to tkinter text position (line.column)"""
        lines = text[:index].split('\n')
        line_num = len(lines)
        col_num = len(lines[-1])
        return f"{line_num}.{col_num}"
    
    def is_valid_reference(self, reference_name: str) -> bool:
        """Check if a reference name is valid (exists in saved queries or variables)"""
        try:
            # Check if it's a saved query shortcut
            if self.schema_browser:
                saved_queries_manager = getattr(self.schema_browser, 'saved_queries_manager', None)
                if saved_queries_manager:
                    query = saved_queries_manager.get_query_by_shortcut(reference_name)
                    if query:
                        return True
                
                # Check if it's a saved variable
                saved_variables_manager = getattr(self.schema_browser, 'saved_variables_manager', None)
                if saved_variables_manager:
                    variable = saved_variables_manager.get_variable(reference_name)
                    if variable is not None:
                        return True
            
            return False
        except Exception:
            return False
    
    def on_mouse_motion(self, event):
        """Handle mouse motion for showing reference tooltips"""
        try:
            # Cancel any pending tooltip
            if self.tooltip_after_id:
                self.after_cancel(self.tooltip_after_id)
                self.tooltip_after_id = None
            
            # Hide existing tooltip
            self.hide_reference_tooltip()
            
            # Get the position under mouse
            x, y = event.x, event.y
            index = self.query_text.index(f"@{x},{y}")
            
            # Check if we're over a reference
            reference_content = self.get_reference_at_position(index)
            if reference_content:
                # Schedule tooltip to appear after a delay
                self.tooltip_after_id = self.after(500, lambda: self.show_reference_tooltip(event, reference_content))
        except Exception:
            pass
    
    def get_reference_at_position(self, index: str) -> dict:
        """Get reference information at a given position"""
        try:
            # Check if position has any reference tags
            tags = self.query_text.tag_names(index)
            if not any(tag.startswith("reference") for tag in tags):
                return None
            
            # Get the line content
            line_start = f"{index.split('.')[0]}.0"
            line_end = f"{index.split('.')[0]}.end"
            line_text = self.query_text.get(line_start, line_end)
            
            # Find the reference at this position
            col = int(index.split('.')[1])
            
            import re
            pattern = r'\{\{([^}]+)\}\}'
            
            for match in re.finditer(pattern, line_text):
                if match.start() <= col <= match.end():
                    reference_name = match.group(1).strip()
                    return {
                        'name': reference_name,
                        'content': self.get_reference_content(reference_name),
                        'type': self.get_reference_type(reference_name)
                    }
            
            return None
        except Exception:
            return None
    
    def get_reference_content(self, reference_name: str) -> str:
        """Get the content of a reference (query or variable)"""
        try:
            if not self.schema_browser:
                return f"Reference '{reference_name}' - Schema browser not available"
            
            # Check saved queries first
            saved_queries_manager = getattr(self.schema_browser, 'saved_queries_manager', None)
            if saved_queries_manager:
                query = saved_queries_manager.get_query_by_shortcut(reference_name)
                if query:
                    return query.query  # Changed from query.sql to query.query
            
            # Check saved variables
            saved_variables_manager = getattr(self.schema_browser, 'saved_variables_manager', None)
            if saved_variables_manager:
                variable = saved_variables_manager.get_variable(reference_name)
                if variable is not None:
                    return str(variable)
            
            return f"Reference '{reference_name}' not found"
        except Exception as e:
            return f"Error retrieving reference content: {str(e)}"
    
    def get_reference_type(self, reference_name: str) -> str:
        """Get the type of reference (query or variable)"""
        try:
            if not self.schema_browser:
                return "Unknown"
                
            # Check saved queries first
            saved_queries_manager = getattr(self.schema_browser, 'saved_queries_manager', None)
            if saved_queries_manager:
                query = saved_queries_manager.get_query_by_shortcut(reference_name)
                if query:
                    return "Saved Query"
            
            # Check saved variables
            saved_variables_manager = getattr(self.schema_browser, 'saved_variables_manager', None)
            if saved_variables_manager:
                variable = saved_variables_manager.get_variable(reference_name)
                if variable is not None:
                    return "Variable"
            
            return "Unknown"
        except Exception as e:
            return "Unknown"
    
    def show_reference_tooltip(self, event, reference_info: dict):
        """Show tooltip with reference content"""
        try:
            if self.reference_tooltip:
                self.hide_reference_tooltip()
            
            # Create tooltip window
            self.reference_tooltip = tk.Toplevel(self)
            self.reference_tooltip.wm_overrideredirect(True)
            
            # Position tooltip near mouse
            x = event.x_root + 10
            y = event.y_root + 10
            self.reference_tooltip.wm_geometry(f"+{x}+{y}")
            
            # Create frame without border (matching section backgrounds)
            border_frame = tk.Frame(
                self.reference_tooltip,
                background=theme_manager.get_color("background.secondary"),  # Light brown background color
                borderwidth=0,
                relief="flat"
            )
            border_frame.pack()
            
            # Inner frame with main section color as background
            tooltip_frame = tk.Frame(
                border_frame,
                background=theme_manager.get_color("background.secondary"),  # Changed to light brown background
                borderwidth=0
            )
            tooltip_frame.pack(padx=1, pady=1)
            
            # Title label with padding
            title_frame = tk.Frame(tooltip_frame, background=theme_manager.get_color("background.secondary"))
            title_frame.pack(fill="x", padx=8, pady=(8, 4))
            
            title_label = tk.Label(
                title_frame,
                text=f"{reference_info['type']}: {reference_info['name']}",
                background=theme_manager.get_color("background.secondary"),
                foreground=theme_manager.get_color("text.primary"),  # Changed text to dark brown for better contrast
                font=("Consolas", 11, "bold")
            )
            title_label.pack(anchor="w")
            
            # Separator
            separator = tk.Frame(tooltip_frame, height=1, background=theme_manager.get_color("accent.main"))
            separator.pack(fill="x", padx=8, pady=(0, 4))
            
            # Content text widget (using query writing section color)
            content_text = tk.Text(
                tooltip_frame,
                background=theme_manager.get_color("background.main"),  # Query writing section background color
                foreground=theme_manager.get_color("text.primary"),  # Query writing section text color
                font=("Consolas", 10),
                wrap="word",
                borderwidth=0,  # Remove border
                relief="flat",
                highlightthickness=0,  # Remove highlight border
                padx=8,
                pady=8,
                width=50,
                height=min(10, len(reference_info['content'].split('\n')) + 1),
                state="normal"
            )
            content_text.pack()
            
            # Insert content
            content_text.insert("1.0", reference_info['content'])
            content_text.configure(state="disabled")
            
        except Exception:
            self.hide_reference_tooltip()
    
    def hide_reference_tooltip(self, event=None):
        """Hide the reference tooltip"""
        try:
            if self.tooltip_after_id:
                self.after_cancel(self.tooltip_after_id)
                self.tooltip_after_id = None
            
            if self.reference_tooltip:
                self.reference_tooltip.destroy()
                self.reference_tooltip = None
        except Exception:
            pass
    
    def apply_theme(self):
        """Apply current theme to query panel components"""
        # Update main frame
        self.configure(fg_color=theme_manager.get_color("background.main"))
        
        # Update toolbar components
        if hasattr(self, 'execute_all_btn'):
            self.execute_all_btn.configure(
                fg_color=theme_manager.get_color("buttons.primary_bg"),
                hover_color=theme_manager.get_color("buttons.primary_hover"),
                text_color=theme_manager.get_color("buttons.primary_text")
            )
        
        if hasattr(self, 'execute_selected_btn'):
            self.execute_selected_btn.configure(
                fg_color=theme_manager.get_color("buttons.primary_bg"),
                hover_color=theme_manager.get_color("buttons.primary_hover"),
                text_color=theme_manager.get_color("buttons.primary_text")
            )
        
        if hasattr(self, 'clear_btn'):
            self.clear_btn.configure(
                fg_color=theme_manager.get_color("buttons.secondary_bg"),
                hover_color=theme_manager.get_color("buttons.secondary_hover"),
                text_color=theme_manager.get_color("buttons.secondary_text")
            )
        
        if hasattr(self, 'ai_btn'):
            self.ai_btn.configure(
                fg_color=theme_manager.get_color("buttons.primary_bg"),
                hover_color=theme_manager.get_color("buttons.primary_hover"),
                text_color=theme_manager.get_color("buttons.primary_text")
            )
        
        if hasattr(self, 'format_btn'):
            self.format_btn.configure(
                fg_color=theme_manager.get_color("buttons.secondary_bg"),
                hover_color=theme_manager.get_color("buttons.secondary_hover"),
                text_color=theme_manager.get_color("buttons.secondary_text")
            )
        
        if hasattr(self, 'ai_entry'):
            self.ai_entry.configure(
                fg_color=theme_manager.get_color("editor.background"),
                text_color=theme_manager.get_color("text.primary"),
                placeholder_text_color=theme_manager.get_color("text.secondary"),
                border_color=theme_manager.get_color("accent.main")
            )
        
        # Update text widgets
        if hasattr(self, 'query_text'):
            self.query_text.configure(
                bg=theme_manager.get_color("background.main"),
                fg=theme_manager.get_color("text.primary"),
                insertbackground=theme_manager.get_color("accent.main"),
                selectbackground=theme_manager.get_color("accent.main"),
                selectforeground=theme_manager.get_color("buttons.primary_text")
            )
            
            # Update text tags
            self.query_text.tag_configure("suggestion", foreground=theme_manager.get_color("text.secondary"))
            self.query_text.tag_configure("reference", foreground=theme_manager.get_color("text.secondary"))
            self.query_text.tag_configure("reference_valid", foreground=theme_manager.get_color("text.secondary"))
            self.query_text.tag_configure("reference_invalid", foreground=theme_manager.get_color("buttons.danger_bg"))
        
        if hasattr(self, 'line_numbers'):
            self.line_numbers.configure(
                bg=theme_manager.get_color("background.secondary"),
                fg=theme_manager.get_color("text.secondary")
            )
        
        # Update info labels
        if hasattr(self, 'query_info'):
            self.query_info.configure(text_color=theme_manager.get_color("text.primary"))
        
        if hasattr(self, 'execution_time'):
            self.execution_time.configure(text_color=theme_manager.get_color("text.primary"))
        
        # Update autocomplete popup if it exists
        if hasattr(self, 'autocomplete_popup') and self.autocomplete_popup:
            try:
                self.autocomplete_popup.configure(bg=theme_manager.get_color("background.main"))
            except:
                pass
        
        if hasattr(self, 'autocomplete_listbox') and self.autocomplete_listbox:
            try:
                self.autocomplete_listbox.configure(
                    bg=theme_manager.get_color("background.main"),
                    fg=theme_manager.get_color("text.primary"),
                    selectbackground=theme_manager.get_color("buttons.primary_bg"),
                    selectforeground=theme_manager.get_color("buttons.primary_text")
                )
            except:
                pass
        
        # Update frames
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                try:
                    if "toolbar" in str(child).lower():
                        child.configure(fg_color=theme_manager.get_color("background.secondary"))
                    else:
                        child.configure(fg_color=theme_manager.get_color("background.main"))
                except:
                    pass
