// Analytics utility functions for Google Analytics and Microsoft Clarity
import {
  trackClarityEvent,
  trackClarityFileUpload,
  trackClarityCustomization,
  trackClarityPreview,
  trackClarityPayment,
  trackClarityDownload,
  trackClarityError,
  trackClarityEngagement,
  trackClarityStepProgression,
  trackClarityAdminAction,
  trackClaritySessionCreate,
  trackClarityTemplateSelect,
  trackClarityBackgroundSelect,
  trackClarityConsentChange,
  isClarityAvailable
} from './clarity';

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

// Combined tracking functions for Google Analytics and Microsoft Clarity
export const trackFileUpload = (fileType: 'photo' | 'audio'): void => {
  // Google Analytics
  trackEvent('file_upload', 'user_interaction', fileType);
  // Microsoft Clarity
  trackClarityFileUpload(fileType);
};

export const trackCustomization = (action: string, value?: string): void => {
  // Google Analytics
  trackEvent(action, 'customization', value);
  // Microsoft Clarity
  trackClarityCustomization(action, value);
};

export const trackPreview = (action: string): void => {
  // Google Analytics
  trackEvent(action, 'preview', action);
  // Microsoft Clarity
  trackClarityPreview(action);
};

export const trackPayment = (action: string, value?: number): void => {
  // Google Analytics
  trackEvent(action, 'payment', action, value);
  // Microsoft Clarity
  trackClarityPayment(action, value);
};

export const trackDownload = (format: string): void => {
  // Google Analytics
  trackEvent('download', 'conversion', format);
  // Microsoft Clarity
  trackClarityDownload(format);
};

export const trackError = (error: string, location: string): void => {
  // Google Analytics
  trackEvent('error', 'error_tracking', `${location}: ${error}`);
  // Microsoft Clarity
  trackClarityError(error, location);
};

// Track user engagement
export const trackEngagement = (action: string, details?: string): void => {
  // Google Analytics
  trackEvent(action, 'engagement', details);
  // Microsoft Clarity
  trackClarityEngagement(action, details);
};

// Track step progression
export const trackStepProgression = (step: string, direction: 'forward' | 'backward'): void => {
  // Google Analytics
  trackEvent('step_progression', 'user_flow', `${step}_${direction}`);
  // Microsoft Clarity
  trackClarityStepProgression(step, direction);
};

// Track admin actions (if needed)
export const trackAdminAction = (action: string, details?: string): void => {
  // Google Analytics
  trackEvent(action, 'admin', details);
  // Microsoft Clarity
  trackClarityAdminAction(action, details);
};

// Additional Clarity-specific tracking functions
export const trackSessionCreate = (sessionId: string): void => {
  trackClaritySessionCreate(sessionId);
};

export const trackTemplateSelect = (templateId: string): void => {
  trackClarityTemplateSelect(templateId);
};

export const trackBackgroundSelect = (backgroundId: string): void => {
  trackClarityBackgroundSelect(backgroundId);
};

export const trackConsentChange = (consentType: string, granted: boolean): void => {
  trackClarityConsentChange(consentType, granted);
};
