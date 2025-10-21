"""
ClinChat-RAG FastAPI Application
Retrieval-Augmented Generation service for medical Q&A using Google embeddings and FAISS vectorstore.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import logging

# LangChain imports
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

# Local imports
from nlp.simple_table_processor import SimpleTableProcessor
from nlp.rerank.hybrid_search_manager import HybridSearchManager, HybridSearchConfig, RerankingMethod

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionRequest(BaseModel):
    """Request model for Q&A endpoint"""
    question: str
    max_sources: Optional[int] = 5
    include_scores: Optional[bool] = False

class HybridSearchRequest(BaseModel):
    """Request model for hybrid search endpoint"""
    query: str
    method: Optional[str] = "hybrid_bm25_ce"  # bm25_only, cross_encoder_only, hybrid_bm25_ce, full_hybrid
    top_k: Optional[int] = 5
    bm25_weight: Optional[float] = 0.3
    cross_encoder_weight: Optional[float] = 0.4
    vector_weight: Optional[float] = 0.3
    metadata_filters: Optional[Dict[str, Any]] = None

class SourceDocument(BaseModel):
    """Source document model for provenance tracking"""
    doc_id: str
    chunk_id: str
    content: str
    section: Optional[str] = None
    similarity_score: Optional[float] = None
    metadata: Dict[str, Any] = {}

class RAGResponse(BaseModel):
    """Response model with answer and provenance"""
    answer: str
    sources: List[SourceDocument]
    question: str
    confidence: Optional[str] = None

class ClinChatRAG:
    """Main RAG application class"""
    
    def __init__(self):
        self.app = FastAPI(
            title="ClinChat-RAG API",
            description="Retrieval-Augmented Generation service for medical Q&A",
            version="1.0.0"
        )
        
        # Initialize components
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.qa_chain = None
        self.table_processor = SimpleTableProcessor()
        self.hybrid_search_manager = None
        
        # Setup routes
        self._setup_routes()
        
        # Initialize RAG components
        self._initialize_rag()
    
    async def _process_numeric_query(self, request: QuestionRequest) -> RAGResponse:
        """Process numeric/table-based queries"""
        try:
            # Get relevant documents
            docs_with_scores = self.vectorstore.similarity_search_with_score(
                request.question, 
                k=request.max_sources or 5
            )
            
            # Look for tables in the retrieved documents
            tables_found = []
            sources = []
            
            for doc, score in docs_with_scores:
                # Extract tables from document content
                tables = self.table_processor.extract_tables_from_text(doc.page_content)
                
                if tables:
                    tables_found.extend(tables)
                
                # Add to sources for provenance
                source = SourceDocument(
                    doc_id=doc.metadata.get("doc_id", "unknown"),
                    chunk_id=doc.metadata.get("chunk_id", "unknown"),
                    content=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    section=doc.metadata.get("section"),
                    similarity_score=float(score) if request.include_scores else None,
                    metadata=doc.metadata
                )
                sources.append(source)
            
            if not tables_found:
                # No tables found, fall back to regular processing
                logger.info("No tables found, falling back to text processing")
                return await self._process_text_query(request)
            
            # Process the first table found
            table_data = tables_found[0]['data']
            result = self.table_processor.extract_numeric_values(table_data, request.question)
            
            # Format response
            source_info = f"table from {sources[0].doc_id}" if sources else "source table"
            numeric_answer = self.table_processor.format_numeric_response(
                result, request.question, source_info
            )
            
            logger.info(f"Generated numeric answer with {len(sources)} sources")
            
            return RAGResponse(
                answer=numeric_answer,
                sources=sources,
                question=request.question,
                confidence="Computed from table data"
            )
            
        except Exception as e:
            logger.error(f"Error in numeric query processing: {e}")
            # Fall back to regular processing
            return await self._process_text_query(request)
    
    async def _process_text_query(self, request: QuestionRequest) -> RAGResponse:
        """Process regular text-based queries"""
        try:
            # Get relevant documents with scores
            docs_with_scores = self.vectorstore.similarity_search_with_score(
                request.question, 
                k=request.max_sources or 5
            )
            
            # Generate answer using custom RAG chain
            answer = self.qa_chain.invoke(request.question)
            
            # Extract source documents with provenance
            sources = []
            for doc, score in docs_with_scores:
                source = SourceDocument(
                    doc_id=doc.metadata.get("doc_id", "unknown"),
                    chunk_id=doc.metadata.get("chunk_id", "unknown"),
                    content=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    section=doc.metadata.get("section"),
                    similarity_score=float(score) if request.include_scores else None,
                    metadata={
                        "start_char": doc.metadata.get("start_char"),
                        "end_char": doc.metadata.get("end_char"),
                        "page": doc.metadata.get("page"),
                        "original_file": doc.metadata.get("original_file")
                    }
                )
                sources.append(source)
            
            logger.info(f"Generated answer with {len(sources)} sources")
            
            return RAGResponse(
                answer=answer,
                sources=sources,
                question=request.question,
                confidence="Retrieved from medical documents"
            )
            
        except Exception as e:
            logger.error(f"Error in text query processing: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "ClinChat-RAG",
                "version": "1.0.0",
                "status": "healthy",
                "description": "Medical Q&A service using RAG"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                # Check if components are initialized
                if not all([self.embeddings, self.vectorstore, self.llm, self.qa_chain]):
                    return {"status": "unhealthy", "message": "RAG components not initialized"}
                
                # Test vector search
                test_results = self.vectorstore.similarity_search("test", k=1)
                
                return {
                    "status": "healthy",
                    "components": {
                        "embeddings": "google-generativeai",
                        "vectorstore": "faiss",
                        "llm": "groq",
                        "indexed_documents": len(test_results) > 0
                    }
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return {"status": "unhealthy", "error": str(e)}
        
        @self.app.post("/qa", response_model=RAGResponse)
        async def ask_question(request: QuestionRequest):
            """Main Q&A endpoint with provenance tracking"""
            try:
                logger.info(f"Processing question: {request.question}")
                
                # Check if this is a numeric/table query
                if self.table_processor.is_numeric_query(request.question):
                    logger.info("Detected numeric query - routing to table processor")
                    return await self._process_numeric_query(request)
                
                # Regular text-based RAG processing
                return await self._process_text_query(request)
                
            except Exception as e:
                logger.error(f"Error in Q&A endpoint: {e}")
                raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        
        @self.app.get("/search")
        async def search_documents(query: str, k: int = 5):
            """Direct document search endpoint"""
            try:
                docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)
                
                results = []
                for doc, score in docs_with_scores:
                    results.append({
                        "doc_id": doc.metadata.get("doc_id"),
                        "chunk_id": doc.metadata.get("chunk_id"),
                        "section": doc.metadata.get("section"),
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "similarity_score": float(score),
                        "metadata": doc.metadata
                    })
                
                return {
                    "query": query,
                    "results": results,
                    "total_found": len(results)
                }
                
            except Exception as e:
                logger.error(f"Search error: {e}")
                raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
        
        @self.app.post("/hybrid-search")
        async def hybrid_search(request: HybridSearchRequest):
            """Advanced hybrid search with reranking"""
            try:
                logger.info(f"Processing hybrid search: {request.query}")
                
                if not self.hybrid_search_manager:
                    raise HTTPException(status_code=503, detail="Hybrid search not initialized")
                
                # Get initial vector search results
                docs_with_scores = self.vectorstore.similarity_search_with_score(
                    request.query, 
                    k=(request.top_k or 5) * 4  # Get more candidates for reranking
                )
                
                # Convert to hybrid search format
                documents = []
                for doc, score in docs_with_scores:
                    doc_dict = {
                        'doc_id': doc.metadata.get("doc_id", "unknown"),
                        'chunk_id': doc.metadata.get("chunk_id", "unknown"),
                        'content': doc.page_content,
                        'similarity_score': float(score),
                        'metadata': doc.metadata
                    }
                    documents.append(doc_dict)
                
                # Update hybrid search config if provided
                if any([request.bm25_weight, request.cross_encoder_weight, request.vector_weight]):
                    config = HybridSearchConfig(
                        method=RerankingMethod(request.method),
                        bm25_weight=request.bm25_weight or 0.3,
                        cross_encoder_weight=request.cross_encoder_weight or 0.4,
                        vector_weight=request.vector_weight or 0.3,
                        final_top_k=request.top_k or 5,
                        metadata_filters=request.metadata_filters or {}
                    )
                    search_manager = HybridSearchManager(config)
                    search_manager.build_index(documents)
                else:
                    search_manager = self.hybrid_search_manager
                    search_manager.build_index(documents)
                
                # Perform hybrid search
                reranked_results = search_manager.hybrid_search(
                    request.query, 
                    documents, 
                    top_k=request.top_k
                )
                
                # Format response
                results = []
                for doc in reranked_results:
                    results.append({
                        "doc_id": doc.get('doc_id'),
                        "chunk_id": doc.get('chunk_id'),
                        "content": doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content'],
                        "final_score": doc.get('final_score', 0),
                        "similarity_score": doc.get('similarity_score'),
                        "bm25_score": doc.get('bm25_score'),
                        "cross_encoder_score": doc.get('cross_encoder_score'),
                        "reranking_method": doc.get('reranking_method'),
                        "metadata": doc.get('metadata', {})
                    })
                
                # Get search statistics
                stats = search_manager.get_search_stats(request.query, documents)
                
                return {
                    "query": request.query,
                    "method": request.method,
                    "results": results,
                    "total_candidates": len(documents),
                    "total_returned": len(results),
                    "search_stats": stats
                }
                
            except Exception as e:
                logger.error(f"Hybrid search error: {e}")
                raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(e)}")
    
    def _initialize_rag(self):
        """Initialize RAG components"""
        try:
            logger.info("Initializing RAG components...")
            
            # Check API key
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            # Initialize Google embeddings
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                task_type="retrieval_query"  # For querying
            )
            logger.info("Google embeddings initialized")
            
            # Load FAISS vectorstore
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            vectorstore_path = os.path.join(base_dir, "vectorstore", "faiss_index")
            if not os.path.exists(vectorstore_path):
                raise FileNotFoundError(f"FAISS index not found at {vectorstore_path}")
            
            self.vectorstore = FAISS.load_local(
                vectorstore_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("FAISS vectorstore loaded")
            
            # Initialize hybrid search manager
            config = HybridSearchConfig(
                method=RerankingMethod.HYBRID_BM25_CE,
                bm25_weight=0.3,
                cross_encoder_weight=0.4,
                vector_weight=0.3,
                top_k_retrieval=20,
                final_top_k=5
            )
            self.hybrid_search_manager = HybridSearchManager(config)
            logger.info("Hybrid search manager initialized")
            
            # Initialize Groq LLM (try a current model)
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            
            self.llm = ChatGroq(
                model="llama3-8b-8192",  # Fix parameter name
                temperature=0.3,
                max_tokens=1000
            )
            logger.info("Google LLM initialized")
            
            # Create custom prompt for medical Q&A
            medical_prompt = PromptTemplate.from_template(
                """You are a medical AI assistant. Use the following medical document excerpts to answer the question accurately and professionally.

Context from medical documents:
{context}

Question: {question}

Instructions:
- Provide a clear, professional medical response
- Base your answer on the provided context
- If information is insufficient, state limitations clearly
- Include relevant medical terminology appropriately
- Maintain patient confidentiality (data is already de-identified)

Answer:"""
            )
            
            # Setup retriever
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            # Create custom RAG chain using LCEL (LangChain Expression Language)
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
            self.qa_chain = (
                {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
                | medical_prompt
                | self.llm
                | StrOutputParser()
            )
            
            logger.info("RetrievalQA chain initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
            raise

# Create global app instance
rag_service = ClinChatRAG()
app = rag_service.app

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )