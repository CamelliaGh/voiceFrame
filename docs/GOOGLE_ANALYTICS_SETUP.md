# Google Analytics Setup Guide

This guide explains how to set up Google Analytics 4 (GA4) for the VoiceFrame application.

## Overview

Google Analytics has been integrated into VoiceFrame to track:
- Page views and navigation
- File uploads (photos and audio)
- User interactions and step progression
- Payment events and conversions
- Error tracking
- User engagement metrics

## Setup Instructions

### 1. Create Google Analytics Property

1. Go to [Google Analytics](https://analytics.google.com/)
2. Create a new GA4 property for your website
3. Get your **Measurement ID** (format: `G-XXXXXXXXXX`)

### 2. Configure Environment Variables

Add your Google Analytics Measurement ID to your environment configuration:

#### For Development (.env file)
```bash
# Add to your .env file in the project root
VITE_GA_TRACKING_ID=G-XXXXXXXXXX
```

#### For Production
Set the environment variable in your production environment:
```bash
VITE_GA_TRACKING_ID=G-XXXXXXXXXX
```

**Important:** The `VITE_` prefix is required for Vite to include the variable in the build.

### 3. Verify Installation

1. Start your development server: `npm run dev`
2. Open your browser's developer tools
3. Go to the Network tab
4. Navigate through your app
5. Look for requests to `googletagmanager.com` and `google-analytics.com`

### 4. Test in Google Analytics

1. Go to your Google Analytics dashboard
2. Navigate to **Realtime** reports
3. Use your application and verify events appear in real-time

## Tracked Events

### Page Views
- Automatically tracked on route changes
- Includes page path and title

### File Uploads
- `file_upload` event with category `user_interaction`
- Tracks both photo and audio uploads
- Label indicates file type (`photo` or `audio`)

### Step Progression
- `step_progression` event with category `engagement`
- Tracks navigation between app steps:
  - `upload_to_customize`
  - `customize_to_preview`
  - `preview_to_payment`
  - `customize_to_upload` (back navigation)
  - `preview_to_customize` (back navigation)
  - `payment_to_preview` (back navigation)

### Payment Events
- `payment_success` event with category `payment`
- Includes transaction value
- Tracks successful payments

### Download Events
- `download` event with category `conversion`
- Tracks PDF downloads after purchase
- Label indicates format (`pdf`)

### Error Tracking
- `error` event with category `error_tracking`
- Tracks upload failures and payment errors
- Includes error message and location

### Customization Events
- Various events in category `customization`
- Tracks user customization choices

## Privacy Considerations

### GDPR Compliance
- Google Analytics is configured with standard privacy settings
- Consider implementing cookie consent if required in your jurisdiction
- Review Google's data processing terms

### Data Retention
- Configure data retention settings in Google Analytics
- Default is 26 months, can be reduced to 14 months

### IP Anonymization
- GA4 automatically anonymizes IP addresses
- No additional configuration needed

## Advanced Configuration

### Custom Events
To add custom tracking, use the analytics utilities:

```typescript
import { trackEvent, trackEngagement } from '@/lib/analytics'

// Track custom event
trackEvent('button_click', 'user_interaction', 'header_cta')

// Track engagement
trackEngagement('feature_used', 'template_selection')
```

### Enhanced Ecommerce
The payment tracking is set up for basic ecommerce. To enable enhanced ecommerce:

1. Enable Enhanced Ecommerce in GA4
2. Modify payment tracking to include product details
3. Add purchase event parameters

### Goals and Conversions
Set up goals in Google Analytics:
1. **File Upload Goal**: Track when users upload both photo and audio
2. **Payment Goal**: Track successful payments
3. **Download Goal**: Track PDF downloads

## Troubleshooting

### Analytics Not Working
1. Verify `VITE_GA_TRACKING_ID` is set correctly
2. Check browser console for errors
3. Ensure ad blockers aren't blocking analytics
4. Verify the Measurement ID format (`G-XXXXXXXXXX`)

### Events Not Appearing
1. Check real-time reports in GA4 (events may take 24-48 hours in standard reports)
2. Verify event names and parameters in browser dev tools
3. Check that gtag is loaded: `typeof window.gtag === 'function'`

### Build Warnings
If you see warnings about `%VITE_GA_TRACKING_ID%` during build:
- This is normal if the environment variable isn't set
- The app will work without analytics if the variable is missing
- Set the variable to eliminate warnings

## Files Modified

The following files were modified to add Google Analytics:

- `index.html` - Added GA4 script tags
- `src/lib/analytics.ts` - Analytics utility functions
- `src/lib/useAnalytics.ts` - React hook for page tracking
- `src/App.tsx` - Analytics initialization
- `src/components/UploadSection.tsx` - Upload event tracking
- `src/components/CustomizationPanel.tsx` - Step progression tracking
- `src/components/PreviewSection.tsx` - Navigation tracking
- `src/components/PricingSection.tsx` - Payment and download tracking
- `env.example` - Environment variable documentation

## Security Notes

- The Measurement ID is public and safe to include in client-side code
- No sensitive data is tracked
- All tracking follows Google Analytics best practices
- Consider implementing Content Security Policy (CSP) headers for additional security
