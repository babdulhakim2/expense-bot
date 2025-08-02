#!/usr/bin/env python3
"""
Local testing script for RAG Processor Cloud Function

Run this script to test the RAG processor locally before deployment.
"""

import os
import sys
import json
import tempfile
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load local environment if available
env_local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.local')
if os.path.exists(env_local_path):
    print(f"📄 Loading local environment from {env_local_path}")
    with open(env_local_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Set environment variables for local testing (if not already set)
if 'ENVIRONMENT' not in os.environ:
    print("🔧 Setting up local testing environment...")
    os.environ['ENVIRONMENT'] = 'local'
    os.environ['LANCEDB_URI'] = './data/lancedb'
    os.environ['LANCEDB_API_KEY'] = ''
    os.environ['LANCEDB_REGION'] = ''
    os.environ['LANCEDB_TABLE_NAME'] = 'expense_documents_local'
    print("   Using local LanceDB at ./data/lancedb")

def test_local_rag_function():
    """Test RAG function locally"""
    print("🧪 Testing RAG Processor Cloud Function Locally")
    print("=" * 60)
    
    try:
        # Import the main function
        from main import rag_processor, get_search_engine, get_document_indexer
        
        # Mock Flask request object
        class MockRequest:
            def __init__(self, method='GET', path='/', json_data=None, args=None):
                self.method = method
                self.path = path
                self._json_data = json_data
                self.args = args or {}
                
            def get_json(self):
                return self._json_data
        
        # Test 1: Health check
        print("1. Testing health check...")
        request = MockRequest(method='GET', path='/health')
        response = rag_processor(request)
        print(f"   Health check response: {response}")
        
        # Test 2: Stats
        print("\n2. Testing stats...")
        request = MockRequest(method='GET', path='/stats')
        response = rag_processor(request)
        print(f"   Stats response: {response}")
        
        # Test 3: Search
        print("\n3. Testing search...")
        search_data = {
            'query': 'coffee expense receipt',
            'business_id': 'test_business_local',
            'limit': 5
        }
        request = MockRequest(method='POST', path='/search', json_data=search_data)
        response = rag_processor(request)
        print(f"   Search response: {response}")
        
        # Test 4: Index document
        print("\n4. Testing document indexing...")
        index_data = {
            'business_id': 'test_business_local',
            'document_id': 'test_doc_001',
            'drive_url': 'https://drive.google.com/file/d/test123/view',
            'metadata': {'test': True, 'filename': 'test_receipt.pdf'}
        }
        request = MockRequest(method='POST', path='/index', json_data=index_data)
        response = rag_processor(request)
        print(f"   Index response: {response}")
        
        # Test 5: Component initialization
        print("\n5. Testing component initialization...")
        search_engine = get_search_engine()
        indexer = get_document_indexer() 
        
        print(f"   Search engine initialized: {search_engine is not None}")
        print(f"   Document indexer initialized: {indexer is not None}")
        
        # Test 6: Direct component health checks
        print("\n6. Testing component health checks...")
        if search_engine:
            engine_health = search_engine.health_check()
            print(f"   Search engine health: {engine_health.get('status', 'unknown')}")
        
        if indexer:
            indexer_health = indexer.health_check()
            print(f"   Document indexer health: {indexer_health.get('status', 'unknown')}")
        
        print("\n✅ All local tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Local test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_components():
    """Test RAG components directly"""
    print("\n🔧 Testing RAG Components Directly")
    print("=" * 60)
    
    try:
        # Test vector store
        print("1. Testing vector store...")
        from storage.lancedb_store import ExpenseDocumentVectorStore
        
        vector_store = ExpenseDocumentVectorStore()
        health = vector_store.health_check()
        print(f"   Vector store health: {health.get('status', 'unknown')}")
        
        # Test search engine
        print("\n2. Testing search engine...")
        from core.search_engine import ExpenseDocumentSearchEngine
        
        search_engine = ExpenseDocumentSearchEngine()
        search_response = search_engine.search(
            query="test query",
            business_id="test_business",
            limit=3
        )
        print(f"   Search completed: {search_response.total_results} results")
        
        # Test document parser
        print("\n3. Testing document parser...")
        from processors.document_parser import ExpenseDocumentParser
        
        parser = ExpenseDocumentParser()
        supported_types = parser.get_supported_types()
        print(f"   Supported file types: {len(supported_types)} types")
        
        # Test text chunker
        print("\n4. Testing text chunker...")
        from processors.text_chunker import SemanticTextChunker
        
        chunker = SemanticTextChunker()
        strategies = chunker.get_available_strategies()
        print(f"   Available strategies: {strategies}")
        
        print("\n✅ Direct component tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Direct component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_http_simulation():
    """Simulate HTTP requests to the function"""
    print("\n🌐 Simulating HTTP Requests")
    print("=" * 60)
    
    try:
        import functions_framework
        from flask import Flask
        
        # Create a test Flask app
        app = Flask(__name__)
        
        # Import and register the function
        from main import rag_processor
        
        @app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'OPTIONS'])
        @app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
        def catch_all(path):
            # Simulate the functions framework request handling
            import flask
            return rag_processor(flask.request)
        
        # Test the app
        with app.test_client() as client:
            # Test health endpoint
            print("1. Testing /health endpoint...")
            response = client.get('/health')
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.get_json()}")
            
            # Test search endpoint
            print("\n2. Testing /search endpoint...")
            search_data = {
                'query': 'test search',
                'business_id': 'test_business',
                'limit': 5
            }
            response = client.post('/search', json=search_data)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.get_json()}")
        
        print("\n✅ HTTP simulation completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ HTTP simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 RAG Processor Local Testing Suite")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Component Tests", test_direct_components),
        ("Function Tests", test_local_rag_function),
        ("HTTP Simulation", run_http_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n▶️  Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG function is ready for deployment.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please fix issues before deployment.")
        sys.exit(1)