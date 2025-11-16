"""
Hybrid retrieval combining dense, sparse, and metadata filtering
"""
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from config.settings import settings
from src.embeddings import EmbeddingGenerator, VectorStore

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Retrieve documents using hybrid search (dense + sparse + metadata)"""
    
    def __init__(self, embedding_generator: EmbeddingGenerator, vector_store: VectorStore):
        """Initialize hybrid retriever
        
        Args:
            embedding_generator: EmbeddingGenerator instance
            vector_store: VectorStore instance
        """
        self.embedding_gen = embedding_generator
        self.vector_store = vector_store
        self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Build BM25 sparse index from stored documents"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            # Load documents from metadata
            documents = list(self.vector_store.metadata_store.values())
            texts = [doc.get("text", "") for doc in documents]
            
            if texts:
                self.vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
                self.tfidf_matrix = self.vectorizer.fit_transform(texts)
                logger.info(f"Built BM25 index for {len(texts)} documents")
            else:
                self.vectorizer = None
                self.tfidf_matrix = None
        except Exception as e:
            logger.warning(f"Could not build BM25 index: {e}")
            self.vectorizer = None
            self.tfidf_matrix = None
    
    def retrieve(self, query: str, k: int = None, filters: Dict[str, Any] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Retrieve relevant documents using hybrid search
        
        Args:
            query: Query string
            k: Number of results to return (default from settings)
            filters: Optional metadata filters
            
        Returns:
            List of (document, relevance_score) tuples
        """
        k = k or settings.RETRIEVAL_K
        
        if not settings.USE_HYBRID_RETRIEVAL:
            # Use only dense retrieval
            return self._dense_search(query, k, filters)
        else:
            # Hybrid: combine dense, sparse, and metadata filtering
            dense_results = self._dense_search(query, min(k * 2, settings.RETRIEVAL_K_MAX), filters)
            sparse_results = self._sparse_search(query, min(k * 2, settings.RETRIEVAL_K_MAX))
            
            # Aggregate results
            return self._aggregate_results(dense_results, sparse_results, k)
    
    def _dense_search(self, query: str, k: int, filters: Dict[str, Any] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Dense similarity search using embeddings
        
        Args:
            query: Query string
            k: Number of results
            filters: Optional metadata filters
            
        Returns:
            List of (document, similarity_score) tuples
        """
        try:
            query_embedding = self.embedding_gen.embed_text(query)
            results = self.vector_store.search(query_embedding, k, filters)
            
            # Filter by threshold
            results = [
                (doc, score) for doc, score in results
                if score >= settings.SIMILARITY_THRESHOLD
            ]
            
            logger.info(f"Dense search returned {len(results)} results for query: {query[:50]}")
            return results
        
        except Exception as e:
            logger.error(f"Error in dense search: {e}")
            return []
    
    def _sparse_search(self, query: str, k: int) -> List[Tuple[Dict[str, Any], float]]:
        """Sparse keyword search using BM25/TF-IDF
        
        Args:
            query: Query string
            k: Number of results
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.vectorizer or self.tfidf_matrix is None:
            return []
        
        try:
            query_vector = self.vectorizer.transform([query])
            scores = (query_vector * self.tfidf_matrix.T).toarray()[0]
            
            # Get top k indices
            top_indices = np.argsort(-scores)[:k]
            top_scores = scores[top_indices]
            
            results = []
            for idx, score in zip(top_indices, top_scores):
                if score > 0 and idx < len(self.vector_store.metadata_store):
                    doc = self.vector_store.metadata_store.get(str(idx))
                    if doc:
                        results.append((doc, float(score)))
            
            logger.info(f"Sparse search returned {len(results)} results for query: {query[:50]}")
            return results
        
        except Exception as e:
            logger.error(f"Error in sparse search: {e}")
            return []
    
    def _aggregate_results(self, dense_results: List[Tuple[Dict[str, Any], float]],
                          sparse_results: List[Tuple[Dict[str, Any], float]],
                          k: int) -> List[Tuple[Dict[str, Any], float]]:
        """Aggregate dense and sparse results with rank fusion
        
        Args:
            dense_results: Results from dense search
            sparse_results: Results from sparse search
            k: Final number of results to return
            
        Returns:
            Combined and aggregated results
        """
        # Create combined ranking using RRF (Reciprocal Rank Fusion)
        result_scores = {}
        
        # Score from dense search (normalized)
        for rank, (doc, score) in enumerate(dense_results):
            doc_key = doc.get("text", "")[:100]  # Use text as key
            rrf_score = 1.0 / (60 + rank)  # RRF formula
            result_scores[doc_key] = result_scores.get(doc_key, 0) + rrf_score * score
        
        # Score from sparse search (normalized)
        for rank, (doc, score) in enumerate(sparse_results):
            doc_key = doc.get("text", "")[:100]
            rrf_score = 1.0 / (60 + rank)
            result_scores[doc_key] = result_scores.get(doc_key, 0) + rrf_score * score
        
        # Sort by aggregated score
        sorted_results = sorted(result_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top k with original documents
        final_results = []
        for doc_key, agg_score in sorted_results[:k]:
            # Find the document
            for doc, _ in dense_results + sparse_results:
                if doc.get("text", "")[:100] == doc_key:
                    final_results.append((doc, agg_score))
                    break
        
        return final_results[:k]
    
    def retrieve_with_metadata_filter(self, query: str, filter_key: str, filter_value: str, k: int = None) -> List[Tuple[Dict[str, Any], float]]:
        """Retrieve with specific metadata filtering
        
        Args:
            query: Query string
            filter_key: Metadata key to filter on
            filter_value: Value to match
            k: Number of results
            
        Returns:
            Filtered results
        """
        filters = {filter_key: filter_value} if settings.USE_METADATA_FILTERING else None
        return self.retrieve(query, k, filters)
