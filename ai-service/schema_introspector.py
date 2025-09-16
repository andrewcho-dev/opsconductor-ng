#!/usr/bin/env python3
"""
Schema Introspector - Automatic Database Schema Discovery
Provides the AI system with comprehensive knowledge of all tables, columns, and relationships
"""

import asyncio
import asyncpg
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SchemaIntrospector:
    """
    Automatically discovers and provides comprehensive database schema information
    to the AI system, eliminating the need for manual specification of every table and field
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or "postgresql://opsconductor:opsconductor@postgres:5432/opsconductor"
        self.schema_cache = {}
        self.last_refresh = None
        self.cache_ttl = 3600  # 1 hour cache
    
    async def get_complete_schema(self) -> Dict[str, Any]:
        """Get complete database schema with all tables, columns, relationships, and metadata"""
        
        # Check cache first
        if self._is_cache_valid():
            return self.schema_cache
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            schema_info = {
                "schemas": await self._get_schemas(conn),
                "tables": await self._get_all_tables(conn),
                "columns": await self._get_all_columns(conn),
                "relationships": await self._get_relationships(conn),
                "indexes": await self._get_indexes(conn),
                "constraints": await self._get_constraints(conn),
                "enums": await self._get_enums(conn),
                "functions": await self._get_functions(conn),
                "views": await self._get_views(conn),
                "statistics": await self._get_table_statistics(conn),
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "total_tables": 0,
                    "total_columns": 0,
                    "database_size": await self._get_database_size(conn)
                }
            }
            
            # Calculate totals
            schema_info["metadata"]["total_tables"] = len(schema_info["tables"])
            schema_info["metadata"]["total_columns"] = sum(len(table["columns"]) for table in schema_info["tables"].values())
            
            await conn.close()
            
            # Cache the result
            self.schema_cache = schema_info
            self.last_refresh = datetime.utcnow()
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to introspect database schema: {e}")
            return self._get_fallback_schema()
    
    async def _get_schemas(self, conn) -> List[Dict[str, Any]]:
        """Get all database schemas"""
        query = """
        SELECT schema_name, 
               schema_owner,
               (SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = schema_name) as table_count
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name
        """
        
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    
    async def _get_all_tables(self, conn) -> Dict[str, Dict[str, Any]]:
        """Get all tables with their metadata"""
        query = """
        SELECT 
            t.table_schema,
            t.table_name,
            t.table_type,
            obj_description(c.oid) as table_comment,
            pg_size_pretty(pg_total_relation_size(c.oid)) as table_size,
            pg_stat_get_tuples_returned(c.oid) as row_count_estimate
        FROM information_schema.tables t
        LEFT JOIN pg_class c ON c.relname = t.table_name
        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
        WHERE t.table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY t.table_schema, t.table_name
        """
        
        rows = await conn.fetch(query)
        tables = {}
        
        for row in rows:
            table_key = f"{row['table_schema']}.{row['table_name']}"
            tables[table_key] = {
                "schema": row["table_schema"],
                "name": row["table_name"],
                "type": row["table_type"],
                "comment": row["table_comment"],
                "size": row["table_size"],
                "estimated_rows": row["row_count_estimate"] or 0,
                "columns": {},
                "primary_keys": [],
                "foreign_keys": [],
                "indexes": []
            }
        
        return tables
    
    async def _get_all_columns(self, conn) -> Dict[str, List[Dict[str, Any]]]:
        """Get all columns for all tables"""
        query = """
        SELECT 
            c.table_schema,
            c.table_name,
            c.column_name,
            c.ordinal_position,
            c.column_default,
            c.is_nullable,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.udt_name,
            col_description(pgc.oid, c.ordinal_position) as column_comment,
            CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
            CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_foreign_key
        FROM information_schema.columns c
        LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
        LEFT JOIN pg_namespace pgn ON pgn.oid = pgc.relnamespace AND pgn.nspname = c.table_schema
        LEFT JOIN (
            SELECT ku.table_schema, ku.table_name, ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
        ) pk ON pk.table_schema = c.table_schema AND pk.table_name = c.table_name AND pk.column_name = c.column_name
        LEFT JOIN (
            SELECT ku.table_schema, ku.table_name, ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
        ) fk ON fk.table_schema = c.table_schema AND fk.table_name = c.table_name AND fk.column_name = c.column_name
        WHERE c.table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY c.table_schema, c.table_name, c.ordinal_position
        """
        
        rows = await conn.fetch(query)
        columns_by_table = {}
        
        for row in rows:
            table_key = f"{row['table_schema']}.{row['table_name']}"
            if table_key not in columns_by_table:
                columns_by_table[table_key] = []
            
            column_info = {
                "name": row["column_name"],
                "position": row["ordinal_position"],
                "data_type": row["data_type"],
                "udt_name": row["udt_name"],
                "is_nullable": row["is_nullable"] == "YES",
                "default_value": row["column_default"],
                "max_length": row["character_maximum_length"],
                "numeric_precision": row["numeric_precision"],
                "numeric_scale": row["numeric_scale"],
                "comment": row["column_comment"],
                "is_primary_key": row["is_primary_key"],
                "is_foreign_key": row["is_foreign_key"]
            }
            
            columns_by_table[table_key].append(column_info)
        
        return columns_by_table
    
    async def _get_relationships(self, conn) -> List[Dict[str, Any]]:
        """Get foreign key relationships between tables"""
        query = """
        SELECT
            tc.constraint_name,
            tc.table_schema as source_schema,
            tc.table_name as source_table,
            kcu.column_name as source_column,
            ccu.table_schema as target_schema,
            ccu.table_name as target_table,
            ccu.column_name as target_column,
            rc.update_rule,
            rc.delete_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
        JOIN information_schema.referential_constraints rc ON rc.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_schema, tc.table_name, kcu.ordinal_position
        """
        
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    
    async def _get_indexes(self, conn) -> Dict[str, List[Dict[str, Any]]]:
        """Get indexes for all tables"""
        query = """
        SELECT
            schemaname as schema_name,
            tablename as table_name,
            indexname as index_name,
            indexdef as index_definition
        FROM pg_indexes
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schemaname, tablename, indexname
        """
        
        rows = await conn.fetch(query)
        indexes_by_table = {}
        
        for row in rows:
            table_key = f"{row['schema_name']}.{row['table_name']}"
            if table_key not in indexes_by_table:
                indexes_by_table[table_key] = []
            
            indexes_by_table[table_key].append({
                "name": row["index_name"],
                "definition": row["index_definition"]
            })
        
        return indexes_by_table
    
    async def _get_constraints(self, conn) -> Dict[str, List[Dict[str, Any]]]:
        """Get constraints for all tables"""
        query = """
        SELECT
            tc.table_schema,
            tc.table_name,
            tc.constraint_name,
            tc.constraint_type,
            cc.check_clause
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.check_constraints cc ON tc.constraint_name = cc.constraint_name
        WHERE tc.table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY tc.table_schema, tc.table_name, tc.constraint_name
        """
        
        rows = await conn.fetch(query)
        constraints_by_table = {}
        
        for row in rows:
            table_key = f"{row['table_schema']}.{row['table_name']}"
            if table_key not in constraints_by_table:
                constraints_by_table[table_key] = []
            
            constraints_by_table[table_key].append({
                "name": row["constraint_name"],
                "type": row["constraint_type"],
                "check_clause": row["check_clause"]
            })
        
        return constraints_by_table
    
    async def _get_enums(self, conn) -> List[Dict[str, Any]]:
        """Get custom enum types"""
        query = """
        SELECT
            n.nspname as schema_name,
            t.typname as enum_name,
            array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        GROUP BY n.nspname, t.typname
        ORDER BY n.nspname, t.typname
        """
        
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    
    async def _get_functions(self, conn) -> List[Dict[str, Any]]:
        """Get user-defined functions"""
        query = """
        SELECT
            n.nspname as schema_name,
            p.proname as function_name,
            pg_get_function_result(p.oid) as return_type,
            pg_get_function_arguments(p.oid) as arguments,
            obj_description(p.oid) as description
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY n.nspname, p.proname
        """
        
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    
    async def _get_views(self, conn) -> List[Dict[str, Any]]:
        """Get database views"""
        query = """
        SELECT
            table_schema as schema_name,
            table_name as view_name,
            view_definition
        FROM information_schema.views
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY table_schema, table_name
        """
        
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    
    async def _get_table_statistics(self, conn) -> Dict[str, Dict[str, Any]]:
        """Get table usage statistics"""
        query = """
        SELECT
            schemaname as schema_name,
            relname as table_name,
            seq_scan,
            seq_tup_read,
            idx_scan,
            idx_tup_fetch,
            n_tup_ins,
            n_tup_upd,
            n_tup_del,
            n_live_tup,
            n_dead_tup,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        ORDER BY schemaname, relname
        """
        
        rows = await conn.fetch(query)
        stats_by_table = {}
        
        for row in rows:
            table_key = f"{row['schema_name']}.{row['table_name']}"
            stats_by_table[table_key] = dict(row)
        
        return stats_by_table
    
    async def _get_database_size(self, conn) -> str:
        """Get total database size"""
        query = "SELECT pg_size_pretty(pg_database_size(current_database())) as size"
        row = await conn.fetchrow(query)
        return row["size"] if row else "Unknown"
    
    def _is_cache_valid(self) -> bool:
        """Check if schema cache is still valid"""
        if not self.schema_cache or not self.last_refresh:
            return False
        
        cache_age = (datetime.utcnow() - self.last_refresh).total_seconds()
        return cache_age < self.cache_ttl
    
    def _get_fallback_schema(self) -> Dict[str, Any]:
        """Return fallback schema information when introspection fails"""
        return {
            "schemas": [],
            "tables": {},
            "columns": {},
            "relationships": [],
            "indexes": {},
            "constraints": {},
            "enums": [],
            "functions": [],
            "views": [],
            "statistics": {},
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "total_tables": 0,
                "total_columns": 0,
                "database_size": "Unknown",
                "error": "Schema introspection failed"
            }
        }
    
    async def get_table_info(self, table_name: str, schema_name: str = None) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific table"""
        schema = await self.get_complete_schema()
        
        # Try exact match first
        if schema_name:
            table_key = f"{schema_name}.{table_name}"
            if table_key in schema["tables"]:
                return self._build_table_info(table_key, schema)
        
        # Search across all schemas
        for table_key, table_info in schema["tables"].items():
            if table_info["name"] == table_name:
                return self._build_table_info(table_key, schema)
        
        return None
    
    def _build_table_info(self, table_key: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive table information"""
        table_info = schema["tables"][table_key].copy()
        
        # Add columns
        if table_key in schema["columns"]:
            table_info["columns"] = schema["columns"][table_key]
        
        # Add indexes
        if table_key in schema["indexes"]:
            table_info["indexes"] = schema["indexes"][table_key]
        
        # Add constraints
        if table_key in schema["constraints"]:
            table_info["constraints"] = schema["constraints"][table_key]
        
        # Add statistics
        if table_key in schema["statistics"]:
            table_info["statistics"] = schema["statistics"][table_key]
        
        # Add relationships
        table_info["foreign_keys"] = [
            rel for rel in schema["relationships"]
            if f"{rel['source_schema']}.{rel['source_table']}" == table_key
        ]
        
        table_info["referenced_by"] = [
            rel for rel in schema["relationships"]
            if f"{rel['target_schema']}.{rel['target_table']}" == table_key
        ]
        
        return table_info
    
    async def search_schema(self, search_term: str) -> Dict[str, List[Dict[str, Any]]]:
        """Search for tables, columns, or other schema objects by name"""
        schema = await self.get_complete_schema()
        search_term = search_term.lower()
        
        results = {
            "tables": [],
            "columns": [],
            "functions": [],
            "views": [],
            "enums": []
        }
        
        # Search tables
        for table_key, table_info in schema["tables"].items():
            if search_term in table_info["name"].lower() or search_term in (table_info["comment"] or "").lower():
                results["tables"].append({
                    "table": table_key,
                    "name": table_info["name"],
                    "schema": table_info["schema"],
                    "comment": table_info["comment"]
                })
        
        # Search columns
        for table_key, columns in schema["columns"].items():
            for column in columns:
                if search_term in column["name"].lower() or search_term in (column["comment"] or "").lower():
                    results["columns"].append({
                        "table": table_key,
                        "column": column["name"],
                        "data_type": column["data_type"],
                        "comment": column["comment"]
                    })
        
        # Search functions
        for func in schema["functions"]:
            if search_term in func["function_name"].lower():
                results["functions"].append(func)
        
        # Search views
        for view in schema["views"]:
            if search_term in view["view_name"].lower():
                results["views"].append(view)
        
        # Search enums
        for enum in schema["enums"]:
            if search_term in enum["enum_name"].lower() or any(search_term in val.lower() for val in enum["enum_values"]):
                results["enums"].append(enum)
        
        return results
    
    async def get_schema_summary(self) -> str:
        """Get a human-readable summary of the database schema"""
        schema = await self.get_complete_schema()
        
        summary = f"📊 **OpsConductor Database Schema Summary**\n\n"
        summary += f"**Database Overview:**\n"
        summary += f"• Total size: {schema['metadata']['database_size']}\n"
        summary += f"• Schemas: {len(schema['schemas'])}\n"
        summary += f"• Tables: {schema['metadata']['total_tables']}\n"
        summary += f"• Columns: {schema['metadata']['total_columns']}\n"
        summary += f"• Views: {len(schema['views'])}\n"
        summary += f"• Functions: {len(schema['functions'])}\n"
        summary += f"• Enums: {len(schema['enums'])}\n\n"
        
        # Schema breakdown
        summary += f"**Schemas:**\n"
        for schema_info in schema["schemas"]:
            summary += f"• **{schema_info['schema_name']}** - {schema_info['table_count']} tables\n"
        
        summary += f"\n**Major Tables:**\n"
        # Show top 10 tables by estimated size
        sorted_tables = sorted(
            schema["tables"].items(),
            key=lambda x: x[1]["estimated_rows"],
            reverse=True
        )[:10]
        
        for table_key, table_info in sorted_tables:
            row_count = table_info["estimated_rows"]
            summary += f"• **{table_key}** - ~{row_count:,} rows\n"
        
        summary += f"\n*Last updated: {schema['metadata']['last_updated']}*"
        
        return summary

# Global instance
schema_introspector = SchemaIntrospector()

async def get_schema_info() -> Dict[str, Any]:
    """Get complete schema information"""
    return await schema_introspector.get_complete_schema()

async def search_database_schema(search_term: str) -> Dict[str, List[Dict[str, Any]]]:
    """Search database schema for tables, columns, etc."""
    return await schema_introspector.search_schema(search_term)

async def get_table_details(table_name: str, schema_name: str = None) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific table"""
    return await schema_introspector.get_table_info(table_name, schema_name)

if __name__ == "__main__":
    async def test_introspection():
        introspector = SchemaIntrospector()
        schema = await introspector.get_complete_schema()
        print(json.dumps(schema, indent=2, default=str))
    
    asyncio.run(test_introspection())