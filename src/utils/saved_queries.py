"""
Saved queries manager for NeuronDB
Handles storage and retrieval of saved SQL queries
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class SavedQuery:
    """Represents a saved SQL query"""
    id: str
    title: str
    query: str
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class SavedQueriesManager:
    """Manages saved queries with persistent storage"""
    
    def __init__(self):
        # Determine config directory based on OS
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', '')) / 'NeuronDB'
        else:  # macOS/Linux
            config_dir = Path.home() / '.config' / 'neurondb'

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import uuid


def get_app_config_dir() -> Path:
    """Get application configuration directory"""
    import os
    if os.name == 'nt':  # Windows
        config_dir = Path(os.environ.get('APPDATA', '')) / 'PgWarp'
    else:  # macOS and Linux
        config_dir = Path.home() / '.config' / 'pgwarp'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_saved_queries_file() -> Path:
    """Get path to saved queries file"""
    return get_app_config_dir() / 'saved_queries.json'


class SavedQuery:
    """Represents a saved query"""
    
    def __init__(self, title: str, query: str, shortcut: str = None, query_id: str = None, created_at: str = None, updated_at: str = None):
        self.id = query_id or str(uuid.uuid4())
        self.title = title
        self.query = query
        self.shortcut = shortcut  # New shortcut field
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'query': self.query,
            'shortcut': self.shortcut,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SavedQuery':
        """Create SavedQuery from dictionary"""
        return cls(
            title=data['title'],
            query=data['query'],
            shortcut=data.get('shortcut'),  # Handle existing queries without shortcuts
            query_id=data.get('id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class SavedQueriesManager:
    """Manager for saved queries"""
    
    def __init__(self):
        self.queries_file = get_saved_queries_file()
        self.queries: List[SavedQuery] = []
        self.load_queries()
    
    def load_queries(self):
        """Load saved queries from file"""
        try:
            if self.queries_file.exists():
                with open(self.queries_file, 'r') as f:
                    data = json.load(f)
                    self.queries = [SavedQuery.from_dict(q) for q in data]
            else:
                self.queries = []
        except Exception as e:
            print(f"Error loading saved queries: {e}")
            self.queries = []
    
    def save_queries(self):
        """Save queries to file"""
        try:
            self.queries_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.queries_file, 'w') as f:
                json.dump([q.to_dict() for q in self.queries], f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving queries: {e}")
            return False
    
    def add_query(self, title: str, query: str, shortcut: str = None) -> SavedQuery:
        """Add a new saved query"""
        # Validate shortcut if provided
        if shortcut and not self.is_shortcut_valid(shortcut):
            raise ValueError("Invalid shortcut format. Use only letters, numbers, and underscores.")
        
        if shortcut and self.get_query_by_shortcut(shortcut):
            raise ValueError(f"Shortcut '{shortcut}' already exists.")
        
        saved_query = SavedQuery(title=title, query=query, shortcut=shortcut)
        self.queries.append(saved_query)
        self.save_queries()
        return saved_query
    
    def update_query(self, query_id: str, title: str = None, query: str = None, shortcut: str = None) -> bool:
        """Update an existing saved query"""
        # Validate shortcut if provided
        if shortcut is not None:
            if shortcut and not self.is_shortcut_valid(shortcut):
                raise ValueError("Invalid shortcut format. Use only letters, numbers, and underscores.")
            
            # Check if shortcut is already used by another query
            existing_query = self.get_query_by_shortcut(shortcut)
            if existing_query and existing_query.id != query_id:
                raise ValueError(f"Shortcut '{shortcut}' already exists.")
        
        for q in self.queries:
            if q.id == query_id:
                if title is not None:
                    q.title = title
                if query is not None:
                    q.query = query
                if shortcut is not None:
                    q.shortcut = shortcut
                q.updated_at = datetime.now().isoformat()
                self.save_queries()
                return True
        return False
    
    def delete_query(self, query_id: str) -> bool:
        """Delete a saved query"""
        original_length = len(self.queries)
        self.queries = [q for q in self.queries if q.id != query_id]
        if len(self.queries) < original_length:
            self.save_queries()
            return True
        return False
    
    def get_query(self, query_id: str) -> Optional[SavedQuery]:
        """Get a saved query by ID"""
        for q in self.queries:
            if q.id == query_id:
                return q
        return None
    
    def get_all_queries(self) -> List[SavedQuery]:
        """Get all saved queries"""
        return self.queries.copy()
    
    def search_queries(self, search_term: str) -> List[SavedQuery]:
        """Search queries by title or content"""
        search_term = search_term.lower()
        return [
            q for q in self.queries
            if search_term in q.title.lower() or search_term in q.query.lower()
        ]
    
    def get_query_by_shortcut(self, shortcut: str) -> Optional[SavedQuery]:
        """Get a saved query by its shortcut"""
        if not shortcut:
            return None
        for q in self.queries:
            if q.shortcut and q.shortcut.lower() == shortcut.lower():
                return q
        return None
    
    def get_all_shortcuts(self) -> Dict[str, str]:
        """Get all shortcuts and their corresponding query titles"""
        shortcuts = {}
        for q in self.queries:
            if q.shortcut:
                shortcuts[q.shortcut] = q.title
        return shortcuts
    
    def is_shortcut_valid(self, shortcut: str) -> bool:
        """Validate shortcut format (letters, numbers, underscores only)"""
        import re
        if not shortcut:
            return True  # Empty shortcut is valid (means no shortcut)
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', shortcut))
    
    def substitute_query_shortcuts(self, text: str) -> str:
        """Replace {{shortcut}} patterns with actual query text"""
        import re
        
        def replace_shortcut(match):
            shortcut = match.group(1)
            query = self.get_query_by_shortcut(shortcut)
            if query:
                return query.query
            else:
                return match.group(0)  # Return original if shortcut not found
        
        # Replace {{shortcut}} patterns
        return re.sub(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}', replace_shortcut, text)
