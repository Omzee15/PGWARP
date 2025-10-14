"""
AI Assistant for PgWarp using LangChain and Gemini
Generates SQL queries from natural language prompts
"""

import os
from typing import Dict, List, Optional, Any
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.append(str(Path(__file__).parent.parent))
from config import Config

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SQLOutputParser:
    """Custom output parser for SQL queries"""
    
    def parse(self, text: str) -> str:
        """Parse the LLM output to extract SQL query"""
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith('```sql'):
            text = text[6:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        # Clean up the query
        text = text.strip()
        
        # Remove leading comments that might interfere with query execution
        lines = text.split('\n')
        cleaned_lines = []
        found_sql = False
        
        for line in lines:
            stripped_line = line.strip()
            # Skip leading comment lines (-- or /* */)
            if not found_sql:
                if stripped_line.startswith('--') or stripped_line.startswith('/*'):
                    continue
                elif stripped_line:  # Found first non-comment, non-empty line
                    found_sql = True
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines).strip()
        
        # Ensure the query ends with semicolon
        if not text.endswith(';'):
            text += ';'
            
        return text

class PgWarpAI:
    """AI Assistant for generating SQL queries"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(Config.AI_MODEL)
        
        self.database_schema = {}
        self.conversation_history = []
        
        # Create the prompt template
        self.sql_prompt_template = """
You are an expert PostgreSQL database assistant. Your task is to generate accurate SQL queries based on user requests.

DATABASE SCHEMA:
{schema_context}

CONVERSATION HISTORY:
{conversation_history}

USER REQUEST: {user_query}

INSTRUCTIONS:
1. Generate a PostgreSQL-compatible SQL query that fulfills the user's request
2. Use proper table and column names from the provided schema
3. Include appropriate JOINs when querying multiple tables
4. Use proper PostgreSQL syntax and functions
5. If the request is ambiguous, make reasonable assumptions
6. If the request cannot be fulfilled with the available schema, explain why
7. Always return valid SQL that can be executed

