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
            logger.info(f"[CONNECTION] Starting connection attempt...")
            logger.info(f"[CONNECTION] Host: {host}")
            logger.info(f"[CONNECTION] Port: {port}")
            logger.info(f"[CONNECTION] Database: {database}")
            logger.info(f"[CONNECTION] Username: {username}")
            
            connection_string = f"host='{host}' port='{port}' dbname='{database}' user='{username}' password='{password}'"
            logger.info(f"[CONNECTION] Connecting to PostgreSQL...")
            
            self.connection = psycopg2.connect(connection_string, connect_timeout=10)
            logger.info(f"[CONNECTION] Connection established successfully")
            
            # Set lock timeout to avoid hanging on locked tables
            with self.connection.cursor() as cur:
                cur.execute("SET application_name = 'NeuronDB';")
                cur.execute("SET lock_timeout = '5s';")  # Fail fast if table is locked
                cur.execute("SET statement_timeout = '60s';")  # Overall query timeout
            
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info(f"[CONNECTION] Cursor created")
            
            self.connection_info = {
                'host': host,
                'port': port,
                'database': database,
                'username': username,
                'password': password  # Store password in memory for psql terminal
            }
            
            logger.info(f"[CONNECTION] ✅ Connected to database: {database}@{host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"[CONNECTION] ❌ Connection failed: {type(e).__name__}: {e}")
            raise e
    
    def disconnect(self):
        """Close database connection"""
        try:
            logger.info("[CONNECTION] Closing database connection...")
            
            # Close cursor
            if self.cursor:
                try:
                    self.cursor.close()
                    logger.info("[CONNECTION] Cursor closed")
                except Exception as e:
                    logger.warning(f"[CONNECTION] Error closing cursor: {e}")
            
            # Close connection
            if self.connection:
                try:
                    self.connection.close()
                    logger.info("[CONNECTION] Connection closed")
                except Exception as e:
                    logger.warning(f"[CONNECTION] Error closing connection: {e}")
            
            # Clear connection info
            self.connection = None
            self.cursor = None
            self.connection_info = {}
            
            logger.info("[CONNECTION] ✅ Database connection closed successfully")
            
        except Exception as e:
            logger.error(f"[CONNECTION] ❌ Error during disconnect: {type(e).__name__}: {e}")
            # Force clear even if there's an error
            self.connection = None
            self.cursor = None
            self.connection_info = {}
    
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
        
        logger.info("[SCHEMA] Starting schema retrieval...")
        
        schema_info = {
            'tables': {},
            'views': {},
            'functions': [],
            'schemas': []
        }
        
        try:
            # Get all schemas (excluding system and TimescaleDB internal schemas)
            logger.info("[SCHEMA] Fetching schemas...")
            self.cursor.execute("""
                SELECT nspname as schema_name
                FROM pg_catalog.pg_namespace
                WHERE nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                AND nspname NOT LIKE 'pg_%'
                AND nspname NOT LIKE '_timescaledb%'
                AND nspname NOT LIKE 'timescaledb_%'
                ORDER BY nspname
            """)
            schema_info['schemas'] = [row['schema_name'] for row in self.cursor.fetchall()]
            logger.info(f"[SCHEMA] Found {len(schema_info['schemas'])} user schemas: {schema_info['schemas']}")
            
            # Get all tables with their columns (excluding system and TimescaleDB schemas)
            # Using pg_catalog for better performance with TimescaleDB
            logger.info("[SCHEMA] Fetching tables and columns...")
            self.cursor.execute("""
                SELECT 
                    n.nspname as table_schema,
                    c.relname as table_name,
                    a.attname as column_name,
                    format_type(a.atttypid, a.atttypmod) as data_type,
                    NOT a.attnotnull as is_nullable,
                    pg_get_expr(d.adbin, d.adrelid) as column_default,
                    a.attnum as ordinal_position
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
                LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum
                WHERE c.relkind = 'r'
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                    AND n.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    AND n.nspname NOT LIKE 'pg_%'
                    AND n.nspname NOT LIKE '_timescaledb%'
                    AND n.nspname NOT LIKE 'timescaledb_%'
                ORDER BY n.nspname, c.relname, a.attnum
            """)
            
            logger.info("[SCHEMA] Query executed, fetching results...")
            tables_data = self.cursor.fetchall()
            logger.info(f"[SCHEMA] Retrieved {len(tables_data)} column definitions")
            
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
                    'nullable': row['is_nullable'],
                    'default': row['column_default'],
                    'max_length': None,  # Not available in pg_catalog query
                    'position': row['ordinal_position']
                }
                schema_info['tables'][full_table_name]['columns'].append(column_info)
            
            logger.info(f"[SCHEMA] Processed {len(schema_info['tables'])} tables")
            
            # Get primary keys (using pg_catalog for better performance)
            logger.info("[SCHEMA] Fetching primary keys...")
            self.cursor.execute("""
                SELECT 
                    n.nspname as table_schema,
                    c.relname as table_name,
                    a.attname as column_name
                FROM pg_catalog.pg_constraint con
                JOIN pg_catalog.pg_class c ON con.conrelid = c.oid
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(con.conkey)
                WHERE con.contype = 'p'
                    AND n.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    AND n.nspname NOT LIKE 'pg_%'
                    AND n.nspname NOT LIKE '_timescaledb%'
                    AND n.nspname NOT LIKE 'timescaledb_%'
            """)
            
            pk_rows = self.cursor.fetchall()
            logger.info(f"[SCHEMA] Found {len(pk_rows)} primary key constraints")
            
            for row in pk_rows:
                full_table_name = f"{row['table_schema']}.{row['table_name']}"
                if full_table_name in schema_info['tables']:
                    for col in schema_info['tables'][full_table_name]['columns']:
                        if col['name'] == row['column_name']:
                            col['primary_key'] = True
            
            # Get foreign keys (using pg_catalog for better performance)
            logger.info("[SCHEMA] Fetching foreign keys...")
            self.cursor.execute("""
                SELECT 
                    n1.nspname as table_schema,
                    c1.relname as table_name,
                    a1.attname as column_name,
                    n2.nspname as foreign_table_schema,
                    c2.relname as foreign_table_name,
                    a2.attname as foreign_column_name
                FROM pg_catalog.pg_constraint con
                JOIN pg_catalog.pg_class c1 ON con.conrelid = c1.oid
                JOIN pg_catalog.pg_namespace n1 ON n1.oid = c1.relnamespace
                JOIN pg_catalog.pg_class c2 ON con.confrelid = c2.oid
                JOIN pg_catalog.pg_namespace n2 ON n2.oid = c2.relnamespace
                JOIN pg_catalog.pg_attribute a1 ON a1.attrelid = c1.oid AND a1.attnum = ANY(con.conkey)
                JOIN pg_catalog.pg_attribute a2 ON a2.attrelid = c2.oid AND a2.attnum = ANY(con.confkey)
                WHERE con.contype = 'f'
                    AND n1.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    AND n1.nspname NOT LIKE 'pg_%'
                    AND n1.nspname NOT LIKE '_timescaledb%'
                    AND n1.nspname NOT LIKE 'timescaledb_%'
            """)
            
            fk_rows = self.cursor.fetchall()
            logger.info(f"[SCHEMA] Found {len(fk_rows)} foreign key constraints")
            
            for row in fk_rows:
                full_table_name = f"{row['table_schema']}.{row['table_name']}"
                if full_table_name in schema_info['tables']:
                    for col in schema_info['tables'][full_table_name]['columns']:
                        if col['name'] == row['column_name']:
                            col['foreign_key'] = {
                                'table': f"{row['foreign_table_schema']}.{row['foreign_table_name']}",
                                'column': row['foreign_column_name']
                            }
            
            # Get views (using pg_catalog for better performance)
            logger.info("[SCHEMA] Fetching views...")
            self.cursor.execute("""
                SELECT 
                    n.nspname as table_schema,
                    c.relname as table_name,
                    pg_get_viewdef(c.oid, true) as view_definition
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relkind = 'v'
                    AND n.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    AND n.nspname NOT LIKE 'pg_%'
                    AND n.nspname NOT LIKE '_timescaledb%'
                    AND n.nspname NOT LIKE 'timescaledb_%'
                ORDER BY n.nspname, c.relname
            """)
            
            view_rows = self.cursor.fetchall()
            logger.info(f"[SCHEMA] Found {len(view_rows)} views")
            
            for row in view_rows:
                full_view_name = f"{row['table_schema']}.{row['table_name']}"
                schema_info['views'][full_view_name] = {
                    'schema': row['table_schema'],
                    'name': row['table_name'],
                    'definition': row['view_definition']
                }
            
            logger.info(f"[SCHEMA] ✅ Schema retrieval complete: {len(schema_info['tables'])} tables, {len(schema_info['views'])} views")
            return schema_info
            
        except Exception as e:
            # Handle lock timeout or statement timeout gracefully
            error_msg = str(e)
            error_type = type(e).__name__
            
            if "lock timeout" in error_msg.lower() or error_type == "LockNotAvailable":
                logger.warning(f"[SCHEMA] ⚠️  Lock timeout while fetching schema")
                logger.warning(f"[SCHEMA] Database has locked tables (active queries/transactions)")
                logger.warning(f"[SCHEMA] Returning partial schema: {len(schema_info['tables'])} tables loaded so far")
                # Return what we have so far instead of failing
                return schema_info
            elif "statement timeout" in error_msg.lower():
                logger.warning(f"[SCHEMA] ⚠️  Statement timeout - query took too long")
                logger.warning(f"[SCHEMA] Returning partial schema: {len(schema_info['tables'])} tables loaded")
                return schema_info
            else:
                logger.error(f"[SCHEMA] ❌ Failed to retrieve database schema: {error_type}: {e}")
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