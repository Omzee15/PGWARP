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
        toolbar_frame = ctk.CTkFrame(self, height=60, fg_color="#E8DFD0", corner_radius=8)
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        toolbar_frame.grid_columnconfigure(3, weight=1)
        
        # Execute All button (Play symbol)
        self.execute_all_btn = ctk.CTkButton(
            toolbar_frame, 
            text="▶", 
            command=self.execute_all_query,
            width=45,
            height=36,
            fg_color="#9B8F5E",
            hover_color="#87795A",
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
            fg_color="#9B8F5E",
            hover_color="#87795A",
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
            fg_color="#9B8F5E",
            hover_color="#87795A",
            corner_radius=6
        )
        self.clear_btn.grid(row=0, column=2, padx=8, pady=12)
        
        # AI chat frame
        ai_frame = ctk.CTkFrame(toolbar_frame, corner_radius=8)
        ai_frame.grid(row=0, column=3, sticky="ew", padx=15, pady=8)
        ai_frame.grid_columnconfigure(0, weight=1)
        
        # AI input
        self.ai_entry = ctk.CTkEntry(
            ai_frame, 
            placeholder_text="Ask AI to generate a query...",
            height=36,
            font=ctk.CTkFont(size=12),
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
            fg_color="#9B8F5E",
            hover_color="#87795A",
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
            fg_color="#9B8F5E",
            hover_color="#87795A",
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
            font=("Consolas", 13),
            bg="#E8DFD0",
            fg="#8B7355",
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
            font=("Consolas", 13),
            bg="#F5EFE7",
            fg="#3E2723",
            insertbackground="#9B8F5E",
            selectbackground="#9B8F5E",
            selectforeground="white",
            wrap=tk.NONE,
            undo=True,
            maxundo=50,
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightcolor="#9B8F5E",
            highlightbackground="#E8DFD0",
            padx=12,
            pady=8
        )
        
        # Scrollbars for query editor
        query_v_scroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.query_text.yview)
        query_h_scroll = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.query_text.xview)
        self.query_text.configure(yscrollcommand=query_v_scroll.set, xscrollcommand=query_h_scroll.set)
        
        # Configure scrollbar styles
        style = ttk.Style()
        style.configure("Vertical.TScrollbar", background="#E8DFD0", troughcolor="#F5EFE7", borderwidth=1)
        style.configure("Horizontal.TScrollbar", background="#E8DFD0", troughcolor="#F5EFE7", borderwidth=1)
        
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
        info_frame = ctk.CTkFrame(self, height=35, fg_color="#E8DFD0", corner_radius=8)
        info_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        
        self.query_info = ctk.CTkLabel(
            info_frame, 
            text="Ready to execute queries",
            font=ctk.CTkFont(size=12),
            text_color="#3E2723"
        )
        self.query_info.pack(side="left", padx=15, pady=8)
        
        self.execution_time = ctk.CTkLabel(
            info_frame, 
            text="", 
            font=ctk.CTkFont(size=12),
            text_color="#3E2723"
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
        
        # Configure tag for inline suggestions
        self.query_text.tag_configure("suggestion", foreground="#8B7355", font=("Consolas", 13, "italic"))
        
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
    
    def execute_query(self):
        """Execute the current query"""
        query = self.get_current_query()
        if not query.strip():
            messagebox.showwarning("Empty Query", "Please enter a SQL query to execute")
            return
        
        # Update UI to show execution in progress
        self.query_info.configure(text="Executing query...")
        self.execute_all_btn.configure(text="⏳", state="disabled")
        self.execution_time.configure(text="")
        
        # Execute in background thread to prevent UI freezing
        def execute_in_background():
            start_time = time.time()
            
            try:
                # Execute query using callback
                results, columns_or_error = self.execute_callback(query)
                execution_time = time.time() - start_time
                
                # Update UI on main thread
                self.after(0, lambda: self.handle_query_result(results, columns_or_error, execution_time, query))
                
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
        selected_text = self.get_selected_text().strip()
        if not selected_text:
            messagebox.showwarning("No Selection", "Please select the SQL text you want to execute")
            return
        
        # Update UI to show execution in progress
        self.query_info.configure(text="Executing selected query...")
        self.execute_selected_btn.configure(text="◉⏳", state="disabled")
        self.execution_time.configure(text="")
        
        # Execute in background thread to prevent UI freezing
        def execute_in_background():
            start_time = time.time()
            
            try:
                # Execute query using callback
                results, columns_or_error = self.execute_callback(selected_text)
                execution_time = time.time() - start_time
                
                # Update UI on main thread
                self.after(0, lambda: self.handle_selected_query_result(results, columns_or_error, execution_time, selected_text))
                
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
            return self.query_text.get(tk.SEL_FIRST, tk.SEL_LAST)
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
        
        # Check if we should show table autocomplete (popup)
        self.check_for_table_autocomplete()
        
        # Check for keyword autocomplete (inline) - do this after table autocomplete
        # so we don't suggest keywords when table popup is showing
        if not (self.autocomplete_popup and self.autocomplete_popup.winfo_ismapped()):
            self.check_for_keyword_autocomplete()
    
    def check_for_table_autocomplete(self):
        """Check if we should show table autocomplete popup"""
        try:
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
        if self.autocomplete_popup:
            return
        
        # Create toplevel window
        self.autocomplete_popup = tk.Toplevel(self)
        self.autocomplete_popup.withdraw()  # Hide initially
        self.autocomplete_popup.overrideredirect(True)  # Remove window decorations
        self.autocomplete_popup.wm_attributes("-topmost", True)  # Keep on top
        
        # Create frame
        popup_frame = tk.Frame(self.autocomplete_popup, bg="#F5EFE7", bd=1, relief=tk.SOLID)
        popup_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(popup_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create listbox
        self.autocomplete_listbox = tk.Listbox(
            popup_frame,
            font=("Consolas", 11),
            bg="#F5EFE7",
            fg="#3E2723",
            selectbackground="#9B8F5E",
            selectforeground="white",
            highlightthickness=0,
            borderwidth=0,
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
            self.autocomplete_popup.withdraw()
    
    def on_autocomplete_select(self, event=None):
        """Handle selection from autocomplete popup"""
        if not self.autocomplete_listbox:
            return
        
        selection = self.autocomplete_listbox.curselection()
        if selection:
            selected_table = self.autocomplete_listbox.get(selection[0])
            self.insert_autocomplete_table(selected_table)
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
