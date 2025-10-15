"""
Utility functions for NeuronDB
"""

import os
import logging
import json
from pathlib import Path
from typing import Any, Dict, List
import sqlparse
from sqlparse import sql, tokens

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_file = logs_dir / "neurondb.log"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def format_sql_query(query: str) -> str:
    """Format SQL query for better readability"""
    try:
        formatted = sqlparse.format(
            query,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower',
            strip_comments=False,
            strip_whitespace=True
        )
        return formatted
    except Exception:
        # If formatting fails, return original query
        return query

def validate_sql_syntax(query: str) -> Dict[str, Any]:
    """Basic SQL syntax validation"""
    try:
        # Parse the query
        parsed = sqlparse.parse(query)
        
        if not parsed:
            return {
                'valid': False,
                'error': 'Empty or invalid query'
            }
        
        # Check for common syntax issues
        statement = parsed[0]
        
        # Check if it's a valid statement type
        first_token = None
        for token in statement.flatten():
            if token.ttype not in (tokens.Whitespace, tokens.Comment.Single, tokens.Comment.Multiline):
                first_token = token
                break
        
        if first_token is None:
            return {
                'valid': False,
                'error': 'No valid SQL statement found'
            }
        
        valid_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'WITH']
        if first_token.value.upper() not in valid_keywords:
            return {
                'valid': False,
                'error': f'Unsupported statement type: {first_token.value}'
            }
        
        return {
            'valid': True,
            'statement_type': first_token.value.upper(),
            'formatted_query': format_sql_query(query)
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Syntax validation error: {str(e)}'
        }

def extract_table_names(query: str) -> List[str]:
    """Extract table names from SQL query"""
    try:
        parsed = sqlparse.parse(query)
        tables = []
        
        for statement in parsed:
            for token in statement.flatten():
                if token.ttype is tokens.Name:
                    # Simple heuristic to identify potential table names
                    # In a more sophisticated implementation, you'd use proper SQL parsing
                    tables.append(token.value)
        
        return list(set(tables))  # Remove duplicates
    except Exception:
        return []

def safe_json_load(file_path: Path, default: Any = None) -> Any:
    """Safely load JSON file with fallback"""
    try:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else {}

def safe_json_save(data: Any, file_path: Path) -> bool:
    """Safely save data to JSON file"""
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_bytes(bytes_size: int) -> str:
    """Format bytes size to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def get_app_config_dir() -> Path:
    """Get application configuration directory"""
    if os.name == 'nt':  # Windows
        config_dir = Path(os.environ.get('APPDATA', '')) / 'NeuronDB'
    else:  # macOS and Linux
        config_dir = Path.home() / '.config' / 'neurondb'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_recent_queries_file() -> Path:
    """Get path to recent queries file"""
    return get_app_config_dir() / 'recent_queries.json'

def save_recent_query(query: str, max_recent: int = 50):
    """Save query to recent queries list"""
    recent_file = get_recent_queries_file()
    recent_queries = safe_json_load(recent_file, [])
    
    # Remove query if it already exists (to move it to top)
    if query in recent_queries:
        recent_queries.remove(query)
    
    # Add to beginning
    recent_queries.insert(0, query)
    
    # Keep only max_recent queries
    recent_queries = recent_queries[:max_recent]
    
    safe_json_save(recent_queries, recent_file)

def get_recent_queries() -> List[str]:
    """Get list of recent queries"""
    recent_file = get_recent_queries_file()
    return safe_json_load(recent_file, [])

def is_select_query(query: str) -> bool:
    """Check if query is a SELECT statement"""
    query_upper = query.strip().upper()
    return query_upper.startswith('SELECT') or query_upper.startswith('WITH')

def estimate_query_risk(query: str) -> Dict[str, Any]:
    """Estimate the risk level of executing a query"""
    query_upper = query.strip().upper()
    
    # High risk operations
    high_risk_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
    medium_risk_keywords = ['UPDATE', 'INSERT']
    
    risk_level = 'LOW'
    warnings = []
    
    for keyword in high_risk_keywords:
        if keyword in query_upper:
            risk_level = 'HIGH'
            warnings.append(f'Contains {keyword} operation - can permanently modify or delete data')
            break
    
    if risk_level != 'HIGH':
        for keyword in medium_risk_keywords:
            if keyword in query_upper:
                risk_level = 'MEDIUM'
                warnings.append(f'Contains {keyword} operation - will modify data')
                break
    
    # Check for potentially dangerous patterns
    if 'WHERE' not in query_upper and any(keyword in query_upper for keyword in ['DELETE', 'UPDATE']):
        risk_level = 'HIGH'
        warnings.append('DELETE/UPDATE without WHERE clause - affects all rows')
    
    return {
        'risk_level': risk_level,
        'warnings': warnings,
        'is_safe': risk_level == 'LOW'
    }