"""
FastAPI application for legal document chatbot
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from config.settings import settings
from src.pipeline import RAGPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Legal Document RAG Chatbot",
    description="Advanced RAG pipeline for legal documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline
rag_pipeline = None


class Citation(BaseModel):
    """Citation information"""
    statute: str = Field(..., description="Statute reference (e.g., 18 U.S.C. § 2113)")
    source: Optional[str] = Field(None, description="Source document")
    page: Optional[str] = Field(None, description="Page number")


class RetrievedDocument(BaseModel):
    """Retrieved document chunk"""
    text: str = Field(..., description="Document text")
    source: str = Field(..., description="Source reference")
    section: Optional[str] = Field(None, description="Section number")
    relevance_score: float = Field(..., description="Relevance score 0-1")


class ChatRequest(BaseModel):
    """Chat request"""
    query: str = Field(..., description="User query")
    session_id: Optional[str] = Field(None, description="Session ID for multi-turn context")
    include_retrieved_docs: bool = Field(False, description="Include retrieved documents in response")


class ChatResponse(BaseModel):
    """Chat response"""
    answer: str = Field(..., description="Generated answer")
    citations: List[Citation] = Field(default_factory=list, description="Citations")
    retrieved_documents: Optional[List[RetrievedDocument]] = Field(None, description="Retrieved documents")
    query: str = Field(..., description="Original query")
    model: str = Field(..., description="Model used")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")
    status: str = Field(default="success", description="Response status")


class PipelineStatus(BaseModel):
    """Pipeline status"""
    initialized: bool
    documents_indexed: int
    vector_store_type: str
    embedding_model: str


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    global rag_pipeline
    try:
        logger.info("Initializing RAG pipeline...")
        rag_pipeline = RAGPipeline()
        logger.info("RAG pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG pipeline: {e}")
        raise


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "pipeline_initialized": rag_pipeline is not None
    }


@app.get("/status", response_model=PipelineStatus, tags=["System"])
async def get_status():
    """Get pipeline status"""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    return PipelineStatus(
        initialized=True,
        documents_indexed=rag_pipeline.get_indexed_count(),
        vector_store_type=settings.VECTOR_STORE_TYPE,
        embedding_model=settings.EMBEDDING_MODEL
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Chat endpoint - query the legal documents
    
    Args:
        request: Chat request with query
        background_tasks: Background tasks for logging
        
    Returns:
        ChatResponse with answer and citations
    """
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        # Process query
        logger.info(f"Processing query: {request.query}")
        
        result = rag_pipeline.answer_query(
            query=request.query,
            include_retrieved_docs=request.include_retrieved_docs
        )
        
        # Prepare response
        citations = [
            Citation(**citation) for citation in result.get("citations", [])
        ]
        
        retrieved_docs = None
        if request.include_retrieved_docs and "retrieved_documents" in result:
            retrieved_docs = [
                RetrievedDocument(**doc) for doc in result["retrieved_documents"]
            ]
        
        response = ChatResponse(
            answer=result.get("answer", ""),
            citations=citations,
            retrieved_documents=retrieved_docs,
            query=request.query,
            model=result.get("model", settings.LLM_MODEL),
            status="success"
        )
        
        # Log interaction asynchronously
        background_tasks.add_task(
            rag_pipeline.log_interaction,
            query=request.query,
            answer=response.answer,
            session_id=request.session_id
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback", tags=["Feedback"])
async def provide_feedback(
    query: str,
    answer: str,
    rating: int = Field(..., ge=1, le=5),
    comment: Optional[str] = None
):
    """Provide feedback on answer quality
    
    Args:
        query: Original query
        answer: Generated answer
        rating: Rating from 1-5
        comment: Optional comment
        
    Returns:
        Feedback confirmation
    """
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        rag_pipeline.log_feedback(
            query=query,
            answer=answer,
            rating=rating,
            comment=comment
        )
        
        return {
            "status": "success",
            "message": "Feedback recorded",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/docs", include_in_schema=False)
async def get_docs():
    """Redirect to Swagger UI"""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Legal Chatbot API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
