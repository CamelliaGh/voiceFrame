#!/bin/bash

# Manage nginx sites
# Usage: ./manage-nginx-sites.sh [enable|disable|list|test] [site-name]

set -e

NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"

ACTION=${1:-list}
SITE=${2:-}

show_help() {
    echo "Usage: $0 [enable|disable|list|test] [site-name]"
    echo ""
    echo "Actions:"
    echo "  enable <site>  - Enable a site configuration"
    echo "  disable <site> - Disable a site configuration"
    echo "  list          - List all available and enabled sites"
    echo "  test          - Test nginx configuration"
    echo ""
    echo "Available sites:"
    echo "  - vocaframe.com"
    echo "  - quiethires.com"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 enable vocaframe.com"
    echo "  $0 disable quiethires.com"
    echo "  $0 test"
}

list_sites() {
    echo "=== Available Sites ==="
    if [ -d "$NGINX_SITES_AVAILABLE" ]; then
        ls -la "$NGINX_SITES_AVAILABLE"/*.conf 2>/dev/null || echo "No sites available"
    else
        echo "No sites directory found"
    fi

    echo ""
    echo "=== Enabled Sites ==="
    if [ -d "$NGINX_SITES_ENABLED" ]; then
        ls -la "$NGINX_SITES_ENABLED"/*.conf 2>/dev/null || echo "No sites enabled"
    else
        echo "No sites enabled directory found"
    fi
}

enable_site() {
    if [ -z "$SITE" ]; then
        echo "Error: Site name required"
        show_help
        exit 1
    fi

    CONFIG_FILE="$NGINX_SITES_AVAILABLE/$SITE.conf"
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: Site configuration not found: $CONFIG_FILE"
        exit 1
    fi

    echo "Enabling site: $SITE"
    sudo ln -sf "$CONFIG_FILE" "$NGINX_SITES_ENABLED/"
    echo "✅ Site $SITE enabled"
}

disable_site() {
    if [ -z "$SITE" ]; then
        echo "Error: Site name required"
        show_help
        exit 1
    fi

    ENABLED_FILE="$NGINX_SITES_ENABLED/$SITE.conf"
    if [ ! -L "$ENABLED_FILE" ]; then
        echo "Site $SITE is not enabled"
        exit 1
    fi

    echo "Disabling site: $SITE"
    sudo rm "$ENABLED_FILE"
    echo "✅ Site $SITE disabled"
}

test_config() {
    echo "Testing nginx configuration..."
    sudo nginx -t

    if [ $? -eq 0 ]; then
        echo "✅ Nginx configuration is valid!"
        echo "You can now reload nginx with: sudo systemctl reload nginx"
    else
        echo "❌ Nginx configuration has errors"
        exit 1
    fi
}

case "$ACTION" in
    enable)
        enable_site
        ;;
    disable)
        disable_site
        ;;
    list)
        list_sites
        ;;
    test)
        test_config
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Error: Unknown action '$ACTION'"
        show_help
        exit 1
        ;;
esac