IMPORTANT FORMATTING RULES:
- DO NOT start the query with comments (no -- or /* at the beginning)
- Start directly with the SQL command (SELECT, INSERT, UPDATE, etc.)
- You can add inline comments AFTER the query if needed to explain
- The very first line must be executable SQL, not a comment
- Remove any introductory text or explanations before the query

Return ONLY the SQL query (or explanation if query cannot be generated), no additional text or formatting.

CORRECT FORMAT:
SELECT * FROM users WHERE active = true;

INCORRECT FORMAT:
-- Get all active users
SELECT * FROM users WHERE active = true;
"""
    
    def set_database_schema(self, schema: Dict[str, Any]):
        """Set the database schema context for AI assistant"""
        self.database_schema = schema
        logger.info("Database schema updated for AI assistant")
    
    def _format_schema_context(self) -> str:
        """Format database schema for prompt context"""
        if not self.database_schema:
            return "No database schema available."
        
        context_parts = []
        
        # Add tables information
        if 'tables' in self.database_schema:
            context_parts.append("TABLES:")
            for table_name, table_info in self.database_schema['tables'].items():
                context_parts.append(f"\nTable: {table_name}")
                context_parts.append("Columns:")
                for col in table_info['columns']:
                    col_desc = f"  - {col['name']} ({col['type']}"
                    if not col['nullable']:
                        col_desc += ", NOT NULL"
                    if col.get('primary_key'):
                        col_desc += ", PRIMARY KEY"
                    if col.get('foreign_key'):
                        col_desc += f", REFERENCES {col['foreign_key']['table']}({col['foreign_key']['column']})"
                    col_desc += ")"
                    context_parts.append(col_desc)
        
        # Add views information
        if 'views' in self.database_schema and self.database_schema['views']:
            context_parts.append("\nVIEWS:")
            for view_name, view_info in self.database_schema['views'].items():
                context_parts.append(f"  - {view_name}")
        
        return "\n".join(context_parts)
    
    def _format_conversation_history(self) -> str:
        """Format recent conversation history"""
        if not self.conversation_history:
            return "No previous conversation."
        
        # Get last 5 interactions
        recent_history = self.conversation_history[-5:]
        history_parts = []
        
        for i, interaction in enumerate(recent_history, 1):
            history_parts.append(f"{i}. User: {interaction['user_query']}")
            if interaction['generated_query']:
                history_parts.append(f"   Generated: {interaction['generated_query']}")
            if interaction.get('error'):
                history_parts.append(f"   Error: {interaction['error']}")
        
        return "\n".join(history_parts)
    
    def generate_sql_query(self, user_query: str) -> Dict[str, Any]:
        """Generate SQL query from natural language input"""
        try:
            # Format context
            schema_context = self._format_schema_context()
            conversation_history = self._format_conversation_history()
            
            # Create the full prompt
            prompt = self.sql_prompt_template.format(
                schema_context=schema_context,
                user_query=user_query,
                conversation_history=conversation_history
            )
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            generated_text = response.text
            
            # Parse the SQL query
            parser = SQLOutputParser()
            sql_query = parser.parse(generated_text)
            
            # Store in conversation history
            interaction = {
                'user_query': user_query,
                'generated_query': sql_query,
                'timestamp': None,  # You can add timestamp if needed
                'error': None
            }
            self.conversation_history.append(interaction)
            
            # Keep only last 20 interactions
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            logger.info(f"Generated SQL query for: {user_query[:50]}...")
            
            return {
                'success': True,
                'query': sql_query,
                'explanation': generated_text if generated_text != sql_query else None,
                'user_input': user_query
            }
            
        except Exception as e:
            error_msg = f"Failed to generate SQL query: {str(e)}"
            logger.error(error_msg)
            
            # Store error in conversation history
            interaction = {
                'user_query': user_query,
                'generated_query': None,
                'error': error_msg
            }
            self.conversation_history.append(interaction)
            
            return {
                'success': False,
                'error': error_msg,
                'user_input': user_query
            }
    
    def explain_query(self, sql_query: str) -> Dict[str, Any]:
        """Explain what a SQL query does"""
        try:
            explain_prompt = f"""
Explain what this PostgreSQL query does in simple terms:

{sql_query}

DATABASE SCHEMA:
{self._format_schema_context()}

Provide a clear, concise explanation of:
1. What data is being retrieved or modified
2. Which tables are involved
3. Any filtering conditions
4. Any joins or relationships used
5. The expected result
"""
            
            response = self.model.generate_content(explain_prompt)
            explanation = response.text
            
            return {
                'success': True,
                'explanation': explanation,
                'query': sql_query
            }
            
        except Exception as e:
            error_msg = f"Failed to explain query: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'query': sql_query
            }
    
    def suggest_improvements(self, sql_query: str) -> Dict[str, Any]:
        """Suggest improvements for a SQL query"""
        try:
            improve_prompt = f"""
Analyze this PostgreSQL query and suggest improvements for performance, readability, or best practices:

{sql_query}

DATABASE SCHEMA:
{self._format_schema_context()}

Consider:
1. Index usage optimization
2. Query performance improvements
3. Readability enhancements
4. PostgreSQL-specific optimizations
5. Potential issues or risks

Provide specific suggestions with improved query examples if applicable.
"""
            
            response = self.model.generate_content(improve_prompt)
            suggestions = response.text
            
            return {
                'success': True,
                'suggestions': suggestions,
                'original_query': sql_query
            }
            
        except Exception as e:
            error_msg = f"Failed to analyze query: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'original_query': sql_query
            }
    
    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the current conversation history"""
        return self.conversation_history.copy()
    
    def is_configured(self) -> bool:
        """Check if AI assistant is properly configured"""
        return bool(self.api_key)
    
    def get_schema_summary(self) -> str:
        """Get a summary of the available database schema"""
        if not self.database_schema:
            return "No database schema loaded."
        
        summary_parts = []
        
        if 'tables' in self.database_schema:
            table_count = len(self.database_schema['tables'])
            summary_parts.append(f"Tables: {table_count}")
            
            # List table names
            table_names = list(self.database_schema['tables'].keys())
            if table_names:
                summary_parts.append("Available tables:")
                for table_name in sorted(table_names):
                    column_count = len(self.database_schema['tables'][table_name]['columns'])
                    summary_parts.append(f"  - {table_name} ({column_count} columns)")
        
        if 'views' in self.database_schema and self.database_schema['views']:
            view_count = len(self.database_schema['views'])
            summary_parts.append(f"Views: {view_count}")
        
        return "\n".join(summary_parts)
    
    def generate_query_title(self, sql_query: str) -> str:
        """Generate a concise title for a SQL query (1-4 words)"""
        try:
            title_prompt = f"""
Generate a concise title for this SQL query. The title should be 1-4 words maximum and describe what the query does.

SQL Query:
{sql_query}

Rules:
- Use 1-4 words only
- Be descriptive and clear
- Use title case
- No punctuation at the end
- Examples: "User List", "Sales Report", "Top Products", "Customer Count"

Return ONLY the title, nothing else.
"""
            
            response = self.model.generate_content(title_prompt)
            title = response.text.strip()
            
            # Clean up the title
            title = title.strip('"').strip("'").strip()
            
            # Ensure it's not too long (fallback if AI doesn't follow instructions)
            words = title.split()
            if len(words) > 4:
                title = ' '.join(words[:4])
            
            # If still too long, truncate to 50 chars
            if len(title) > 50:
                title = title[:47] + "..."
            
            logger.info(f"Generated query title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Failed to generate query title: {str(e)}")
            # Return a default title based on query type
            query_upper = sql_query.strip().upper()
            if query_upper.startswith('SELECT'):
                return "Select Query"
            elif query_upper.startswith('INSERT'):
                return "Insert Query"
            elif query_upper.startswith('UPDATE'):
                return "Update Query"
            elif query_upper.startswith('DELETE'):
                return "Delete Query"
            else:
                return "SQL Query"