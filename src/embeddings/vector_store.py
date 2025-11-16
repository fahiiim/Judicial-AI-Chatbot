"""
Vector store for storing and retrieving embeddings
Supports Chroma and FAISS backends
"""
import logging
import json
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import numpy as np
from config.settings import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Unified interface for vector storage and retrieval"""
    
    def __init__(self, store_type: str = None, collection_name: str = None):
        """Initialize vector store
        
        Args:
            store_type: Type of store ("chroma" or "faiss")
            collection_name: Name of collection
        """
        self.store_type = store_type or settings.VECTOR_STORE_TYPE
        self.collection_name = collection_name or settings.VECTOR_STORE_COLLECTION
        self.store_path = settings.VECTOR_STORE_PATH
        
        self.store = None
        self.metadata_store = {}  # Local store for metadata
        self.metadata_db_path = self.store_path / f"{self.collection_name}_metadata.json"
        
        logger.info(f"Initializing {self.store_type} vector store at {self.store_path}")
        self._initialize_store()
        self._load_metadata()
    
    def _initialize_store(self):
        """Initialize the appropriate vector store backend"""
        try:
            if self.store_type.lower() == "chroma":
                import chromadb
                self.store = chromadb.PersistentClient(path=str(self.store_path))
                self.collection = self.store.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("Initialized Chroma vector store")
            
            elif self.store_type.lower() == "faiss":
                try:
                    import faiss
                    self.store = self._init_faiss()
                    logger.info("Initialized FAISS vector store")
                except ImportError:
                    logger.warning("FAISS not available, falling back to Chroma")
                    self._initialize_store_with_fallback()
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def _initialize_store_with_fallback(self):
        """Fallback to Chroma if primary store fails"""
        import chromadb
        self.store = chromadb.PersistentClient(path=str(self.store_path))
        self.collection = self.store.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def _init_faiss(self):
        """Initialize FAISS index"""
        import faiss
        index_path = self.store_path / f"{self.collection_name}.index"
        
        if index_path.exists():
            return faiss.read_index(str(index_path))
        else:
            # Create empty index (will be sized on first insert)
            return None
    
    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[np.ndarray]) -> bool:
        """Add documents with embeddings to the store
        
        Args:
            documents: List of document dictionaries with 'text' and other metadata
            embeddings: List of embedding vectors
            
        Returns:
            True if successful
        """
        if len(documents) != len(embeddings):
            logger.error("Number of documents and embeddings mismatch")
            return False
        
        try:
            if self.store_type.lower() == "chroma":
                return self._add_to_chroma(documents, embeddings)
            elif self.store_type.lower() == "faiss":
                return self._add_to_faiss(documents, embeddings)
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def _add_to_chroma(self, documents: List[Dict[str, Any]], embeddings: List[np.ndarray]) -> bool:
        """Add documents to Chroma with proper batching"""
        try:
            # Chroma has a batch size limit, so batch the additions
            batch_size = 5000  # Conservative batch size for Chroma
            total_added = 0
            
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_embeddings = embeddings[i:i+batch_size]
                batch_end_idx = i + len(batch_docs)
                
                ids = [f"{self.collection_name}_{j}" for j in range(i, batch_end_idx)]
                
                # Separate embeddings and metadata
                embedding_lists = [emb.tolist() for emb in batch_embeddings]
                texts = [doc.get("text", "") for doc in batch_docs]
                
                # Prepare metadata (filter out text field)
                metadatas = []
                for doc in batch_docs:
                    meta = {k: str(v) for k, v in doc.items() if k != "text"}
                    metadatas.append(meta)
                
                self.collection.add(
                    ids=ids,
                    embeddings=embedding_lists,
                    documents=texts,
                    metadatas=metadatas
                )
                
                total_added += len(batch_docs)
                logger.info(f"Added batch {i//batch_size + 1}: {len(batch_docs)} documents to Chroma (total: {total_added})")
            
            logger.info(f"Successfully added all {total_added} documents to Chroma")
            self._save_metadata(documents)
            return True
        
        except Exception as e:
            logger.error(f"Error adding to Chroma: {e}")
            return False
    
    def _add_to_faiss(self, documents: List[Dict[str, Any]], embeddings: List[np.ndarray]) -> bool:
        """Add documents to FAISS"""
        try:
            import faiss
            
            # Convert embeddings to the right format
            embeddings_array = np.array(embeddings).astype('float32')
            
            if self.store is None:
                # Create new index
                dim = embeddings_array.shape[1]
                self.store = faiss.IndexFlatL2(dim)
            
            # Add vectors
            self.store.add(embeddings_array)
            
            # Save index
            index_path = self.store_path / f"{self.collection_name}.index"
            faiss.write_index(self.store, str(index_path))
            
            logger.info(f"Added {len(documents)} documents to FAISS")
            self._save_metadata(documents)
            return True
        
        except Exception as e:
            logger.error(f"Error adding to FAISS: {e}")
            return False
    
    def search(self, query_embedding: np.ndarray, k: int = 5, 
               filter_dict: Dict[str, Any] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar documents
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of (document, similarity_score) tuples
        """
        try:
            if self.store_type.lower() == "chroma":
                return self._search_chroma(query_embedding, k, filter_dict)
            elif self.store_type.lower() == "faiss":
                return self._search_faiss(query_embedding, k)
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def _search_chroma(self, query_embedding: np.ndarray, k: int = 5,
                      filter_dict: Dict[str, Any] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Search in Chroma"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k,
                where=filter_dict if filter_dict else None
            )
            
            output = []
            for i, doc_id in enumerate(results.get("ids", [[]])[0]):
                distance = results.get("distances", [[]])[0][i] if results.get("distances") else 0
                similarity = 1 - (distance / 2)  # Convert distance to similarity
                
                metadata = results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
                text = results.get("documents", [[]])[0][i] if results.get("documents") else ""
                
                doc = {"text": text, **metadata}
                output.append((doc, similarity))
            
            return output
        except Exception as e:
            logger.error(f"Error searching Chroma: {e}")
            return []
    
    def _search_faiss(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Search in FAISS"""
        try:
            import faiss
            
            query_array = query_embedding.astype('float32').reshape(1, -1)
            distances, indices = self.store.search(query_array, k)
            
            output = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx >= 0:  # Valid result
                    # Convert L2 distance to similarity
                    similarity = 1.0 / (1.0 + float(distance))
                    
                    # Retrieve metadata from local store
                    if idx < len(self.metadata_store):
                        doc = self.metadata_store[idx]
                        output.append((doc, similarity))
            
            return output
        except Exception as e:
            logger.error(f"Error searching FAISS: {e}")
            return []
    
    def _save_metadata(self, documents: List[Dict[str, Any]]):
        """Save metadata locally for reference"""
        try:
            self.metadata_db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing metadata
            if self.metadata_db_path.exists():
                with open(self.metadata_db_path, "r") as f:
                    self.metadata_store = json.load(f)
            
            # Append new documents
            start_idx = len(self.metadata_store)
            for i, doc in enumerate(documents):
                # Convert numpy arrays and other non-serializable types
                serializable_doc = {}
                for k, v in doc.items():
                    if isinstance(v, np.ndarray):
                        serializable_doc[k] = v.tolist()
                    else:
                        serializable_doc[k] = v
                
                self.metadata_store[str(start_idx + i)] = serializable_doc
            
            # Save to disk
            with open(self.metadata_db_path, "w") as f:
                json.dump(self.metadata_store, f, indent=2)
        
        except Exception as e:
            logger.warning(f"Could not save metadata: {e}")
    
    def _load_metadata(self):
        """Load metadata from disk"""
        try:
            if self.metadata_db_path.exists():
                with open(self.metadata_db_path, "r") as f:
                    self.metadata_store = json.load(f)
                logger.info(f"Loaded {len(self.metadata_store)} metadata entries")
        except Exception as e:
            logger.warning(f"Could not load metadata: {e}")
            self.metadata_store = {}
    
    def get_collection_size(self) -> int:
        """Get number of documents in collection"""
        try:
            if self.store_type.lower() == "chroma":
                return self.collection.count()
            elif self.store_type.lower() == "faiss":
                return self.store.ntotal if self.store else 0
        except Exception as e:
            logger.error(f"Error getting collection size: {e}")
            return 0
