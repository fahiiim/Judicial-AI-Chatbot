"""
Configuration settings for the Legal Document RAG Pipeline
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration"""
    
    # Project paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    PDF_DIR: Path = BASE_DIR
    
    # PDF Configuration
    PDF_PATH: str = str(BASE_DIR / "USCODE-2011-title18.pdf")
    
    # Chunking configuration
    CHUNK_SIZE: int = 500  # Characters per chunk
    CHUNK_OVERLAP: int = 100  # Characters overlap between chunks
    MIN_CHUNK_SIZE: int = 50  # Minimum chunk size
    
    # Embedding configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"  # Fast, lightweight
    EMBEDDING_DIMENSION: int = 384  # MiniLM dimension
    EMBEDDING_BATCH_SIZE: int = 32
    
    # Vector store configuration
    VECTOR_STORE_TYPE: str = "chroma"  # Options: "chroma", "faiss"
    VECTOR_STORE_PATH: Path = DATA_DIR / "vector_store"
    VECTOR_STORE_COLLECTION: str = "legal_documents"
    
    # Retrieval configuration
    RETRIEVAL_K: int = 5  # Number of chunks to retrieve
    RETRIEVAL_K_MAX: int = 15  # Maximum chunks for hybrid retrieval
    SIMILARITY_THRESHOLD: float = 0.3  # Minimum similarity score
    USE_HYBRID_RETRIEVAL: bool = True
    USE_METADATA_FILTERING: bool = True
    
    # Query configuration
    QUERY_EXPANSION_ENABLED: bool = True
    QUERY_CLASSIFICATION_ENABLED: bool = True
    
    # LLM configuration
    LLM_MODEL: str = "gpt-4"  # Options: "gpt-4", "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.3  # Lower for more consistent legal answers
    LLM_MAX_TOKENS: int = 2000
    OPENAI_API_KEY: Optional[str] = None
    
    # API configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    CORS_ORIGINS: list = ["*"]
    
    # Database configuration
    DB_PATH: Path = DATA_DIR / "chat_history.db"
    
    # Processing configuration
    NUM_WORKERS: int = 4
    CACHE_EMBEDDINGS: bool = True
    
    # Legal document specific patterns
    SECTION_PATTERN: str = r"§\s*\d+\.\d+"  # Pattern for section numbers like § 2113.1
    SUBSECTION_PATTERN: str = r"\([a-zA-Z0-9]+\)"  # Pattern for subsections like (a), (b), etc.
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.create_directories()
