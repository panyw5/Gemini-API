#!/bin/bash

# Gemini API Server Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Setup environment file
setup_environment() {
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        
        print_warning "Please edit .env file with your Google cookies:"
        print_warning "1. Go to https://gemini.google.com and login"
        print_warning "2. Press F12, go to Network tab, refresh page"
        print_warning "3. Copy __Secure-1PSID and __Secure-1PSIDTS cookie values"
        print_warning "4. Edit .env file with these values"
        
        echo
        read -p "Press Enter after you've updated the .env file..."
    else
        print_status ".env file already exists"
    fi
    
    # Check if required environment variables are set
    source .env
    if [ -z "$SECURE_1PSID" ] || [ "$SECURE_1PSID" = "your_secure_1psid_cookie_value_here" ]; then
        print_error "SECURE_1PSID is not set in .env file"
        print_error "Please edit .env file with your actual Google cookie values"
        exit 1
    fi
    
    print_success "Environment configuration is ready"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p gemini_cookies
    mkdir -p logs
    
    print_success "Directories created"
}

# Build and start services
start_services() {
    print_status "Building and starting Gemini API server..."
    
    # Stop any existing containers
    docker-compose down 2>/dev/null || true
    
    # Build and start
    docker-compose up -d --build
    
    print_success "Services started"
}

# Wait for service to be ready
wait_for_service() {
    print_status "Waiting for service to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:50014/health >/dev/null 2>&1; then
            print_success "Service is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Service failed to start within expected time"
    print_error "Check logs with: docker-compose logs -f"
    return 1
}

# Show service information
show_info() {
    echo
    echo "🎉 Gemini API Server is running!"
    echo
    echo "📍 Service Information:"
    echo "   - API Base URL: http://localhost:50014"
    echo "   - Models endpoint: http://localhost:50014/v1/models"
    echo "   - Chat completions: http://localhost:50014/v1/chat/completions"
    echo "   - Health check: http://localhost:50014/health"
    echo
    echo "🔧 Management Commands:"
    echo "   - View logs: docker-compose logs -f"
    echo "   - Stop service: docker-compose down"
    echo "   - Restart service: docker-compose restart"
    echo "   - Test API: python test_api.py"
    echo
    echo "📚 Usage Examples:"
    echo "   # List models"
    echo "   curl http://localhost:50014/v1/models"
    echo
    echo "   # Chat completion"
    echo "   curl -X POST http://localhost:50014/v1/chat/completions \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"model\": \"gemini-2.5-flash\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}'"
    echo
}

# Run tests
run_tests() {
    if [ "$1" = "--test" ]; then
        print_status "Running API tests..."
        python test_api.py
    fi
}

# Main function
main() {
    echo "🚀 Gemini API Server Setup"
    echo "=========================="
    echo
    
    check_prerequisites
    setup_environment
    create_directories
    start_services
    
    if wait_for_service; then
        show_info
        run_tests "$1"
    else
        print_error "Failed to start service"
        echo
        echo "Troubleshooting:"
        echo "1. Check logs: docker-compose logs -f"
        echo "2. Verify .env file has correct cookie values"
        echo "3. Make sure port 50014 is not in use"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--test] [--help]"
        echo
        echo "Options:"
        echo "  --test    Run API tests after starting the service"
        echo "  --help    Show this help message"
        exit 0
        ;;
    *)
        main "$1"
        ;;
esac
