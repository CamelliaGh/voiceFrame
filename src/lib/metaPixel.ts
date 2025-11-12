type PixelParams = Record<string, any>;

declare global {
  interface Window {
    fbq?: (...args: any[]) => void;
  }
}

const isMetaPixelAvailable = (): boolean => {
  return typeof window !== 'undefined' && typeof window.fbq === 'function';
};

export const trackPixelPageView = (path?: string, title?: string): void => {
  if (!isMetaPixelAvailable()) return;

  const payload: PixelParams = {};

  if (path) {
    payload.path = path;
  }

  if (title) {
    payload.title = title;
  }

  window.fbq?.('track', 'PageView', Object.keys(payload).length ? payload : undefined);
};

export const trackPixelEvent = (event: string, params?: PixelParams): void => {
  if (!isMetaPixelAvailable()) return;

  window.fbq?.('track', event, params);
};

export const trackPixelCustomEvent = (event: string, params?: PixelParams): void => {
  if (!isMetaPixelAvailable()) return;

  window.fbq?.('trackCustom', event, params);
};

export const trackPixelConsentChange = (consentType: string, granted: boolean): void => {
  trackPixelCustomEvent('ConsentChange', {
    consent_type: consentType,
    granted,
  });
};
