# Meta Pixel Setup Guide

This guide explains how to enable and manage the Meta (Facebook) Pixel integration for the VoiceFrame frontend.

## Overview

Meta Pixel is wired into the React app to capture:
- Page views on every route change
- Key funnel interactions such as file uploads, customization actions, previews, payments, and downloads
- Consent changes for analytics tracking

Events are dispatched alongside existing Google Analytics and Microsoft Clarity tracking through the shared analytics utility layer in `src/lib/analytics.ts`.

## Setup Instructions

### 1. Create a Meta Pixel

1. Sign in to [Meta Events Manager](https://business.facebook.com/events_manager2/list/pixel/).
2. Create a new Pixel or reuse an existing one for VoiceFrame.
3. Copy the **Pixel ID** (numeric format, e.g., `123456789012345`).

### 2. Configure Environment Variables

Add the Pixel ID to the environment so Vite can inject it at build time:

#### Development (`.env`)
```bash
# Add to your .env file at the project root
VITE_META_PIXEL_ID=123456789012345
```

#### Production
Set the same variable wherever the frontend is built or served:
```bash
VITE_META_PIXEL_ID=123456789012345
```

**Important:** The `VITE_` prefix is required for Vite to expose the variable to the client bundle.

### 3. Rebuild the Frontend

After setting the variable, rebuild the app:
```bash
npm run build
```

Deploy the updated `build/` output or the Docker image depending on your deployment workflow.

## Verifying the Integration

1. Start the development server: `npm run dev`.
2. Open the app in your browser and install the [Meta Pixel Helper](https://developers.facebook.com/docs/meta-pixel/support/pixel-helper).
3. Confirm that the helper reports a successful `PageView` event.
4. Navigate between routes and perform key actions (upload files, move between steps, preview, start payment, download) to see custom events fire.
5. In production, you can also check the Events Manager realtime dashboard for incoming events.

Network requests to look for:
- `https://connect.facebook.net/en_US/fbevents.js`
- `https://www.facebook.com/tr?id=<PIXEL_ID>&ev=PageView`

## Tracked Events

Meta Pixel is triggered from the shared analytics utilities, meaning no extra wiring is required in components beyond what already exists.

| Event Name | Trigger | Parameters |
|------------|---------|------------|
| `PageView` | Initial load and every route change | `path`, `title` |
| `file_upload` (trackCustom) | Photo or audio upload | `category`, `label` |
| `customization` (trackCustom) | Customization interactions | `category`, `label` |
| `preview` (trackCustom) | Preview-related actions | `category`, `label` |
| `payment` (trackCustom) | Payment flow actions | `category`, `value` |
| `download` (trackCustom) | Poster downloads | `category`, `label` |
| `error` (trackCustom) | Error tracking | `category`, `label` |
| `engagement` (trackCustom) | General engagement | `category`, `label` |
| `step_progression` (trackCustom) | Step navigation | `category`, `label` |
| `admin_action` (trackCustom) | Admin dashboard actions | `category`, `label` |
| `consent_change` (trackCustom) | Consent updates | `consent_type`, `granted` |

All custom events include the Google Analytics metadata (`category`, optional `label`, optional `value`) to keep analysis consistent across platforms.

## Using the Analytics Helper

To dispatch additional Pixel events, continue using the existing helpers:

```typescript
import { trackEvent, trackEngagement } from '@/lib/analytics'

trackEvent('cta_click', 'marketing', 'homepage_banner')
trackEngagement('video_play', 'hero_section')
```

These helpers now forward events to Meta Pixel, Google Analytics, and Microsoft Clarity simultaneously.

## Privacy & Compliance Notes

- The Pixel script only loads when `VITE_META_PIXEL_ID` is defined.
- A `<noscript>` fallback beacon is included to cover users without JavaScript.
- Consent changes should be dispatched through `useAnalyticsConsent` to respect user preferences.
- Review Meta’s data processing terms and ensure your consent banner reflects Meta tracking if required in your jurisdiction.

## Files Updated

- `index.html` / `build/index.html` – Conditional Meta Pixel bootstrap script and `<noscript>` fallback
- `env.example` – Documented `VITE_META_PIXEL_ID`
- `src/lib/metaPixel.ts` – New helper utilities for Meta Pixel
- `src/lib/analytics.ts` – Pixel-aware tracking wrappers

No component changes are needed because the analytics abstractions fan out events automatically.
