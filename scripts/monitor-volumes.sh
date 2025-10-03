#!/bin/bash

# VoiceFrame Volume Monitoring Script
# Optimized for clean Docker systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DATA_DIR="/opt/voiceframe/data"
LOG_FILE="/opt/voiceframe/logs/volume-monitor.log"
ALERT_THRESHOLD=80  # Alert when disk usage exceeds 80%

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

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

# Function to check disk usage
check_disk_usage() {
    local usage=$(df /opt/voiceframe | awk 'NR==2 {print $5}' | sed 's/%//')
    echo $usage
}

# Function to get volume sizes
get_volume_sizes() {
    echo "=== Volume Size Report ==="
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
}

# Function to clean up old files
cleanup_old_files() {
    print_info "Cleaning up old files..."

    # Clean temp files older than 24 hours
    if [ -d "$DATA_DIR/temp" ]; then
        find "$DATA_DIR/temp" -type f -mtime +1 -delete 2>/dev/null || true
        print_status "Cleaned temp files older than 24 hours"
    fi

    # Clean old logs
    if [ -d "$(dirname "$LOG_FILE")" ]; then
        find "$(dirname "$LOG_FILE")" -name "*.log" -mtime +30 -delete 2>/dev/null || true
        print_status "Cleaned log files older than 30 days"
    fi

    # Clean Docker system
    docker system prune -f > /dev/null 2>&1 || true
    print_status "Cleaned Docker system"
}

# Function to check for alerts
check_alerts() {
    local disk_usage=$(check_disk_usage)

    if [ "$disk_usage" -gt "$ALERT_THRESHOLD" ]; then
        print_warning "Disk usage is at ${disk_usage}% (threshold: ${ALERT_THRESHOLD}%)"
        log_message "ALERT: Disk usage at ${disk_usage}%"

        # Send alert (you can customize this)
        echo "ALERT: Disk usage critical at ${disk_usage}%" | mail -s "VoiceFrame Disk Alert" admin@yourdomain.com 2>/dev/null || true
    else
        print_status "Disk usage is normal at ${disk_usage}%"
    fi
}

# Function to show help
show_help() {
    echo "VoiceFrame Volume Monitor"
    echo "========================"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -c, --clean    Clean up old files"
    echo "  -a, --alert    Check for alerts only"
    echo "  -w, --watch    Watch mode (refresh every 30 seconds)"
    echo "  -l, --log      Show recent log entries"
    echo ""
    echo "Examples:"
    echo "  $0              # Show current volume status"
    echo "  $0 --clean      # Clean up old files"
    echo "  $0 --watch      # Watch mode"
    echo "  $0 --log        # Show recent logs"
}

# Function to show recent logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "Recent log entries:"
        echo "=================="
        tail -20 "$LOG_FILE"
    else
        echo "No log file found: $LOG_FILE"
    fi
}

# Function to watch mode
watch_mode() {
    print_info "Starting watch mode (press Ctrl+C to stop)..."
    while true; do
        clear
        get_volume_sizes
        check_alerts
        echo ""
        echo "Refreshing in 30 seconds... (Press Ctrl+C to stop)"
        sleep 30
    done
}

# Main execution
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -c|--clean)
        cleanup_old_files
        get_volume_sizes
        ;;
    -a|--alert)
        check_alerts
        ;;
    -w|--watch)
        watch_mode
        ;;
    -l|--log)
        show_logs
        ;;
    "")
        get_volume_sizes
        check_alerts
        log_message "Volume check completed"
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
