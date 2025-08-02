#!/usr/bin/env python3
"""
Start RAG Processor as local HTTP server for development testing
"""

import os
import logging
from flask import Flask
from main import rag_processor

# Set environment - only override if not already set
if 'ENVIRONMENT' not in os.environ:
    os.environ['ENVIRONMENT'] = 'local'

# Only set local database if no cloud configuration is provided
if 'LANCEDB_URI' not in os.environ:
    os.environ['LANCEDB_URI'] = './.lancedb/data'
    os.environ['LANCEDB_TABLE_NAME'] = 'expense_documents_local'
elif not os.environ.get('LANCEDB_TABLE_NAME'):
    # Set default table name based on URI
    if os.environ['LANCEDB_URI'].startswith('db://'):
        os.environ['LANCEDB_TABLE_NAME'] = 'expense_documents'  # Cloud
    else:
        os.environ['LANCEDB_TABLE_NAME'] = 'expense_documents_local'  # Local

# Load SERVICE_ACCOUNT_KEY from backend .env if not already set
if 'SERVICE_ACCOUNT_KEY' not in os.environ:
    env_path = '../../backend/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
            # Find SERVICE_ACCOUNT_KEY and extract its multiline JSON value
            start_marker = 'SERVICE_ACCOUNT_KEY='
            start_idx = content.find(start_marker)
            if start_idx != -1:
                start_idx += len(start_marker)
                # Find the start of the JSON (should be '{')
                json_start = content.find('{', start_idx)
                if json_start != -1:
                    # Find the matching closing brace by counting braces
                    brace_count = 0
                    json_end = json_start
                    for i, char in enumerate(content[json_start:], json_start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    json_value = content[json_start:json_end]
                    os.environ['SERVICE_ACCOUNT_KEY'] = json_value
                    print(f"✅ Loaded SERVICE_ACCOUNT_KEY from backend/.env ({len(json_value)} chars)")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_local_app():
    """Create Flask app for local testing"""
    app = Flask(__name__)
    
    # Route all requests to rag_processor
    @app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'OPTIONS'])
    @app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
    def handle_request(path):
        from flask import request
        return rag_processor(request)
    
    return app

if __name__ == '__main__':
    print("🚀 Starting RAG Processor locally at http://localhost:8090")
    print("📋 Available endpoints:")
    print("  - GET  /health - Health check")
    print("  - GET  /stats - System statistics") 
    print("  - POST /search - Search documents")
    print("  - POST /index - Index documents")
    print()
    
    app = create_local_app()
    app.run(host='0.0.0.0', port=8090, debug=True)