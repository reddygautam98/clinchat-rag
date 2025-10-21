# 🐳 ClinChat-RAG Docker Deployment Guide

## Unified Database System with Google Gemini & Groq APIs

This Docker setup provides a complete containerized deployment of the ClinChat-RAG system with integrated Google Gemini API and Groq Cloud APIs sharing a unified database.

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM recommended
- Valid Google Gemini and Groq API keys

### 1. Environment Setup
```bash
# Copy environment template
cp .env.docker .env

# Edit with your actual API keys
notepad .env  # Windows
# or
nano .env     # Linux/Mac
```

### 2. Build and Run (Production)
```bash
# Start complete stack
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f clinchat-rag
```

### 3. Development Mode
```bash
# Run in development mode with auto-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Or use development profile
docker-compose --profile development up -d clinchat-dev
```

## 📋 Services Overview

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| **clinchat-rag** | 8002 | Main Fusion AI API | http://localhost:8002/health |
| **postgres** | 5432 | PostgreSQL + pgvector | Internal |
| **redis** | 6379 | Cache & Sessions | Internal |
| **chroma** | 8001 | Vector Database | http://localhost:8001/api/v1/heartbeat |
| **prometheus** | 9091 | Monitoring | http://localhost:9091 |
| **grafana** | 3000 | Dashboard | http://localhost:3000 |
| **nginx** | 80/443 | Reverse Proxy | http://localhost |

## 🔧 Configuration

### Database Options

#### SQLite (Default - Development)
```env
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/clinchat_fusion.db
```

#### PostgreSQL (Production)
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://clinchat_user:password@postgres:5432/clinchat_rag
```

### API Configuration
```env
# Google Gemini API (Required)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_MODEL=gemini-2.0-flash

# Groq Cloud API (Required)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

## 🎯 API Endpoints

### Fusion AI API (Port 8002)
- **Health Check**: `GET /health`
- **Database Health**: `GET /health/database`
- **Chat Completion**: `POST /chat/completions`
- **Analyze Document**: `POST /analyze`
- **Upload Document**: `POST /upload`
- **API Documentation**: `GET /docs`

### Example Usage
```bash
# Health check
curl http://localhost:8002/health

# Chat with Fusion AI
curl -X POST http://localhost:8002/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this clinical case for potential diagnoses",
    "strategy": "fusion"
  }'
```

## 📊 Monitoring & Observability

### Grafana Dashboard
- URL: http://localhost:3000
- Username: `admin`
- Password: Set in `GRAFANA_PASSWORD` env var
- Pre-configured dashboards for API metrics

### Prometheus Metrics
- URL: http://localhost:9091
- Monitors all services and API performance
- Custom metrics for Fusion AI performance

### Application Logs
```bash
# View all logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f clinchat-rag
docker-compose logs -f postgres
docker-compose logs -f redis
```

## 🔒 Security Features

### Network Isolation
- All services in isolated Docker network
- Only necessary ports exposed
- Internal service communication

### Data Protection
- Encrypted environment variables
- Secure database connections
- PHI redaction capabilities
- Audit logging enabled

### Access Control
- Rate limiting via Nginx
- API key authentication
- CORS protection
- Security headers

## 📁 Volume Management

### Persistent Data
```bash
# Database data
clinchat_postgres_data  # PostgreSQL data
clinchat_sqlite_data    # SQLite database
clinchat_redis_data     # Redis cache

# Application data
./data/uploads/         # Document uploads
./data/processed/       # Processed files
./logs/                 # Application logs
```

### Backup Database
```bash
# SQLite backup
docker-compose exec clinchat-rag cp /app/data/clinchat_fusion.db /app/data/backup_$(date +%Y%m%d).db

# PostgreSQL backup
docker-compose exec postgres pg_dump -U clinchat_user clinchat_rag > backup_$(date +%Y%m%d).sql
```

## 🛠️ Advanced Operations

### Scaling Services
```bash
# Scale API service
docker-compose up -d --scale clinchat-rag=3

# Update configuration
docker-compose up -d --force-recreate clinchat-rag
```

### Database Migration
```bash
# Run database migrations
docker-compose exec clinchat-rag python scripts/migrate_database.py

# Initialize with sample data
docker-compose exec clinchat-rag python scripts/test_database_integration.py
```

### Development Debugging
```bash
# Enter container for debugging
docker-compose exec clinchat-rag bash

# Check Python environment
docker-compose exec clinchat-rag python --version

# Install additional packages
docker-compose exec clinchat-rag pip install package_name
```

## 🐛 Troubleshooting

### Common Issues

#### API Keys Not Working
```bash
# Check environment variables
docker-compose exec clinchat-rag env | grep -E "(GOOGLE|GROQ)"

# Test API connectivity
docker-compose exec clinchat-rag python scripts/test_gemini_groq.py
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready -U clinchat_user

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### Port Conflicts
```bash
# Check port usage
docker-compose ps
netstat -tlnp | grep :8002

# Use alternative ports
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Service Health Checks
```bash
# Check all service health
docker-compose ps

# Individual health checks
curl http://localhost:8002/health          # API
curl http://localhost:8001/api/v1/heartbeat # Chroma
curl http://localhost:9091/-/healthy        # Prometheus
```

## 📈 Performance Tuning

### Resource Limits
```yaml
# Add to docker-compose.yml services
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      memory: 2G
```

### Optimization Tips
- Use SSD storage for database volumes
- Increase shared_buffers for PostgreSQL
- Enable Redis persistence for production
- Configure log rotation

## 🔄 Updates & Maintenance

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d --force-recreate
```

### Clean Up
```bash
# Remove unused containers/images
docker system prune -a

# Remove specific volumes (⚠️ DATA LOSS)
docker-compose down -v
docker volume rm clinchat_postgres_data
```

## 🌐 Production Deployment

### SSL/TLS Setup
1. Add SSL certificates to `./infra/ssl/`
2. Update `nginx.conf` with SSL configuration
3. Enable production profile: `--profile production`

### Environment Variables
- Use Docker Secrets for sensitive data
- Enable proper logging and monitoring
- Configure backup strategies
- Set up health monitoring alerts

## 📚 Additional Resources

- **API Documentation**: http://localhost:8002/docs
- **Redoc Documentation**: http://localhost:8002/redoc
- **Grafana Dashboards**: http://localhost:3000
- **Prometheus Metrics**: http://localhost:9091

---

## 🎉 Success!

Your ClinChat-RAG system is now running in Docker with:
- ✅ **Unified Database** connecting Google Gemini & Groq APIs
- ✅ **Complete monitoring** with Prometheus & Grafana  
- ✅ **Production-ready** with security and scaling
- ✅ **Development support** with hot reloading
- ✅ **Comprehensive logging** and audit trails

The system is ready for production use with both AI providers sharing conversation history, analytics, and performance metrics through the unified database! 🚀
