"""
Database connection management for PgWarp
Handles PostgreSQL connections and schema introspection
"""

import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manages PostgreSQL database connections"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connection_info = {}
        
    def connect(self, host: str, port: int, database: str, username: str, password: str) -> bool:
        """Establish connection to PostgreSQL database"""
        try:
            connection_string = f"host='{host}' port='{port}' dbname='{database}' user='{username}' password='{password}'"
            self.connection = psycopg2.connect(connection_string)
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            self.connection_info = {
                'host': host,
                'port': port,
                'database': database,
                'username': username
            }
            
            logger.info(f"Connected to database: {database}@{host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise e
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.connection = None
        self.cursor = None
        self.connection_info = {}
        logger.info("Database connection closed")
    
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        try:
            if self.connection is None:
                return False
            # Test connection with a simple query
            with self.connection.cursor() as test_cursor:
                test_cursor.execute("SELECT 1")
            return True
        except:
            return False
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Tuple[List[Dict], List[str]]:
        """Execute SQL query and return results"""
        if not self.is_connected():
            raise Exception("Not connected to database")
        
        try:
            self.cursor.execute(query, params)
            
            # For SELECT queries, fetch results
            if query.strip().upper().startswith('SELECT'):
                results = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
                return results, columns
            else:
                # For non-SELECT queries, commit and return affected rows
                self.connection.commit()
                affected_rows = self.cursor.rowcount
                return [{'affected_rows': affected_rows}], ['affected_rows']
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Query execution failed: {e}")
            raise e
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Get complete database schema information"""
        if not self.is_connected():
            raise Exception("Not connected to database")
        
        schema_info = {
            'tables': {},
            'views': {},
            'functions': [],
            'schemas': []
        }
        
        try:
            # Get all schemas
            self.cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name
            """)
            schema_info['schemas'] = [row['schema_name'] for row in self.cursor.fetchall()]
            
            # Get all tables with their columns
            self.cursor.execute("""
                SELECT 
                    t.table_schema,
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    c.character_maximum_length,
                    c.ordinal_position
                FROM information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name 
                    AND t.table_schema = c.table_schema
                WHERE t.table_type = 'BASE TABLE' 
                    AND t.table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY t.table_schema, t.table_name, c.ordinal_position
            """)
            
            tables_data = self.cursor.fetchall()
            for row in tables_data:
                schema_name = row['table_schema']
                table_name = row['table_name']
                full_table_name = f"{schema_name}.{table_name}"
                
                if full_table_name not in schema_info['tables']:
                    schema_info['tables'][full_table_name] = {
                        'schema': schema_name,
                        'name': table_name,
                        'columns': []
                    }
                
                column_info = {
                    'name': row['column_name'],
                    'type': row['data_type'],
                    'nullable': row['is_nullable'] == 'YES',
                    'default': row['column_default'],
                    'max_length': row['character_maximum_length'],
                    'position': row['ordinal_position']
                }
                schema_info['tables'][full_table_name]['columns'].append(column_info)
            
            # Get primary keys
            self.cursor.execute("""
                SELECT 
                    tc.table_schema,
                    tc.table_name,
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            """)
            
            for row in self.cursor.fetchall():
                full_table_name = f"{row['table_schema']}.{row['table_name']}"
                if full_table_name in schema_info['tables']:
                    for col in schema_info['tables'][full_table_name]['columns']:
                        if col['name'] == row['column_name']:
                            col['primary_key'] = True
            
            # Get foreign keys
            self.cursor.execute("""
                SELECT 
                    tc.table_schema,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            """)
            
            for row in self.cursor.fetchall():
                full_table_name = f"{row['table_schema']}.{row['table_name']}"
                if full_table_name in schema_info['tables']:
                    for col in schema_info['tables'][full_table_name]['columns']:
                        if col['name'] == row['column_name']:
                            col['foreign_key'] = {
                                'table': f"{row['foreign_table_schema']}.{row['foreign_table_name']}",
                                'column': row['foreign_column_name']
                            }
            
            # Get views
            self.cursor.execute("""
                SELECT 
                    table_schema,
                    table_name,
                    view_definition
                FROM information_schema.views
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY table_schema, table_name
            """)
            
            for row in self.cursor.fetchall():
                full_view_name = f"{row['table_schema']}.{row['table_name']}"
                schema_info['views'][full_view_name] = {
                    'schema': row['table_schema'],
                    'name': row['table_name'],
                    'definition': row['view_definition']
                }
            
            logger.info(f"Retrieved schema for {len(schema_info['tables'])} tables and {len(schema_info['views'])} views")
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to retrieve database schema: {e}")
            raise e

class ConnectionManager:
    """Manages saved database connections"""
    
    def __init__(self, connections_file: str = "connections.json"):
        self.connections_file = Path(connections_file)
        self.connections = self.load_connections()
    
    def load_connections(self) -> Dict[str, Dict]:
        """Load saved connections from file"""
        if not self.connections_file.exists():
            return {}
        
        try:
            with open(self.connections_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load connections: {e}")
            return {}
    
    def save_connections(self):
        """Save connections to file"""
        try:
            with open(self.connections_file, 'w') as f:
                json.dump(self.connections, f, indent=2)
            logger.info("Connections saved successfully")
        except Exception as e:
            logger.error(f"Failed to save connections: {e}")
            raise e
    
    def add_connection(self, name: str, host: str, port: int, database: str, username: str, password: str = ""):
        """Add a new connection configuration"""
        self.connections[name] = {
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'password': password  # Note: In production, passwords should be encrypted
        }
        self.save_connections()
        logger.info(f"Added new connection: {name}")
    
    def remove_connection(self, name: str):
        """Remove a connection configuration"""
        if name in self.connections:
            del self.connections[name]
            self.save_connections()
            logger.info(f"Removed connection: {name}")
    
    def get_connection(self, name: str) -> Optional[Dict]:
        """Get connection configuration by name"""
        return self.connections.get(name)
    
    def get_all_connections(self) -> Dict[str, Dict]:
        """Get all saved connections"""
        return self.connections.copy()
    
    def test_connection(self, connection_config: Dict) -> bool:
        """Test if a connection configuration works"""
        test_conn = DatabaseConnection()
        try:
            test_conn.connect(
                host=connection_config['host'],
                port=connection_config['port'],
                database=connection_config['database'],
                username=connection_config['username'],
                password=connection_config['password']
            )
            test_conn.disconnect()
            return True
        except:
            return False