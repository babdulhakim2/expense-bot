"""
RAG Processor Cloud Function

Standalone cloud function for expense document processing and semantic search.
Handles document indexing, vector storage, and search operations independently.
"""

# For pytest compatibility, avoid relative imports in __init__.py
# Components will be imported directly by modules that need them

__all__ = [
    'ExpenseDocumentSearchEngine',
    'ExpenseDocumentIndexer', 
    'ExpenseDocumentVectorStore',
    'ExpenseDocumentParser',
    'SemanticTextChunker'
]

__version__ = '1.0.0'