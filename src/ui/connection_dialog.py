"""
Connection dialog for managing database connections
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Dict, Any, Optional

class ConnectionDialog(ctk.CTkToplevel):
    """Dialog for creating and managing database connections"""
    
    def __init__(self, parent, connection_manager):
        super().__init__(parent)
        
        self.connection_manager = connection_manager
        self.selected_connection = None
        
        # Configure dialog
        self.title("Database Connection")
        self.geometry("600x750")
        self.minsize(550, 700)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.center_window()
        
        # Create UI components
        self.create_widgets()
        self.load_saved_connections()
        
        # Focus on dialog
        self.focus()
    
    def center_window(self):
        """Center the dialog on the parent window"""
        self.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        # Calculate position for centering
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        self.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create dialog widgets"""
        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Main frame inside scrollable frame
        main_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#F5EFE7")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Database Connection", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Saved connections section
        saved_frame = ctk.CTkFrame(main_frame, fg_color="#E8DFD0")
        saved_frame.pack(fill="x", pady=(0, 25))
        
        saved_label = ctk.CTkLabel(
            saved_frame, 
            text="Saved Connections", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        saved_label.pack(pady=(15, 10))
        
        # Connections listbox frame
        listbox_frame = ctk.CTkFrame(saved_frame, fg_color="#E8DFD0")
        listbox_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Create listbox with scrollbar
        self.connections_listbox = tk.Listbox(
            listbox_frame, 
            height=5,
            font=("Consolas", 11),
            bg="#F5EFE7",
            fg="#3E2723",
            selectbackground="#9B8F5E",
            selectforeground="white",
            borderwidth=1,
            highlightthickness=1,
            highlightcolor="#9B8F5E",
            relief="solid"
        )
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
        scrollbar.config(command=self.connections_listbox.yview)
        self.connections_listbox.config(yscrollcommand=scrollbar.set)
        
        self.connections_listbox.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side="right", fill="y", pady=5, padx=(0, 5))
        
        # Bind selection event
        self.connections_listbox.bind("<<ListboxSelect>>", self.on_connection_select)
        self.connections_listbox.bind("<Double-Button-1>", self.on_connection_double_click)
        
        # Connection buttons
        conn_buttons_frame = ctk.CTkFrame(saved_frame, fg_color="#E8DFD0")
        conn_buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.connect_btn = ctk.CTkButton(
            conn_buttons_frame, 
            text="Connect", 
            command=self.connect_selected,
            state="disabled",
            height=32,
            width=90,
            font=ctk.CTkFont(size=12)
        )
        self.connect_btn.pack(side="left", padx=(0, 8), pady=8)
        
        self.edit_btn = ctk.CTkButton(
            conn_buttons_frame, 
            text="Edit", 
            command=self.edit_selected,
            state="disabled",
            height=32,
            width=70,
            font=ctk.CTkFont(size=12)
        )
        self.edit_btn.pack(side="left", padx=8, pady=8)
        
        self.delete_btn = ctk.CTkButton(
            conn_buttons_frame, 
            text="Delete", 
            command=self.delete_selected,
            state="disabled",
            fg_color="#9B8F5E",
            hover_color="#87795A",
            height=32,
            width=80,
            font=ctk.CTkFont(size=12)
        )
        self.delete_btn.pack(side="left", padx=8, pady=8)
        
        # Separator
        separator = ctk.CTkFrame(main_frame, height=3, fg_color="#9B8F5E")
        separator.pack(fill="x", pady=(0, 25))
        
        # New connection section
        new_conn_label = ctk.CTkLabel(
            main_frame, 
            text="New Connection", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        new_conn_label.pack(pady=(0, 15))
        
        # Connection form
        form_frame = ctk.CTkFrame(main_frame, fg_color="#E8DFD0")
        form_frame.pack(fill="x", pady=(0, 20))
        
        # Connection name
        ctk.CTkLabel(form_frame, text="Connection Name:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="My Database", height=32, font=ctk.CTkFont(size=12))
        self.name_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Host
        ctk.CTkLabel(form_frame, text="Host:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(0, 5))
        self.host_entry = ctk.CTkEntry(form_frame, placeholder_text="localhost", height=32, font=ctk.CTkFont(size=12))
        self.host_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.host_entry.insert(0, "localhost")  # Default value
        
        # Port
        ctk.CTkLabel(form_frame, text="Port:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(0, 5))
        self.port_entry = ctk.CTkEntry(form_frame, placeholder_text="5432", height=32, font=ctk.CTkFont(size=12))
        self.port_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.port_entry.insert(0, "5432")  # Default value
        
        # Database
        ctk.CTkLabel(form_frame, text="Database:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(0, 5))
        db_note = ctk.CTkLabel(form_frame, text="(Initial database to connect to - usually 'postgres')", 
                              font=ctk.CTkFont(size=10), text_color="#8B7355")
        db_note.pack(anchor="w", padx=15)
        self.database_entry = ctk.CTkEntry(form_frame, placeholder_text="postgres", height=32, font=ctk.CTkFont(size=12))
        self.database_entry.pack(fill="x", padx=15, pady=(5, 15))
        self.database_entry.insert(0, "postgres")  # Default value
        
        # Username
        ctk.CTkLabel(form_frame, text="Username:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(0, 5))
        self.username_entry = ctk.CTkEntry(form_frame, placeholder_text="postgres", height=32, font=ctk.CTkFont(size=12))
        self.username_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Password
        ctk.CTkLabel(form_frame, text="Password:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(0, 5))
        self.password_entry = ctk.CTkEntry(form_frame, placeholder_text="password", show="*", height=32, font=ctk.CTkFont(size=12))
        self.password_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Dialog buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="#F5EFE7")
        buttons_frame.pack(fill="x", pady=(20, 10))
        
        self.test_btn = ctk.CTkButton(
            buttons_frame, 
            text="Test Connection", 
            command=self.test_connection,
            height=36,
            width=140,
            font=ctk.CTkFont(size=12)
        )
        self.test_btn.pack(side="left", padx=(15, 8), pady=10)
        
        self.save_btn = ctk.CTkButton(
            buttons_frame, 
            text="Save", 
            command=self.save_connection,
            height=36,
            width=80,
            font=ctk.CTkFont(size=12)
        )
        self.save_btn.pack(side="left", padx=8, pady=10)
        
        self.connect_now_btn = ctk.CTkButton(
            buttons_frame, 
            text="Connect", 
            command=self.connect_now,
            height=36,
            width=100,
            font=ctk.CTkFont(size=12),
            fg_color="#9B8F5E",
            hover_color="#87795A"
        )
        self.connect_now_btn.pack(side="left", padx=8, pady=10)
        
        self.save_connect_btn = ctk.CTkButton(
            buttons_frame, 
            text="Save & Connect", 
            command=self.save_and_connect,
            height=36,
            width=140,
            font=ctk.CTkFont(size=12),
            fg_color="#9B8F5E",
            hover_color="#87795A"
        )
        self.save_connect_btn.pack(side="left", padx=8, pady=10)
        
        self.cancel_btn = ctk.CTkButton(
            buttons_frame, 
            text="Cancel", 
            command=self.cancel,
            fg_color="#E8DFD0",
            hover_color="#D9CDBF",
            height=36,
            width=80,
            font=ctk.CTkFont(size=12)
        )
        self.cancel_btn.pack(side="right", padx=(8, 15), pady=10)
    
    def load_saved_connections(self):
        """Load saved connections into listbox"""
        self.connections_listbox.delete(0, tk.END)
        
        connections = self.connection_manager.get_all_connections()
        for name, config in connections.items():
            display_text = f"{name} ({config['username']}@{config['host']}:{config['port']}/{config['database']})"
            self.connections_listbox.insert(tk.END, display_text)
    
    def on_connection_select(self, event):
        """Handle connection selection"""
        selection = self.connections_listbox.curselection()
        if selection:
            self.connect_btn.configure(state="normal")
            self.edit_btn.configure(state="normal")
            self.delete_btn.configure(state="normal")
        else:
            self.connect_btn.configure(state="disabled")
            self.edit_btn.configure(state="disabled")
            self.delete_btn.configure(state="disabled")
    
    def on_connection_double_click(self, event):
        """Handle double-click on connection"""
        self.connect_selected()
    
    def get_selected_connection_name(self) -> Optional[str]:
        """Get the name of the selected connection"""
        selection = self.connections_listbox.curselection()
        if not selection:
            return None
        
        display_text = self.connections_listbox.get(selection[0])
        # Extract connection name (everything before the first parenthesis)
        return display_text.split(" (")[0]
    
    def connect_selected(self):
        """Connect to the selected saved connection"""
        conn_name = self.get_selected_connection_name()
        if not conn_name:
            return
        
        config = self.connection_manager.get_connection(conn_name)
        if config:
            self.selected_connection = config
            self.destroy()
    
    def edit_selected(self):
        """Edit the selected connection"""
        conn_name = self.get_selected_connection_name()
        if not conn_name:
            return
        
        config = self.connection_manager.get_connection(conn_name)
        if config:
            # Fill form with connection details
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, conn_name)
            
            self.host_entry.delete(0, tk.END)
            self.host_entry.insert(0, config['host'])
            
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, str(config['port']))
            
            self.database_entry.delete(0, tk.END)
            self.database_entry.insert(0, config['database'])
            
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, config['username'])
            
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, config.get('password', ''))
    
    def delete_selected(self):
        """Delete the selected connection"""
        conn_name = self.get_selected_connection_name()
        if not conn_name:
            return
        
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete the connection '{conn_name}'?"
        )
        
        if result:
            self.connection_manager.remove_connection(conn_name)
            self.load_saved_connections()
            messagebox.showinfo("Success", f"Connection '{conn_name}' deleted successfully")
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get connection data from form"""
        return {
            'name': self.name_entry.get().strip(),
            'host': self.host_entry.get().strip() or 'localhost',
            'port': int(self.port_entry.get().strip() or '5432'),
            'database': self.database_entry.get().strip() or 'postgres',
            'username': self.username_entry.get().strip() or 'postgres',
            'password': self.password_entry.get()
        }
    
    def validate_form(self, require_name: bool = True) -> bool:
        """Validate form data"""
        data = self.get_form_data()
        
        if require_name and not data['name']:
            messagebox.showerror("Validation Error", "Connection name is required")
            return False
        
        if not data['host']:
            messagebox.showerror("Validation Error", "Host is required")
            return False
        
        if not data['database']:
            messagebox.showerror("Validation Error", "Database name is required")
            return False
        
        if not data['username']:
            messagebox.showerror("Validation Error", "Username is required")
            return False
        
        try:
            port = int(data['port'])
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Port must be a valid number between 1 and 65535")
            return False
        
        return True
    
    def test_connection(self):
        """Test the connection with current form data"""
        if not self.validate_form(require_name=False):
            return
        
        data = self.get_form_data()
        
        try:
            # Create connection config for testing
            config = {
                'host': data['host'],
                'port': data['port'],
                'database': data['database'],
                'username': data['username'],
                'password': data['password']
            }
            
            # Test connection
            if self.connection_manager.test_connection(config):
                messagebox.showinfo("Test Connection", "Connection successful!")
            else:
                messagebox.showerror("Test Connection", "Connection failed!")
                
        except Exception as e:
            messagebox.showerror("Test Connection", f"Connection failed:\n{e}")
    
    def save_connection(self):
        """Save the connection configuration"""
        if not self.validate_form():
            return
        
        data = self.get_form_data()
        
        try:
            self.connection_manager.add_connection(
                name=data['name'],
                host=data['host'],
                port=data['port'],
                database=data['database'],
                username=data['username'],
                password=data['password']
            )
            
            self.load_saved_connections()
            messagebox.showinfo("Success", f"Connection '{data['name']}' saved successfully")
            
            # Clear form
            self.clear_form()
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save connection:\n{e}")
    
    def connect_now(self):
        """Connect using current form data without saving"""
        if not self.validate_form(require_name=False):
            return
        
        data = self.get_form_data()
        
        # Create connection config
        config = {
            'host': data['host'],
            'port': data['port'],
            'database': data['database'],
            'username': data['username'],
            'password': data['password']
        }
        
        # Test connection first
        try:
            if self.connection_manager.test_connection(config):
                self.selected_connection = config
                self.destroy()
            else:
                messagebox.showerror("Connection Error", "Failed to connect to database. Please check your connection details.")
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Connection failed:\n{e}")
    
    def save_and_connect(self):
        """Save the connection and connect to it"""
        self.save_connection()
        
        # Get the saved connection and connect
        data = self.get_form_data()
        config = self.connection_manager.get_connection(data['name'])
        if config:
            self.selected_connection = config
            self.destroy()
    
    def clear_form(self):
        """Clear the connection form"""
        self.name_entry.delete(0, tk.END)
        self.host_entry.delete(0, tk.END)
        self.port_entry.delete(0, tk.END)
        self.database_entry.delete(0, tk.END)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
    
    def cancel(self):
        """Cancel dialog"""
        self.selected_connection = None
        self.destroy()