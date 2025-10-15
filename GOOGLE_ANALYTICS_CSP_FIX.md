# Google Analytics CSP Fix

## Problem
Google Analytics was being blocked by Content Security Policy (CSP) with the error:
```
Refused to load the script 'https://www.googletagmanager.com/gtag/js?id=G-FY0SLNS6JW' because it violates the following Content Security Policy directive: "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://static.cloudflareinsights.com"
```

## Solution
Updated CSP configuration in three locations to allow Google Analytics:

### 1. FastAPI Security Headers Middleware
**File:** `backend/middleware/security_headers.py`

**Changes:**
- Added `https://www.googletagmanager.com` to `script-src` directive
- Added `https://www.google-analytics.com https://analytics.google.com` to `connect-src` directive

**Updated CSP for Production:**
```
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://static.cloudflareinsights.com https://www.googletagmanager.com
connect-src 'self' https://api.stripe.com https://api.sendgrid.com https://cloudflareinsights.com https://www.google-analytics.com https://analytics.google.com
```

**Updated CSP for Development:**
```
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://static.cloudflareinsights.com https://www.googletagmanager.com
connect-src 'self' http://localhost:* https://api.stripe.com https://cloudflareinsights.com https://www.google-analytics.com https://analytics.google.com
```

### 2. Nginx Site Configuration
**File:** `nginx-sites/vocaframe.com.conf`

**Changes:**
- Added `https://www.googletagmanager.com` to `script-src` directive
- Added `https://www.google-analytics.com https://analytics.google.com` to `connect-src` directive

### 3. Nginx Production Configuration
**File:** `nginx.prod.conf`

**Changes:**
- Added `https://www.googletagmanager.com` to `script-src` directive
- Added `https://www.google-analytics.com https://analytics.google.com` to `connect-src` directive

## Testing

### 1. Test File
Created `test_google_analytics_csp.html` for manual testing:
- Opens in browser to test CSP compliance
- Checks for console errors
- Tests Google Analytics functionality
- Verifies network connectivity

### 2. Manual Testing Steps
1. **Restart Services:**
   ```bash
   # Restart FastAPI backend
   docker-compose restart api

   # Restart nginx (if using nginx)
   sudo systemctl reload nginx
   ```

2. **Check Browser Console:**
   - Open browser developer tools
   - Navigate to your site
   - Check Console tab for CSP violations
   - Should see no errors related to googletagmanager.com

3. **Verify Google Analytics Loading:**
   - Open Network tab in developer tools
   - Refresh the page
   - Look for successful request to `https://www.googletagmanager.com/gtag/js?id=G-FY0SLNS6JW`
   - Should return 200 status code

4. **Test Analytics Events:**
   - Use the analytics functions in `src/lib/analytics.ts`
   - Check that events are being tracked in Google Analytics dashboard

### 3. Verification Commands
```bash
# Check if CSP headers are properly set
curl -I https://yourdomain.com | grep -i content-security-policy

# Test the test file
open test_google_analytics_csp.html
```

## Security Considerations

### What Was Added
- `https://www.googletagmanager.com` - Required for loading Google Analytics script
- `https://www.google-analytics.com` - Required for sending analytics data
- `https://analytics.google.com` - Required for Google Analytics 4 features

### Security Impact
- **Low Risk:** These are official Google domains for analytics
- **Minimal Attack Surface:** Only allows specific Google Analytics functionality
- **Standard Practice:** These domains are commonly allowed in CSP for GA

### Alternatives Considered
1. **Self-hosted Analytics:** Would require significant infrastructure changes
2. **Different Analytics Provider:** Would require code changes and data migration
3. **Disable Analytics:** Would lose valuable user insights

## Files Modified
- `backend/middleware/security_headers.py`
- `nginx-sites/vocaframe.com.conf`
- `nginx.prod.conf`

## Files Created
- `test_google_analytics_csp.html` - Test file for verification
- `GOOGLE_ANALYTICS_CSP_FIX.md` - This documentation

## Next Steps
1. Deploy changes to production
2. Monitor Google Analytics dashboard for data
3. Remove test file after verification: `rm test_google_analytics_csp.html`
4. Update any deployment documentation if needed
