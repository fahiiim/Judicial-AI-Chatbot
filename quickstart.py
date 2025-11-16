"""
Quick start utility for testing the RAG pipeline
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...\n")
    
    dependencies = [
        "pypdf",
        "pdfplumber",
        "spacy",
        "sentence_transformers",
        "chromadb",
        "fastapi",
        "pydantic",
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep} (MISSING)")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies installed")
    return True


def check_pdf():
    """Check if PDF file exists"""
    print("\nChecking PDF file...\n")
    
    from config.settings import settings
    
    pdf_path = Path(settings.PDF_PATH)
    if pdf_path.exists():
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        print(f"✓ Found PDF: {pdf_path}")
        print(f"  Size: {size_mb:.1f} MB")
        return True
    else:
        print(f"✗ PDF not found: {pdf_path}")
        return False


def check_directories():
    """Check if data directories exist"""
    print("\nChecking directories...\n")
    
    from config.settings import settings
    
    dirs = [settings.DATA_DIR, settings.LOGS_DIR]
    
    for dir_path in dirs:
        if dir_path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} (will be created)")
    
    return True


def test_imports():
    """Test importing all modules"""
    print("\nTesting imports...\n")
    
    try:
        from src.ingestion import PDFParser, TextCleaner
        print("✓ Ingestion module")
        
        from src.chunking import SemanticChunker, MetadataExtractor
        print("✓ Chunking module")
        
        from src.embeddings import EmbeddingGenerator, VectorStore
        print("✓ Embeddings module")
        
        from src.retrieval import QueryProcessor, HybridRetriever
        print("✓ Retrieval module")
        
        from src.generation import RAGGenerator, CitationHandler
        print("✓ Generation module")
        
        from src.pipeline import RAGPipeline
        print("✓ Pipeline module")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


def test_embedding_model():
    """Test downloading embedding model"""
    print("\nTesting embedding model...\n")
    
    try:
        from sentence_transformers import SentenceTransformer
        from config.settings import settings
        
        print(f"Downloading {settings.EMBEDDING_MODEL}...")
        print("(This may take a minute on first run)\n")
        
        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Test embedding
        test_text = "This is a test sentence about federal criminal law."
        embedding = model.encode(test_text)
        
        print(f"✓ Model downloaded and working")
        print(f"  Embedding dimension: {len(embedding)}")
        
        return True
    except Exception as e:
        print(f"✗ Embedding model error: {e}")
        return False


def test_spacy_model():
    """Test spaCy model"""
    print("\nTesting spaCy model...\n")
    
    try:
        import spacy
        
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✓ spaCy model loaded")
            
            # Test processing
            doc = nlp("The defendant was convicted of bank robbery.")
            print(f"  Processed: {len(doc)} tokens, {len(doc.ents)} entities")
            
            return True
        except OSError:
            print("⚠ spaCy model not found")
            print("  Download with: python -m spacy download en_core_web_sm")
            return False
    except Exception as e:
        print(f"✗ spaCy error: {e}")
        return False


def run_quickstart():
    """Run quick start tests"""
    print("\n" + "="*70)
    print("Legal Document RAG Chatbot - Quick Start Check")
    print("="*70 + "\n")
    
    all_pass = True
    
    all_pass &= check_dependencies()
    all_pass &= check_pdf()
    all_pass &= check_directories()
    all_pass &= test_imports()
    all_pass &= test_spacy_model()
    all_pass &= test_embedding_model()
    
    print("\n" + "="*70)
    if all_pass:
        print("✓ All checks passed!")
        print("\nNext steps:")
        print("  1. Build the index:  python main.py build")
        print("  2. Start chatting:   python main.py chat")
        print("  3. Or start API:     python main.py api")
    else:
        print("✗ Some checks failed. Please resolve the issues above.")
        sys.exit(1)
    
    print("="*70 + "\n")


if __name__ == "__main__":
    run_quickstart()
