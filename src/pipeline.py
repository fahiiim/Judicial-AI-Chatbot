"""
Main RAG Pipeline orchestration
Coordinates all components: ingestion, chunking, embedding, retrieval, generation
"""
import logging
import json
from typing import List, Dict, Any
from pathlib import Path
from tqdm import tqdm
import sqlite3
from datetime import datetime

from config.settings import settings
from src.ingestion import PDFParser, TextCleaner
from src.chunking import SemanticChunker, MetadataExtractor
from src.embeddings import EmbeddingGenerator, VectorStore
from src.retrieval import QueryProcessor, HybridRetriever
from src.generation import RAGGenerator, CitationHandler

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Complete RAG pipeline for legal documents"""
    
    def __init__(self, pdf_path: str = None):
        """Initialize the RAG pipeline
        
        Args:
            pdf_path: Path to PDF file (default from settings)
        """
        self.pdf_path = pdf_path or settings.PDF_PATH
        
        # Initialize components
        logger.info("Initializing RAG Pipeline components...")
        self.pdf_parser = PDFParser(self.pdf_path)
        self.text_cleaner = TextCleaner()
        self.chunker = SemanticChunker()
        self.metadata_extractor = MetadataExtractor()
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStore()
        self.query_processor = QueryProcessor()
        self.retriever = HybridRetriever(self.embedding_gen, self.vector_store)
        self.generator = RAGGenerator()
        
        # Initialize database for chat history and feedback
        self._init_database()
        
        logger.info("RAG Pipeline initialized successfully")
    
    def _init_database(self):
        """Initialize SQLite database for chat history"""
        try:
            settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
            self.db_path = settings.DB_PATH
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Chat history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT,
                    query TEXT,
                    answer TEXT,
                    model TEXT,
                    timestamp DATETIME,
                    tokens_used INTEGER
                )
            """)
            
            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY,
                    query TEXT,
                    answer TEXT,
                    rating INTEGER,
                    comment TEXT,
                    timestamp DATETIME
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def build_index(self, force_rebuild: bool = False) -> bool:
        """Build the entire index from PDF
        
        Args:
            force_rebuild: Force rebuild even if index exists
            
        Returns:
            True if successful
        """
        try:
            # Check if index already exists
            if self.vector_store.get_collection_size() > 0 and not force_rebuild:
                logger.info("Index already exists, skipping build")
                return True
            
            logger.info("Starting index building process...")
            
            # Step 1: Extract documents from PDF
            logger.info("Step 1: Extracting documents from PDF...")
            pages_with_metadata = self.pdf_parser.extract_text_with_metadata()
            logger.info(f"Extracted {len(pages_with_metadata)} pages")
            
            # Step 2: Clean and preprocess text
            logger.info("Step 2: Cleaning and preprocessing text...")
            for page in pages_with_metadata:
                page["text"] = self.text_cleaner.preprocess_for_chunking(page["text"])
            
            # Step 3: Chunk documents semantically
            logger.info("Step 3: Creating semantic chunks...")
            all_chunks = []
            for page in pages_with_metadata:
                chunks = self.chunker.chunk_text(
                    page["text"],
                    metadata={
                        "page_num": page["page_num"],
                        "section": page["section"],
                        "subsection": page["subsection"],
                        "document_title": page["document_title"]
                    }
                )
                all_chunks.extend(chunks)
            
            logger.info(f"Created {len(all_chunks)} chunks")
            
            # Step 4: Extract metadata from chunks
            logger.info("Step 4: Extracting metadata from chunks...")
            for chunk in tqdm(all_chunks, desc="Extracting metadata"):
                chunk["metadata"] = self.metadata_extractor.extract_metadata(
                    chunk["text"],
                    chunk
                )
            
            # Step 5: Generate embeddings
            logger.info("Step 5: Generating embeddings...")
            texts = [chunk["text"] for chunk in all_chunks]
            embeddings = self.embedding_gen.embed_texts(texts)
            
            # Step 6: Index in vector store
            logger.info("Step 6: Indexing in vector store...")
            self.vector_store.add_documents(all_chunks, embeddings)
            
            logger.info(f"Successfully indexed {len(all_chunks)} chunks")
            return True
        
        except Exception as e:
            logger.error(f"Error building index: {e}")
            return False
    
    def answer_query(self, query: str, include_retrieved_docs: bool = False) -> Dict[str, Any]:
        """Answer a user query using the RAG pipeline
        
        Args:
            query: User query
            include_retrieved_docs: Whether to include retrieved documents in response
            
        Returns:
            Dictionary with answer, citations, and metadata
        """
        try:
            # Step 1: Process query
            logger.info(f"Processing query: {query[:50]}...")
            processed_query = self.query_processor.process_query(query)
            
            # Step 2: Retrieve relevant documents
            logger.info("Retrieving relevant documents...")
            retrieved_docs = self.retriever.retrieve(
                query=processed_query["cleaned"],
                k=settings.RETRIEVAL_K
            )
            
            # Convert to list of dictionaries
            retrieved_doc_list = [
                {**doc, "relevance_score": score}
                for doc, score in retrieved_docs
            ]
            
            logger.info(f"Retrieved {len(retrieved_doc_list)} documents")
            
            # Step 3: Generate answer using LLM
            logger.info("Generating answer...")
            result = self.generator.generate_answer(query, retrieved_doc_list)
            
            # Step 4: Process citations
            logger.info("Processing citations...")
            citations = CitationHandler.extract_citations(result.get("answer", ""))
            result["citations"] = citations
            
            # Add retrieved documents if requested
            if include_retrieved_docs:
                result["retrieved_documents"] = [
                    {
                        "text": doc.get("text", "")[:500],  # Truncate for API response
                        "source": doc.get("source", ""),
                        "section": doc.get("section", ""),
                        "relevance_score": doc.get("relevance_score", 0)
                    }
                    for doc in retrieved_doc_list
                ]
            
            return result
        
        except Exception as e:
            logger.error(f"Error answering query: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "citations": [],
                "model": settings.LLM_MODEL,
                "status": "error"
            }
    
    def log_interaction(self, query: str, answer: str, session_id: str = None):
        """Log a chat interaction
        
        Args:
            query: User query
            answer: Generated answer
            session_id: Optional session ID
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO chat_history (session_id, query, answer, model, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id or "default",
                query,
                answer,
                settings.LLM_MODEL,
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug("Interaction logged successfully")
        
        except Exception as e:
            logger.warning(f"Error logging interaction: {e}")
    
    def log_feedback(self, query: str, answer: str, rating: int, comment: str = None):
        """Log user feedback on answer quality
        
        Args:
            query: Original query
            answer: Generated answer
            rating: Rating 1-5
            comment: Optional comment
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO feedback (query, answer, rating, comment, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (query, answer, rating, comment, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Feedback logged: rating={rating}")
        
        except Exception as e:
            logger.warning(f"Error logging feedback: {e}")
    
    def get_indexed_count(self) -> int:
        """Get number of indexed documents
        
        Returns:
            Number of documents in vector store
        """
        return self.vector_store.get_collection_size()
