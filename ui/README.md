# ClinChat-RAG UI

A minimal clinician-facing web interface for the ClinChat-RAG medical AI assistant.

## Features

- 🏥 **Professional Medical Interface**: Clean, clinical design optimized for healthcare professionals
- 🔍 **Intelligent Search**: Support for both standard and hybrid search modes
- 📊 **Source Attribution**: Clear display of supporting sources with relevance scores
- 💡 **Real-time Status**: Connection status monitoring and health checks
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- ⚡ **Fast & Lightweight**: Pure HTML/CSS/JS with React CDN - no build process required

## Quick Start

### 1. Start the API Server
```bash
# From the main clinchat-rag directory
cd ../
python -m uvicorn main:app --reload --port 8000
```

### 2. Serve the UI
```bash
# Option 1: Using Python's built-in server
python -m http.server 3000

# Option 2: Using Node.js (if available)
npx serve . -p 3000

# Option 3: Using any other static file server
# Just serve the current directory on any port
```

### 3. Open in Browser
Navigate to: `http://localhost:3000`

## Usage

1. **Enter Clinical Question**: Type your medical question in the text area
2. **Choose Search Mode**: 
   - ✅ Hybrid Search (recommended): Uses advanced BM25 + cross-encoder reranking
   - Standard Search: Uses vector similarity only
3. **Submit Query**: Click "Ask ClinChat" to get AI-powered answers
4. **Review Results**: 
   - View the clinical answer with confidence scoring
   - Check supporting sources with relevance scores
   - Follow document references and page numbers

## Example Questions

- "What are the contraindications for metformin?"
- "How is acute myocardial infarction diagnosed?"
- "What are the side effects of warfarin therapy?"
- "When should ACE inhibitors be discontinued?"
- "What is the recommended dosing for amoxicillin in adults?"

## API Integration

The UI connects to the ClinChat-RAG API running on `http://localhost:8000`:

- **POST /qa**: Submit questions and receive answers with sources
- **GET /health**: Check API availability and status

### Request Format
```json
{
    "question": "What are the contraindications for metformin?",
    "use_hybrid_search": true
}
```

### Response Format
```json
{
    "answer": "Metformin is contraindicated in patients with...",
    "sources": [
        {
            "doc_id": "drug_reference_123",
            "page": 45,
            "content": "Contraindications include severe renal impairment...",
            "score": 0.89
        }
    ],
    "search_method": "Hybrid Search",
    "response_time": 1.23,
    "confidence": 0.85
}
```

## File Structure

```
ui/
├── index.html          # Main HTML page
├── app.js             # React application code
├── styles.css         # Professional clinical styling
├── package.json       # Project metadata
└── README.md          # This file
```

## Browser Compatibility

- ✅ Chrome 70+
- ✅ Firefox 65+  
- ✅ Safari 12+
- ✅ Edge 79+

## Security Notes

- This is a demonstration UI for educational/testing purposes
- In production, implement proper authentication and authorization
- Consider HTTPS for sensitive medical data
- Add appropriate CORS policies for API access

## Customization

### Styling
Edit `styles.css` to customize:
- Color scheme and branding
- Typography and spacing
- Component layouts
- Responsive breakpoints

### Features  
Modify `app.js` to add:
- User authentication
- Query history
- Favorite sources
- Advanced filtering
- Export functionality

## Troubleshooting

### Connection Issues
- Ensure the API server is running on port 8000
- Check browser console for CORS or network errors
- Verify the API_BASE_URL in app.js matches your setup

### Display Issues
- Clear browser cache and reload
- Check browser compatibility
- Verify all files are served correctly

### API Errors
- Check API server logs for error details
- Verify the question format and parameters
- Ensure all required API dependencies are installed

## Development

This UI uses:
- **React 18** (via CDN)
- **Vanilla CSS** with modern features
- **Fetch API** for HTTP requests
- **ES6+** JavaScript features

No build process required - just edit and reload!