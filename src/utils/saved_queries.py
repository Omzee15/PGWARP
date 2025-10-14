"""
Saved queries manager for PgWarp
"""

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
    
    def __init__(self, title: str, query: str, query_id: str = None, created_at: str = None, updated_at: str = None):
        self.id = query_id or str(uuid.uuid4())
        self.title = title
        self.query = query
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'query': self.query,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SavedQuery':
        """Create SavedQuery from dictionary"""
        return cls(
            title=data['title'],
            query=data['query'],
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
    
    def add_query(self, title: str, query: str) -> SavedQuery:
        """Add a new saved query"""
        saved_query = SavedQuery(title=title, query=query)
        self.queries.append(saved_query)
        self.save_queries()
        return saved_query
    
    def update_query(self, query_id: str, title: str = None, query: str = None) -> bool:
        """Update an existing saved query"""
        for q in self.queries:
            if q.id == query_id:
                if title is not None:
                    q.title = title
                if query is not None:
                    q.query = query
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
