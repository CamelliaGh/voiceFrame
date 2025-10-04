#!/bin/bash

# VoiceFrame MVP Deployment Script
# Simplified deployment for MVP testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 VoiceFrame MVP Deployment${NC}"
echo "============================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please create it from env.example"
    exit 1
fi

print_info "Starting MVP deployment..."

# Step 1: Build frontend
print_info "Building frontend..."
if command -v npm &> /dev/null; then
    npm install
    npm run build
    print_status "Frontend built successfully"
else
    print_warning "npm not found. Please install Node.js first."
    exit 1
fi

# Step 2: Build Docker images
print_info "Building Docker images..."
docker-compose -f docker-compose.mvp.yml build
print_status "Docker images built"

# Step 3: Start services
print_info "Starting services..."
docker-compose -f docker-compose.mvp.yml up -d
print_status "Services started"

# Step 4: Wait for services to be healthy
print_info "Waiting for services to be healthy..."
sleep 30

# Step 5: Run database migrations
print_info "Running database migrations..."
docker-compose -f docker-compose.mvp.yml exec -T api alembic upgrade head
print_status "Database migrations completed"

# Step 6: Create admin user
print_info "Creating admin user..."
if docker-compose -f docker-compose.mvp.yml exec -T api python scripts/create_admin_user.py; then
    print_status "Admin user created"
else
    print_warning "Failed to create admin user. You may need to create it manually."
fi

# Step 7: Final health check
print_info "Running final health check..."
sleep 10

# Check if API is responding
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_status "API health check passed"
else
    print_warning "API health check failed. Check logs with: docker-compose -f docker-compose.mvp.yml logs"
fi

# Display final status
echo ""
echo -e "${GREEN}🎉 MVP Deployment completed!${NC}"
echo "============================="
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker-compose -f docker-compose.mvp.yml ps
echo ""
echo -e "${BLUE}🔗 Access URLs:${NC}"
echo "- Application: http://your-server-ip"
echo "- API Health: http://your-server-ip/health"
echo "- API Docs: http://your-server-ip/api/docs"
echo ""
echo -e "${BLUE}🛠️  Useful Commands:${NC}"
echo "- View logs: docker-compose -f docker-compose.mvp.yml logs -f"
echo "- Check status: docker-compose -f docker-compose.mvp.yml ps"
echo "- Restart services: docker-compose -f docker-compose.mvp.yml restart"
echo "- Stop services: docker-compose -f docker-compose.mvp.yml down"
echo ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo "1. Test the application functionality"
echo "2. Configure your domain name (optional)"
echo "3. Set up SSL certificates (optional)"
echo "4. Monitor system resources"
echo ""
print_status "MVP deployment completed!"
