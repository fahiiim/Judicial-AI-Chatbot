"""
Example usage and testing script
"""
from src.pipeline import RAGPipeline
from config.settings import settings


def example_basic_query():
    """Basic example of querying the chatbot"""
    print("="*70)
    print("Example 1: Basic Query")
    print("="*70)
    
    # Initialize pipeline
    pipeline = RAGPipeline()
    
    # Build index if not already built
    if pipeline.get_indexed_count() == 0:
        print("Building index...")
        pipeline.build_index()
    
    # Ask a question
    query = "What is the punishment for bank robbery under federal law?"
    print(f"\nQuery: {query}\n")
    
    result = pipeline.answer_query(query, include_retrieved_docs=True)
    
    print("Answer:")
    print(result.get("answer", "No answer"))
    
    print("\nCitations:")
    for citation in result.get("citations", []):
        print(f"  - {citation}")


def example_with_intent():
    """Example showing intent classification"""
    print("\n" + "="*70)
    print("Example 2: Intent Classification")
    print("="*70)
    
    from src.retrieval import QueryProcessor
    
    processor = QueryProcessor()
    
    queries = [
        "What is the punishment for fraud?",
        "Define assault under federal law",
        "What elements must be proven for murder?",
        "What are the exceptions to this crime?",
    ]
    
    for query in queries:
        processed = processor.process_query(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {processed['intent']}")
        print(f"Keywords: {processed['keywords']}")


def example_metadata_filtering():
    """Example showing metadata filtering"""
    print("\n" + "="*70)
    print("Example 3: Metadata Filtering")
    print("="*70)
    
    from src.retrieval import HybridRetriever
    from src.embeddings import EmbeddingGenerator, VectorStore
    
    pipeline = RAGPipeline()
    
    if pipeline.get_indexed_count() == 0:
        print("Building index...")
        pipeline.build_index()
    
    # Get documents with specific crime type
    print("\nRetrieving punishment clauses for robbery...")
    results = pipeline.retriever.retrieve_with_metadata_filter(
        query="robbery punishment",
        filter_key="crime_types",
        filter_value="robbery"
    )
    
    print(f"Found {len(results)} relevant sections")
    for doc, score in results[:2]:
        print(f"\nScore: {score:.3f}")
        print(f"Text: {doc.get('text', '')[:200]}...")


def example_citation_extraction():
    """Example showing citation handling"""
    print("\n" + "="*70)
    print("Example 4: Citation Extraction")
    print("="*70)
    
    from src.generation import CitationHandler
    
    sample_text = """
    Bank robbery is defined in 18 U.S.C. § 2113. According to this statute,
    the punishment can include imprisonment and fines. 18 U.S.C. § 2113(b)
    provides specific penalties for certain circumstances.
    """
    
    print(f"Sample text:\n{sample_text}\n")
    
    citations = CitationHandler.extract_citations(sample_text)
    print("Extracted citations:")
    for citation in citations:
        print(f"  - {citation['statute']}")
    
    # HTML highlighting
    html = CitationHandler.highlight_citations(sample_text, citations)
    print(f"\nHTML formatted:\n{html}")


def example_full_pipeline():
    """Complete pipeline example"""
    print("\n" + "="*70)
    print("Example 5: Full Pipeline")
    print("="*70)
    
    pipeline = RAGPipeline()
    
    # Step 1: Build index
    print("\nStep 1: Building index...")
    if pipeline.get_indexed_count() == 0:
        pipeline.build_index()
    
    indexed_count = pipeline.get_indexed_count()
    print(f"Indexed {indexed_count} documents")
    
    # Step 2: Process query
    print("\nStep 2: Processing query...")
    query = "What are the elements of federal murder?"
    processed = pipeline.query_processor.process_query(query)
    print(f"Intent: {processed['intent']}")
    print(f"Expanded queries: {processed['expanded_queries']}")
    
    # Step 3: Retrieve documents
    print("\nStep 3: Retrieving documents...")
    results = pipeline.retriever.retrieve(processed['cleaned'], k=5)
    print(f"Retrieved {len(results)} documents")
    
    # Step 4: Generate answer
    print("\nStep 4: Generating answer...")
    answer_result = pipeline.generator.generate_answer(
        query,
        [doc for doc, _ in results]
    )
    
    print("\nFinal Answer:")
    print(answer_result.get("answer", "No answer"))
    
    print("\nCitations Found:")
    for citation in answer_result.get("citations", [])[:5]:
        print(f"  - {citation}")


if __name__ == "__main__":
    print("\nLegal Document RAG Chatbot - Examples\n")
    
    # Uncomment examples to run
    
    # example_with_intent()
    # example_citation_extraction()
    
    try:
        example_basic_query()
    except Exception as e:
        print(f"Note: First run requires index building. Run: python main.py build")
        print(f"Error: {e}")
    
    # example_metadata_filtering()
    # example_full_pipeline()
