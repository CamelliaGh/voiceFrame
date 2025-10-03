#!/bin/bash

# VoiceFrame Production Deployment Script (Standalone)
# This script handles the complete deployment process without external dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/voiceframe"
DATA_DIR="$APP_DIR/data"
BACKUP_DIR="$APP_DIR/backups"
LOG_DIR="$APP_DIR/logs"

echo -e "${BLUE}🚀 VoiceFrame Production Deployment${NC}"
echo "=================================="

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please create it from env.example"
    exit 1
fi

print_info "Starting deployment process..."

# Step 1: Set up directories and volumes
print_info "Setting up directories and volumes..."

# Create data directories
mkdir -p "$DATA_DIR"/{postgres,redis,temp}
mkdir -p "$LOG_DIR"
mkdir -p "$BACKUP_DIR"

# Set proper permissions
chown -R $USER:$USER "$DATA_DIR" 2>/dev/null || true
chown -R $USER:$USER "$LOG_DIR" 2>/dev/null || true
chown -R $USER:$USER "$BACKUP_DIR" 2>/dev/null || true

print_status "Directories and volumes configured"

# Step 2: Build frontend
print_info "Building frontend..."
if command -v npm &> /dev/null; then
    npm install
    npm run build
    print_status "Frontend built successfully"
else
    print_warning "npm not found. Skipping frontend build. You'll need to build it manually."
fi

# Step 3: Build Docker images
print_info "Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache
print_status "Docker images built"

# Step 4: Start services
print_info "Starting services..."
docker-compose -f docker-compose.prod.yml up -d
print_status "Services started"

# Step 5: Wait for services to be healthy
print_info "Waiting for services to be healthy..."
sleep 30

# Check service health
print_info "Checking service health..."
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up (healthy)"; then
    print_status "Services are healthy"
else
    print_warning "Some services may not be healthy. Check logs with: docker-compose -f docker-compose.prod.yml logs"
fi

# Step 6: Run database migrations
print_info "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head
print_status "Database migrations completed"

# Step 7: Create admin user
print_info "Creating admin user..."
if docker-compose -f docker-compose.prod.yml exec -T api python scripts/create_admin_user.py; then
    print_status "Admin user created"
else
    print_warning "Failed to create admin user. You may need to create it manually."
fi

# Step 8: Create volume monitoring script
print_info "Creating volume monitoring script..."
mkdir -p scripts

cat > scripts/monitor-volumes.sh << 'EOF'
#!/bin/bash

# VoiceFrame Volume Monitoring Script
# Simple version for production use

DATA_DIR="/opt/voiceframe/data"
LOG_FILE="/opt/voiceframe/logs/volume-monitor.log"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

echo "=== VoiceFrame Volume Report ==="
echo "Timestamp: $(date)"
echo ""

# Check if data directory exists
if [ -d "$DATA_DIR" ]; then
    echo "📁 Data Directory Sizes:"
    echo "========================"
    for dir in "$DATA_DIR"/*; do
        if [ -d "$dir" ]; then
            size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            echo "  $(basename "$dir"): $size"
        fi
    done
    echo ""
else
    echo "📁 Data directory not found: $DATA_DIR"
    echo ""
fi

# Check Docker system usage
echo "🐳 Docker System Usage:"
echo "======================"
docker system df
echo ""

# Check individual container sizes
echo "📦 Container Sizes:"
echo "==================="
docker ps --format "table {{.Names}}\t{{.Size}}" 2>/dev/null || echo "No running containers"
echo ""

# Check disk usage
echo "💾 Disk Usage:"
echo "============="
df -h /opt/voiceframe 2>/dev/null || df -h /
echo ""

log_message "Volume check completed"
EOF

chmod +x scripts/monitor-volumes.sh
print_status "Volume monitoring script created"

# Step 9: Create cleanup script
print_info "Creating cleanup script..."
cat > scripts/cleanup-volumes.sh << 'EOF'
#!/bin/bash

# VoiceFrame Volume Cleanup Script
# Simple version for production use

DATA_DIR="/opt/voiceframe/data"
LOG_DIR="/opt/voiceframe/logs"

echo "VoiceFrame Volume Cleanup"
echo "========================"

# Function to show current sizes
show_sizes() {
    echo "Current volume sizes:"
    echo "===================="
    if [ -d "$DATA_DIR" ]; then
        echo "PostgreSQL data: $(du -sh "$DATA_DIR/postgres" 2>/dev/null | cut -f1 || echo 'N/A')"
        echo "Redis data: $(du -sh "$DATA_DIR/redis" 2>/dev/null | cut -f1 || echo 'N/A')"
        echo "Temp files: $(du -sh "$DATA_DIR/temp" 2>/dev/null | cut -f1 || echo 'N/A')"
        echo "Total data: $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1 || echo 'N/A')"
    else
        echo "Data directory not found"
    fi
    echo ""
}

# Function to clean temp files
clean_temp() {
    echo "Cleaning temporary files..."
    if [ -d "$DATA_DIR/temp" ]; then
        find "$DATA_DIR/temp" -type f -mtime +1 -delete 2>/dev/null || true
        echo "Temporary files cleaned."
    else
        echo "No temp directory found."
    fi
}

# Function to clean Docker system
clean_docker() {
    echo "Cleaning Docker system..."
    docker system prune -f
    echo "Docker system cleaned."
}

# Show current sizes
show_sizes

# Ask for cleanup
read -p "Do you want to clean up old files? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    clean_temp
    clean_docker
    echo ""
    show_sizes
fi

echo "Cleanup complete!"
EOF

chmod +x scripts/cleanup-volumes.sh
print_status "Cleanup script created"

# Step 10: Set up automated backups
print_info "Setting up automated backups..."
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/voiceframe/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U audioposter audioposter > "$BACKUP_DIR/db_backup_$DATE.sql"

# Backup environment file
cp .env "$BACKUP_DIR/env_backup_$DATE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "env_backup_*" -mtime +7 -delete 2>/dev/null || true

echo "Backup completed: $DATE"
EOF

chmod +x scripts/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * $APP_DIR/scripts/backup.sh") | crontab -
print_status "Automated backups configured"

# Step 11: Final health check
print_info "Running final health check..."
sleep 10

# Check if API is responding
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_status "API health check passed"
else
    print_warning "API health check failed. Check if nginx is running and configured correctly."
fi

# Display final status
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "=================================="
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo -e "${BLUE}💾 Volume Usage:${NC}"
docker system df
echo ""
echo -e "${BLUE}📁 Data Directory Usage:${NC}"
du -sh /opt/voiceframe/data/* 2>/dev/null || echo "No data directories found yet"
echo ""
echo -e "${BLUE}🔗 Access URLs:${NC}"
echo "- Application: http://localhost (or your domain)"
echo "- API Health: http://localhost/health"
echo "- API Docs: http://localhost/api/docs"
echo ""
echo -e "${BLUE}🛠️  Useful Commands:${NC}"
echo "- View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "- Check status: docker-compose -f docker-compose.prod.yml ps"
echo "- Monitor volumes: ./scripts/monitor-volumes.sh"
echo "- Run cleanup: ./scripts/cleanup-volumes.sh"
echo "- Run backup: ./scripts/backup.sh"
echo "- Restart services: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo "1. Configure your domain name in nginx.prod.conf"
echo "2. Set up SSL certificates"
echo "3. Test all functionality"
echo "4. Set up log rotation"
echo ""
print_status "Deployment script completed!"
