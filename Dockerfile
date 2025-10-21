# =============================================================================
# ClinChat-RAG Docker Image
# Multi-stage build for production-ready container with Google Gemini & Groq APIs
# =============================================================================

# Stage 1: Base Python Environment
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies and create user
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    g++ \
    gcc \
    git \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash clinchat
WORKDIR /app
RUN chown clinchat:clinchat /app

# Stage 2: Dependencies Installation
FROM base AS dependencies

# Copy requirements first for better caching
COPY requirements.minimal.txt ./requirements.txt

# Install Python dependencies and download spaCy models
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm && \
    python -m spacy download en_core_web_md

# Stage 3: Application
FROM dependencies AS application

# Switch to app user
USER clinchat

# Copy application code
COPY --chown=clinchat:clinchat . .

# Create necessary directories
RUN mkdir -p data/uploads data/processed data/chroma_db logs/audit

# Stage 4: Production
FROM application AS production

# Set production environment
ENV ENVIRONMENT=production
ENV DEBUG=false

# Expose ports
EXPOSE 8000 8002 9090

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - runs Fusion AI API
CMD ["python", "-m", "uvicorn", "api.fusion_api:app", "--host", "0.0.0.0", "--port", "8002"]

# =============================================================================
# Development Stage (override CMD for development)
# =============================================================================
FROM application AS development

ENV ENVIRONMENT=development
ENV DEBUG=true
ENV API_RELOAD=true

# Install development dependencies
RUN pip install --no-cache-dir \
    black==23.11.0 \
    flake8==6.1.0 \
    mypy==1.7.1 \
    pytest-asyncio==0.21.1 \
    pytest==7.4.3

# Development command with auto-reload
CMD ["python", "-m", "uvicorn", "api.fusion_api:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]