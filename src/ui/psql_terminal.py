"""
PSQL Terminal component for interactive PostgreSQL command-line interface
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
import customtkinter as ctk
import subprocess
import threading
import queue
import os
from typing import Optional

class PSQLTerminal(ctk.CTkFrame):
    """Interactive PSQL terminal interface"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.connection = None
        self.process = None
        self.output_queue = queue.Queue()
        self.command_history = []
        self.history_index = -1
        
        # Create UI components
        self.create_widgets()
    
    def create_widgets(self):
        """Create PSQL terminal widgets"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, height=50)
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        header_frame.grid_columnconfigure(0, weight=1)
        
        self.header_label = ctk.CTkLabel(
            header_frame, 
            text="PSQL Terminal - Not Connected", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.header_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        # Connect button
        self.connect_btn = ctk.CTkButton(
            header_frame, 
            text="Connect", 
            command=self.connect_psql,
            width=120,
            height=32,
            state="disabled"
        )
        self.connect_btn.grid(row=0, column=1, padx=12, pady=10)
        
        # Disconnect button
        self.disconnect_btn = ctk.CTkButton(
            header_frame, 
            text="Disconnect", 
            command=self.disconnect_psql,
            width=120,
            height=32,
            state="disabled"
        )
        self.disconnect_btn.grid(row=0, column=2, padx=8, pady=10)
        
        # Clear button
        self.clear_btn = ctk.CTkButton(
            header_frame, 
            text="Clear", 
            command=self.clear_terminal,
            width=100,
            height=32
        )
        self.clear_btn.grid(row=0, column=3, padx=(8, 15), pady=10)
        
        # Terminal area
        terminal_frame = ctk.CTkFrame(self)
        terminal_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        terminal_frame.grid_columnconfigure(0, weight=1)
        terminal_frame.grid_rowconfigure(0, weight=1)
        
        # Terminal text widget
        self.terminal_text = tk.Text(
            terminal_frame,
            font=("Consolas", 12),
            bg="#F5EFE7",
            fg="#3E2723",
            insertbackground="#9B8F5E",
            selectbackground="#9B8F5E",
            selectforeground="white",
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightcolor="#9B8F5E",
            padx=10,
            pady=5
        )
        
        # Scrollbar
        terminal_scroll = ttk.Scrollbar(terminal_frame, command=self.terminal_text.yview)
        self.terminal_text.configure(yscrollcommand=terminal_scroll.set)
        
        # Configure scrollbar style
        style = ttk.Style()
        style.configure("Terminal.Vertical.TScrollbar", 
                        background="#E8DFD0", 
                        troughcolor="#F5EFE7", 
                        borderwidth=1,
                        arrowcolor="#9B8F5E")
        terminal_scroll.configure(style="Terminal.Vertical.TScrollbar")
        
        # Pack terminal and scrollbar
        self.terminal_text.grid(row=0, column=0, sticky="nsew", padx=(1, 0), pady=(1, 0))
        terminal_scroll.grid(row=0, column=1, sticky="ns", pady=(1, 0))
        
        # Command input frame
        input_frame = ctk.CTkFrame(self, height=50)
        input_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Prompt label
        self.prompt_label = ctk.CTkLabel(
            input_frame, 
            text="psql>", 
            font=ctk.CTkFont(family="Consolas", size=12),
            width=60
        )
        self.prompt_label.grid(row=0, column=0, padx=(15, 8), pady=12)
        
        # Command input
        self.command_entry = ctk.CTkEntry(
            input_frame, 
            font=ctk.CTkFont(family="Consolas", size=12),
            height=32,
            state="disabled"
        )
        self.command_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=12)
        self.command_entry.bind("<Return>", self.execute_command)
        self.command_entry.bind("<Up>", self.history_up)
        self.command_entry.bind("<Down>", self.history_down)
        
        # Send button
        self.send_btn = ctk.CTkButton(
            input_frame, 
            text="Send", 
            command=self.execute_command,
            width=100,
            height=32,
            state="disabled"
        )
        self.send_btn.grid(row=0, column=2, padx=(8, 15), pady=12)
        
        # Initial message
        self.write_to_terminal("Welcome to PgWarp PSQL Terminal\n")
        self.write_to_terminal("Connect to a database to start using the interactive PostgreSQL shell.\n\n")
    
    def set_connection(self, db_connection):
        """Set the database connection"""
        self.connection = db_connection
        if db_connection and db_connection.is_connected():
            self.header_label.configure(text="PSQL Terminal - Connected")
            self.connect_btn.configure(state="normal")
        else:
            self.header_label.configure(text="PSQL Terminal - Not Connected")
            self.connect_btn.configure(state="disabled")
    
    def clear_connection(self):
        """Clear the database connection"""
        self.disconnect_psql()
        self.connection = None
        self.header_label.configure(text="PSQL Terminal - Not Connected")
        self.connect_btn.configure(state="disabled")
    
    def connect_psql(self):
        """Connect to PSQL process"""
        if not self.connection or not self.connection.is_connected():
            self.write_to_terminal("Error: No database connection available.\n", color="#CD853F")
            return
        
        if self.process and self.process.poll() is None:
            self.write_to_terminal("PSQL is already running.\n")
            return
        
        try:
            # Get connection info
            conn_info = self.connection.connection_info
            
            # Construct psql command
            cmd = [
                "psql",
                "-h", conn_info['host'],
                "-p", str(conn_info['port']),
                "-U", conn_info['username'],
                "-d", conn_info['database']
            ]
            
            # Set environment for password (if available)
            env = os.environ.copy()
            if 'password' in conn_info and conn_info['password']:
                env['PGPASSWORD'] = conn_info['password']
            
            # Start psql process
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            
            # Start output reader thread
            self.start_output_reader()
            
            # Update UI
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.command_entry.configure(state="normal")
            self.send_btn.configure(state="normal")
            
            self.write_to_terminal(f"Connected to PSQL: {conn_info['database']}@{conn_info['host']}:{conn_info['port']}\n")
            
            # Focus on command input
            self.command_entry.focus()
            
        except FileNotFoundError:
            self.write_to_terminal("Error: 'psql' command not found. Please ensure PostgreSQL client is installed and in PATH.\n", color="#CD853F")
        except Exception as e:
            self.write_to_terminal(f"Error connecting to PSQL: {e}\n", color="#CD853F")
    
    def disconnect_psql(self):
        """Disconnect from PSQL process"""
        if self.process and self.process.poll() is None:
            try:
                # Send quit command
                self.process.stdin.write("\\q\n")
                self.process.stdin.flush()
                
                # Wait for process to terminate
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't quit gracefully
                self.process.kill()
            except Exception:
                pass
            
            self.process = None
        
        # Update UI
        self.connect_btn.configure(state="normal" if self.connection else "disabled")
        self.disconnect_btn.configure(state="disabled")
        self.command_entry.configure(state="disabled")
        self.send_btn.configure(state="disabled")
        
        self.write_to_terminal("Disconnected from PSQL.\n")
    
    def start_output_reader(self):
        """Start thread to read PSQL output"""
        def read_output():
            try:
                while self.process and self.process.poll() is None:
                    line = self.process.stdout.readline()
                    if line:
                        self.output_queue.put(line)
                    
                # Read any remaining output
                if self.process:
                    remaining = self.process.stdout.read()
                    if remaining:
                        self.output_queue.put(remaining)
                        
            except Exception as e:
                self.output_queue.put(f"Error reading output: {e}\n")
        
        # Start reader thread
        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()
        
        # Start output processor
        self.process_output()
    
    def process_output(self):
        """Process output from PSQL"""
        try:
            while True:
                try:
                    line = self.output_queue.get_nowait()
                    self.write_to_terminal(line)
                except queue.Empty:
                    break
        except Exception:
            pass
        
        # Schedule next check
        if self.process and self.process.poll() is None:
            self.after(100, self.process_output)
        else:
            # Process has ended
            if self.process:
                self.disconnect_psql()
    
    def execute_command(self, event=None):
        """Execute a command in PSQL"""
        if not self.process or self.process.poll() is not None:
            self.write_to_terminal("Error: PSQL is not running.\n", color="#CD853F")
            return
        
        command = self.command_entry.get().strip()
        if not command:
            return
        
        try:
            # Add to history
            if command not in self.command_history:
                self.command_history.append(command)
                # Keep only last 100 commands
                if len(self.command_history) > 100:
                    self.command_history.pop(0)
            
            self.history_index = len(self.command_history)
            
            # Display command in terminal
            self.write_to_terminal(f"psql> {command}\n", color="#8B7355")  # Brown for commands
            
            # Send command to PSQL
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            
            # Clear input
            self.command_entry.delete(0, tk.END)
            
        except Exception as e:
            self.write_to_terminal(f"Error executing command: {e}\n", color="#CD853F")
    
    def history_up(self, event):
        """Navigate up in command history"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
    
    def history_down(self, event):
        """Navigate down in command history"""
        if self.command_history:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_entry.delete(0, tk.END)
                self.command_entry.insert(0, self.command_history[self.history_index])
            elif self.history_index == len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self.command_entry.delete(0, tk.END)
    
    def write_to_terminal(self, text: str, color: Optional[str] = None):
        """Write text to terminal display"""
        self.terminal_text.configure(state=tk.NORMAL)
        
        if color:
            # Create tag for colored text
            tag_name = f"color_{color}"
            self.terminal_text.tag_configure(tag_name, foreground=color)
            self.terminal_text.insert(tk.END, text, tag_name)
        else:
            self.terminal_text.insert(tk.END, text)
        
        # Auto-scroll to bottom
        self.terminal_text.see(tk.END)
        self.terminal_text.configure(state=tk.DISABLED)
        
        # Update display
        self.terminal_text.update_idletasks()
    
    def clear_terminal(self):
        """Clear the terminal display"""
        self.terminal_text.configure(state=tk.NORMAL)
        self.terminal_text.delete(1.0, tk.END)
        self.terminal_text.configure(state=tk.DISABLED)
        
        # Show welcome message again
        self.write_to_terminal("Terminal cleared.\n")
    
    def insert_common_command(self, command: str):
        """Insert a common PSQL command"""
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, command)
        self.command_entry.focus()
    
    def get_common_commands(self) -> list:
        """Get list of common PSQL commands"""
        return [
            "\\l",  # List databases
            "\\dt",  # List tables
            "\\d",  # Describe table
            "\\du",  # List users
            "\\dn",  # List schemas
            "\\df",  # List functions
            "\\dv",  # List views
            "\\di",  # List indexes
            "\\q",  # Quit
            "\\h",  # Help
            "\\?",  # List commands
            "SELECT version();",
            "SELECT current_database();",
            "SELECT current_user;",
            "SHOW ALL;",
        ]
    
    def show_help(self):
        """Show PSQL help information"""
        help_text = """
Common PSQL Commands:
\\l          - List all databases
\\dt         - List tables in current database
\\d [table]  - Describe table structure
\\du         - List database users
\\dn         - List schemas
\\df         - List functions
\\dv         - List views
\\di         - List indexes
\\q          - Quit PSQL
\\h [cmd]    - Help on SQL command
\\?          - List all PSQL commands

Navigation:
- Use Up/Down arrows to navigate command history
- Use Tab for auto-completion (if supported)
- Semicolon (;) ends SQL statements

SQL Examples:
SELECT * FROM table_name LIMIT 10;
INSERT INTO table_name (col1, col2) VALUES ('val1', 'val2');
UPDATE table_name SET col1 = 'new_value' WHERE condition;
DELETE FROM table_name WHERE condition;
"""
        self.write_to_terminal(help_text)
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except:
                pass