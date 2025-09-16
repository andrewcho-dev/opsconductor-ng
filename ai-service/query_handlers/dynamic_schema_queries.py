#!/usr/bin/env python3
"""
Dynamic Schema Query Handler
Automatically handles queries about ANY table or field in the database
using schema introspection - no manual specification required!
"""

import asyncio
import re
import json
from typing import Dict, List, Any, Optional
from .base_handler import BaseQueryHandler
from ..schema_introspector import schema_introspector

class DynamicSchemaQueryHandler(BaseQueryHandler):
    """
    Handles queries about database schema dynamically
    No need to manually specify every table and field!
    """
    
    def __init__(self, service_clients: Dict[str, Any]):
        super().__init__(service_clients)
        self.schema_cache = None
    
    async def get_supported_intents(self) -> List[str]:
        """Return list of supported intents"""
        return [
            "query_schema_info",
            "query_table_structure", 
            "query_database_search",
            "query_table_data",
            "query_column_info",
            "query_relationships",
            "query_database_summary"
        ]
    
    async def can_handle(self, intent: str, message: str, context: List[Dict]) -> bool:
        """Check if this handler can process the given intent"""
        supported_intents = await self.get_supported_intents()
        
        if intent in supported_intents:
            return True
        
        # Also handle if message contains schema-related keywords
        schema_keywords = [
            "table", "column", "field", "database", "schema", "structure",
            "what tables", "show tables", "describe", "explain", "fields in",
            "columns in", "what's in", "database structure", "table structure"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in schema_keywords)
    
    async def handle_query(self, intent: str, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle schema-related queries dynamically"""
        
        # Classify the specific type of schema query
        query_type = await self._classify_schema_query(message)
        
        if query_type == "database_summary":
            return await self._handle_database_summary(message, context)
        elif query_type == "table_list":
            return await self._handle_table_list(message, context)
        elif query_type == "table_structure":
            return await self._handle_table_structure(message, context)
        elif query_type == "column_search":
            return await self._handle_column_search(message, context)
        elif query_type == "data_search":
            return await self._handle_data_search(message, context)
        elif query_type == "relationships":
            return await self._handle_relationships(message, context)
        elif query_type == "schema_search":
            return await self._handle_schema_search(message, context)
        else:
            return await self._handle_general_schema_query(message, context)
    
    async def _classify_schema_query(self, message: str) -> str:
        """Classify the type of schema query"""
        message_lower = message.lower()
        
        # Database summary queries
        if any(phrase in message_lower for phrase in [
            "database summary", "schema overview", "what tables", "show all tables",
            "database structure", "what's in the database"
        ]):
            return "database_summary"
        
        # Table structure queries
        if any(phrase in message_lower for phrase in [
            "describe table", "table structure", "columns in", "fields in",
            "what's in table", "table schema", "show table"
        ]):
            return "table_structure"
        
        # Column search queries
        if any(phrase in message_lower for phrase in [
            "find column", "search column", "which table has", "column named",
            "field named", "where is column"
        ]):
            return "column_search"
        
        # Relationship queries
        if any(phrase in message_lower for phrase in [
            "relationships", "foreign key", "references", "related tables",
            "table connections", "joins"
        ]):
            return "relationships"
        
        # Data search queries
        if any(phrase in message_lower for phrase in [
            "search data", "find data", "query data", "data in table",
            "records in", "rows in"
        ]):
            return "data_search"
        
        # General schema search
        if any(phrase in message_lower for phrase in [
            "search", "find", "look for"
        ]):
            return "schema_search"
        
        # Table list queries
        if any(phrase in message_lower for phrase in [
            "list tables", "show tables", "all tables"
        ]):
            return "table_list"
        
        return "general"
    
    async def _handle_database_summary(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle database summary queries"""
        try:
            summary = await schema_introspector.get_schema_summary()
            
            return self.create_success_response(
                "query_database_summary",
                summary,
                {"type": "database_summary"}
            )
            
        except Exception as e:
            return self.create_error_response(
                "query_database_summary",
                f"❌ **Error getting database summary**\n\nFailed to retrieve database schema information: {str(e)}"
            )
    
    async def _handle_table_list(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle table listing queries"""
        try:
            schema = await schema_introspector.get_complete_schema()
            
            if not schema["tables"]:
                return self.create_success_response(
                    "query_table_structure",
                    "📋 **No tables found**\n\nThe database appears to be empty or inaccessible.",
                    {"tables": []}
                )
            
            response = "📋 **Database Tables**\n\n"
            
            # Group tables by schema
            tables_by_schema = {}
            for table_key, table_info in schema["tables"].items():
                schema_name = table_info["schema"]
                if schema_name not in tables_by_schema:
                    tables_by_schema[schema_name] = []
                tables_by_schema[schema_name].append(table_info)
            
            for schema_name, tables in tables_by_schema.items():
                response += f"**{schema_name} schema:**\n"
                
                for table in sorted(tables, key=lambda x: x["name"]):
                    row_count = table.get("estimated_rows", 0)
                    size = table.get("size", "Unknown")
                    comment = table.get("comment", "")
                    
                    response += f"• **{table['name']}** "
                    if row_count > 0:
                        response += f"(~{row_count:,} rows, {size})"
                    if comment:
                        response += f"\n  *{comment}*"
                    response += "\n"
                
                response += "\n"
            
            response += f"**Total:** {len(schema['tables'])} tables across {len(tables_by_schema)} schemas"
            
            return self.create_success_response(
                "query_table_structure",
                response,
                {
                    "tables": list(schema["tables"].keys()),
                    "schemas": list(tables_by_schema.keys()),
                    "total_tables": len(schema["tables"])
                }
            )
            
        except Exception as e:
            return self.create_error_response(
                "query_table_structure",
                f"❌ **Error listing tables**\n\nFailed to retrieve table information: {str(e)}"
            )
    
    async def _handle_table_structure(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle table structure queries"""
        try:
            # Extract table name from message
            table_name = self._extract_table_name(message)
            
            if not table_name:
                return self.create_success_response(
                    "query_table_structure",
                    "🤔 **Table name not specified**\n\n"
                    "Please specify which table you'd like to see the structure for.\n\n"
                    "**Example:** *\"Describe the users table\"* or *\"Show structure of targets table\"*",
                    {"available_tables": await self._get_available_tables()}
                )
            
            table_info = await schema_introspector.get_table_info(table_name)
            
            if not table_info:
                # Try to find similar table names
                schema = await schema_introspector.get_complete_schema()
                similar_tables = [
                    table_key for table_key in schema["tables"].keys()
                    if table_name.lower() in table_key.lower()
                ]
                
                response = f"❌ **Table '{table_name}' not found**\n\n"
                if similar_tables:
                    response += "**Did you mean:**\n"
                    for table in similar_tables[:5]:
                        response += f"• {table}\n"
                else:
                    response += "**Available tables:**\n"
                    for table_key in list(schema["tables"].keys())[:10]:
                        response += f"• {table_key}\n"
                
                return self.create_success_response(
                    "query_table_structure",
                    response,
                    {"suggested_tables": similar_tables[:5]}
                )
            
            # Build detailed table structure response
            response = f"📋 **Table Structure: {table_info['schema']}.{table_info['name']}**\n\n"
            
            if table_info.get("comment"):
                response += f"*{table_info['comment']}*\n\n"
            
            # Basic info
            response += f"**Basic Information:**\n"
            response += f"• Type: {table_info['type']}\n"
            response += f"• Schema: {table_info['schema']}\n"
            if table_info.get("estimated_rows"):
                response += f"• Estimated rows: {table_info['estimated_rows']:,}\n"
            if table_info.get("size"):
                response += f"• Size: {table_info['size']}\n"
            response += "\n"
            
            # Columns
            if table_info.get("columns"):
                response += f"**Columns ({len(table_info['columns'])}):**\n"
                for col in table_info["columns"]:
                    response += f"• **{col['name']}** "
                    response += f"`{col['data_type']}`"
                    
                    if col["is_primary_key"]:
                        response += " 🔑"
                    if col["is_foreign_key"]:
                        response += " 🔗"
                    if not col["is_nullable"]:
                        response += " ⚠️"
                    
                    response += "\n"
                    
                    if col.get("comment"):
                        response += f"  *{col['comment']}*\n"
                
                response += "\n"
            
            # Indexes
            if table_info.get("indexes"):
                response += f"**Indexes ({len(table_info['indexes'])}):**\n"
                for idx in table_info["indexes"]:
                    response += f"• {idx['name']}\n"
                response += "\n"
            
            # Foreign keys
            if table_info.get("foreign_keys"):
                response += f"**Foreign Keys:**\n"
                for fk in table_info["foreign_keys"]:
                    response += f"• {fk['source_column']} → {fk['target_schema']}.{fk['target_table']}.{fk['target_column']}\n"
                response += "\n"
            
            # Referenced by
            if table_info.get("referenced_by"):
                response += f"**Referenced By:**\n"
                for ref in table_info["referenced_by"]:
                    response += f"• {ref['source_schema']}.{ref['source_table']}.{ref['source_column']}\n"
                response += "\n"
            
            return self.create_success_response(
                "query_table_structure",
                response,
                {
                    "table": table_info,
                    "column_count": len(table_info.get("columns", [])),
                    "index_count": len(table_info.get("indexes", []))
                }
            )
            
        except Exception as e:
            return self.create_error_response(
                "query_table_structure",
                f"❌ **Error describing table**\n\nFailed to retrieve table structure: {str(e)}"
            )
    
    async def _handle_column_search(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle column search queries"""
        try:
            # Extract column name from message
            column_name = self._extract_column_name(message)
            
            if not column_name:
                return self.create_success_response(
                    "query_column_info",
                    "🤔 **Column name not specified**\n\n"
                    "Please specify which column you're looking for.\n\n"
                    "**Example:** *\"Find column named email\"* or *\"Which table has password field?\"*"
                )
            
            search_results = await schema_introspector.search_schema(column_name)
            
            if not search_results["columns"]:
                return self.create_success_response(
                    "query_column_info",
                    f"❌ **Column '{column_name}' not found**\n\n"
                    "No columns matching that name were found in the database."
                )
            
            response = f"🔍 **Column Search Results for '{column_name}'**\n\n"
            response += f"**Found {len(search_results['columns'])} matching columns:**\n\n"
            
            for col in search_results["columns"]:
                response += f"• **{col['table']}.{col['column']}**\n"
                response += f"  Type: `{col['data_type']}`\n"
                if col.get("comment"):
                    response += f"  Description: *{col['comment']}*\n"
                response += "\n"
            
            return self.create_success_response(
                "query_column_info",
                response,
                {
                    "search_term": column_name,
                    "matches": search_results["columns"],
                    "match_count": len(search_results["columns"])
                }
            )
            
        except Exception as e:
            return self.create_error_response(
                "query_column_info",
                f"❌ **Error searching columns**\n\nFailed to search for column: {str(e)}"
            )
    
    async def _handle_schema_search(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle general schema search queries"""
        try:
            # Extract search term from message
            search_term = self._extract_search_term(message)
            
            if not search_term:
                return self.create_success_response(
                    "query_database_search",
                    "🤔 **Search term not specified**\n\n"
                    "Please specify what you're looking for in the database.\n\n"
                    "**Example:** *\"Search for user\"* or *\"Find anything related to password\"*"
                )
            
            search_results = await schema_introspector.search_schema(search_term)
            
            # Count total results
            total_results = (
                len(search_results["tables"]) +
                len(search_results["columns"]) +
                len(search_results["functions"]) +
                len(search_results["views"]) +
                len(search_results["enums"])
            )
            
            if total_results == 0:
                return self.create_success_response(
                    "query_database_search",
                    f"❌ **No results found for '{search_term}'**\n\n"
                    "No tables, columns, functions, views, or enums match your search term."
                )
            
            response = f"🔍 **Search Results for '{search_term}'**\n\n"
            response += f"**Found {total_results} total matches:**\n\n"
            
            # Tables
            if search_results["tables"]:
                response += f"**Tables ({len(search_results['tables'])}):**\n"
                for table in search_results["tables"]:
                    response += f"• **{table['table']}**"
                    if table.get("comment"):
                        response += f" - *{table['comment']}*"
                    response += "\n"
                response += "\n"
            
            # Columns
            if search_results["columns"]:
                response += f"**Columns ({len(search_results['columns'])}):**\n"
                for col in search_results["columns"][:10]:  # Limit to 10
                    response += f"• **{col['table']}.{col['column']}** (`{col['data_type']}`)\n"
                if len(search_results["columns"]) > 10:
                    response += f"  ... and {len(search_results['columns']) - 10} more columns\n"
                response += "\n"
            
            # Functions
            if search_results["functions"]:
                response += f"**Functions ({len(search_results['functions'])}):**\n"
                for func in search_results["functions"]:
                    response += f"• **{func['schema_name']}.{func['function_name']}**\n"
                response += "\n"
            
            # Views
            if search_results["views"]:
                response += f"**Views ({len(search_results['views'])}):**\n"
                for view in search_results["views"]:
                    response += f"• **{view['schema_name']}.{view['view_name']}**\n"
                response += "\n"
            
            # Enums
            if search_results["enums"]:
                response += f"**Enums ({len(search_results['enums'])}):**\n"
                for enum in search_results["enums"]:
                    response += f"• **{enum['schema_name']}.{enum['enum_name']}**\n"
                response += "\n"
            
            return self.create_success_response(
                "query_database_search",
                response,
                {
                    "search_term": search_term,
                    "results": search_results,
                    "total_matches": total_results
                }
            )
            
        except Exception as e:
            return self.create_error_response(
                "query_database_search",
                f"❌ **Error searching database**\n\nFailed to search database schema: {str(e)}"
            )
    
    async def _handle_relationships(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle relationship queries"""
        try:
            schema = await schema_introspector.get_complete_schema()
            
            if not schema["relationships"]:
                return self.create_success_response(
                    "query_relationships",
                    "📊 **No foreign key relationships found**\n\n"
                    "The database doesn't appear to have any foreign key constraints defined."
                )
            
            response = f"🔗 **Database Relationships**\n\n"
            response += f"**Found {len(schema['relationships'])} foreign key relationships:**\n\n"
            
            # Group by source table
            relationships_by_table = {}
            for rel in schema["relationships"]:
                source_table = f"{rel['source_schema']}.{rel['source_table']}"
                if source_table not in relationships_by_table:
                    relationships_by_table[source_table] = []
                relationships_by_table[source_table].append(rel)
            
            for source_table, rels in relationships_by_table.items():
                response += f"**{source_table}:**\n"
                for rel in rels:
                    target_table = f"{rel['target_schema']}.{rel['target_table']}"
                    response += f"• {rel['source_column']} → {target_table}.{rel['target_column']}"
                    if rel.get("delete_rule") and rel["delete_rule"] != "NO ACTION":
                        response += f" (on delete: {rel['delete_rule']})"
                    response += "\n"
                response += "\n"
            
            return self.create_success_response(
                "query_relationships",
                response,
                {
                    "relationships": schema["relationships"],
                    "relationship_count": len(schema["relationships"])
                }
            )
            
        except Exception as e:
            return self.create_error_response(
                "query_relationships",
                f"❌ **Error getting relationships**\n\nFailed to retrieve database relationships: {str(e)}"
            )
    
    async def _handle_data_search(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle data search queries (placeholder - would need actual data access)"""
        return self.create_success_response(
            "query_table_data",
            "🔍 **Data Search**\n\n"
            "Data search functionality is available but requires specific table access permissions.\n\n"
            "**Available options:**\n"
            "• Use the asset service API to query target data\n"
            "• Use the automation service API to query job data\n"
            "• Use the communication service API to query notification data\n\n"
            "**Example:** *\"Show me recent targets\"* or *\"List failed jobs\"*"
        )
    
    async def _handle_general_schema_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle general schema queries"""
        return await self._handle_database_summary(message, context)
    
    def _extract_table_name(self, message: str) -> Optional[str]:
        """Extract table name from message"""
        # Common patterns for table name extraction
        patterns = [
            r"table\s+(\w+)",
            r"(\w+)\s+table",
            r"describe\s+(\w+)",
            r"structure\s+of\s+(\w+)",
            r"columns\s+in\s+(\w+)",
            r"fields\s+in\s+(\w+)",
            r"what's\s+in\s+(\w+)"
        ]
        
        message_lower = message.lower()
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_column_name(self, message: str) -> Optional[str]:
        """Extract column name from message"""
        patterns = [
            r"column\s+(\w+)",
            r"field\s+(\w+)",
            r"named\s+(\w+)",
            r"called\s+(\w+)",
            r"(\w+)\s+column",
            r"(\w+)\s+field"
        ]
        
        message_lower = message.lower()
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_search_term(self, message: str) -> Optional[str]:
        """Extract search term from message"""
        patterns = [
            r"search\s+for\s+(\w+)",
            r"find\s+(\w+)",
            r"look\s+for\s+(\w+)",
            r"related\s+to\s+(\w+)"
        ]
        
        message_lower = message.lower()
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1)
        
        # If no pattern matches, try to extract the last meaningful word
        words = message_lower.split()
        if words:
            # Skip common words
            skip_words = {"the", "a", "an", "in", "on", "at", "for", "with", "about", "search", "find", "look"}
            meaningful_words = [word for word in words if word not in skip_words and len(word) > 2]
            if meaningful_words:
                return meaningful_words[-1]
        
        return None
    
    async def _get_available_tables(self) -> List[str]:
        """Get list of available table names"""
        try:
            schema = await schema_introspector.get_complete_schema()
            return list(schema["tables"].keys())
        except:
            return []