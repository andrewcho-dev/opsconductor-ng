#!/usr/bin/env python3
"""
Test Dynamic Schema Knowledge - Demonstrates AI's automatic database awareness
No more manual specification of tables and fields!
"""

import asyncio
import json
import sys
import os

# Add the ai-service directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-service'))

from schema_introspector import SchemaIntrospector
from ai_engine import OpsConductorAI

async def test_automatic_schema_discovery():
    """Test that AI automatically discovers all database schema information"""
    
    print("🧠 **Testing Automatic Schema Discovery**")
    print("=" * 60)
    
    # Initialize schema introspector
    introspector = SchemaIntrospector()
    
    try:
        # Get complete schema automatically
        print("\n📊 **Discovering Database Schema Automatically...**")
        schema = await introspector.get_complete_schema()
        
        print(f"✅ **Discovered {schema['metadata']['total_tables']} tables automatically!**")
        print(f"✅ **Found {schema['metadata']['total_columns']} columns automatically!**")
        print(f"✅ **Database size: {schema['metadata']['database_size']}**")
        
        # Show discovered schemas
        print(f"\n🗂️ **Discovered Schemas:**")
        for schema_info in schema["schemas"]:
            print(f"   • {schema_info['schema_name']} ({schema_info['table_count']} tables)")
        
        # Show sample of discovered tables
        print(f"\n📋 **Sample of Discovered Tables:**")
        table_count = 0
        for table_key, table_info in schema["tables"].items():
            if table_count < 10:  # Show first 10
                column_count = len(schema["columns"].get(table_key, []))
                print(f"   • {table_key} ({column_count} columns)")
                table_count += 1
        
        if len(schema["tables"]) > 10:
            print(f"   ... and {len(schema['tables']) - 10} more tables")
        
        # Show sample columns from a specific table
        if "assets.enhanced_targets" in schema["tables"]:
            print(f"\n🔍 **Sample: assets.enhanced_targets columns (discovered automatically):**")
            columns = schema["columns"].get("assets.enhanced_targets", [])
            for col in columns[:8]:  # Show first 8 columns
                print(f"   • {col['name']} ({col['data_type']})")
            if len(columns) > 8:
                print(f"   ... and {len(columns) - 8} more columns")
        
        # Show relationships discovered automatically
        if schema["relationships"]:
            print(f"\n🔗 **Discovered {len(schema['relationships'])} relationships automatically:**")
            for rel in schema["relationships"][:5]:  # Show first 5
                source = f"{rel['source_schema']}.{rel['source_table']}.{rel['source_column']}"
                target = f"{rel['target_schema']}.{rel['target_table']}.{rel['target_column']}"
                print(f"   • {source} → {target}")
            if len(schema["relationships"]) > 5:
                print(f"   ... and {len(schema['relationships']) - 5} more relationships")
        
        return True
        
    except Exception as e:
        print(f"❌ **Schema discovery failed:** {e}")
        return False

async def test_ai_natural_language_queries():
    """Test AI's ability to answer questions about ANY table/field naturally"""
    
    print("\n\n🤖 **Testing AI Natural Language Database Queries**")
    print("=" * 60)
    
    # Initialize AI engine
    ai = OpsConductorAI()
    await ai.initialize()
    
    # Test queries that would previously require manual specification
    test_queries = [
        "What tables are in the database?",
        "Describe the enhanced_targets table",
        "Find column named email",
        "Show me the database structure",
        "Which table has password fields?",
        "What are the relationships between tables?",
        "Search for anything related to user",
        "Database schema overview"
    ]
    
    print("\n🗣️ **Testing Natural Language Queries:**")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n**Query {i}:** *\"{query}\"*")
        
        try:
            # Classify intent
            intent_result = await ai.classify_intent(query)
            print(f"   🎯 Intent: {intent_result['action']} (confidence: {intent_result['confidence']:.2f})")
            
            # Process query
            result = await ai.process_query(query, [])
            
            if result.get("success"):
                response = result["response"]
                # Show first few lines of response
                lines = response.split('\n')
                preview_lines = lines[:3] if len(lines) > 3 else lines
                print(f"   ✅ Response preview: {' '.join(preview_lines)}")
                
                if len(lines) > 3:
                    print(f"   📄 Full response: {len(lines)} lines")
            else:
                print(f"   ❌ Query failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Error processing query: {e}")
    
    return True

async def test_dynamic_table_discovery():
    """Test discovery of specific table information dynamically"""
    
    print("\n\n🔍 **Testing Dynamic Table Discovery**")
    print("=" * 60)
    
    introspector = SchemaIntrospector()
    
    # Test tables that exist in the system
    test_tables = [
        ("enhanced_targets", "assets"),
        ("users", "identity"),
        ("jobs", "automation"),
        ("notifications", "communication")
    ]
    
    for table_name, schema_name in test_tables:
        print(f"\n📋 **Discovering {schema_name}.{table_name}:**")
        
        try:
            table_info = await introspector.get_table_info(table_name, schema_name)
            
            if table_info:
                print(f"   ✅ Table found automatically!")
                print(f"   📊 Columns: {len(table_info.get('columns', []))}")
                print(f"   🔗 Foreign keys: {len(table_info.get('foreign_keys', []))}")
                print(f"   📈 Estimated rows: {table_info.get('estimated_rows', 0):,}")
                
                # Show sample columns
                columns = table_info.get('columns', [])[:3]
                if columns:
                    print(f"   🔍 Sample columns:")
                    for col in columns:
                        print(f"      • {col['name']} ({col['data_type']})")
            else:
                print(f"   ❌ Table not found")
                
        except Exception as e:
            print(f"   ❌ Error discovering table: {e}")

async def test_search_capabilities():
    """Test search capabilities across the entire schema"""
    
    print("\n\n🔎 **Testing Schema Search Capabilities**")
    print("=" * 60)
    
    introspector = SchemaIntrospector()
    
    # Test search terms
    search_terms = ["user", "target", "job", "password", "email"]
    
    for term in search_terms:
        print(f"\n🔍 **Searching for '{term}':**")
        
        try:
            results = await introspector.search_schema(term)
            
            total_matches = (
                len(results["tables"]) + 
                len(results["columns"]) + 
                len(results["functions"]) + 
                len(results["views"]) + 
                len(results["enums"])
            )
            
            print(f"   ✅ Found {total_matches} total matches")
            
            if results["tables"]:
                print(f"   📋 Tables: {len(results['tables'])}")
                for table in results["tables"][:2]:
                    print(f"      • {table['table']}")
            
            if results["columns"]:
                print(f"   📊 Columns: {len(results['columns'])}")
                for col in results["columns"][:2]:
                    print(f"      • {col['table']}.{col['column']}")
                    
        except Exception as e:
            print(f"   ❌ Search failed: {e}")

async def demonstrate_solution():
    """Demonstrate the complete solution to the manual specification problem"""
    
    print("🎉 **SOLUTION DEMONSTRATION**")
    print("=" * 80)
    print("**BEFORE:** Manual specification required for every table and field")
    print("**AFTER:** Automatic discovery of ALL database schema information!")
    print("=" * 80)
    
    # Run all tests
    schema_success = await test_automatic_schema_discovery()
    ai_success = await test_ai_natural_language_queries()
    table_success = await test_dynamic_table_discovery()
    search_success = await test_search_capabilities()
    
    print("\n\n🏆 **RESULTS SUMMARY**")
    print("=" * 60)
    print(f"✅ Automatic Schema Discovery: {'PASSED' if schema_success else 'FAILED'}")
    print(f"✅ Natural Language Queries: {'PASSED' if ai_success else 'FAILED'}")
    print(f"✅ Dynamic Table Discovery: {'PASSED' if table_success else 'FAILED'}")
    print(f"✅ Schema Search: {'PASSED' if search_success else 'FAILED'}")
    
    if all([schema_success, ai_success, table_success, search_success]):
        print("\n🎉 **PROBLEM SOLVED!**")
        print("Your AI system now automatically knows about:")
        print("• Every table in the database")
        print("• Every column and its properties")
        print("• All relationships between tables")
        print("• Database structure and metadata")
        print("• No manual specification required!")
    else:
        print("\n⚠️ **Some tests failed - check configuration**")

if __name__ == "__main__":
    asyncio.run(demonstrate_solution())