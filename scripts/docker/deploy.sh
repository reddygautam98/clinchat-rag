#!/bin/bash
# =============================================================================
# Docker Deployment Script for ClinChat-RAG Fusion AI System
# =============================================================================

set -e  # Exit on any error

echo "🐳 ClinChat-RAG Docker Deployment"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
PROJECT_NAME="clinchat-rag"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Setup environment file
setup_environment() {
    log_info "Setting up environment..."
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f ".env.docker" ]; then
            cp .env.docker $ENV_FILE
            log_info "Copied .env.docker to .env"
        else
            log_warning "No .env file found. Please create one with your API keys."
            return 1
        fi
    fi
    
    # Check for required API keys
    if ! grep -q "GOOGLE_API_KEY=" $ENV_FILE || ! grep -q "GROQ_API_KEY=" $ENV_FILE; then
        log_warning "Please ensure GOOGLE_API_KEY and GROQ_API_KEY are set in $ENV_FILE"
    fi
    
    log_success "Environment setup complete"
}

# Build images
build_images() {
    log_info "Building Docker images..."
    docker-compose build --no-cache
    log_success "Images built successfully"
}

# Start services
start_services() {
    local mode=$1
    log_info "Starting services in $mode mode..."
    
    if [ "$mode" = "development" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    else
        docker-compose up -d
    fi
    
    log_success "Services started"
}

# Wait for services
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"
        
        # Check main API
        if curl -f -s http://localhost:8002/health > /dev/null 2>&1; then
            log_success "Main API is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Services failed to become healthy"
            return 1
        fi
        
        sleep 10
        ((attempt++))
    done
}

# Show status
show_status() {
    log_info "Service Status:"
    echo ""
    docker-compose ps
    echo ""
    
    log_info "Available endpoints:"
    echo "- Main API: http://localhost:8002"
    echo "- API Docs: http://localhost:8002/docs"
    echo "- Health Check: http://localhost:8002/health"
    echo "- Chroma Vector DB: http://localhost:8001"
    echo "- Grafana Dashboard: http://localhost:3000"
    echo "- Prometheus: http://localhost:9091"
    echo ""
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."
    
    # Test health endpoint
    if curl -f -s http://localhost:8002/health > /dev/null; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        return 1
    fi
    
    # Test database connection
    response=$(curl -s http://localhost:8002/health/database 2>/dev/null || echo "failed")
    if [[ "$response" == *"healthy"* ]]; then
        log_success "Database connection test passed"
    else
        log_warning "Database connection test failed or not available"
    fi
    
    log_success "Deployment test completed"
}

# Run database migration
migrate_database() {
    log_info "Running database migration..."
    docker-compose exec -T clinchat-rag python scripts/migrate_database.py
    log_success "Database migration completed"
}

# Show logs
show_logs() {
    local service=$1
    if [ -n "$service" ]; then
        docker-compose logs -f "$service"
    else
        docker-compose logs -f
    fi
}

# Cleanup
cleanup() {
    log_info "Cleaning up..."
    docker-compose down
    docker system prune -f
    log_success "Cleanup completed"
}

# Main script logic
case "${1:-help}" in
    "start")
        check_prerequisites
        setup_environment
        build_images
        start_services "production"
        wait_for_services
        migrate_database
        test_deployment
        show_status
        log_success "🚀 ClinChat-RAG Fusion AI deployment complete!"
        ;;
    
    "dev")
        check_prerequisites
        setup_environment
        build_images
        start_services "development"
        wait_for_services
        migrate_database
        show_status
        log_success "🚀 ClinChat-RAG development environment ready!"
        ;;
    
    "stop")
        log_info "Stopping services..."
        docker-compose down
        log_success "Services stopped"
        ;;
    
    "restart")
        log_info "Restarting services..."
        docker-compose restart
        wait_for_services
        log_success "Services restarted"
        ;;
    
    "logs")
        show_logs "${2}"
        ;;
    
    "status")
        show_status
        ;;
    
    "test")
        test_deployment
        ;;
    
    "migrate")
        migrate_database
        ;;
    
    "clean")
        cleanup
        ;;
    
    "help"|*)
        echo "ClinChat-RAG Docker Management Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start     - Deploy production environment"
        echo "  dev       - Start development environment"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  logs      - Show logs (optionally specify service)"
        echo "  status    - Show service status"
        echo "  test      - Test deployment"
        echo "  migrate   - Run database migration"
        echo "  clean     - Clean up containers and images"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start              # Deploy production"
        echo "  $0 dev                # Start development"
        echo "  $0 logs clinchat-rag  # Show specific service logs"
        ;;
esac