# 👩‍💻 ClinChat-RAG Developer Guide

## 🎯 Purpose
This guide helps developers integrate, extend, and maintain ClinChat-RAG. It covers architecture, local development, testing, API usage, and deployment considerations with security and HIPAA-conscious best practices.

## 📋 Table of Contents
- [Local Development Setup](#local-development-setup)
- [Repository Structure](#repository-structure)
- [API Integration](#api-integration)
- [Extending Knowledge Base](#extending-knowledge-base)
- [Testing and CI/CD](#testing-and-cicd)
- [Security Best Practices](#security-best-practices)
- [Debugging Tips](#debugging-tips)
- [Contribution Process](#contribution-process)

## 🧰 Local Development Setup

### Prerequisites
- Node.js >= 18
- Python >= 3.11
- Docker >= 24
- PostgreSQL >= 14 (local or Docker)
- Redis >= 7 (optional)
- Docker Compose

### Clone and Install

```powershell
# Clone repository
git clone <repo-url> clinchat-rag
cd clinchat-rag

# Install backend Python deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Install frontend deps
cd ui
npm install
```

### Run Locally (dev)

```powershell
# Start backend
cd server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend
cd ui
npm run dev

# Or use docker-compose for full stack
docker-compose -f docker-compose.dev.yml up --build
```

## 📁 Repository Structure

```
clinchat-rag/
├─ server/                # FastAPI backend
├─ ui/                    # React frontend
├─ infra/                 # Kubernetes & Helm charts
├─ docs/                  # Documentation
├─ scripts/               # Utility scripts
└─ tests/                 # Unit & integration tests
```

## 🔌 API Integration

### Authentication
- OAuth 2.0 client credentials for service-to-service calls
- JWT tokens for user sessions
- Scopes: clinical:read, clinical:write, admin:manage

### Example Request

```http
POST /v1/clinical/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "What are the contraindications for metformin?",
  "context": {"age": 65}
}
```

### SDKs and Clients
- Official Python client: `clinchat_sdk` (internal)
- TypeScript client: `@clinchat/sdk` (auto-generated)
- Use OpenAPI spec (`/docs/openapi.json`) for client generation

## 🧠 Extending Knowledge Base

### Adding New Guideline Source
1. Submit content via Content Management UI (Admin → Content → New Submission)
2. Medical review workflow triggers (medical review, QA, approval)
3. Automated ingestion and normalization into knowledge graph
4. Version control for guideline source

### Manual Ingestion (developer)
- Place JSON/CSV in `infra/knowledge_ingest/` and run ingestion script

```powershell
python infra/knowledge_ingest/ingest.py --file new_guideline.json
```

## 🧪 Testing and CI/CD

### Unit & Integration Tests
- Python: pytest
- Frontend: Jest + React Testing Library
- Integration: pytest + Testcontainers

```powershell
# Run backend tests
cd server
pytest -q

# Run frontend tests
cd ui
npm test
```

### GitHub Actions
- Workflow: `ci.yml`, `deploy.yml`
- Security gates: secret scanning, license checks, HIPAA policy lint
- PR requirements: tests pass, code review, medical approval for content changes

## 🔐 Security Best Practices
- Do NOT store PHI in development environment
- Use feature flags for risky experiments
- Enforce RBAC and MFA
- Run dependency scanners (Snyk/Trivy) in CI

## 🐞 Debugging Tips
- Backend: enable debug logs `LOG_LEVEL=debug`
- DB: watch slow queries with `pg_stat_activity`
- Frontend: dev tools & network tab

## 🤝 Contribution Process
- Fork → branch (feature/your-feature) → PR to `develop`
- Include tests and documentation
- Tag PR with `medical-review` if content changes relate to clinical guidance
- Run security checks locally

---

**Document Version**: 1.0  
**Last Updated**: October 20, 2025
