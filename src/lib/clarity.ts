// Microsoft Clarity utility functions
declare global {
  interface Window {
    clarity: (...args: any[]) => void;
  }
}

// Check if Microsoft Clarity is available
export const isClarityAvailable = (): boolean => {
  return typeof window !== 'undefined' && typeof window.clarity === 'function';
};

// Track custom events in Clarity
export const trackClarityEvent = (eventName: string, data?: Record<string, any>): void => {
  if (!isClarityAvailable()) return;

  window.clarity('event', eventName, data);
};

// Set custom tags for user identification
export const setClarityTag = (tag: string, value: string): void => {
  if (!isClarityAvailable()) return;

  window.clarity('set', tag, value);
};

// Track page views
export const trackClarityPageView = (url: string, title?: string): void => {
  if (!isClarityAvailable()) return;

  window.clarity('set', 'page', url);
  if (title) {
    window.clarity('set', 'title', title);
  }
};

// Track user interactions specific to VoiceFrame
export const trackClarityFileUpload = (fileType: 'photo' | 'audio', fileSize?: number): void => {
  trackClarityEvent('file_upload', {
    file_type: fileType,
    file_size: fileSize
  });
};

export const trackClarityCustomization = (action: string, value?: string): void => {
  trackClarityEvent('customization', {
    action: action,
    value: value
  });
};

export const trackClarityPreview = (action: string): void => {
  trackClarityEvent('preview', {
    action: action
  });
};

export const trackClarityPayment = (action: string, value?: number): void => {
  trackClarityEvent('payment', {
    action: action,
    value: value
  });
};

export const trackClarityDownload = (format: string): void => {
  trackClarityEvent('download', {
    format: format
  });
};

export const trackClarityError = (error: string, location: string): void => {
  trackClarityEvent('error', {
    error: error,
    location: location
  });
};

// Track user engagement
export const trackClarityEngagement = (action: string, details?: string): void => {
  trackClarityEvent('engagement', {
    action: action,
    details: details
  });
};

// Track step progression
export const trackClarityStepProgression = (step: string, direction: 'forward' | 'backward'): void => {
  trackClarityEvent('step_progression', {
    step: step,
    direction: direction
  });
};

// Track admin actions
export const trackClarityAdminAction = (action: string, details?: string): void => {
  trackClarityEvent('admin_action', {
    action: action,
    details: details
  });
};

// Track session creation
export const trackClaritySessionCreate = (sessionId: string): void => {
  setClarityTag('session_id', sessionId);
  trackClarityEvent('session_created', {
    session_id: sessionId
  });
};

// Track template selection
export const trackClarityTemplateSelect = (templateId: string): void => {
  trackClarityEvent('template_selected', {
    template_id: templateId
  });
};

// Track background selection
export const trackClarityBackgroundSelect = (backgroundId: string): void => {
  trackClarityEvent('background_selected', {
    background_id: backgroundId
  });
};

// Track consent changes
export const trackClarityConsentChange = (consentType: string, granted: boolean): void => {
  trackClarityEvent('consent_change', {
    consent_type: consentType,
    granted: granted
  });
};
