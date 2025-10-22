import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { trackPageView, trackConsentChange } from './analytics';

// Custom hook to handle Google Analytics and Microsoft Clarity initialization and page tracking
export const useAnalytics = () => {
  const location = useLocation();

  useEffect(() => {
    // Track page view on route change
    trackPageView(location.pathname + location.search);
  }, [location]);

  return null;
};

// Hook to handle consent changes for analytics
export const useAnalyticsConsent = (consentData: { analytics: boolean }) => {
  useEffect(() => {
    // Track consent changes
    trackConsentChange('analytics', consentData.analytics);
  }, [consentData.analytics]);
};
