"""
Citation handling and highlighting
"""
import logging
import re
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class CitationHandler:
    """Handle citation extraction, formatting, and linking"""
    
    # Patterns for different citation types
    CITATION_PATTERNS = {
        "usc": r"(?:18\s+)?U\.S\.C\.?\s+(?:§\s*)?(\d+(?:\.\d+)?(?:\s*\([a-zA-Z0-9]+\))?)",
        "section": r"§\s*(\d+(?:\.\d+)?)",
        "subsection": r"\(([a-zA-Z0-9]+)\)",
        "cfr": r"(\d+)\s+C\.F\.R\.?\s+(?:§\s*)?(\d+(?:\.\d+)?)",
    }
    
    @staticmethod
    def extract_citations(text: str) -> List[Dict[str, Any]]:
        """Extract all citations from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        # Extract USC citations
        usc_matches = re.finditer(CitationHandler.CITATION_PATTERNS["usc"], text)
        for match in usc_matches:
            citations.append({
                "type": "usc",
                "statute": f"18 U.S.C. § {match.group(1)}",
                "reference": match.group(1),
                "start": match.start(),
                "end": match.end(),
                "text": match.group(0)
            })
        
        # Extract CFR citations
        cfr_matches = re.finditer(CitationHandler.CITATION_PATTERNS["cfr"], text)
        for match in cfr_matches:
            citations.append({
                "type": "cfr",
                "statute": f"{match.group(1)} C.F.R. § {match.group(2)}",
                "reference": f"{match.group(1)}_{match.group(2)}",
                "start": match.start(),
                "end": match.end(),
                "text": match.group(0)
            })
        
        # Remove duplicates (keep longest/most specific)
        unique_citations = {}
        for citation in citations:
            key = citation["reference"]
            if key not in unique_citations or len(citation["text"]) > len(unique_citations[key]["text"]):
                unique_citations[key] = citation
        
        return list(unique_citations.values())
    
    @staticmethod
    def highlight_citations(text: str, citations: List[Dict[str, Any]] = None) -> str:
        """Highlight citations in text (HTML format)
        
        Args:
            text: Text to highlight
            citations: Optional pre-extracted citations
            
        Returns:
            Text with HTML highlighting
        """
        if citations is None:
            citations = CitationHandler.extract_citations(text)
        
        if not citations:
            return text
        
        # Sort by position (reverse to maintain indices)
        sorted_citations = sorted(citations, key=lambda c: c["start"], reverse=True)
        
        # Insert HTML tags
        for citation in sorted_citations:
            start = citation["start"]
            end = citation["end"]
            citation_ref = citation["reference"]
            
            highlight = f'<span class="citation" data-statute="{citation_ref}" title="{citation["statute"]}">{text[start:end]}</span>'
            text = text[:start] + highlight + text[end:]
        
        return text
    
    @staticmethod
    def format_markdown_citations(text: str, citations: List[Dict[str, Any]] = None) -> str:
        """Format citations as markdown with links
        
        Args:
            text: Text to format
            citations: Optional pre-extracted citations
            
        Returns:
            Text with markdown formatting
        """
        if citations is None:
            citations = CitationHandler.extract_citations(text)
        
        if not citations:
            return text
        
        # Sort by position (reverse to maintain indices)
        sorted_citations = sorted(citations, key=lambda c: c["start"], reverse=True)
        
        # Insert markdown
        for citation in sorted_citations:
            start = citation["start"]
            end = citation["end"]
            statute = citation["statute"]
            
            # Create footnote-style reference
            markdown = f"[{text[start:end]}]({statute})"
            text = text[:start] + markdown + text[end:]
        
        return text
    
    @staticmethod
    def create_citation_index(documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Create an index of all citations in documents
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Dictionary mapping statutes to documents
        """
        citation_index = {}
        
        for doc in documents:
            text = doc.get("text", "")
            citations = CitationHandler.extract_citations(text)
            
            for citation in citations:
                statute = citation["statute"]
                if statute not in citation_index:
                    citation_index[statute] = []
                
                citation_index[statute].append({
                    "document": doc.get("source", "Unknown"),
                    "page": doc.get("page_num", ""),
                    "excerpt": text[max(0, citation["start"]-50):min(len(text), citation["end"]+50)]
                })
        
        return citation_index
    
    @staticmethod
    def validate_citations(text: str, known_statutes: List[str]) -> Dict[str, bool]:
        """Validate if citations in text match known statutes
        
        Args:
            text: Text with citations
            known_statutes: List of valid statute references
            
        Returns:
            Dictionary mapping citations to validity
        """
        citations = CitationHandler.extract_citations(text)
        validity = {}
        
        for citation in citations:
            reference = citation["reference"]
            is_valid = any(ref in reference for ref in known_statutes)
            validity[citation["statute"]] = is_valid
        
        return validity
