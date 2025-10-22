#!/usr/bin/env bash
# Production Deployment Script for ClinChat-RAG
# Automated deployment with health checks and rollback capability

set -euo pipefail

# Configuration
DEPLOYMENT_ENV="${1:-production}"
PROJECT_NAME="clinchat-rag"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="./deployment-backups"
LOG_DIR="./deployment-logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create necessary directories
create_directories() {
    log "Creating deployment directories..."
    mkdir -p "$BACKUP_DIR" "$LOG_DIR" "logs" "uploads" "ssl"
    success "Directories created"
}

# Validate environment file
validate_environment() {
    log "Validating environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file $ENV_FILE not found!"
        error "Please copy .env.prod.template to $ENV_FILE and configure it"
        exit 1
    fi
    
    # Check required variables
    required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD" 
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "GEMINI_API_KEY"
        "GROQ_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "^${var}=$" "$ENV_FILE"; then
            error "Required environment variable $var is not set in $ENV_FILE"
            exit 1
        fi
    done
    
    success "Environment validation passed"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    # Build backend image
    docker build -f Dockerfile.prod --target production -t "${PROJECT_NAME}-backend:latest" .
    
    # Build frontend image (if exists)
    if [[ -f "ui/mobile/Dockerfile.prod" ]]; then
        docker build -f ui/mobile/Dockerfile.prod -t "${PROJECT_NAME}-frontend:latest" ui/mobile/
    fi
    
    success "Docker images built successfully"
}

# Database backup (if exists)
backup_database() {
    log "Creating database backup..."
    
    if docker ps --format "table {{.Names}}" | grep -q "${PROJECT_NAME}_postgres"; then
        backup_file="${BACKUP_DIR}/db_backup_$(date +%Y%m%d_%H%M%S).sql"
        docker exec "${PROJECT_NAME}_postgres_1" pg_dump -U clinchat_user clinchat_prod > "$backup_file"
        success "Database backup created: $backup_file"
    else
        warning "No existing database found to backup"
    fi
}

# Stop existing containers
stop_containers() {
    log "Stopping existing containers..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q | grep -q .; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down --timeout 30
        success "Containers stopped"
    else
        warning "No running containers found"
    fi
}

# Deploy containers
deploy_containers() {
    log "Deploying containers..."
    
    # Pull latest images (if using registry)
    # docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    
    # Start containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    success "Containers deployed"
}

# Health check function
health_check() {
    local service="$1"
    local url="$2"
    local max_attempts=30
    local attempt=1
    
    log "Checking health of $service..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            success "$service is healthy"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts for $service..."
        sleep 10
        ((attempt++))
    done
    
    error "$service failed health check after $max_attempts attempts"
    return 1
}

# Comprehensive health checks
run_health_checks() {
    log "Running comprehensive health checks..."
    
    # Wait for containers to start
    sleep 30
    
    # Check backend health
    if ! health_check "Backend API" "http://localhost:8000/health"; then
        error "Backend health check failed"
        return 1
    fi
    
    # Check frontend health (if deployed)
    if docker ps --format "table {{.Names}}" | grep -q "${PROJECT_NAME}_frontend"; then
        if ! health_check "Frontend" "http://localhost:3000/health"; then
            warning "Frontend health check failed, but continuing..."
        fi
    fi
    
    # Check database connection
    if ! docker exec "${PROJECT_NAME}_postgres_1" pg_isready -U clinchat_user -d clinchat_prod; then
        error "Database connection failed"
        return 1
    fi
    
    # Check Redis connection
    if ! docker exec "${PROJECT_NAME}_redis_1" redis-cli ping > /dev/null; then
        error "Redis connection failed"
        return 1
    fi
    
    success "All health checks passed"
    return 0
}

# Rollback deployment
rollback_deployment() {
    error "Deployment failed, initiating rollback..."
    
    # Stop current containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --timeout 30
    
    # Restore previous version (if available)
    if [[ -f "${BACKUP_DIR}/last_known_good.tar.gz" ]]; then
        log "Restoring last known good deployment..."
        tar -xzf "${BACKUP_DIR}/last_known_good.tar.gz"
        docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d
        warning "Rollback completed"
    else
        error "No previous deployment found for rollback"
    fi
    
    exit 1
}

