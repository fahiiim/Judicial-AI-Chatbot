"""
Embedding generation using sentence transformers
"""
import logging
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate dense embeddings for text chunks"""
    
    def __init__(self, model_name: str = None):
        """Initialize embedding generator
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        logger.info(f"Loading embedding model: {self.model_name}")
        
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Embedding dimension: {self.embedding_dim}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        if not text or len(text.strip()) == 0:
            return np.zeros(self.embedding_dim)
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return np.zeros(self.embedding_dim)
    
    def embed_texts(self, texts: List[str], batch_size: int = None) -> List[np.ndarray]:
        """Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding (default from settings)
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        
        try:
            logger.info(f"Embedding {len(texts)} texts with batch size {batch_size}")
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            
            logger.info(f"Successfully embedded {len(texts)} texts")
            return [emb for emb in embeddings]
        
        except Exception as e:
            logger.error(f"Error embedding texts: {e}")
            return [np.zeros(self.embedding_dim) for _ in texts]
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1
        """
        try:
            # Cosine similarity
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(np.dot(embedding1, embedding2) / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
    
    def get_embedding_dimension(self) -> int:
        """Get dimension of embeddings
        
        Returns:
            Embedding dimension
        """
        return self.embedding_dim
