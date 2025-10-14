// Google Analytics utility functions
declare global {
  interface Window {
    gtag: (...args: any[]) => void;
  }
}

// Check if Google Analytics is available
export const isGAAvailable = (): boolean => {
  return typeof window !== 'undefined' && typeof window.gtag === 'function';
};

// Track page views
export const trackPageView = (url: string, title?: string): void => {
  if (!isGAAvailable()) return;

  window.gtag('config', import.meta.env.VITE_GA_TRACKING_ID, {
    page_path: url,
    page_title: title || document.title,
  });
};

// Track custom events
export const trackEvent = (
  action: string,
  category: string,
  label?: string,
  value?: number
): void => {
  if (!isGAAvailable()) return;

  window.gtag('event', action, {
    event_category: category,
    event_label: label,
    value: value,
  });
};

// Specific event tracking functions for VoiceFrame
export const trackFileUpload = (fileType: 'photo' | 'audio'): void => {
  trackEvent('file_upload', 'user_interaction', fileType);
};

export const trackCustomization = (action: string, value?: string): void => {
  trackEvent(action, 'customization', value);
};

export const trackPreview = (action: string): void => {
  trackEvent(action, 'preview', action);
};

export const trackPayment = (action: string, value?: number): void => {
  trackEvent(action, 'payment', action, value);
};

export const trackDownload = (format: string): void => {
  trackEvent('download', 'conversion', format);
};

export const trackError = (error: string, location: string): void => {
  trackEvent('error', 'error_tracking', `${location}: ${error}`);
};

// Track user engagement
export const trackEngagement = (action: string, details?: string): void => {
  trackEvent(action, 'engagement', details);
};

// Track step progression
export const trackStepProgression = (step: string, direction: 'forward' | 'backward'): void => {
  trackEvent('step_progression', 'user_flow', `${step}_${direction}`);
};

// Track admin actions (if needed)
export const trackAdminAction = (action: string, details?: string): void => {
  trackEvent(action, 'admin', details);
};
