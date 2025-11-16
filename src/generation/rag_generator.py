"""
RAG generation with LLM integration and citation handling
"""
import logging
from typing import List, Dict, Any, Tuple
from config.settings import settings

logger = logging.getLogger(__name__)


class RAGGenerator:
    """Generate answers using RAG with citations to legal documents"""
    
    def __init__(self):
        """Initialize RAG generator with LLM"""
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM based on settings"""
        try:
            from openai import OpenAI
            
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                logger.warning("OPENAI_API_KEY not set, OpenAI features will be limited")
            
            self.client = OpenAI(api_key=api_key) if api_key else None
            logger.info(f"Initialized LLM: {settings.LLM_MODEL}")
        except ImportError:
            logger.warning("OpenAI library not installed")
            self.client = None
    
    def generate_answer(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate answer using retrieved documents
        
        Args:
            query: User query
            retrieved_docs: List of retrieved document chunks
            
        Returns:
            Dictionary with answer, citations, and metadata
        """
        if not self.client:
            return self._generate_fallback_answer(query, retrieved_docs)
        
        try:
            # Prepare context from retrieved documents
            context = self._prepare_context(retrieved_docs)
            
            # Create prompt with legal instructions
            prompt = self._create_legal_prompt(query, context)
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
            
            answer_text = response.choices[0].message.content
            
            # Extract and format citations
            citations = self._extract_citations(answer_text, retrieved_docs)
            
            return {
                "answer": answer_text,
                "citations": citations,
                "retrieved_docs_count": len(retrieved_docs),
                "model": settings.LLM_MODEL,
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return self._generate_fallback_answer(query, retrieved_docs)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for legal document chatbot
        
        Returns:
            System prompt string
        """
        return """You are an expert legal assistant specializing in U.S. Code Title 18 (Federal Criminal Law).
        
Your responsibilities:
1. Provide accurate, helpful answers about federal crimes, punishments, and legal procedures
2. ALWAYS cite the relevant statute numbers (e.g., "18 U.S.C. § 2113") in your answers
3. Use legal terminology and be precise in your explanations
4. When describing crimes, include the elements that must be proven
5. When describing punishments, include minimum and maximum sentences and fines
6. Clarify exceptions and special provisions when relevant
7. If you're unsure about something, say so rather than guessing

Format your answers with:
- Clear, authoritative language
- Inline citations to relevant statutes
- Specific references to sections and subsections
- Practical examples when helpful
- Warnings about serious legal consequences when appropriate"""
    
    def _create_legal_prompt(self, query: str, context: str) -> str:
        """Create a prompt for legal question answering
        
        Args:
            query: User query
            context: Retrieved document context
            
        Returns:
            Formatted prompt
        """
        return f"""Based on the following legal documents from 18 U.S.C. Title 18, please answer this question:

QUESTION: {query}

RELEVANT LEGAL TEXT:
{context}

Please provide a comprehensive, well-cited answer that:
1. Directly answers the question
2. Cites specific statute numbers (18 U.S.C. § XXX)
3. Explains key legal concepts
4. Notes any important exceptions or special cases
5. Uses clear, authoritative legal language"""
    
    def _prepare_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Prepare context from retrieved documents
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for doc in retrieved_docs:
            text = doc.get("text", "")
            section = doc.get("section", "Unknown")
            source = doc.get("source", "Unknown")
            
            context_parts.append(f"[{section} - {source}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def _extract_citations(self, answer_text: str, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract and verify citations from answer
        
        Args:
            answer_text: Generated answer
            retrieved_docs: Original retrieved documents
            
        Returns:
            List of citation dictionaries
        """
        import re
        
        # Find citations in answer (pattern: 18 U.S.C. § 2113)
        citation_pattern = r"(?:18\s+)?U\.S\.C\.?\s+(?:§\s*)?(\d+(?:\.\d+)?(?:\s*\([a-zA-Z0-9]+\))?)"
        citations = re.findall(citation_pattern, answer_text)
        
        # Create citation dictionaries with links to source docs
        citation_list = []
        for citation in citations:
            # Find matching document
            matching_doc = None
            for doc in retrieved_docs:
                if citation in doc.get("section", ""):
                    matching_doc = doc
                    break
            
            citation_list.append({
                "statute": f"18 U.S.C. § {citation}",
                "source": matching_doc.get("source", "") if matching_doc else "",
                "page": matching_doc.get("page_num", "") if matching_doc else ""
            })
        
        return citation_list
    
    def _generate_fallback_answer(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fallback answer when LLM is unavailable
        
        Args:
            query: User query
            retrieved_docs: Retrieved documents
            
        Returns:
            Fallback answer dictionary
        """
        context = self._prepare_context(retrieved_docs)
        citations = []
        
        for doc in retrieved_docs:
            if doc.get("section"):
                citations.append({
                    "statute": f"18 U.S.C. § {doc.get('section')}",
                    "source": doc.get("source", "")
                })
        
        return {
            "answer": f"Based on the following relevant legal text:\n\n{context}\n\nFor a detailed answer, please consult an attorney.",
            "citations": citations,
            "retrieved_docs_count": len(retrieved_docs),
            "model": "fallback",
            "status": "fallback - LLM unavailable"
        }
