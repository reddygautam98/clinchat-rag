// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// PropTypes for validation
const PropTypes = globalThis.PropTypes || {
    func: { isRequired: true },
    bool: { isRequired: true },
    object: { isRequired: true },
    string: { isRequired: true },
    array: { isRequired: true },
    number: { isRequired: true }
};

// Helper Functions
const getScoreClass = (score) => {
    if (score > 0.8) return 'high';
    if (score > 0.6) return 'medium';
    return 'low';
};

const getConnectionStatus = (isOnline) => {
    if (isOnline === null) return 'checking';
    return isOnline ? 'online' : 'offline';
};

const getConnectionText = (isOnline) => {
    if (isOnline === null) return 'Checking...';
    return isOnline ? 'Connected' : 'Disconnected';
};

// API Service
class ClinChatAPI {
    static async askQuestion(question, useHybridSearch = true) {
        try {
            const response = await fetch(`${API_BASE_URL}/qa`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question,
                    use_hybrid_search: useHybridSearch
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw new Error(`Failed to get response: ${error.message}`);
        }
    }

    static async healthCheck() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }
}

// Query Input Component
const QueryInput = ({ onSubmit, loading }) => {
    const [question, setQuestion] = React.useState('');
    const [useHybridSearch, setUseHybridSearch] = React.useState(true);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (question.trim() && !loading) {
            onSubmit(question.trim(), useHybridSearch);
        }
    };

    return (
        <div className="query-section">
            <form onSubmit={handleSubmit} className="query-form">
                <div className="input-group">
                    <label htmlFor="question" className="input-label">
                        Clinical Question
                    </label>
                    <textarea
                        id="question"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Enter your clinical question here... (e.g., 'What are the contraindications for metformin?')"
                        className="question-input"
                        rows="3"
                        disabled={loading}
                    />
                </div>

                <div className="options-group">
                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={useHybridSearch}
                            onChange={(e) => setUseHybridSearch(e.target.checked)}
                            disabled={loading}
                        />{' '}
                        Use Hybrid Search (recommended)
                    </label>
                </div>
                
                <button 
                    type="submit" 
                    className={`submit-btn ${loading ? 'loading' : ''}`}
                    disabled={loading || !question.trim()}
                >
                    {loading ? (
                        <>
                            <div className="spinner"></div>
                            Processing...
                        </>
                    ) : (
                        'Ask ClinChat'
                    )}
                </button>
            </form>
        </div>
    );
};

QueryInput.propTypes = {
    onSubmit: PropTypes.func.isRequired,
    loading: PropTypes.bool.isRequired
};

// Helper function for confidence level
const getConfidenceLevel = (confidence) => {
    if (confidence > 0.8) return 'high';
    if (confidence > 0.6) return 'medium';
    return 'low';
};

