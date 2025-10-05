# Nginx Multi-Site Configuration

This directory contains separate nginx configuration files for each site, allowing you to manage multiple domains with a single nginx instance.

## Structure

```
nginx-sites/
├── README.md
├── vocaframe.com.conf      # VoiceFrame application
└── quiethires.com.conf     # QuietHires application
```

## Site Configurations

### VoiceFrame (vocaframe.com)
- **Port**: 80 (HTTP)
- **Backend**: Docker container `api:8000`
- **Frontend**: Static files from `/var/www/html`
- **Features**:
  - API rate limiting
  - File upload support
  - Static file caching
  - Security headers

### QuietHires (quiethires.com)
- **Port**: 80 (HTTP) → 443 (HTTPS redirect)
- **Backend**: `localhost:6080`
- **Features**:
  - HTTPS with Let's Encrypt
  - WebSocket support
  - www → apex redirect
  - ACME challenge support

## Setup

1. **Run the setup script**:
   ```bash
   sudo ./scripts/setup-nginx-sites.sh
   ```

2. **Test the configuration**:
   ```bash
   sudo nginx -t
   ```

3. **Reload nginx**:
   ```bash
   sudo systemctl reload nginx
   ```

## Management

Use the management script to control sites:

```bash
# List all sites
./scripts/manage-nginx-sites.sh list

# Enable a site
./scripts/manage-nginx-sites.sh enable vocaframe.com

# Disable a site
./scripts/manage-nginx-sites.sh disable quiethires.com

# Test configuration
./scripts/manage-nginx-sites.sh test
```

## File Locations

- **Available sites**: `/etc/nginx/sites-available/`
- **Enabled sites**: `/etc/nginx/sites-enabled/`
- **Main config**: `/etc/nginx/nginx.conf`

## How It Works

The main `nginx.conf` includes all enabled site configurations:
```nginx
# Include site-specific configurations
include /etc/nginx/sites-enabled/*.conf;
```

Each site configuration file contains server blocks that handle routing based on the `server_name` directive.

## Adding New Sites

1. Create a new `.conf` file in `nginx-sites/`
2. Copy it to `/etc/nginx/sites-available/`
3. Enable it: `sudo ln -sf /etc/nginx/sites-available/newsite.conf /etc/nginx/sites-enabled/`
4. Test and reload nginx

## Troubleshooting

- **Check nginx status**: `sudo systemctl status nginx`
- **View nginx logs**: `sudo tail -f /var/log/nginx/error.log`
- **Test configuration**: `sudo nginx -t`
- **List enabled sites**: `ls -la /etc/nginx/sites-enabled/`
