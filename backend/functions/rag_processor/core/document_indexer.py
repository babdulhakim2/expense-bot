"""
Document Indexing Pipeline for RAG

Orchestrates the end-to-end document processing workflow from raw documents
to indexed chunks in the vector store and ColBERT index.
"""

import logging
import os
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json
import hashlib
from pathlib import Path

from processors.document_parser import ExpenseDocumentParser
from processors.text_chunker import SemanticTextChunker, Chunk
from storage.lancedb_store import ExpenseDocumentVectorStore

from config import Config

logger = logging.getLogger(__name__)

class IndexingJob:
    """Represents a document indexing job"""
    
    def __init__(self, 
                 job_id: str,
                 file_path: str,
                 business_id: str,
                 document_id: str = None,
                 metadata: Dict[str, Any] = None,
                 priority: int = 1):
        """
        Initialize indexing job
        
        Args:
            job_id: Unique job identifier
            file_path: Path to document file
            business_id: Business ID for context
            document_id: Optional document ID
            metadata: Additional metadata
            priority: Job priority (1=high, 2=medium, 3=low)
        """
        self.job_id = job_id
        self.file_path = file_path
        self.business_id = business_id
        self.metadata = metadata or {}
        self.priority = priority
        self.status = 'pending'
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.chunks_created = 0
        self.processing_time = None
        self.progress = {
            'stage': None,
            'percentage': 0,
            'stage_start_time': None,
            'stages_completed': []
        }
        
        # Set document_id after created_at is set (needed for _generate_document_id)
        self.document_id = document_id or self._generate_document_id()
    
    def _generate_document_id(self) -> str:
        """Generate unique document ID"""
        content = f"{self.file_path}_{self.business_id}_{self.created_at.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            'job_id': self.job_id,
            'file_path': self.file_path,
            'business_id': self.business_id,
            'document_id': self.document_id,
            'metadata': self.metadata,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'chunks_created': self.chunks_created,
            'processing_time': self.processing_time,
            'progress': self.progress
        }
    
    def update_progress(self, stage: str, percentage: int = 0):
        """Update job progress"""
        if self.progress['stage'] != stage:
            # Starting new stage
            if self.progress['stage']:
                self.progress['stages_completed'].append({
                    'stage': self.progress['stage'],
                    'completed_at': datetime.now().isoformat()
                })
            
            self.progress['stage'] = stage
            self.progress['stage_start_time'] = datetime.now().isoformat()
        
        self.progress['percentage'] = percentage


