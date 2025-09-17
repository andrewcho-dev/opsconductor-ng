#!/usr/bin/env python3
"""Test vector store directly to see what's stored"""

import chromadb
from chromadb.config import Settings
import asyncio

async def test_vector_store():
    print("Testing Vector Store Contents...")
    
    # Create ChromaDB client
    client = chromadb.Client(Settings(anonymized_telemetry=False))
    
    # Check collections
    collections = client.list_collections()
    print(f"\n📚 Found {len(collections)} collections:")
    for col in collections:
        print(f"  - {col.name}")
    
    # Try to get the knowledge collection
    try:
        knowledge_col = client.get_collection("system_knowledge")
        count = knowledge_col.count()
        print(f"\n📖 Knowledge collection has {count} documents")
        
        if count > 0:
            # Get a sample of documents
            results = knowledge_col.get(limit=3)
            print("\nFirst 3 documents:")
            for i, doc in enumerate(results['documents'][:3], 1):
                preview = doc[:200] if len(doc) > 200 else doc
                print(f"\n{i}. {preview}...")
                if results['metadatas'] and i <= len(results['metadatas']):
                    print(f"   Metadata: {results['metadatas'][i-1]}")
        
        # Test a search query
        print("\n🔍 Testing search for 'Docker':")
        search_results = knowledge_col.query(
            query_texts=["Docker containers commands"],
            n_results=2
        )
        
        if search_results['documents'] and search_results['documents'][0]:
            for i, doc in enumerate(search_results['documents'][0], 1):
                preview = doc[:300] if len(doc) > 300 else doc
                print(f"\n{i}. {preview}...")
        else:
            print("   No results found")
            
    except Exception as e:
        print(f"Error accessing knowledge collection: {e}")
    
    # Check troubleshooting solutions
    try:
        solutions_col = client.get_collection("troubleshooting_solutions")
        count = solutions_col.count()
        print(f"\n🔧 Solutions collection has {count} documents")
        
        if count > 0:
            # Test a search query
            print("\n🔍 Testing search for 'disk space':")
            search_results = solutions_col.query(
                query_texts=["server disk space"],
                n_results=1
            )
            
            if search_results['documents'] and search_results['documents'][0]:
                for doc in search_results['documents'][0]:
                    preview = doc[:400] if len(doc) > 400 else doc
                    print(f"\n{preview}...")
            else:
                print("   No results found")
                
    except Exception as e:
        print(f"Error accessing solutions collection: {e}")

if __name__ == "__main__":
    asyncio.run(test_vector_store())