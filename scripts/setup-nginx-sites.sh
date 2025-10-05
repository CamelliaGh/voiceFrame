#!/bin/bash

# Setup nginx sites configuration
# This script helps manage multiple sites with separate nginx configs

set -e

NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Setting up nginx sites configuration..."

# Create directories if they don't exist
sudo mkdir -p "$NGINX_SITES_AVAILABLE"
sudo mkdir -p "$NGINX_SITES_ENABLED"

# Copy site configurations
echo "Copying site configurations..."
sudo cp "$PROJECT_ROOT/nginx-sites/vocaframe.com.conf" "$NGINX_SITES_AVAILABLE/"
sudo cp "$PROJECT_ROOT/nginx-sites/quiethires.com.conf" "$NGINX_SITES_AVAILABLE/"

# Enable sites (create symlinks)
echo "Enabling sites..."
sudo ln -sf "$NGINX_SITES_AVAILABLE/vocaframe.com.conf" "$NGINX_SITES_ENABLED/"
sudo ln -sf "$NGINX_SITES_AVAILABLE/quiethires.com.conf" "$NGINX_SITES_ENABLED/"

# Remove default nginx site if it exists
if [ -f "$NGINX_SITES_ENABLED/default" ]; then
    echo "Removing default nginx site..."
    sudo rm "$NGINX_SITES_ENABLED/default"
fi

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid!"
    echo "To apply changes, run: sudo systemctl reload nginx"
else
    echo "❌ Nginx configuration has errors. Please fix them before reloading."
    exit 1
fi

echo ""
echo "Site configurations:"
echo "- vocaframe.com: Routes to VoiceFrame app (api:8000, frontend: /var/www/html)"
echo "- quiethires.com: Routes to QuietHires app (localhost:6080) with HTTPS"
echo ""
echo "To manage sites:"
echo "- Enable site: sudo ln -sf $NGINX_SITES_AVAILABLE/site.conf $NGINX_SITES_ENABLED/"
echo "- Disable site: sudo rm $NGINX_SITES_ENABLED/site.conf"
echo "- Test config: sudo nginx -t"
echo "- Reload nginx: sudo systemctl reload nginx"
