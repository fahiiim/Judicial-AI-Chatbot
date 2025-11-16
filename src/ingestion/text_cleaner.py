"""
Text cleaning and normalization for legal documents
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


class TextCleaner:
    """Clean and normalize text from legal documents"""
    
    # Common patterns to remove or normalize
    PATTERNS = {
        "multiple_spaces": r"\s{2,}",
        "page_breaks": r"\f",
        "line_numbers": r"^\s*\d+\s*",
        "extra_whitespace": r"\n\s*\n",
        "urls": r"https?://\S+",
        "emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    }
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove page breaks and excessive whitespace
        text = re.sub(TextCleaner.PATTERNS["page_breaks"], " ", text)
        text = re.sub(TextCleaner.PATTERNS["multiple_spaces"], " ", text)
        text = re.sub(TextCleaner.PATTERNS["extra_whitespace"], "\n\n", text)
        
        # Remove line numbers (common in PDFs)
        text = re.sub(TextCleaner.PATTERNS["line_numbers"], "", text, flags=re.MULTILINE)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def normalize_legal_references(text: str) -> str:
        """Normalize legal references (e.g., USC, CFR)
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized references
        """
        # Normalize "U.S.C." variations
        text = re.sub(r"U\.?\s?S\.?\s?C\.?", "U.S.C.", text)
        
        # Normalize "§" symbol (section)
        text = re.sub(r"&sect;|Sec\.|Section", "§", text)
        
        # Normalize "et seq." (and following)
        text = re.sub(r"et\s*seq\.?", "et seq.", text)
        
        return text
    
    @staticmethod
    def remove_artifacts(text: str) -> str:
        """Remove common PDF artifacts and formatting issues
        
        Args:
            text: Text to clean
            
        Returns:
            Text without artifacts
        """
        # Remove URLs
        text = re.sub(TextCleaner.PATTERNS["urls"], "", text)
        
        # Remove emails
        text = re.sub(TextCleaner.PATTERNS["emails"], "", text)
        
        # Remove control characters
        text = "".join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text
    
    @staticmethod
    def preprocess_for_chunking(text: str) -> str:
        """Prepare text for semantic chunking
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text ready for chunking
        """
        text = TextCleaner.clean_text(text)
        text = TextCleaner.remove_artifacts(text)
        text = TextCleaner.normalize_legal_references(text)
        
        logger.debug(f"Preprocessed text: {len(text)} characters")
        return text
