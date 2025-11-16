"""
Query processing, understanding, and expansion
"""
import logging
import re
from typing import List, Dict, Any, Tuple
from collections import Counter
import spacy
from config.settings import settings

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Process and understand user queries for legal documents"""
    
    # Legal keywords that often appear in queries
    LEGAL_KEYWORDS = {
        "punishment", "sentence", "fine", "prison", "crime", "guilty",
        "offense", "violation", "charged", "convicted", "imprisoned",
        "robbery", "theft", "assault", "fraud", "murder", "penalty"
    }
    
    INTENT_TYPES = {
        "punishment": ["what", "how", "sentence", "penalty", "fine", "prison"],
        "crime_definition": ["what", "define", "is", "criminal", "offense"],
        "elements": ["element", "requires", "must", "need", "necessary"],
        "exceptions": ["except", "unless", "provided", "exclude"],
        "references": ["cite", "section", "statute", "usc", "code"],
    }
    
    def __init__(self):
        """Initialize query processor"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("SpaCy model not found")
            self.nlp = None
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process and analyze a user query
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with processed query information
        """
        if not query or len(query.strip()) == 0:
            return {"original": query, "expanded": []}
        
        processed = {
            "original": query,
            "cleaned": self._clean_query(query),
            "keywords": self._extract_keywords(query),
            "intent": self._classify_intent(query),
            "entities": self._extract_entities(query),
            "expanded_queries": self._expand_query(query) if settings.QUERY_EXPANSION_ENABLED else [],
        }
        
        logger.info(f"Processed query: {query} -> Intent: {processed['intent']}")
        return processed
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query
        
        Args:
            query: Raw query
            
        Returns:
            Cleaned query
        """
        # Remove extra whitespace
        query = " ".join(query.split())
        
        # Normalize common patterns
        query = re.sub(r"U\.?\s?S\.?\s?C\.?", "U.S.C.", query)
        query = re.sub(r"§", "§", query)
        
        return query.strip()
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query
        
        Args:
            query: Query text
            
        Returns:
            List of keywords
        """
        if not self.nlp:
            return query.lower().split()
        
        doc = self.nlp(query)
        keywords = []
        
        for token in doc:
            # Include nouns, proper nouns, and verbs
            if token.pos_ in ["NOUN", "PROPN", "VERB"] and len(token.text) > 2:
                if not token.is_stop:
                    keywords.append(token.text.lower())
        
        return list(set(keywords)) or query.lower().split()
    
    def _classify_intent(self, query: str) -> str:
        """Classify query intent (punishment, crime definition, etc.)
        
        Args:
            query: Query text
            
        Returns:
            Intent classification
        """
        query_lower = query.lower()
        scores = {}
        
        for intent, keywords in self.INTENT_TYPES.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[intent] = score
        
        # Return intent with highest score, or "general"
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            return "general"
    
    def _extract_entities(self, query: str) -> List[Dict[str, str]]:
        """Extract named entities from query
        
        Args:
            query: Query text
            
        Returns:
            List of entities
        """
        if not self.nlp:
            return []
        
        doc = self.nlp(query)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "LAW"]:
                entities.append({
                    "text": ent.text,
                    "type": ent.label_
                })
        
        return entities
    
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with related terms and legal references
        
        Args:
            query: Original query
            
        Returns:
            List of expanded query variations
        """
        expanded = []
        
        # Expansion 1: Add "law" context
        expanded.append(f"{query} law")
        expanded.append(f"{query} statute")
        expanded.append(f"{query} legal")
        
        # Expansion 2: Replace common abbreviations
        if "robbery" in query.lower():
            expanded.append(query.replace("robbery", "18 U.S.C. § 2113"))
        
        if "theft" in query.lower():
            expanded.append(query.replace("theft", "larceny"))
        
        # Expansion 3: Add legal terms
        keywords = self._extract_keywords(query)
        if keywords:
            expanded.append(" ".join(keywords) + " punishment")
            expanded.append(" ".join(keywords) + " offense")
        
        return list(set(expanded))  # Remove duplicates


class QueryReformulator:
    """Reformulate queries for better retrieval"""
    
    @staticmethod
    def reformulate_for_similarity(query: str) -> str:
        """Reformulate query to improve semantic similarity
        
        Args:
            query: Original query
            
        Returns:
            Reformulated query
        """
        # Remove question marks and extra punctuation
        query = query.rstrip("?!.")
        
        # Convert to complete sentence form if needed
        if not query.endswith(("is", "are", "was", "were")):
            if not any(query.lower().startswith(w) for w in ["what", "where", "when", "who", "which"]):
                query = f"information about {query}"
        
        return query