class ExpenseDocumentIndexer:
    """
    End-to-end document indexing pipeline
    """
    
    def __init__(self,
                 vector_store: ExpenseDocumentVectorStore = None,
                 max_workers: int = None,
                 batch_size: int = None):
        """
        Initialize indexing pipeline
        
        Args:
            vector_store: Vector store instance
            max_workers: Maximum number of worker threads (defaults to config)
            batch_size: Batch size for processing (defaults to config)
        """
        self.document_processor = ExpenseDocumentParser()
        self.chunking_orchestrator = SemanticTextChunker()
        self.vector_store = vector_store or ExpenseDocumentVectorStore()
        self.max_workers = max_workers or getattr(Config, 'RAG_MAX_WORKERS', 4)
        self.batch_size = batch_size or getattr(Config, 'CHUNK_BATCH_SIZE', 50)
        
        # Job management
        self.job_queue = []
        self.active_jobs = {}
        self.completed_jobs = {}
        self.failed_jobs = {}
        
        # Performance metrics
        self.metrics = {
            'total_jobs_processed': 0,
            'total_documents_processed': 0,
            'total_chunks_created': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'success_rate': 0.0,
            'last_processed': None
        }
        
        # Pipeline configuration
        self.config = {
            'enable_parallel_processing': getattr(Config, 'ENABLE_PARALLEL_PROCESSING', True),
            'auto_retry_failed': getattr(Config, 'AUTO_RETRY_FAILED', True),
            'max_retries': getattr(Config, 'MAX_INDEXING_RETRIES', 3),
            'chunk_batch_size': getattr(Config, 'CHUNK_BATCH_SIZE', 100)
        }
        
        logger.info(f"Initialized ExpenseDocumentIndexer with {max_workers} workers")
    
    def add_document(self,
                    file_path: str,
                    business_id: str,
                    document_id: str = None,
                    metadata: Dict[str, Any] = None,
                    priority: int = 1) -> str:
        """
        Add document to indexing queue
        
        Args:
            file_path: Path to document file
            business_id: Business ID for context
            document_id: Optional document ID
            metadata: Additional metadata
            priority: Job priority (1=high, 2=medium, 3=low)
            
        Returns:
            Job ID for tracking
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document not found: {file_path}")
            
            # Check if document type is supported
            # Use mime_type from metadata if available, otherwise detect from file path
            mime_type = metadata.get('mime_type') if metadata else None
            if mime_type:
                # Check if the mime_type is directly supported
                if mime_type not in self.document_processor.supported_types:
                    raise ValueError(f"Unsupported document type: {mime_type}")
            else:
                # Fall back to file path detection
                if not self.document_processor.is_supported(file_path):
                    raise ValueError(f"Unsupported document type: {file_path}")
            
            # Generate job ID
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
            
            # Create indexing job
            job = IndexingJob(
                job_id=job_id,
                file_path=file_path,
                business_id=business_id,
                document_id=document_id,
                metadata=metadata,
                priority=priority
            )
            
            # Add to queue (maintain priority order)
            self.job_queue.append(job)
            self.job_queue.sort(key=lambda x: x.priority)
            
            logger.info(f"Added document to indexing queue: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error adding document to queue: {str(e)}")
            raise
    
    def process_next_job(self) -> Optional[Dict[str, Any]]:
        """
        Process the next job in the queue
        
        Returns:
            Job result dictionary or None if queue is empty
        """
        if not self.job_queue:
            return None
        
        job = self.job_queue.pop(0)
        return self.process_job(job)
    
    def process_job(self, job: IndexingJob) -> Dict[str, Any]:
        """
        Process a single indexing job
        
        Args:
            job: IndexingJob to process
            
        Returns:
            Job result dictionary
        """
        job.status = 'processing'
        job.started_at = datetime.now()
        self.active_jobs[job.job_id] = job
        
        logger.info(f"Processing job: {job.job_id}")
        
        try:
            # Step 1: Process document
            job.update_progress('parsing', 10)
            logger.debug(f"Step 1: Processing document {job.file_path}")
            processed_doc = self.document_processor.process_document(
                file_path=job.file_path,
                business_id=job.business_id,
                document_id=job.document_id,
                metadata=job.metadata
            )
            
            # Step 2: Extract text content
            job.update_progress('parsing', 30)
            text_content = processed_doc['content_data'].get('text', '')
            if not text_content.strip():
                raise ValueError("No text content extracted from document")
            
            # Step 3: Determine document type for chunking strategy
            document_type = processed_doc['metadata'].get('document_type', 'general_document')
            
            # Step 4: Chunk document
            job.update_progress('chunking', 40)
            logger.debug(f"Step 2: Chunking document using {document_type} strategy")
            chunks = self.chunking_orchestrator.chunk_document(
                text=text_content,
                document_id=job.document_id,
                document_type=document_type,
                metadata=processed_doc['metadata']
            )
            
            if not chunks:
                raise ValueError("No chunks created from document")
            
            # Step 5: Prepare chunks for indexing
            job.update_progress('chunking', 60)
            logger.debug(f"Step 3: Preparing {len(chunks)} chunks for indexing")
            vector_documents = []
            
            for chunk in chunks:
                # Prepare for vector store
                vector_doc = {
                    'id': chunk.metadata.chunk_id,
                    'business_id': job.business_id,
                    'document_id': job.document_id,
                    'content': chunk.content,
                    **chunk.metadata.__dict__
                }
                vector_documents.append(vector_doc)
            
            # Step 6: Index in vector store
            job.update_progress('indexing', 80)
            logger.debug("Step 4: Indexing chunks in vector store")
            indexed_ids = self.vector_store.add_documents(vector_documents)
            
            # Update job status
            job.update_progress('completed', 100)
            job.status = 'completed'
            job.completed_at = datetime.now()
            job.chunks_created = len(chunks)
            job.processing_time = (job.completed_at - job.started_at).total_seconds()
            
            # Move to completed jobs
            self.active_jobs.pop(job.job_id, None)
            self.completed_jobs[job.job_id] = job
            
            # Update metrics
            self._update_metrics(job)
            
            result = {
                'job_id': job.job_id,
                'status': 'completed',
                'document_id': job.document_id,
                'chunks_created': job.chunks_created,
                'processing_time': job.processing_time,
                'vector_store_success': len(indexed_ids) > 0,
                'document_metadata': processed_doc['metadata']
            }
            
            # Cache the result if document has a hash (for avoiding reprocessing)
            if hasattr(self, '_rag_service_ref') and self._rag_service_ref:
                document_hash = job.metadata.get('document_hash')
                if document_hash:
                    self._rag_service_ref.cache_document_result(
                        document_hash=document_hash,
                        business_id=job.business_id,
                        job_result=result
                    )
            
            logger.info(f"Successfully processed job: {job.job_id} ({job.chunks_created} chunks)")
            return result
            
        except Exception as e:
            # Handle job failure
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.now()
            job.processing_time = (job.completed_at - job.started_at).total_seconds()
            
            # Move to failed jobs
            self.active_jobs.pop(job.job_id, None)
            self.failed_jobs[job.job_id] = job
            
            logger.error(f"Job failed: {job.job_id} - {str(e)}")
            
            return {
                'job_id': job.job_id,
                'status': 'failed',
                'error': str(e),
                'processing_time': job.processing_time
            }
    
    def process_batch(self, max_jobs: int = None) -> List[Dict[str, Any]]:
        """
        Process multiple jobs in batch
        
        Args:
            max_jobs: Maximum number of jobs to process (default: batch_size)
            
        Returns:
            List of job results
        """
        max_jobs = max_jobs or self.batch_size
        results = []
        
        logger.info(f"Processing batch of up to {max_jobs} jobs")
        
        if self.config['enable_parallel_processing'] and self.max_workers > 1:
            # Parallel processing
            jobs_to_process = []
            for _ in range(min(max_jobs, len(self.job_queue))):
                if self.job_queue:
                    jobs_to_process.append(self.job_queue.pop(0))
            
            if jobs_to_process:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = [executor.submit(self.process_job, job) for job in jobs_to_process]
                    results = [future.result() for future in futures]
        else:
            # Sequential processing
            for _ in range(min(max_jobs, len(self.job_queue))):
                result = self.process_next_job()
                if result:
                    results.append(result)
                else:
                    break
        
        logger.info(f"Completed batch processing: {len(results)} jobs processed")
        return results
    
    def process_directory(self,
                         directory_path: str,
                         business_id: str,
                         recursive: bool = True,
                         file_pattern: str = None) -> List[str]:
        """
        Add all documents in a directory to the indexing queue
        
        Args:
            directory_path: Path to directory containing documents
            business_id: Business ID for context
            recursive: Whether to search subdirectories
            file_pattern: Optional file pattern to filter (e.g., "*.pdf")
            
        Returns:
            List of job IDs created
        """
        try:
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            job_ids = []
            path_obj = Path(directory_path)
            
            # Get all files
            if recursive:
                files = path_obj.rglob(file_pattern or "*")
            else:
                files = path_obj.glob(file_pattern or "*")
            
            for file_path in files:
                if file_path.is_file() and self.document_processor.is_supported(str(file_path)):
                    try:
                        job_id = self.add_document(
                            file_path=str(file_path),
                            business_id=business_id,
                            metadata={'source_directory': directory_path}
                        )
                        job_ids.append(job_id)
                    except Exception as e:
                        logger.warning(f"Failed to add file {file_path}: {str(e)}")
            
            logger.info(f"Added {len(job_ids)} documents from directory: {directory_path}")
            return job_ids
            
        except Exception as e:
            logger.error(f"Error processing directory {directory_path}: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        # Check active jobs
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].to_dict()
        
        # Check completed jobs
        if job_id in self.completed_jobs:
            return self.completed_jobs[job_id].to_dict()
        
        # Check failed jobs
        if job_id in self.failed_jobs:
            return self.failed_jobs[job_id].to_dict()
        
        # Check queue
        for job in self.job_queue:
            if job.job_id == job_id:
                return job.to_dict()
        
        return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        return {
            'pending_jobs': len(self.job_queue),
            'active_jobs': len(self.active_jobs),
            'completed_jobs': len(self.completed_jobs),
            'failed_jobs': len(self.failed_jobs),
            'total_jobs': len(self.job_queue) + len(self.active_jobs) + len(self.completed_jobs) + len(self.failed_jobs),
            'metrics': self.metrics
        }
    
    def retry_failed_jobs(self) -> List[str]:
        """Retry all failed jobs"""
        retried_jobs = []
        
        for job_id, job in list(self.failed_jobs.items()):
            try:
                # Reset job status
                job.status = 'pending'
                job.started_at = None
                job.completed_at = None
                job.error_message = None
                
                # Move back to queue
                self.job_queue.append(job)
                self.failed_jobs.pop(job_id)
                retried_jobs.append(job_id)
                
            except Exception as e:
                logger.error(f"Error retrying job {job_id}: {str(e)}")
        
        # Sort queue by priority
        self.job_queue.sort(key=lambda x: x.priority)
        
        logger.info(f"Retried {len(retried_jobs)} failed jobs")
        return retried_jobs
    
    def clear_completed_jobs(self) -> int:
        """Clear completed job history"""
        count = len(self.completed_jobs)
        self.completed_jobs.clear()
        logger.info(f"Cleared {count} completed jobs from history")
        return count
    
    def _update_metrics(self, job: IndexingJob):
        """Update performance metrics"""
        self.metrics['total_jobs_processed'] += 1
        if job.status == 'completed':
            self.metrics['total_documents_processed'] += 1
            self.metrics['total_chunks_created'] += job.chunks_created
            self.metrics['total_processing_time'] += job.processing_time
            self.metrics['last_processed'] = job.completed_at.isoformat()
        
        # Calculate average processing time
        if self.metrics['total_jobs_processed'] > 0:
            self.metrics['average_processing_time'] = (
                self.metrics['total_processing_time'] / self.metrics['total_jobs_processed']
            )
        
        # Calculate success rate
        total_completed = len(self.completed_jobs)
        total_failed = len(self.failed_jobs)
        total_finished = total_completed + total_failed
        
        if total_finished > 0:
            self.metrics['success_rate'] = total_completed / total_finished
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on indexing pipeline"""
        try:
            status = 'healthy'
            issues = []
            
            # Check document processor
            doc_processor_health = self.document_processor.health_check()
            if doc_processor_health['status'] != 'healthy':
                issues.append(f"Document processor: {doc_processor_health.get('status', 'unknown')}")
            
            # Check vector store
            vector_store_health = self.vector_store.health_check()
            if vector_store_health['status'] != 'healthy':
                issues.append(f"Vector store: {vector_store_health.get('status', 'unknown')}")
            
            
            # Check chunking orchestrator
            chunking_health = self.chunking_orchestrator.health_check()
            if chunking_health['status'] != 'healthy':
                issues.append(f"Chunking orchestrator: {chunking_health.get('status', 'unknown')}")
            
            if issues:
                status = 'warning' if all('unhealthy' not in issue for issue in issues) else 'unhealthy'
            
            return {
                'status': status,
                'issues': issues,
                'queue_status': self.get_queue_status(),
                'config': self.config,
                'supported_document_types': self.document_processor.get_supported_types(),
                'available_chunking_strategies': self.chunking_orchestrator.get_available_strategies()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }