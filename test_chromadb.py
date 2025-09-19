#!/usr/bin/env python3
"""
Test script to verify the new ChromaDB implementation.
"""

import os
import sys
import sqlite3

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from iftttwh.app import init_db, semantic_search_tweets, DB_PATH

def test_chromadb_implementation():
    """Test the ChromaDB implementation."""
    print("Testing ChromaDB implementation...")
    
    # Initialize the database
    init_db()
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print("ERROR: Database was not created")
        return False
        
    # Check if we can perform semantic search
    try:
        results = semantic_search_tweets("market finance", 5)
        print(f"Semantic search returned {len(results)} results")
        
        # Print first result if available
        if results:
            print(f"First result: {results[0]['text']}")
            
        print("ChromaDB implementation test PASSED")
        return True
    except Exception as e:
        print(f"ERROR: Semantic search failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_chromadb_implementation()
    sys.exit(0 if success else 1)