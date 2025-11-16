# 🚀 Quick Start Guide - 5 Minutes to Legal RAG Chatbot

## 30-Second Overview

You have a **production-ready legal document RAG chatbot** that can answer questions about federal criminal law (18 U.S.C.).

## ⚡ Quick Start (3 Steps)

### Step 1: Install Dependencies (2 minutes)
```bash
cd "C:\Users\WIN\OneDrive\Desktop\LegalBot AI"
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 2: Build Index (15-20 minutes)
```bash
python main.py build
```
*Processes the PDF and creates searchable index*

### Step 3: Start Chatting!
```bash
python main.py chat
```

**Example questions:**
```
✓ Query: What is bank robbery under federal law?
✓ Query: What are the punishments for fraud?
✓ Query: Define assault under 18 U.S.C. § 113
✓ Query: What elements must be proven for murder?
```

---

## 🌐 Using the Web API

**Instead of interactive chat, start the API server:**

```bash
python main.py api
```

Then visit: **http://localhost:8000/docs**

**Example API call:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is bank robbery?"}'
```

---

## ✅ Verify Installation

```bash
python quickstart.py
```

Should show:
```
✓ All dependencies installed
✓ Found PDF
✓ All imports working
✓ Ready to build index!
```

---

## 📊 What's Included

- ✅ 15 Python modules (~3,500 lines)
- ✅ Advanced NLP & semantic chunking
- ✅ Hybrid retrieval (dense + sparse + metadata)
- ✅ GPT-4 integration with citation handling
- ✅ REST API with Swagger documentation
- ✅ Chat history & feedback logging
- ✅ Comprehensive documentation

---

## 🏗️ System Architecture

```
PDF → Parse → Chunk → Embed → Index → Retrieve → LLM → Answer + Citations
                      ↓
                   Vector DB
                (Chroma/FAISS)
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point (build, chat, api) |
| `config/settings.py` | Configuration |
| `src/pipeline.py` | Main RAG orchestration |
| `src/ingestion/` | PDF parsing |
| `src/chunking/` | Semantic splitting & metadata |
| `src/embeddings/` | Vector storage |
| `src/retrieval/` | Hybrid search |
| `src/generation/` | LLM & citations |
| `src/api/` | REST API |

---

## ⚙️ Configuration

### Use Different LLM
Edit `.env`:
```ini
LLM_MODEL=gpt-3.5-turbo  # Faster, cheaper
```

### Use Different Embedding Model
Edit `config/settings.py`:
```python
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

### Use FAISS Instead of Chroma
Edit `config/settings.py`:
```python
VECTOR_STORE_TYPE = "faiss"
```

---

## 🔍 Example Queries

### Crime Definitions
- "Define bank robbery"
- "What is federal murder?"
- "What is fraud under federal law?"

### Punishments
- "What is the penalty for robbery?"
- "What is the sentence for fraud?"
- "How many years for theft?"

### Legal References
- "What is 18 U.S.C. § 2113?"
- "Explain § 113 of Title 18"

### Elements & Requirements
- "What elements must be proven for robbery?"
- "What are the elements of federal assault?"

---

## 📈 Performance

| Operation | Time |
|-----------|------|
| Build index | 15-30 min (one-time) |
| Query response | 5-10 sec |
| Retrieval | 200-500 ms |
| LLM generation | 3-5 sec |

---

## 🆘 Troubleshooting

### "No module named X"
```bash
pip install -r requirements.txt
```

### "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

### "OpenAI API error"
- Check `.env` has valid API key
- Verify account has credits

### "Out of memory"
- Reduce `EMBEDDING_BATCH_SIZE` in `config/settings.py`
- Use FAISS instead of Chroma

### "Port 8000 in use"
- Edit `config/settings.py`: `API_PORT = 8001`

---

## 📚 Full Documentation

- **README.md** - Complete overview
- **INSTALLATION.md** - Detailed setup
- **ARCHITECTURE.md** - System design
- **PROJECT_SUMMARY.md** - Project details
- **QUICKSTART.md** - This file

---

## 🎯 Common Workflows

### Workflow 1: Interactive Exploration
```bash
python main.py chat --show-sources
```

### Workflow 2: API Integration
```bash
python main.py api
# Call from your app via http://localhost:8000
```

### Workflow 3: Rebuild Index
```bash
python main.py build --force-rebuild
```

### Workflow 4: Custom PDF
```bash
python main.py --pdf /path/to/document.pdf build
```

---

## 🔑 Key Features

### 1. **Semantic Chunking**
- NLP-based section awareness
- Intelligent paragraph breaking
- Overlap for continuity

### 2. **Metadata Extraction**
- Crime types (robbery, fraud, etc.)
- Punishments (sentences, fines)
- Legal concepts
- Statute references

### 3. **Hybrid Retrieval**
- Dense (vector similarity)
- Sparse (keyword matching)
- Metadata filtering
- RRF aggregation

### 4. **Smart Citations**
- Automatic statute extraction
- Verification & linking
- HTML/Markdown formatting

### 5. **Feedback Loop**
- Rate answers (1-5 stars)
- Chat history storage
- Analytics ready

---

## 🚀 Deployment Options

### Local CLI
```bash
python main.py chat
```

### Local API Server
```bash
python main.py api
```

### Docker (template)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py", "api"]
```

### Cloud Deployment
Works with AWS, Azure, Google Cloud, Heroku, etc.

---

## 💡 Tips & Tricks

### Faster Startup
```bash
# Pre-build index before deploying
python main.py build
```

### Better Answers
```bash
# Enable query expansion in settings.py
QUERY_EXPANSION_ENABLED = True
```

### Debugging
```bash
# Check logs
tail -f logs/legal_chatbot.log

# Run diagnostics
python quickstart.py

# Test imports
python -c "from src.pipeline import RAGPipeline; print('OK')"
```

### Performance Tuning
```python
# In config/settings.py:
RETRIEVAL_K = 3        # Fewer results, faster
CHUNK_SIZE = 300       # Smaller chunks, faster retrieval
EMBEDDING_BATCH_SIZE = 64  # Larger batches, faster embedding
```

---

## 📊 Database & Logs

### Chat History
```
data/chat_history.db
- Table: chat_history
- Table: feedback
```

### Logs
```
logs/legal_chatbot.log
- All operations logged
- Searchable by time
```

### Vector Store
```
data/vector_store/
- Chroma (SQLite-backed)
- Metadata indices
- ~500 MB for full legal code
```

---

## 🎓 Learning Path

1. **Understand the system**: Read README.md
2. **Set it up**: Follow INSTALLATION.md
3. **See it work**: Run `python main.py chat`
4. **Explore the code**: Check src/ modules
5. **Customize**: Modify config/settings.py
6. **Integrate**: Use the REST API
7. **Extend**: Read ARCHITECTURE.md

---

## 📞 Support

- **Logs**: `logs/legal_chatbot.log`
- **Diagnostics**: `python quickstart.py`
- **API Docs**: `http://localhost:8000/docs`
- **Config**: `config/settings.py`
- **Examples**: `examples.py`

---

## ⏱️ Time Estimates

| Task | Time |
|------|------|
| Install | 5 min |
| Build index | 20 min |
| First query | 10 sec |
| Learn system | 30 min |
| Deploy API | 5 min |

---

## 🎉 You're Ready!

Your advanced legal RAG chatbot is ready. 

**Next step**: `python main.py build`

Then start asking questions about federal criminal law!

---

**Questions?** Check the documentation files or review the code comments.

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Status**: Production Ready ✅
