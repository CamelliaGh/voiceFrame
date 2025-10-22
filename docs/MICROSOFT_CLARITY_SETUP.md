# Microsoft Clarity Setup Guide

This guide explains how to set up and configure Microsoft Clarity analytics for the VoiceFrame application.

## Overview

Microsoft Clarity is a free analytics tool that provides session recordings, heatmaps, and user behavior insights. It has been integrated alongside Google Analytics to provide comprehensive user behavior tracking.

## Setup Steps

### 1. Create Microsoft Clarity Account

1. Go to [Microsoft Clarity](https://clarity.microsoft.com/)
2. Sign in with your Microsoft account
3. Create a new project for VoiceFrame
4. Copy your Project ID (format: `abc123def`)

### 2. Configure Environment Variables

Add your Clarity Project ID to your environment variables:

```bash
# Add to your .env file
VITE_CLARITY_PROJECT_ID=your-clarity-project-id
```

For production deployment, ensure the environment variable is set in your hosting platform.

### 3. Verify Implementation

The Clarity tracking script is automatically loaded in `index.html` when the environment variable is present:

```html
<!-- Microsoft Clarity -->
<script type="text/javascript">
  // Only initialize if Clarity project ID is available
  if ('%VITE_CLARITY_PROJECT_ID%' && '%VITE_CLARITY_PROJECT_ID%' !== 'undefined') {
    (function(c,l,a,r,i,t,y){
      c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
      t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
      y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "%VITE_CLARITY_PROJECT_ID%");
  }
</script>
```

## Features Implemented

### 1. Automatic Page Tracking
- Page views are automatically tracked on route changes
- URL and title information is captured

### 2. Event Tracking
The following events are tracked in both Google Analytics and Microsoft Clarity:

- **File Uploads**: Photo and audio file uploads
- **Customization**: Template and design changes
- **Preview Actions**: Preview generation and interactions
- **Payment Events**: Payment initiation and completion
- **Downloads**: PDF downloads and conversions
- **Errors**: Application errors and their locations
- **User Engagement**: Various user interactions
- **Step Progression**: User flow through the application
- **Admin Actions**: Administrative actions (if applicable)

### 3. Custom Tracking Functions

Additional Clarity-specific tracking functions:

```typescript
// Track session creation
trackSessionCreate(sessionId: string)

// Track template selection
trackTemplateSelect(templateId: string)

// Track background selection
trackBackgroundSelect(backgroundId: string)

// Track consent changes
trackConsentChange(consentType: string, granted: boolean)
```

### 4. Consent Management

Clarity tracking respects user consent preferences:
- Users can opt-in/opt-out of analytics tracking
- Consent changes are tracked and logged
- Both Google Analytics and Clarity are controlled by the same consent setting

## Testing

### 1. Verify Script Loading

Check browser developer tools:
1. Open Network tab
2. Look for requests to `clarity.ms`
3. Verify the script loads without errors

### 2. Check Event Tracking

Use browser console to test:
```javascript
// Check if Clarity is loaded
console.log(typeof window.clarity);

// Test custom event
window.clarity('event', 'test_event', { test: true });
```

### 3. Verify in Clarity Dashboard

1. Visit your Clarity project dashboard
2. Check for incoming sessions
3. Verify events are being recorded
4. Review session recordings and heatmaps

## Privacy Considerations

### GDPR Compliance
- Clarity tracking is included in the analytics consent category
- Users can opt-out of analytics tracking
- Consent preferences are respected and logged

### Data Collection
- Clarity collects anonymous usage data
- No personally identifiable information is tracked
- Session recordings are anonymized

### Cookie Usage
- Clarity uses cookies for session tracking
- Cookie usage is disclosed in privacy policy
- Users can control cookie preferences

## Troubleshooting

### Common Issues

1. **Script Not Loading**
   - Verify `VITE_CLARITY_PROJECT_ID` is set correctly
   - Check for typos in the project ID
   - Ensure environment variable is available during build

2. **Events Not Tracking**
   - Verify Clarity script is loaded
   - Check browser console for JavaScript errors
   - Ensure consent is granted for analytics

3. **No Data in Dashboard**
   - Wait 24-48 hours for data to appear
   - Verify project ID matches the one in your dashboard
   - Check if ad blockers are interfering

### Debug Mode

Enable debug mode in development:
```javascript
// Add to browser console for debugging
window.clarity('set', 'debug', true);
```

## Integration with Existing Analytics

Microsoft Clarity works alongside Google Analytics:
- Both tools track the same events
- Data is collected independently
- Provides complementary insights (quantitative vs qualitative)

## Best Practices

1. **Respect User Privacy**: Always honor consent preferences
2. **Monitor Performance**: Ensure tracking doesn't impact site performance
3. **Regular Review**: Periodically review and update tracking implementation
4. **Data Retention**: Be aware of Clarity's data retention policies
5. **Testing**: Test tracking implementation in staging before production

## Support

For issues specific to Microsoft Clarity:
- [Clarity Documentation](https://docs.microsoft.com/en-us/clarity/)
- [Clarity Support](https://docs.microsoft.com/en-us/clarity/support)

For VoiceFrame-specific implementation issues:
- Check the implementation in `src/lib/clarity.ts`
- Review the integrated analytics functions in `src/lib/analytics.ts`
- Verify environment configuration
