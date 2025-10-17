# Rate Limiting Configuration

This document explains the rate limiting configuration for the VoiceFrame application and how to manage it for different environments.

## Overview

Rate limiting is implemented at the nginx level to protect the application from abuse and ensure fair usage. The configuration includes different rate limits for different types of operations.

## Rate Limiting Zones

### Production Configuration (`nginx.conf`)

- **API endpoints**: `30r/s` (30 requests per second) with `burst=50`
- **Upload endpoints**: `5r/s` (5 requests per second) with `burst=10`
- **Admin endpoints**: `50r/s` (50 requests per second) with `burst=100`

### Development Configuration (`nginx.dev.conf`)

- **API endpoints**: `100r/s` (100 requests per second) with `burst=200`
- **Upload endpoints**: `20r/s` (20 requests per second) with `burst=50`
- **Admin endpoints**: `200r/s` (200 requests per second) with `burst=500`

## Configuration Files

### Main Configuration
- `nginx.conf` - Production nginx configuration
- `nginx.dev.conf` - Development nginx configuration with relaxed limits

### Site Configurations
- `nginx-sites/vocaframe.com.conf` - Production site configuration
- `nginx-sites/dev.conf` - Development site configuration

## Switching Configurations

Use the provided script to switch between development and production configurations:

```bash
# Switch to development (relaxed rate limits)
./scripts/switch-nginx-config.sh dev

# Switch to production (standard rate limits)
./scripts/switch-nginx-config.sh prod
```

## Error Handling

### Frontend Error Display

The admin panel now includes proper error handling for 429 (Too Many Requests) errors:

- **Error Display**: Red error banner with dismissible message
- **Specific Messages**: "Too many requests. Please wait a moment and try again."
- **Auto-retry**: Some operations include automatic retry logic
- **User Guidance**: Clear instructions on what to do when rate limited

### Error Types Handled

1. **429 Rate Limiting**: Too many requests
2. **401/403 Authentication**: Invalid credentials (auto-logout)
3. **500+ Server Errors**: Server issues
4. **Network Errors**: Connection problems

## Troubleshooting

### Common Issues

1. **Admin operations failing with 429 errors**
   - **Solution**: Switch to development configuration or increase rate limits
   - **Command**: `./scripts/switch-nginx-config.sh dev`

2. **File uploads failing**
   - **Cause**: Upload rate limits too restrictive
   - **Solution**: Check upload endpoint rate limits in nginx configuration

3. **No error messages displayed**
   - **Cause**: Missing error handling in frontend
   - **Solution**: Ensure error state is properly managed in components

### Rate Limit Testing

To test rate limiting:

```bash
# Test API rate limits
for i in {1..35}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost/api/health; done

# Test admin rate limits
for i in {1..55}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost/admin/stats; done
```

Expected results:
- First requests should return `200`
- After rate limit exceeded, requests should return `429`

## Best Practices

### Development
- Use development configuration for local development
- Higher rate limits allow for rapid iteration
- Monitor logs for rate limiting issues

### Production
- Use production configuration for live deployment
- Monitor rate limiting metrics
- Adjust limits based on actual usage patterns
- Consider implementing user-specific rate limiting for authenticated users

### Monitoring
- Monitor nginx access logs for 429 responses
- Track rate limiting patterns
- Adjust limits based on legitimate usage patterns
- Consider implementing rate limiting bypass for admin users

## Configuration Examples

### Custom Rate Limits

To customize rate limits, edit the `limit_req_zone` directives in nginx configuration:

```nginx
# Example: Increase admin rate limits
limit_req_zone $binary_remote_addr zone=admin:10m rate=100r/s;

# Example: Decrease upload rate limits
limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;
```

### Bypass Rate Limiting

To bypass rate limiting for specific IPs:

```nginx
# Allow specific IPs to bypass rate limiting
geo $rate_limit_bypass {
    default 0;
    127.0.0.1 1;  # localhost
    192.168.1.0/24 1;  # local network
}

map $rate_limit_bypass $rate_limit_key {
    0 $binary_remote_addr;
    1 "";
}

limit_req_zone $rate_limit_key zone=api:10m rate=30r/s;
```

## Related Files

- `nginx.conf` - Main nginx configuration
- `nginx.dev.conf` - Development nginx configuration
- `nginx-sites/vocaframe.com.conf` - Production site configuration
- `nginx-sites/dev.conf` - Development site configuration
- `scripts/switch-nginx-config.sh` - Configuration switching script
- `src/components/AdminDashboard.tsx` - Admin panel with error handling
