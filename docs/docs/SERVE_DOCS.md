# 📚 Serve ClinChat-RAG Documentation Locally

This script sets up and serves the ClinChat-RAG documentation using MkDocs Material theme.

## Prerequisites
- Python 3.8+ 
- pip

## Quick Start

```powershell
# Navigate to docs directory
cd docs

# Install MkDocs and dependencies
pip install -r requirements.txt

# Serve documentation locally
mkdocs serve

# Open browser to http://127.0.0.1:8000
```

## Build Static Site

```powershell
# Build static HTML files
mkdocs build

# Output will be in site/ directory
# Deploy site/ directory to web server
```

## Development

```powershell
# Live reload during development
mkdocs serve --dev-addr=127.0.0.1:8000

# Strict mode (warnings as errors)
mkdocs serve --strict
```

## Configuration

The documentation is configured via `mkdocs.yml`:
- **Theme**: Material Design
- **Features**: Navigation tabs, search, code highlighting
- **Extensions**: Admonitions, code blocks, diagrams
- **Plugins**: Search, minification

## Content Structure

- `index.md` - Landing page with role-based navigation
- `user-guides/` - User documentation by role
- `api/` - API reference documentation  
- `architecture/` - Technical architecture docs
- `deployment/` - Production deployment guides
- `medical-compliance/` - HIPAA and regulatory compliance

## Customization

Edit `mkdocs.yml` to customize:
- Site metadata and URLs
- Theme colors and features
- Navigation structure
- Plugin configuration

---

**Documentation Version**: 1.0  
**Last Updated**: October 20, 2025