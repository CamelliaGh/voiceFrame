#!/bin/bash

# VoiceFrame Volume Cleanup Script
# This script helps manage Docker volume sizes

set -e

DATA_DIR="/opt/voiceframe/data"
LOG_DIR="/opt/voiceframe/logs"

echo "VoiceFrame Volume Cleanup"
echo "========================"

# Function to show current sizes
show_sizes() {
    echo "Current volume sizes:"
    echo "===================="
    echo "PostgreSQL data: $(du -sh "$DATA_DIR/postgres" 2>/dev/null | cut -f1 || echo 'N/A')"
    echo "Redis data: $(du -sh "$DATA_DIR/redis" 2>/dev/null | cut -f1 || echo 'N/A')"
    echo "Temp files: $(du -sh "$DATA_DIR/temp" 2>/dev/null | cut -f1 || echo 'N/A')"
    echo "Total data: $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1 || echo 'N/A')"
    echo ""
}

# Function to clean temp files
clean_temp() {
    echo "Cleaning temporary files..."
    find "$DATA_DIR/temp" -type f -mtime +1 -delete 2>/dev/null || true
    echo "Temporary files cleaned."
}

# Function to clean Docker system
clean_docker() {
    echo "Cleaning Docker system..."
    docker system prune -f
    docker volume prune -f
    echo "Docker system cleaned."
}

# Function to backup database
backup_db() {
    echo "Creating database backup..."
    BACKUP_FILE="$LOG_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U audioposter audioposter > "$BACKUP_FILE"
    echo "Database backed up to: $BACKUP_FILE"
}

# Function to show cleanup options
show_menu() {
    echo "Cleanup options:"
    echo "1. Show current sizes"
    echo "2. Clean temporary files"
    echo "3. Clean Docker system"
    echo "4. Backup database"
    echo "5. Full cleanup (temp + Docker)"
    echo "6. Exit"
    echo ""
    read -p "Choose an option (1-6): " choice
}

# Main menu loop
while true; do
    show_menu
    case $choice in
        1)
            show_sizes
            ;;
        2)
            clean_temp
            show_sizes
            ;;
        3)
            clean_docker
            show_sizes
            ;;
        4)
            backup_db
            ;;
        5)
            clean_temp
            clean_docker
            show_sizes
            ;;
        6)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option. Please choose 1-6."
            ;;
    esac
    echo ""
    read -p "Press Enter to continue..."
done