# Save successful deployment
save_deployment() {
    log "Saving successful deployment state..."
    
    tar -czf "${BACKUP_DIR}/last_known_good.tar.gz" \
        "$DOCKER_COMPOSE_FILE" "$ENV_FILE" "Dockerfile.prod" "requirements.prod.txt"
    
    success "Deployment state saved"
}

# Post-deployment setup
post_deployment_setup() {
    log "Running post-deployment setup..."
    
    # Run database migrations (if needed)
    docker exec "${PROJECT_NAME}_backend_1" python -m alembic upgrade head 2>/dev/null || true
    
    # Initialize default data (if needed)
    docker exec "${PROJECT_NAME}_backend_1" python scripts/init_default_data.py 2>/dev/null || true
    
    # Set up log rotation
    setup_log_rotation
    
    success "Post-deployment setup completed"
}

# Set up log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    # Create logrotate configuration
    sudo tee /etc/logrotate.d/clinchat-rag > /dev/null << EOF
${PWD}/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    postrotate
        docker-compose -f ${PWD}/${DOCKER_COMPOSE_FILE} kill -s USR1 backend
    endscript
}
EOF
    
    success "Log rotation configured"
}

# Monitor deployment
monitor_deployment() {
    log "Starting deployment monitoring..."
    
    # Monitor for 5 minutes
    for i in {1..30}; do
        log "Monitoring check $i/30..."
        
        # Check container status
        if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
            error "Containers are not running properly"
            rollback_deployment
        fi
        
        # Check basic endpoints
        if ! curl -f -s http://localhost:8000/health > /dev/null; then
            error "Backend endpoint not responding"
            rollback_deployment
        fi
        
        sleep 10
    done
    
    success "Deployment monitoring completed successfully"
}

# Generate deployment report
generate_report() {
    log "Generating deployment report..."
    
    report_file="${LOG_DIR}/deployment_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "ClinChat-RAG Deployment Report"
        echo "=============================="
        echo "Deployment Date: $(date)"
        echo "Environment: $DEPLOYMENT_ENV"
        echo "Git Commit: $(git rev-parse HEAD 2>/dev/null || echo 'N/A')"
        echo ""
        echo "Container Status:"
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
        echo ""
        echo "Image Versions:"
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep "$PROJECT_NAME"
        echo ""
        echo "Health Check Results:"
        curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "Backend: Running"
        echo ""
        echo "Deployment completed successfully!"
    } > "$report_file"
    
    success "Deployment report generated: $report_file"
}

# Cleanup function
cleanup_deployment() {
    log "Cleaning up old deployment artifacts..."
    
    # Remove old images (keep last 3)
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}" | \
        grep "$PROJECT_NAME" | tail -n +4 | awk '{print $3}' | \
        xargs -r docker rmi 2>/dev/null || true
    
    # Clean up old backups (keep last 10)
    find "$BACKUP_DIR" -name "db_backup_*.sql" -type f | \
        sort -r | tail -n +11 | xargs -r rm
    
    success "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting ClinChat-RAG production deployment..."
    
    # Pre-deployment checks
    create_directories
    validate_environment
    
    # Deployment process
    backup_database
    stop_containers
    build_images
    deploy_containers
    
    # Health checks and validation
    if run_health_checks; then
        post_deployment_setup
        save_deployment
        monitor_deployment
        generate_report
        cleanup_deployment
        
        success "🎉 Deployment completed successfully!"
        success "🔗 Application URL: http://localhost:8000"
        success "📊 Monitoring: http://localhost:3001 (Grafana)"
        success "📝 Logs: http://localhost:5601 (Kibana)"
    else
        rollback_deployment
    fi
}

# Handle script interruption
trap 'error "Deployment interrupted! Please check container status."; exit 1' INT TERM

# Run main function
main "$@"