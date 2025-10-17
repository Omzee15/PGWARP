"""
Saved variables management for NeuronDB
Allows users to define and reuse variables in queries
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SavedVariablesManager:
    """Manages user-defined variables for query reuse"""
    
    def __init__(self):
        """Initialize the saved variables manager"""
        # Determine config directory based on OS
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', '')) / 'PgWarp'
        else:  # macOS/Linux
            config_dir = Path.home() / '.config' / 'pgwarp'
        
        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        
        self.variables_file = config_dir / 'saved_variables.json'
        self.variables = self.load_variables()
    
    def load_variables(self) -> Dict[str, str]:
        """Load saved variables from file"""
        if not self.variables_file.exists():
            return {}
        
        try:
            with open(self.variables_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load variables: {e}")
            return {}
    
    def save_variables(self) -> bool:
        """Save variables to file"""
        try:
            with open(self.variables_file, 'w', encoding='utf-8') as f:
                json.dump(self.variables, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save variables: {e}")
            return False
    
    def add_variable(self, name: str, value: str) -> bool:
        """Add or update a variable"""
        try:
            # Clean variable name (remove {{ }} if present)
            clean_name = name.strip()
            if clean_name.startswith('{{') and clean_name.endswith('}}'):
                clean_name = clean_name[2:-2].strip()
            
            self.variables[clean_name] = value
            return self.save_variables()
        except Exception as e:
            logger.error(f"Failed to add variable: {e}")
            return False
    
    def delete_variable(self, name: str) -> bool:
        """Delete a variable"""
        try:
            if name in self.variables:
                del self.variables[name]
                return self.save_variables()
            return False
        except Exception as e:
            logger.error(f"Failed to delete variable: {e}")
            return False
    
    def get_variable(self, name: str) -> Optional[str]:
        """Get a variable value by name"""
        return self.variables.get(name)
    
    def get_all_variables(self) -> Dict[str, str]:
        """Get all variables"""
        return self.variables.copy()
    
    def get_variable_names(self) -> List[str]:
        """Get list of all variable names"""
        return list(self.variables.keys())
    
    def substitute_variables(self, query: str) -> Tuple[str, List[str]]:
        """
        Substitute variables in query (format: {{variable_name}})
        Returns: (substituted_query, list_of_missing_variables)
        """
        import re
        
        # Find all variable placeholders
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, query)
        
        missing_variables = []
        substituted_query = query
        
        for var_name in matches:
            var_name = var_name.strip()
            if var_name in self.variables:
                # Replace the variable with its value
                placeholder = '{{' + var_name + '}}'
                substituted_query = substituted_query.replace(placeholder, self.variables[var_name])
            else:
                missing_variables.append(var_name)
        
        return substituted_query, missing_variables
    
    def clear_all_variables(self) -> bool:
        """Clear all saved variables"""
        try:
            self.variables = {}
            return self.save_variables()
        except Exception as e:
            logger.error(f"Failed to clear variables: {e}")
            return False
    
    def import_variables(self, variables: Dict[str, str]) -> bool:
        """Import variables from a dictionary"""
        try:
            self.variables.update(variables)
            return self.save_variables()
        except Exception as e:
            logger.error(f"Failed to import variables: {e}")
            return False
    
    def export_variables(self) -> Dict[str, str]:
        """Export all variables"""
        return self.variables.copy()
