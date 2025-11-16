"""
Semantic chunking using NLP to split documents meaningfully
"""
import logging
import re
from typing import List, Dict, Any
import spacy
from config.settings import settings

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Split documents into semantically meaningful chunks"""
    
    def __init__(self):
        """Initialize the semantic chunker"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("SpaCy model not found. Downloading...")
            import os
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into semantic chunks
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Split by legal sections first
        section_chunks = self._split_by_sections(text)
        
        # Further split large sections
        final_chunks = []
        for section_chunk in section_chunks:
            if len(section_chunk) > settings.CHUNK_SIZE:
                # Split by sentences and recombine
                sub_chunks = self._split_by_sentences(section_chunk)
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(section_chunk)
        
        # Convert to chunk dictionaries with metadata
        chunk_dicts = []
        for i, chunk_text in enumerate(final_chunks):
            chunk_dict = {
                "text": chunk_text,
                "chunk_id": i,
                "length": len(chunk_text),
            }
            
            # Merge with provided metadata
            if metadata:
                chunk_dict.update(metadata)
            
            chunk_dicts.append(chunk_dict)
        
        logger.info(f"Created {len(chunk_dicts)} chunks from text of {len(text)} characters")
        return chunk_dicts
    
    def _split_by_sections(self, text: str) -> List[str]:
        """Split text by legal section markers
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # Pattern for section headers: § 2113, § 2113.1, etc.
        section_pattern = r"(§\s*\d+(?:\.\d+)?(?:\s*\([a-zA-Z0-9]+\))?)"
        
        # Split while keeping the section header
        parts = re.split(section_pattern, text)
        
        chunks = []
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                chunk = parts[i] + parts[i + 1]  # Header + content
                chunks.append(chunk)
        
        # If no sections found, return original text
        if not chunks:
            chunks = [text]
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text into sentences and recombine into chunks
        
        Args:
            text: Text to split
            
        Returns:
            List of combined sentence chunks
        """
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        if not sentences:
            return [text] if len(text) >= settings.MIN_CHUNK_SIZE else []
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(test_chunk) <= settings.CHUNK_SIZE:
                current_chunk = test_chunk
            else:
                if len(current_chunk) >= settings.MIN_CHUNK_SIZE:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        # Add remaining chunk
        if len(current_chunk) >= settings.MIN_CHUNK_SIZE:
            chunks.append(current_chunk)
        
        # Add overlap if needed
        if settings.CHUNK_OVERLAP > 0:
            chunks = self._add_overlap(chunks)
        
        return chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Add overlap between chunks for context continuity
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of overlapped chunks
        """
        if len(chunks) < 2:
            return chunks
        
        overlapped = [chunks[0]]
        
        for i in range(1, len(chunks)):
            # Get overlap from end of previous chunk
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]
            
            # Calculate overlap
            overlap_size = min(settings.CHUNK_OVERLAP, len(prev_chunk))
            overlap_text = prev_chunk[-overlap_size:]
            
            # Create chunk with overlap
            combined = overlap_text + " " + curr_chunk
            overlapped.append(combined)
        
        return overlapped
