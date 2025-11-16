"""
Metadata extraction from legal documents using NER and regex patterns
"""
import logging
import re
from typing import Dict, Any, List, Set
import spacy

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract structured metadata from legal document chunks"""
    
    # Legal entity types to extract
    CRIME_KEYWORDS = {
        "robbery", "theft", "assault", "battery", "burglary", "larceny",
        "fraud", "embezzlement", "forgery", "counterfeiting", "kidnapping",
        "murder", "manslaughter", "homicide", "rape", "arson", "drug",
        "conspiracy", "corruption", "bribery", "extortion", "blackmail"
    }
    
    PUNISHMENT_KEYWORDS = {
        "imprisonment", "fine", "penalty", "punishment", "sentence",
        "incarceration", "detention", "confinement", "probation", "restitution"
    }
    
    LEGAL_PROCEDURE_KEYWORDS = {
        "shall", "may", "must", "required", "prohibited", "unlawful",
        "offense", "violation", "crime", "guilty", "convicted", "person"
    }
    
    def __init__(self):
        """Initialize the metadata extractor"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("SpaCy model not found.")
            self.nlp = None
    
    def extract_metadata(self, chunk_text: str, chunk_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract metadata from a chunk
        
        Args:
            chunk_text: Text of the chunk
            chunk_metadata: Existing metadata dictionary
            
        Returns:
            Enriched metadata dictionary
        """
        if chunk_metadata is None:
            chunk_metadata = {}
        
        # Extract various metadata types
        chunk_metadata["entities"] = self._extract_entities(chunk_text)
        chunk_metadata["crime_types"] = self._extract_crime_types(chunk_text)
        chunk_metadata["punishment_types"] = self._extract_punishment_types(chunk_text)
        chunk_metadata["legal_concepts"] = self._extract_legal_concepts(chunk_text)
        chunk_metadata["section_references"] = self._extract_section_references(chunk_text)
        chunk_metadata["keywords"] = self._extract_keywords(chunk_text)
        chunk_metadata["text_type"] = self._classify_text_type(chunk_text)
        
        return chunk_metadata
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities using NER
        
        Args:
            text: Text to analyze
            
        Returns:
            List of entities with types
        """
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            # Focus on relevant entity types for legal documents
            if ent.label_ in ["PERSON", "ORG", "GPE", "LAW"]:
                entities.append({
                    "text": ent.text,
                    "type": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        
        return entities
    
    def _extract_crime_types(self, text: str) -> List[str]:
        """Extract crime type references
        
        Args:
            text: Text to analyze
            
        Returns:
            List of identified crime types
        """
        text_lower = text.lower()
        crimes = []
        
        for crime in self.CRIME_KEYWORDS:
            if crime in text_lower:
                crimes.append(crime)
        
        return list(set(crimes))  # Remove duplicates
    
    def _extract_punishment_types(self, text: str) -> List[str]:
        """Extract punishment/penalty references
        
        Args:
            text: Text to analyze
            
        Returns:
            List of identified punishment types
        """
        text_lower = text.lower()
        punishments = []
        
        for punishment in self.PUNISHMENT_KEYWORDS:
            if punishment in text_lower:
                punishments.append(punishment)
        
        # Extract specific numbers (fines, years)
        numbers = re.findall(r"\$\d+(?:,\d{3})*|\d+\s*(?:years?|months?|days?)", text)
        if numbers:
            punishments.extend(numbers)
        
        return list(set(punishments))
    
    def _extract_legal_concepts(self, text: str) -> List[str]:
        """Extract key legal concepts
        
        Args:
            text: Text to analyze
            
        Returns:
            List of legal concepts
        """
        text_lower = text.lower()
        concepts = []
        
        for keyword in self.LEGAL_PROCEDURE_KEYWORDS:
            if keyword in text_lower:
                concepts.append(keyword)
        
        return list(set(concepts))
    
    def _extract_section_references(self, text: str) -> List[str]:
        """Extract legal section references
        
        Args:
            text: Text to analyze
            
        Returns:
            List of section references
        """
        # Pattern: § 2113, § 2113.1, 18 U.S.C. § 2113
        patterns = [
            r"(?:\d+\s+U\.S\.C\.?)?\s*§\s*(\d+(?:\.\d+)?)",
            r"18\s+U\.S\.C\.?\s+(?:§\s*)?\d+",
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            references.extend(matches)
        
        return list(set(references))
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract top keywords from text
        
        Args:
            text: Text to analyze
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        
        # Extract nouns and adjectives
        keywords = []
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN", "ADJ"] and len(token.text) > 3:
                if not token.is_stop:
                    keywords.append(token.text.lower())
        
        # Count frequencies
        from collections import Counter
        freq = Counter(keywords)
        
        return [word for word, _ in freq.most_common(top_n)]
    
    def _classify_text_type(self, text: str) -> str:
        """Classify the type of text (definition, punishment, etc.)
        
        Args:
            text: Text to analyze
            
        Returns:
            Classification string
        """
        text_lower = text.lower()
        
        if "definition" in text_lower or "means" in text_lower:
            return "definition"
        elif any(word in text_lower for word in ["prison", "fine", "penalty", "imprisonment"]):
            return "punishment"
        elif any(word in text_lower for word in ["guilty", "conviction", "offense", "crime"]):
            return "crime_description"
        elif "provided" in text_lower or "except" in text_lower:
            return "exception_clause"
        else:
            return "general"
