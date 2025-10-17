#!/bin/bash

# Script to switch between development and production nginx configurations
# Usage: ./scripts/switch-nginx-config.sh [dev|prod]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default to development if no argument provided
MODE=${1:-dev}

echo "🔄 Switching nginx configuration to: $MODE"

if [ "$MODE" = "dev" ]; then
    echo "📝 Using development configuration with relaxed rate limits..."

    # Copy development nginx config
    if [ -f "$PROJECT_ROOT/nginx.dev.conf" ]; then
        cp "$PROJECT_ROOT/nginx.dev.conf" "$PROJECT_ROOT/nginx.conf"
        echo "✅ Copied nginx.dev.conf to nginx.conf"
    else
        echo "❌ nginx.dev.conf not found!"
        exit 1
    fi

    # Copy development site config
    if [ -f "$PROJECT_ROOT/nginx-sites/dev.conf" ]; then
        cp "$PROJECT_ROOT/nginx-sites/dev.conf" "$PROJECT_ROOT/nginx-sites/vocaframe.com.conf"
        echo "✅ Copied nginx-sites/dev.conf to nginx-sites/vocaframe.com.conf"
    else
        echo "❌ nginx-sites/dev.conf not found!"
        exit 1
    fi

elif [ "$MODE" = "prod" ]; then
    echo "📝 Using production configuration with standard rate limits..."

    # Restore production nginx config (assuming it's the default)
    if [ -f "$PROJECT_ROOT/nginx.prod.conf" ]; then
        cp "$PROJECT_ROOT/nginx.prod.conf" "$PROJECT_ROOT/nginx.conf"
        echo "✅ Copied nginx.prod.conf to nginx.conf"
    else
        echo "⚠️  nginx.prod.conf not found, using current nginx.conf"
    fi

    # Restore production site config (assuming it's the default)
    if [ -f "$PROJECT_ROOT/nginx-sites/prod.conf" ]; then
        cp "$PROJECT_ROOT/nginx-sites/prod.conf" "$PROJECT_ROOT/nginx-sites/vocaframe.com.conf"
        echo "✅ Copied nginx-sites/prod.conf to nginx-sites/vocaframe.com.conf"
    else
        echo "⚠️  nginx-sites/prod.conf not found, using current vocaframe.com.conf"
    fi

else
    echo "❌ Invalid mode: $MODE"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

echo ""
echo "🔧 Current rate limiting configuration:"
echo "   - API endpoints: $(grep -A1 "limit_req_zone.*api" "$PROJECT_ROOT/nginx.conf" | tail -1 | grep -o "rate=[^;]*")"
echo "   - Upload endpoints: $(grep -A1 "limit_req_zone.*upload" "$PROJECT_ROOT/nginx.conf" | tail -1 | grep -o "rate=[^;]*")"
echo "   - Admin endpoints: $(grep -A1 "limit_req_zone.*admin" "$PROJECT_ROOT/nginx.conf" | tail -1 | grep -o "rate=[^;]*")"

echo ""
echo "📋 Next steps:"
echo "   1. Restart nginx: sudo systemctl reload nginx"
echo "   2. Or if using Docker: docker-compose restart nginx"
echo "   3. Test your admin operations"

echo ""
echo "✅ Nginx configuration switched to: $MODE"
