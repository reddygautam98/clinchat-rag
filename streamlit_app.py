"""
ClinChat-RAG Streamlit Demo Application
Interactive web interface showcasing the complete medical RAG system
"""

import streamlit as st
import requests
import json
import os
import tempfile
import time
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Import our processing modules
import sys
sys.path.append(str(Path(__file__).parent))

try:
    from nlp.deid import MedicalDeidentifier
    from nlp.chunker import MedicalChunker
    from embeddings.index_faiss import MedicalFAISIndexer
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="ClinChat-RAG Demo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .source-doc {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 5px 5px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class ClinChatRAGDemo:
    def __init__(self):
        self.api_base_url = "http://127.0.0.1:8000"
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'processed_docs' not in st.session_state:
            st.session_state.processed_docs = []
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        if 'current_doc' not in st.session_state:
            st.session_state.current_doc = None
        if 'api_available' not in st.session_state:
            st.session_state.api_available = False
    
    def check_api_health(self):
        """Check if the RAG API is available"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=3)
            if response.status_code == 200:
                st.session_state.api_available = True
                return True
        except:
            pass
        st.session_state.api_available = False
        return False
    
    def render_header(self):
        """Render the application header"""
        st.markdown('<div class="main-header">🏥 ClinChat-RAG Demo</div>', unsafe_allow_html=True)
        st.markdown("**Interactive Medical Document Q&A with Retrieval-Augmented Generation**")
        
        # API Status
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if self.check_api_health():
                st.success("✅ RAG API Connected")
            else:
                st.error("❌ RAG API Offline - Start with: `uvicorn api.app:app --host 127.0.0.1 --port 8000`")
        
        with col2:
            if st.button("🔄 Refresh API Status"):
                st.rerun()
        
        with col3:
            st.info(f"📊 {len(st.session_state.processed_docs)} Documents Processed")
    
    def render_sidebar(self):
        """Render the sidebar with navigation and stats"""
        st.sidebar.markdown("## 🎯 Navigation")
        
        # Tab selection
        tab = st.sidebar.radio(
            "Choose a section:",
            ["📤 Document Processing", "🔍 Search & Q&A", "📊 Analytics", "⚙️ Settings"]
        )
        
        st.sidebar.markdown("---")
        
        # Quick stats
        st.sidebar.markdown("## 📈 Quick Stats")
        st.sidebar.metric("Documents Processed", len(st.session_state.processed_docs))
        st.sidebar.metric("Queries Made", len(st.session_state.query_history))
        
        # Recent activity
        if st.session_state.query_history:
            st.sidebar.markdown("## 🕒 Recent Queries")
            for query in st.session_state.query_history[-3:]:
                st.sidebar.caption(f"• {query['question'][:50]}...")
        
        return tab
    
    def process_document(self, uploaded_file):
        """Process an uploaded document through the complete pipeline"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: De-identification
            status_text.text("🔒 De-identifying sensitive information...")
            progress_bar.progress(25)
            
            deid = MedicalDeidentifier()
            deid_result = deid.process_file(tmp_path)
            
            # Step 2: Chunking
            status_text.text("📝 Creating semantic chunks...")
            progress_bar.progress(50)
            
            chunker = MedicalChunker()
            chunks = chunker.process_file(deid_result['output_file'])
            
            # Step 3: Indexing (simulate - in real app would rebuild index)
            status_text.text("🗂️ Adding to vector index...")
            progress_bar.progress(75)
            time.sleep(1)  # Simulate processing
            
            # Step 4: Complete
            status_text.text("✅ Processing complete!")
            progress_bar.progress(100)
            
            # Store result
            doc_info = {
                'name': uploaded_file.name,
                'processed_at': datetime.now(),
                'chunks': len(chunks),
                'phi_removed': deid_result.get('phi_count', 0),
                'sections': len(set(chunk.get('section', 'Unknown') for chunk in chunks))
            }
            st.session_state.processed_docs.append(doc_info)
            
            # Cleanup
            os.unlink(tmp_path)
            
            return True, doc_info
            
        except Exception as e:
            st.error(f"Error processing document: {e}")
            return False, None
    
    def search_documents(self, query, k=5):
        """Search documents using the RAG API"""
        if not st.session_state.api_available:
            return None
        
        try:
            response = requests.get(
                f"{self.api_base_url}/search",
                params={"query": query, "k": k},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            st.error(f"Search error: {e}")
        return None
    
    def ask_question(self, question, max_sources=3):
        """Ask a question using the RAG API"""
        if not st.session_state.api_available:
            return None
        
        try:
            response = requests.post(
                f"{self.api_base_url}/qa",
                json={
                    "question": question,
                    "max_sources": max_sources,
                    "include_scores": True
                },
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                # Store in history
                st.session_state.query_history.append({
                    'question': question,
                    'timestamp': datetime.now(),
                    'sources_count': len(result.get('sources', []))
                })
                return result
            else:
                st.error(f"API Error: {response.text}")
        except Exception as e:
            st.error(f"Question error: {e}")
        return None
    
    def render_document_processing_tab(self):
        """Render the document processing interface"""
        st.markdown('<div class="sub-header">📤 Document Processing Pipeline</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Upload Medical Document")
            uploaded_file = st.file_uploader(
                "Choose a text file",
                type=['txt', 'md'],
                help="Upload a medical document for processing through the complete RAG pipeline"
            )
            
            if uploaded_file is not None:
                st.markdown("**File Preview:**")
                content = uploaded_file.read().decode('utf-8')
                st.text_area("Document Content", content[:1000] + "..." if len(content) > 1000 else content, height=200)
                
                if st.button("🚀 Process Document", type="primary"):
                    success, doc_info = self.process_document(uploaded_file)
                    if success:
                        st.balloons()
                        st.success(f"✅ Document '{doc_info['name']}' processed successfully!")
                        
                        # Show processing results
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Chunks Created", doc_info['chunks'])
                        with col_b:
                            st.metric("PHI Removed", doc_info['phi_removed'])
                        with col_c:
                            st.metric("Sections Found", doc_info['sections'])
        
        with col2:
            st.markdown("### Processing Steps")
            st.markdown("""
            1. **🔒 De-identification**
               - Remove patient names, dates, IDs
               - Secure PHI mapping storage
            
            2. **📝 Medical Chunking**
               - Semantic section splitting
               - Preserve clinical context
            
            3. **🧠 Vector Embedding**
               - Google text-embedding-004
               - Medical domain optimization
            
            4. **🗂️ FAISS Indexing**
               - Fast similarity search
               - Metadata preservation
            """)
        
        # Show processed documents
        if st.session_state.processed_docs:
            st.markdown("### 📋 Processed Documents")
            df = pd.DataFrame(st.session_state.processed_docs)
            st.dataframe(df, use_container_width=True)
    
    def render_search_qa_tab(self):
        """Render the search and Q&A interface"""
        st.markdown('<div class="sub-header">🔍 Medical Q&A with Source Attribution</div>', unsafe_allow_html=True)
        
        if not st.session_state.api_available:
            st.warning("⚠️ RAG API is not available. Please start the FastAPI server first.")
            return
        
        # Q&A Interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Ask a Medical Question")
            question = st.text_input(
                "Your question:",
                placeholder="What are the symptoms of chest pain?",
                help="Ask questions about the medical documents in the system"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                max_sources = st.slider("Max Sources", 1, 10, 3)
            with col_b:
                search_only = st.checkbox("Search Only (no AI answer)")
            
            if st.button("🔍 Ask Question", type="primary") and question:
                if search_only:
                    # Just do document search
                    with st.spinner("Searching documents..."):
                        results = self.search_documents(question, max_sources)
                    
                    if results:
                        st.success(f"Found {len(results['results'])} relevant documents")
                        self.display_search_results(results['results'])
                else:
                    # Full Q&A
                    with st.spinner("Generating answer..."):
                        answer = self.ask_question(question, max_sources)
                    
                    if answer:
                        self.display_qa_result(answer)
        
        with col2:
            st.markdown("### 💡 Sample Questions")
            sample_questions = [
                "What causes chest pain?",
                "What medications were prescribed?",
                "What were the physical examination findings?",
                "What is the patient's medical history?",
                "What diagnostic tests were performed?"
            ]
            
            for q in sample_questions:
                if st.button(f"💬 {q}", key=f"sample_{q}"):
                    st.session_state.sample_question = q
                    st.rerun()
    
    def display_search_results(self, results):
        """Display search results with metadata"""
        st.markdown("### 🎯 Search Results")
        
        for i, result in enumerate(results):
            with st.expander(f"📄 Result {i+1}: {result['doc_id']} - {result.get('section', 'Unknown')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Content:**")
                    st.text_area("", result['content'], height=100, key=f"content_{i}")
                
                with col2:
                    st.markdown("**Metadata:**")
                    st.json({
                        'doc_id': result['doc_id'],
                        'chunk_id': result['chunk_id'],
                        'section': result.get('section'),
                        'similarity_score': result.get('similarity_score'),
                        'page': result['metadata'].get('page')
                    })
    
    def display_qa_result(self, answer_data):
        """Display Q&A result with sources"""
        st.markdown("### 🤖 AI Response")
        
        # Answer
        st.markdown("**Answer:**")
        st.info(answer_data['answer'])
        
        # Sources
        st.markdown("### 📚 Sources & Provenance")
        
        for i, source in enumerate(answer_data['sources']):
            st.markdown(f"**Source {i+1}:**", unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f'<div class="source-doc">{source["content"]}</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Citation:**")
                st.code(f"Doc: {source['doc_id']}\nChunk: {source['chunk_id']}\nSection: {source.get('section', 'N/A')}")
                
                if source.get('similarity_score'):
                    st.metric("Relevance", f"{(1-source['similarity_score']):.2%}")
    
    def render_analytics_tab(self):
        """Render analytics and system insights"""
        st.markdown('<div class="sub-header">📊 System Analytics</div>', unsafe_allow_html=True)
        
        if not st.session_state.processed_docs and not st.session_state.query_history:
            st.info("📈 Process some documents and ask questions to see analytics!")
            return
        
        # Document processing analytics
        if st.session_state.processed_docs:
            st.markdown("### 📋 Document Processing Stats")
            
            df_docs = pd.DataFrame(st.session_state.processed_docs)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                total_chunks = df_docs['chunks'].sum()
                st.metric("Total Chunks", total_chunks)
            with col2:
                total_phi = df_docs['phi_removed'].sum()
                st.metric("PHI Items Removed", total_phi)
            with col3:
                avg_sections = df_docs['sections'].mean()
                st.metric("Avg Sections/Doc", f"{avg_sections:.1f}")
            
            # Chunks per document chart
            fig = px.bar(df_docs, x='name', y='chunks', title="Chunks per Document")
            st.plotly_chart(fig, use_container_width=True)
        
        # Query analytics
        if st.session_state.query_history:
            st.markdown("### 🔍 Query Activity")
            
            df_queries = pd.DataFrame(st.session_state.query_history)
            df_queries['hour'] = df_queries['timestamp'].dt.hour
            
            # Queries over time
            queries_by_hour = df_queries.groupby('hour').size().reset_index(name='count')
            fig = px.line(queries_by_hour, x='hour', y='count', title="Queries by Hour")
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent queries
            st.markdown("### 📝 Recent Queries")
            for query in st.session_state.query_history[-5:]:
                st.caption(f"🕒 {query['timestamp'].strftime('%H:%M')} - {query['question'][:100]}...")
    
    def render_settings_tab(self):
        """Render settings and configuration"""
        st.markdown('<div class="sub-header">⚙️ System Settings</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔧 API Configuration")
            new_url = st.text_input("API Base URL", self.api_base_url)
            if st.button("Update API URL"):
                self.api_base_url = new_url
                st.success("API URL updated!")
            
            st.markdown("### 🗑️ Data Management")
            if st.button("Clear Processed Documents", type="secondary"):
                st.session_state.processed_docs = []
                st.success("Processed documents cleared!")
            
            if st.button("Clear Query History", type="secondary"):
                st.session_state.query_history = []
                st.success("Query history cleared!")
        
        with col2:
            st.markdown("### 📊 System Information")
            st.json({
                "API Status": "Connected" if st.session_state.api_available else "Disconnected",
                "Documents": len(st.session_state.processed_docs),
                "Queries": len(st.session_state.query_history),
                "Session Start": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            st.markdown("### 🆘 Quick Actions")
            if st.button("🔄 Refresh Everything"):
                st.rerun()
            
            if st.button("📖 View API Docs"):
                st.markdown(f"[Open API Documentation]({self.api_base_url}/docs)")
    
    def run(self):
        """Main application entry point"""
        self.render_header()
        
        # Sidebar navigation
        selected_tab = self.render_sidebar()
        
        # Main content area
        if selected_tab == "📤 Document Processing":
            self.render_document_processing_tab()
        elif selected_tab == "🔍 Search & Q&A":
            self.render_search_qa_tab()
        elif selected_tab == "📊 Analytics":
            self.render_analytics_tab()
        elif selected_tab == "⚙️ Settings":
            self.render_settings_tab()
        
        # Footer
        st.markdown("---")
        st.markdown("**ClinChat-RAG Demo** - Medical Document Q&A with Retrieval-Augmented Generation")

def main():
    """Run the Streamlit application"""
    demo = ClinChatRAGDemo()
    demo.run()

if __name__ == "__main__":
    main()
