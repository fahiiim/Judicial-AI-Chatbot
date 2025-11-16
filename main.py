"""
Main entry point for the Legal Document RAG Chatbot
Supports both CLI and API modes
"""
import logging
import argparse
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/legal_chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)


def build_index(args):
    """Build the document index"""
    from src.pipeline import RAGPipeline
    
    logger.info("Building document index...")
    pipeline = RAGPipeline(pdf_path=args.pdf)
    
    success = pipeline.build_index(force_rebuild=args.force_rebuild)
    
    if success:
        indexed_count = pipeline.get_indexed_count()
        logger.info(f"✓ Successfully indexed {indexed_count} documents")
        print(f"\n✓ Index built successfully with {indexed_count} documents")
    else:
        logger.error("Failed to build index")
        print("\n✗ Failed to build index")
        sys.exit(1)


def chat_cli(args):
    """Interactive CLI chat mode"""
    from src.pipeline import RAGPipeline
    
    logger.info("Starting CLI chat mode...")
    pipeline = RAGPipeline(pdf_path=args.pdf)
    
    # Check if index exists
    if pipeline.get_indexed_count() == 0:
        logger.warning("No indexed documents found. Building index...")
        print("Building index... (this may take a few minutes)")
        pipeline.build_index()
    
    print("\n" + "="*70)
    print("Legal Document RAG Chatbot - Interactive Mode")
    print("="*70)
    print("Ask questions about federal criminal law (18 U.S.C.)")
    print("Type 'exit' or 'quit' to stop\n")
    
    session_id = "cli_session"
    
    while True:
        try:
            query = input("\n✓ Query: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break
            
            if not query:
                continue
            
            print("\nProcessing query...\n")
            result = pipeline.answer_query(query, include_retrieved_docs=args.show_sources)
            
            print("📋 Answer:")
            print("-" * 70)
            print(result.get("answer", "No answer generated"))
            print("-" * 70)
            
            if result.get("citations"):
                print("\n📚 Citations:")
                for citation in result["citations"]:
                    print(f"  • {citation.get('statute', 'Unknown')}")
            
            if args.show_sources and result.get("retrieved_documents"):
                print("\n📑 Retrieved Documents:")
                for doc in result["retrieved_documents"]:
                    print(f"  • {doc.get('source', 'Unknown')} (relevance: {doc.get('relevance_score', 0):.2f})")
            
            # Log interaction
            pipeline.log_interaction(query, result.get("answer", ""), session_id)
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            print(f"Error: {e}")


def start_api(args):
    """Start the FastAPI server"""
    import uvicorn
    from config.settings import settings
    from src.pipeline import RAGPipeline
    
    logger.info("Starting API server...")
    
    # Pre-initialize pipeline
    try:
        print("Initializing RAG pipeline...")
        pipeline = RAGPipeline(pdf_path=args.pdf)
        
        # Build index if needed
        if pipeline.get_indexed_count() == 0:
            logger.warning("No indexed documents found. Building index...")
            print("Building index... (this may take a few minutes)")
            pipeline.build_index()
        
        indexed_count = pipeline.get_indexed_count()
        print(f"✓ Pipeline ready with {indexed_count} indexed documents\n")
    
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        print(f"Error initializing pipeline: {e}")
        sys.exit(1)
    
    # Start server
    print("="*70)
    print("Legal Document RAG Chatbot - API Server")
    print("="*70)
    print(f"Starting server at http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"API Documentation: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        "src.api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD and args.reload
    )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Legal Document RAG Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Build index:
    python main.py build

  Interactive chat:
    python main.py chat

  Start API server:
    python main.py api

  With specific PDF:
    python main.py --pdf /path/to/document.pdf chat
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="chat",
        choices=["build", "chat", "api"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to PDF file (default from config)"
    )
    
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Force rebuild of index"
    )
    
    parser.add_argument(
        "--show-sources",
        action="store_true",
        help="Show source documents in chat (CLI only)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable reload mode for API development"
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == "build":
            build_index(args)
        elif args.command == "chat":
            chat_cli(args)
        elif args.command == "api":
            start_api(args)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nInterrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
