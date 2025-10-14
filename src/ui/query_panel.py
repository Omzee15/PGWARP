"""
Query panel component for SQL editing and execution
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import customtkinter as ctk
from typing import Dict, Any, Callable, Optional, List, Tuple
import threading
import time

class QueryPanel(ctk.CTkFrame):
    """Query panel with SQL editor and AI assistant"""
    
    def __init__(self, parent, execute_callback, ai_callback, results_callback=None):
        super().__init__(parent)
        
        # Callbacks
        self.execute_callback = execute_callback
        self.ai_callback = ai_callback  
        self.results_callback = results_callback  # Callback to display results in main window
        
        # Current state
        self.current_results = []
        self.current_columns = []
        
        # Create UI components
        self.create_widgets()
    
    def create_widgets(self):
        """Create query panel widgets"""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Query editor
        
        # Top toolbar
        toolbar_frame = ctk.CTkFrame(self, height=60, fg_color="#E8DFD0")
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        toolbar_frame.grid_columnconfigure(2, weight=1)
        
        # Execute button
        self.execute_btn = ctk.CTkButton(
            toolbar_frame, 
            text="▶ Execute", 
            command=self.execute_query,
            width=120,
            height=36
        )
        self.execute_btn.grid(row=0, column=0, padx=(10, 8), pady=12)
        
        # Clear button
        self.clear_btn = ctk.CTkButton(
            toolbar_frame, 
            text="🗑 Clear", 
            command=self.clear_query,
            width=100,
            height=36,
            fg_color="#E8DFD0",
            hover_color="#D9CDBF"
        )
        self.clear_btn.grid(row=0, column=1, padx=8, pady=12)
        
        # AI chat frame
        ai_frame = ctk.CTkFrame(toolbar_frame)
        ai_frame.grid(row=0, column=2, sticky="ew", padx=15, pady=8)
        ai_frame.grid_columnconfigure(0, weight=1)
        
        # AI input
        self.ai_entry = ctk.CTkEntry(
            ai_frame, 
            placeholder_text="Ask AI to generate a query...",
            height=36,
            font=ctk.CTkFont(size=12)
        )
        self.ai_entry.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.ai_entry.bind("<Return>", self.on_ai_enter)
        
        # AI generate button
        self.ai_btn = ctk.CTkButton(
            ai_frame, 
            text="🤖 Generate", 
            command=self.generate_with_ai,
            width=120,
            height=36
        )
        self.ai_btn.grid(row=0, column=1, padx=8, pady=8)
        
        # Format button
        self.format_btn = ctk.CTkButton(
            toolbar_frame, 
            text="📐 Format", 
            command=self.format_query,
            width=100,
            height=36
        )
        self.format_btn.grid(row=0, column=3, padx=(8, 10), pady=12)
        
        # Query editor
        editor_frame = ctk.CTkFrame(self)
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(0, weight=1)
        
        # Query text area
        self.query_text = tk.Text(
            editor_frame,
            font=("Consolas", 13),
            bg="#F5EFE7",
            fg="#3E2723",
            insertbackground="#9B8F5E",
            selectbackground="#9B8F5E",
            selectforeground="white",
            wrap=tk.WORD,
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
        
        # Pack query editor and scrollbars
        self.query_text.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=(2, 0))
        query_v_scroll.grid(row=0, column=1, sticky="ns", pady=(2, 0))
        query_h_scroll.grid(row=1, column=0, sticky="ew", padx=(2, 0))
        
        # Query info frame
        info_frame = ctk.CTkFrame(self, height=35, fg_color="#E8DFD0")
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
        self.query_text.bind("<Control-Return>", lambda e: self.execute_query())
        self.query_text.bind("<F5>", lambda e: self.execute_query())
        
        # Add some sample placeholder text
        sample_query = "-- Welcome to PgWarp Query Tool\n-- Write your SQL queries here\n-- Press Ctrl+Enter or F5 to execute\n-- Use the AI assistant above to generate queries\n\nSELECT version();"
        self.query_text.insert("1.0", sample_query)
    
    def execute_query(self):
        """Execute the current query"""
        query = self.get_current_query()
        if not query.strip():
            messagebox.showwarning("Empty Query", "Please enter a SQL query to execute")
            return
        
        # Update UI to show execution in progress
        self.query_info.configure(text="Executing query...")
        self.execute_btn.configure(text="⏳ Executing...", state="disabled")
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
    
    def handle_query_result(self, results: Optional[List[Dict]], columns_or_error, execution_time: float, query: str):
        """Handle successful query execution result"""
        # Restore execute button
        self.execute_btn.configure(text="▶ Execute", state="normal")
        
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
        self.execute_btn.configure(text="▶ Execute", state="normal")
        
        # Update info
        self.query_info.configure(text=f"Query failed: {error_message}")
        self.execution_time.configure(text=f"Execution time: {execution_time:.3f}s")
        
        # Clear results in main window
        if self.results_callback:
            self.results_callback([], [])
        
        # Show error dialog
        messagebox.showerror("Query Error", f"Query execution failed:\n\n{error_message}")
    
    def get_current_query(self) -> str:
        """Get the current query text"""
        return self.query_text.get("1.0", tk.END).strip()
    
    def set_query(self, query: str):
        """Set the query text"""
        self.query_text.delete("1.0", tk.END)
        self.query_text.insert("1.0", query)
    
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