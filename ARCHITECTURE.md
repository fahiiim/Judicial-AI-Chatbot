# Advanced RAG Pipeline Architecture

## Overview

This document describes the complete architecture of the Legal Document RAG Chatbot, an advanced Retrieval-Augmented Generation system designed specifically for querying federal criminal law documents (18 U.S.C.).

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  CLI Chat          │  FastAPI Server    │  Python Scripts          │
│  (Interactive)     │  (REST API)        │  (Integration)           │
│                                                                       │
└────────────┬────────────────┬──────────────────┬────────────────────┘
             │                │                  │
             └────────────────┼──────────────────┘
                              │
                   ┌──────────▼─────────────┐
                   │   PIPELINE LAYER      │
                   │  (Orchestration)      │
                   │  - RAGPipeline        │
                   │  - Query routing      │
                   │  - Session mgmt       │
                   └─────────┬──────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼─────────┐  ┌─────▼────────┐  ┌──────▼──────────┐
    │   RETRIEVAL   │  │ GENERATION    │  │  DATA LOGGING   │
    │    LAYER      │  │   LAYER       │  │    & FEEDBACK   │
    └────┬─────────┘  └─────┬────────┘  └──────┬──────────┘
         │                  │                   │
         │            ┌─────▼────────┐          │
         │            │  RAGGenerator │         │
         │            │  - LLM call   │         │
         │            │  - Prompt eng │    ┌────▼──────┐
         │            │  - Citation   │    │  Database │
         │            │    formatting │    │ Chat Hist │
         │            └──────────────┘    │ Feedback  │
         │                                 └───────────┘
    ┌────▼──────────────────────┐
    │   RETRIEVAL COMPONENTS    │
    ├───────────────────────────┤
    │                           │
    │  HybridRetriever          │
    │  ├─ Dense Search (Vector) │
    │  ├─ Sparse Search (BM25)  │
    │  ├─ Metadata Filter       │
    │  └─ Result Aggregation    │
    │                           │
    │  QueryProcessor           │
    │  ├─ Intent Classification │
    │  ├─ Query Expansion       │
    │  ├─ Entity Extraction     │
    │  └─ Keyword Analysis      │
    └────┬──────────────────────┘
         │
    ┌────▼─────────────────────────────────┐
    │    INDEXING & EMBEDDING LAYER        │
    ├──────────────────────────────────────┤
    │                                      │
    │  VectorStore (Chroma/FAISS)          │
    │  ├─ Dense vectors                    │
    │  ├─ Metadata index                   │
    │  └─ Retrieval API                    │
    │                                      │
    │  EmbeddingGenerator                  │
    │  ├─ Sentence Transformers            │
    │  ├─ BGE Model                        │
    │  └─ Batch Encoding                   │
    └────┬──────────────────────────────────┘
         │
    ┌────▼─────────────────────────────────┐
    │   CHUNKING & METADATA LAYER          │
    ├──────────────────────────────────────┤
    │                                      │
    │  SemanticChunker                     │
    │  ├─ Section-based splitting          │
    │  ├─ Sentence-based splitting         │
    │  └─ Overlap handling                 │
    │                                      │
    │  MetadataExtractor                   │
    │  ├─ NER (Named Entity Recognition)   │
    │  ├─ Regex patterns (legal)           │
    │  ├─ Crime type classification        │
    │  ├─ Punishment extraction            │
    │  └─ Keyword extraction               │
    └────┬──────────────────────────────────┘
         │
    ┌────▼─────────────────────────────────┐
    │   INGESTION & PREPROCESSING LAYER    │
    ├──────────────────────────────────────┤
    │                                      │
    │  PDFParser                           │
    │  ├─ PDF extraction (pdfplumber)      │
    │  ├─ Metadata preservation            │
    │  └─ Page normalization               │
    │                                      │
    │  TextCleaner                         │
    │  ├─ Whitespace normalization         │
    │  ├─ Artifact removal                 │
    │  ├─ Legal reference normalization    │
    │  └─ Format standardization           │
    └──────────────────────────────────────┘
         │
    ┌────▼─────────────────────────────────┐
    │      DATA LAYER (PDF DOCUMENTS)      │
    ├──────────────────────────────────────┤
    │                                      │
    │  USCODE-2011-title18.pdf             │
    │  ├─ Federal Criminal Law             │
    │  ├─ Crime definitions & elements     │
    │  ├─ Punishments & sentences          │
    │  └─ Exceptions & special cases       │
    │                                      │
    │  Storage:                            │
    │  ├─ data/vector_store/   (Chroma)    │
    │  ├─ data/*.json           (Metadata) │
    │  └─ data/chat_history.db  (SQLite)   │
    └──────────────────────────────────────┘
```

## Component Details

### 1. Ingestion & Preprocessing Layer

**PDFParser** (`src/ingestion/pdf_parser.py`)
- **Input**: PDF file path
- **Processing**:
  - Extracts text using `pdfplumber`
  - Preserves page numbers and structure
  - Identifies legal sections (§ 2113)
  - Extracts subsections and references
- **Output**: List of pages with metadata
```python
{
    "text": "Section content...",
    "page_num": 123,
    "section": "2113",
    "subsection": "a",
    "document_title": "USCODE-2011-title18"
}
```

**TextCleaner** (`src/ingestion/text_cleaner.py`)
- **Cleaning operations**:
  - Remove PDF artifacts (page breaks, control chars)
  - Normalize whitespace
  - Remove embedded URLs/emails
  - Standardize legal references (U.S.C., §, etc.)
  - Preserve semantic meaning

### 2. Chunking & Metadata Enrichment Layer

**SemanticChunker** (`src/chunking/semantic_chunker.py`)
- **Algorithm**:
  1. First pass: Split by legal sections (§ patterns)
  2. Second pass: If chunks > CHUNK_SIZE, split by sentences
  3. Add overlap between chunks for context continuity
  
- **Chunking strategy**:
  ```
  Original text: "§ 2113. Bank robbery. (a) Penalty... (b) Enhanced..."
  
  Result chunks:
  Chunk 1: "§ 2113. Bank robbery. (a) Penalty for entry..."
  Chunk 2: "...armed with dangerous weapon. (b) Enhanced penalty..."
  Chunk 3: "...during flight, twenty years imprisonment..."
  ```

**MetadataExtractor** (`src/chunking/metadata_extractor.py`)
- **Extraction techniques**:
  - **NER (spaCy)**: PERSON, ORG, GPE, LAW entities
  - **Keyword matching**: Crime types, punishment keywords
  - **Regex patterns**: Section references, dates, amounts
  - **Text classification**: Definition, punishment, exception
  
- **Metadata per chunk**:
  ```json
  {
    "entities": [{"text": "federal", "type": "LAW"}],
    "crime_types": ["robbery", "theft"],
    "punishment_types": ["imprisonment", "fine"],
    "legal_concepts": ["guilty", "offense"],
    "section_references": ["2113"],
    "keywords": ["bank", "federal", "crime"],
    "text_type": "punishment"
  }
  ```

### 3. Embedding & Indexing Layer

**EmbeddingGenerator** (`src/embeddings/embedding_generator.py`)
- **Model**: Sentence Transformers (BGE - BAAI General Embeddings)
- **Characteristics**:
  - Dimension: 768
  - Speed: ~1000 texts/minute on CPU
  - Quality: Excellent for legal domain
  
- **Process**:
  ```
  Text → Tokenization → Transformer encoding → 768-dim vector
  "Bank robbery is a federal crime"
  → embedding = [-0.023, 0.156, ..., 0.089]  (768 values)
  ```

**VectorStore** (`src/embeddings/vector_store.py`)
- **Backend options**:
  - **Chroma**: Default, easier management, persistent
  - **FAISS**: Faster similarity search, memory efficient
  
- **Storage structure**:
  ```
  Chroma (SQLite-backed):
  - Collection: "legal_documents"
  - Fields: id, embedding[], text, metadata{}
  
  FAISS:
  - Index: flat or hierarchical
  - Metadata: separate JSON file
  - Similarity metric: L2 distance
  ```

- **Indexing statistics** (typical):
  - Documents: ~1,250 chunks
  - Vector dimension: 768
  - Storage size: ~500 MB
  - Index time: 15-20 minutes

### 4. Query Processing & Retrieval Layer

**QueryProcessor** (`src/retrieval/query_processor.py`)
- **Processing pipeline**:
  1. **Cleaning**: Remove punctuation, normalize references
  2. **Intent Classification**: 
     - Punishment (questions about sentencing)
     - Crime definition (questions about elements)
     - Elements (what must be proven)
     - Exceptions (special cases)
     - References (statute citations)
  
  3. **Keyword Extraction**: Extract nouns, verbs, legal terms
  4. **Entity Recognition**: People, organizations, law references
  5. **Query Expansion**:
     ```
     Original: "bank robbery"
     Expanded:
     - "bank robbery law"
     - "18 U.S.C. § 2113"
     - "federal bank robbery"
     - "bank robbery statute"
     - "bank robbery punishment"
     ```

**HybridRetriever** (`src/retrieval/hybrid_retriever.py`)
- **Retrieval strategy**:
  
  ```
  Query: "What is the punishment for bank robbery?"
  
  1. DENSE SEARCH (Vector Similarity)
     Query embedding → cosine similarity with all chunk embeddings
     Returns: Top 10 most similar chunks
     Scores: 0.85, 0.82, 0.79, ...
  
  2. SPARSE SEARCH (Keyword/BM25)
     Query terms → TF-IDF weighted matching
     Returns: Top 10 keyword-matched chunks
     Scores: 0.73, 0.68, 0.65, ...
  
  3. METADATA FILTERING
     Filter by: crime_types=robbery, text_type=punishment
     Further restricts results
  
  4. RESULT AGGREGATION (RRF - Reciprocal Rank Fusion)
     Dense score: 0.85 @ rank 1 → RRF = 1/(60+1) = 0.0164
     Sparse score: 0.73 @ rank 1 → RRF = 1/(60+1) = 0.0164
     Combined: 0.0164 + 0.0164 = 0.0328
     
     Final ranking: Combines both signals
     Returns: Top 5 final results
  ```

### 5. Generation & Answering Layer

**RAGGenerator** (`src/generation/rag_generator.py`)
- **System prompt** (specialized for legal domain):
  ```
  You are an expert legal assistant specializing in U.S. Code Title 18.
  
  Guidelines:
  1. Provide accurate answers about federal crimes
  2. ALWAYS cite relevant statutes (18 U.S.C. § XXX)
  3. Use legal terminology and be precise
  4. When describing crimes, include elements
  5. Include minimum and maximum sentences
  6. Clarify exceptions when relevant
  ```

- **Prompt engineering**:
  ```python
  Prompt = f"""
  Based on: {retrieved_legal_text}
  
  Answer this: {user_query}
  
  Requirements:
  - Cite 18 U.S.C. § numbers
  - Explain legal concepts
  - Include penalties
  - Note exceptions
  """
  ```

- **LLM Call**:
  - Model: GPT-4 (default) or GPT-3.5-turbo
  - Temperature: 0.3 (consistent, factual)
  - Max tokens: 2000
  - Response format: Markdown with citations

**CitationHandler** (`src/generation/citation_handler.py`)
- **Citation extraction**:
  ```regex
  Pattern 1: 18 U.S.C. § 2113
  Pattern 2: § 2113(b)
  Pattern 3: 18 USC 2113
  Pattern 4: 45 C.F.R. § 123
  ```

- **Citation formatting**:
  - HTML: `<span class="citation" data-statute="2113">§ 2113</span>`
  - Markdown: `[§ 2113](https://www.law.cornell.edu/uscode/text/18/2113)`
  - JSON: `{"statute": "18 U.S.C. § 2113", "page": "123"}`

### 6. API & Web Interface Layer

**FastAPI Application** (`src/api/chat_api.py`)
- **Endpoints**:
  - `POST /chat`: Query the chatbot
  - `GET /status`: Pipeline status
  - `GET /health`: Health check
  - `POST /feedback`: Submit feedback
  - `GET /docs`: API documentation

- **Response format**:
  ```json
  {
    "answer": "Bank robbery is defined in 18 U.S.C. § 2113...",
    "citations": [
      {"statute": "18 U.S.C. § 2113", "source": "USCODE:p123"}
    ],
    "retrieved_documents": [...],
    "model": "gpt-4",
    "status": "success"
  }
  ```

### 7. Data Logging & Feedback Layer

**Database Schema** (`data/chat_history.db`)
```sql
-- Chat interactions
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    query TEXT,
    answer TEXT,
    model TEXT,
    timestamp DATETIME,
    tokens_used INTEGER
);

-- User feedback
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY,
    query TEXT,
    answer TEXT,
    rating INTEGER,  -- 1-5
    comment TEXT,
    timestamp DATETIME
);
```

## Data Flow Diagram

```
User Query
    │
    ▼
┌─────────────────────┐
│ Query Processor     │
│ - Clean            │
│ - Classify intent  │
│ - Extract entities │
│ - Expand query     │
└────────┬────────────┘
         │
         ▼
    ┌──────────────────────────┐
    │  HybridRetriever         │
    │  ┌──────────────────┐    │
    │  │ Dense Search     │    │
    │  │ + Sparse Search  │    │
    │  │ + Metadata Filt  │    │
    │  └────────┬─────────┘    │
    │           │              │
    │     Results: [doc1, doc2,│
    │               doc3, ...]  │
    └────────┬────────────────┘
             │
             ▼
        ┌────────────────────┐
        │ RAG Generator      │
        │ - Create prompt    │
        │ - Call LLM (GPT-4) │
        │ - Parse response   │
        └────────┬───────────┘
                 │
                 ▼
            ┌─────────────────┐
            │Citation Handler │
            │ - Extract cites │
            │ - Format links  │
            │ - Verify refs   │
            └────────┬────────┘
                     │
                     ▼
                ┌──────────────┐
                │ API Response │
                │ - Answer     │
                │ - Citations  │
                │ - Metadata   │
                └─────────────┘
                     │
                     ▼
                 User Display
                     │
                     ▼
            ┌──────────────────┐
            │ Database Logging │
            │ - Chat history   │
            │ - Feedback       │
            └──────────────────┘
```

## Key Algorithms

### 1. Reciprocal Rank Fusion (RRF)

Combines rankings from multiple retrievers:

```python
score(doc) = Σ 1/(60 + rank_i(doc))

Example:
Dense: rank 1 → 1/(60+1) = 0.0164
Sparse: rank 3 → 1/(60+3) = 0.0152
Combined: 0.0164 + 0.0152 = 0.0316
```

### 2. Semantic Chunking

Dynamic chunking based on content:

```python
def chunk_text(text, CHUNK_SIZE=500):
    sections = split_by_legal_sections(text)
    
    chunks = []
    for section in sections:
        if len(section) > CHUNK_SIZE:
            # Split by sentences
            sentences = nlp(section).sents
            current = ""
            
            for sent in sentences:
                if len(current + sent) <= CHUNK_SIZE:
                    current += sent
                else:
                    chunks.append(current)
                    current = sent
            
            chunks.append(current)
        else:
            chunks.append(section)
    
    return add_overlap(chunks)
```

### 3. Intent-Based Retrieval

Different retrieval strategies for different intents:

```python
if intent == "punishment":
    filters = {"text_type": "punishment"}
    k = 5
elif intent == "crime_definition":
    filters = {"text_type": "definition"}
    k = 3
elif intent == "elements":
    keywords = expand_with("elements", "requires")
    k = 7
```

## Performance Characteristics

### Throughput
- **Indexing**: 500-1000 chunks/minute
- **Embedding**: 100-200 texts/minute (CPU)
- **Retrieval**: 50-100 queries/minute
- **Generation**: 5-10 answers/minute (LLM limited)

### Latency
- **Query processing**: 100-200 ms
- **Retrieval**: 200-500 ms
- **LLM generation**: 3-5 seconds
- **Total E2E**: 5-10 seconds

### Resource Usage
- **Memory**: 2-4 GB (index + models in memory)
- **Storage**: 500 MB (vectors) + 100 MB (models)
- **CPU**: 2-4 cores recommended
- **GPU**: Optional, accelerates embedding

## Scalability Considerations

1. **For larger documents**:
   - Use FAISS instead of Chroma
   - Reduce CHUNK_SIZE
   - Implement chunking in batches

2. **For more queries**:
   - Add API load balancer
   - Cache frequently asked questions
   - Pre-compute embeddings

3. **For multiple users**:
   - Use session management
   - Implement request queuing
   - Add database connection pooling

## Security Considerations

1. **API Security**:
   - Add API authentication
   - Rate limiting per user
   - CORS configuration

2. **Data Privacy**:
   - Encrypt stored chat history
   - Option to delete conversation
   - No data sharing with LLM (optional)

3. **Content Validation**:
   - Validate user input
   - Sanitize API responses
   - Monitor for malicious usage

## Monitoring & Analytics

**Metrics to track**:
- Query success rate
- Response latency
- User feedback ratings
- Most common questions
- System resource usage
- Vector store growth

---

This architecture provides a robust, scalable, and specialized RAG system for legal document analysis.