// Answer Display Component
const AnswerDisplay = ({ response, loading, error }) => {
    if (loading) {
        return (
            <div className="answer-section loading">
                <div className="loading-content">
                    <div className="spinner large"></div>
                    <p>Analyzing clinical data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="answer-section error">
                <div className="error-content">
                    <h3>⚠️ Error</h3>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    if (!response) {
        return (
            <div className="answer-section welcome">
                <div className="welcome-content">
                    <h3>🏥 Welcome to ClinChat-RAG</h3>
                    <p>Your AI-powered medical assistant. Ask any clinical question to get evidence-based answers with supporting sources.</p>
                    <div className="example-questions">
                        <h4>Example Questions:</h4>
                        <ul>
                            <li>"What are the contraindications for metformin?"</li>
                            <li>"How is acute myocardial infarction diagnosed?"</li>
                            <li>"What are the side effects of warfarin?"</li>
                        </ul>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="answer-section">
            <div className="answer-content">
                <div className="answer-header">
                    <h3>📋 Clinical Answer</h3>
                    <div className="metadata">
                        <span className="search-type">
                            {response.search_method || 'Standard Search'}
                        </span>
                        <span className="response-time">
                            {response.response_time ? `${response.response_time.toFixed(2)}s` : ''}
                        </span>
                    </div>
                </div>
                
                <div className="answer-text">
                    {response.answer}
                </div>
                
                {response.confidence && (
                    <div className="confidence-indicator">
                        <span className="confidence-label">Confidence:</span>
                        <div className={`confidence-bar confidence-${getConfidenceLevel(response.confidence)}`}>
                            <div 
                                className="confidence-fill" 
                                style={{width: `${response.confidence * 100}%`}}
                            ></div>
                        </div>
                        <span className="confidence-value">{Math.round(response.confidence * 100)}%</span>
                    </div>
                )}
            </div>
        </div>
    );
};

AnswerDisplay.propTypes = {
    response: PropTypes.object,
    loading: PropTypes.bool.isRequired,
    error: PropTypes.string
};

// Sources List Component
const SourcesList = ({ sources }) => {
    if (!sources || sources.length === 0) {
        return null;
    }

    return (
        <div className="sources-section">
            <div className="sources-header">
                <h3>📚 Supporting Sources</h3>
                <span className="sources-count">{sources.length} source{sources.length === 1 ? '' : 's'}</span>
            </div>
            
            <div className="sources-list">
                {sources.map((source, index) => (
                    <div key={`source-${source.content?.substring(0, 50) || index}`} className="source-item">
                        <div className="source-header">
                            <div className="source-info">
                                <span className="doc-id">
                                    📄 {source.doc_id || `Document ${index + 1}`}
                                </span>
                                {source.page && (
                                    <span className="page-number">
                                        Page {source.page}
                                    </span>
                                )}
                            </div>
                            
                            {source.score && (
                                <div className="relevance-score">
                                    <span className="score-label">Relevance:</span>
                                    <span className={`score-value ${getScoreClass(source.score)}`}>
                                        {Math.round(source.score * 100)}%
                                    </span>
                                </div>
                            )}
                        </div>
                        
                        <div className="source-content">
                            <div className="source-snippet">
                                {source.content || source.snippet || 'No content available'}
                            </div>
                            
                            {source.metadata && (
                                <div className="source-metadata">
                                    {source.metadata.section && (
                                        <span className="metadata-item">
                                            📍 {source.metadata.section}
                                        </span>
                                    )}
                                    {source.metadata.type && (
                                        <span className="metadata-item">
                                            🏷️ {source.metadata.type}
                                        </span>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

SourcesList.propTypes = {
    sources: PropTypes.array
};

// Main App Component
const App = () => {
    const [response, setResponse] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [isOnline, setIsOnline] = React.useState(null);

    // Check API health on mount
    React.useEffect(() => {
        const checkHealth = async () => {
            const healthy = await ClinChatAPI.healthCheck();
            setIsOnline(healthy);
        };
        
        checkHealth();
        
        // Check every 30 seconds
        const interval = setInterval(checkHealth, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleSubmit = async (question, useHybridSearch) => {
        setLoading(true);
        setError(null);
        
        try {
            const result = await ClinChatAPI.askQuestion(question, useHybridSearch);
            setResponse(result);
        } catch (err) {
            setError(err.message);
            setResponse(null);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app">
            <header className="app-header">
                <div className="header-content">
                    <h1>🏥 ClinChat-RAG</h1>
                    <p>AI-Powered Clinical Assistant</p>
                    
                    <div className="status-indicator">
                        <div className={`status-dot ${getConnectionStatus(isOnline)}`}></div>
                        <span className="status-text">
                            {getConnectionText(isOnline)}
                        </span>
                    </div>
                </div>
            </header>
            
            <main className="app-main">
                <div className="container">
                    <QueryInput onSubmit={handleSubmit} loading={loading} />
                    <AnswerDisplay response={response} loading={loading} error={error} />
                    {response?.sources && (
                        <SourcesList sources={response.sources} />
                    )}
                </div>
            </main>
            
            <footer className="app-footer">
                <p>ClinChat-RAG © 2024 | For medical education and reference only</p>
            </footer>
        </div>
    );
};

// Render App
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(App));