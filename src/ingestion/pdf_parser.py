"""
PDF Parser for legal documents
Extracts text with metadata (page numbers, sections, references)
"""
import logging
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
import pypdf
import pdfplumber

logger = logging.getLogger(__name__)


class PDFParser:
    """Parse legal PDFs and extract structured text with metadata"""
    
    def __init__(self, pdf_path: str | Path):
        """Initialize PDF parser
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        
        self.document_title = self.pdf_path.stem
        logger.info(f"Initialized PDFParser for {self.pdf_path}")
    
    def extract_text_with_metadata(self) -> List[Dict[str, Any]]:
        """Extract text from PDF with metadata
        
        Returns:
            List of dictionaries with keys: text, page_num, section, subsection
        """
        pages_with_metadata = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text or text.strip() == "":
                        continue
                    
                    # Extract section and subsection information
                    section, subsection = self._extract_legal_references(text)
                    
                    pages_with_metadata.append({
                        "text": text,
                        "page_num": page_num,
                        "section": section,
                        "subsection": subsection,
                        "document_title": self.document_title,
                        "source": f"{self.document_title}:p{page_num}"
                    })
                    
                    logger.debug(f"Extracted page {page_num} with section: {section}")
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
        
        logger.info(f"Extracted {len(pages_with_metadata)} pages with metadata")
        return pages_with_metadata
    
    def _extract_legal_references(self, text: str) -> Tuple[str, str]:
        """Extract section and subsection numbers from text
        
        Args:
            text: Text content to analyze
            
        Returns:
            Tuple of (section, subsection)
        """
        # Pattern for legal sections: § 2113, § 2113.1, etc.
        section_pattern = r"§\s*(\d+(?:\.\d+)?)"
        # Pattern for subsections: (a), (b), (1), (2), etc.
        subsection_pattern = r"\(([a-zA-Z0-9]+)\)"
        
        sections = re.findall(section_pattern, text)
        subsections = re.findall(subsection_pattern, text[:500])  # Look in first part
        
        section = sections[0] if sections else "Unknown"
        subsection = subsections[0] if subsections else ""
        
        return section, subsection
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get metadata about the PDF document
        
        Returns:
            Dictionary with document metadata
        """
        try:
            with pypdf.PdfReader(self.pdf_path) as reader:
                num_pages = len(reader.pages)
                metadata = reader.metadata
                
                return {
                    "title": self.document_title,
                    "num_pages": num_pages,
                    "author": metadata.author if metadata else None,
                    "subject": metadata.subject if metadata else None,
                    "creation_date": metadata.creation_date if metadata else None,
                }
        except Exception as e:
            logger.warning(f"Could not extract metadata: {e}")
            return {"title": self.document_title, "error": str(e)}
