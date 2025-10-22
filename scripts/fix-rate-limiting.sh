#!/bin/bash

# Fix Rate Limiting Script
# This script updates nginx configuration to fix 429 errors

echo "🔧 Fixing rate limiting configuration..."

# Check if we're on the production server
if [ ! -f "/etc/nginx/sites-available/vocaframe.com.conf" ]; then
    echo "❌ This script should be run on the production server"
    echo "   Please copy the updated nginx.prod.conf to your server"
    exit 1
fi

# Backup current nginx config
echo "📦 Creating backup of current nginx configuration..."
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)

# Update nginx configuration with more permissive rate limiting
echo "⚙️  Updating nginx configuration..."

# Update the main nginx.conf file
sudo tee /etc/nginx/nginx.conf > /dev/null << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/javascript application/xml+rss
               application/json application/xml;

    # Rate limiting - More permissive for normal usage
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=5r/s;
    limit_req_zone $binary_remote_addr zone=admin:10m rate=50r/s;

    # WebSocket support mapping
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    # Include site-specific configurations
    include /etc/nginx/sites-enabled/*.conf;
}
EOF

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"

    # Reload nginx
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx

    if [ $? -eq 0 ]; then
        echo "✅ Nginx reloaded successfully"
        echo ""
        echo "🎉 Rate limiting has been fixed!"
        echo "   - API rate limit: 30 requests/second (was 10)"
        echo "   - Upload rate limit: 5 requests/second (was 2)"
        echo "   - Admin rate limit: 50 requests/second (new)"
        echo ""
        echo "📊 New rate limits:"
        echo "   - General API: 30 req/s with 50 burst"
        echo "   - Uploads: 5 req/s with 10 burst"
        echo "   - Admin: 50 req/s with 100 burst"
        echo ""
        echo "🌐 Try accessing your site now!"
    else
        echo "❌ Failed to reload nginx"
        exit 1
    fi
else
    echo "❌ Nginx configuration test failed"
    echo "   Restoring backup..."
    sudo cp /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S) /etc/nginx/nginx.conf
    exit 1
fi

echo ""
echo "🔍 To monitor rate limiting, check nginx logs:"
echo "   sudo tail -f /var/log/nginx/access.log | grep 429"
