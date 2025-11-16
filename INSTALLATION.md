# Installation Guide - Legal Document RAG Chatbot

## System Requirements

- **Python**: 3.9 or higher
- **RAM**: 8GB minimum (16GB recommended for smooth embedding generation)
- **Storage**: 5GB free space (for vector store and models)
- **OS**: Windows, macOS, or Linux

## Step-by-Step Installation

### 1. Download the Project

```bash
cd "C:\Users\WIN\OneDrive\Desktop\LegalBot AI"
```

### 2. Create a Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This may take 5-10 minutes depending on your internet connection and system.

### 5. Download spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

### 6. Set Up Environment Configuration

```bash
# Copy example configuration
cp .env.example .env
```

**Edit `.env` file and add your OpenAI API key:**

```ini
OPENAI_API_KEY=sk-your-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### 7. Verify Installation

Run the quick start check:

```bash
python quickstart.py
```

You should see:
```
✓ All dependencies installed
✓ Found PDF: ...USCODE-2011-title18.pdf
✓ All checks passed!
```

## Installation Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'pdfplumber'"

**Solution:**
```bash
pip install pdfplumber pypdf
```

### Issue: "ModuleNotFoundError: No module named 'spacy'"

**Solution:**
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

### Issue: "ModuleNotFoundError: No module named 'sentence_transformers'"

**Solution:**
```bash
pip install sentence-transformers
```

### Issue: "CUDA not available" warnings (safe to ignore)

This just means GPU acceleration is not available. The system will use CPU instead, which is fine for most use cases.

**Optional - Enable GPU (NVIDIA only):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install sentence-transformers[torch]
```

### Issue: "Long path" errors on Windows

If you get long filename errors:
```bash
# Enable long paths on Windows
reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1
```

### Issue: Permission denied errors

```bash
# Run PowerShell as Administrator and execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## First Run Setup

### Step 1: Build the Index (Required)

```bash
python main.py build
```

**What happens:**
1. Extracts text from the PDF (2-5 minutes)
2. Cleans and normalizes the text
3. Splits into semantic chunks
4. Extracts legal metadata
5. Generates embeddings (5-20 minutes depending on CPU)
6. Creates vector index

**Total time**: 10-30 minutes on first run

**Progress indicators:**
```
Step 1: Extracting documents from PDF...
Extracted 300 pages
Step 2: Cleaning and preprocessing text...
Step 3: Creating semantic chunks...
Created 1250 chunks
Step 4: Extracting metadata from chunks...
Extracting metadata: 100%|████| 1250/1250
Step 5: Generating embeddings...
Encoding: 100%|████| 1250/1250
Step 6: Indexing in vector store...
✓ Successfully indexed 1250 documents
```

### Step 2: Start Using the System

**Interactive Chat:**
```bash
python main.py chat
```

**Web API Server:**
```bash
python main.py api
```

Then visit: http://localhost:8000/docs

## Detailed Configuration

### Optional: Change LLM Model

Edit `.env`:
```ini
# Use GPT-3.5 Turbo (faster, cheaper)
LLM_MODEL=gpt-3.5-turbo

# Use GPT-4 (more powerful, more expensive)
LLM_MODEL=gpt-4
```

### Optional: Change Vector Store

Edit `config/settings.py`:
```python
# Use FAISS (faster, more memory efficient)
VECTOR_STORE_TYPE = "faiss"

# Use Chroma (default, easier to manage)
VECTOR_STORE_TYPE = "chroma"
```

### Optional: Change Embedding Model

Edit `config/settings.py`:
```python
# Fast, lightweight
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Medium (default, balanced)
EMBEDDING_MODEL = "sentence-transformers/bge-base-en-v1.5"

# Large, most accurate
EMBEDDING_MODEL = "sentence-transformers/bge-large-en-v1.5"
```

## Verification Tests

### Test 1: Basic Functionality
```bash
python -c "from src.pipeline import RAGPipeline; print('✓ Pipeline imports successfully')"
```

### Test 2: Embedding Model
```bash
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/bge-base-en-v1.5'); print('✓ Embedding model loaded')"
```

### Test 3: Vector Store
```bash
python -c "from src.embeddings import VectorStore; vs = VectorStore(); print(f'✓ Vector store initialized with {vs.get_collection_size()} documents')"
```

### Test 4: API
```bash
python -c "from src.api import app; print('✓ API module loads successfully')"
```

## Performance Optimization

### For Faster Embedding Generation:

1. **Install CUDA support** (GPU acceleration):
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. **Reduce batch size** (if running out of memory):
   Edit `config/settings.py`:
   ```python
   EMBEDDING_BATCH_SIZE = 16  # Default: 32
   ```

### For Faster Retrieval:

1. **Use FAISS instead of Chroma**:
   ```python
   VECTOR_STORE_TYPE = "faiss"
   ```

2. **Reduce retrieval k**:
   ```python
   RETRIEVAL_K = 3  # Default: 5
   ```

### For Faster API Response:

1. **Use gpt-3.5-turbo instead of gpt-4**:
   ```bash
   export LLM_MODEL=gpt-3.5-turbo
   ```

2. **Disable query expansion**:
   ```python
   QUERY_EXPANSION_ENABLED = False
   ```

## Upgrading Dependencies

To update all packages to latest versions:

```bash
pip install -r requirements.txt --upgrade
```

## Uninstallation

To completely remove the system:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rmdir /s venv  # Windows
rm -rf venv    # macOS/Linux

# Or just delete the entire project folder
```

## Getting Help

1. **Check logs:**
   ```bash
   tail -f logs/legal_chatbot.log
   ```

2. **Run diagnostics:**
   ```bash
   python quickstart.py
   ```

3. **Check configuration:**
   ```bash
   python -c "from config.settings import settings; print(settings)"
   ```

## Next Steps

After successful installation:

1. **Build the index**: `python main.py build`
2. **Try interactive chat**: `python main.py chat`
3. **Start API server**: `python main.py api`
4. **Read examples**: `python examples.py`

## Troubleshooting Common Issues

### All tests pass but system doesn't work

1. Make sure `.env` file has valid `OPENAI_API_KEY`
2. Check internet connection
3. Verify PDF file exists at configured path
4. Check logs: `logs/legal_chatbot.log`

### API starts but gives errors

1. Check if port 8000 is available: `netstat -an | findstr 8000` (Windows)
2. Try different port in `.env`: `API_PORT=8001`
3. Make sure index was built: `python main.py build`

### Out of memory errors

1. Use smaller embedding batch size
2. Use FAISS instead of Chroma
3. Reduce CHUNK_SIZE in settings
4. Close other applications to free up RAM

## System Architecture

The installation creates:

```
data/
  ├── vector_store/        # Vector database files
  ├── chat_history.db      # SQLite database
  └── metadata/            # Metadata indices

logs/
  └── legal_chatbot.log    # Application logs

src/                       # Python source code
├── ingestion/            # PDF parsing
├── chunking/             # Document splitting
├── embeddings/           # Vector storage
├── retrieval/            # Search and retrieval
├── generation/           # LLM integration
└── api/                  # Web API
```

---

**Installation complete!** Proceed with building the index and start using the chatbot.
