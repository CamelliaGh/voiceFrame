#!/bin/bash

# VoiceFrame Volume Setup Script
# This script creates and manages Docker volumes with size monitoring

set -e

# Configuration
APP_DIR="/opt/voiceframe"
DATA_DIR="$APP_DIR/data"
LOG_DIR="$APP_DIR/logs"

echo "Setting up VoiceFrame volumes..."

# Create data directories
sudo mkdir -p "$DATA_DIR"/{postgres,redis,temp}
sudo mkdir -p "$LOG_DIR"

# Set proper permissions
sudo chown -R $USER:$USER "$DATA_DIR"
sudo chown -R $USER:$USER "$LOG_DIR"

# Set up log rotation for Docker volumes
sudo tee /etc/logrotate.d/voiceframe > /dev/null <<EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

# Create volume monitoring script
cat > "$APP_DIR/scripts/monitor-volumes.sh" << 'EOF'
#!/bin/bash

# Volume monitoring script
DATA_DIR="/opt/voiceframe/data"
LOG_FILE="/opt/voiceframe/logs/volume-monitor.log"

echo "$(date): Checking volume sizes..." >> "$LOG_FILE"

# Check disk usage
df -h >> "$LOG_FILE"

# Check Docker volume sizes
docker system df >> "$LOG_FILE"

# Check specific volume sizes
echo "PostgreSQL data size:" >> "$LOG_FILE"
du -sh "$DATA_DIR/postgres" >> "$LOG_FILE"

echo "Redis data size:" >> "$LOG_FILE"
du -sh "$DATA_DIR/redis" >> "$LOG_FILE"

echo "Temp files size:" >> "$LOG_FILE"
du -sh "$DATA_DIR/temp" >> "$LOG_FILE"

# Clean up old temp files (older than 24 hours)
find "$DATA_DIR/temp" -type f -mtime +1 -delete 2>/dev/null || true

echo "$(date): Volume check complete" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
EOF

chmod +x "$APP_DIR/scripts/monitor-volumes.sh"

# Set up cron job for volume monitoring
(crontab -l 2>/dev/null; echo "0 */6 * * * $APP_DIR/scripts/monitor-volumes.sh") | crontab -

echo "Volume setup complete!"
echo "Data directory: $DATA_DIR"
echo "Log directory: $LOG_DIR"
echo "Volume monitoring script: $APP_DIR/scripts/monitor-volumes.sh"
