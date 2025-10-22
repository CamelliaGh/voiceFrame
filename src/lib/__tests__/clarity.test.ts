import { vi } from 'vitest';
import {
  isClarityAvailable,
  trackClarityEvent,
  trackClarityFileUpload,
  trackClarityCustomization,
  trackClarityPayment,
  trackClarityDownload,
  trackClarityError,
  trackClarityEngagement,
  trackClaritySessionCreate,
  trackClarityTemplateSelect,
  trackClarityBackgroundSelect,
  trackClarityConsentChange
} from '../clarity';

// Mock window object
const mockClarity = vi.fn();
const mockWindow = {
  clarity: mockClarity
};

// Mock global window
Object.defineProperty(window, 'window', {
  value: mockWindow,
  writable: true
});

describe('Microsoft Clarity Analytics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset window.clarity
    (window as any).clarity = mockClarity;
  });

  describe('isClarityAvailable', () => {
    it('should return true when clarity is available', () => {
      expect(isClarityAvailable()).toBe(true);
    });

    it('should return false when clarity is not available', () => {
      (window as any).clarity = undefined;
      expect(isClarityAvailable()).toBe(false);
    });

    it('should return false when window is undefined', () => {
      const originalWindow = window;
      delete (global as any).window;
      expect(isClarityAvailable()).toBe(false);
      (global as any).window = originalWindow;
    });
  });

  describe('trackClarityEvent', () => {
    it('should call clarity event when available', () => {
      trackClarityEvent('test_event', { test: true });
      expect(mockClarity).toHaveBeenCalledWith('event', 'test_event', { test: true });
    });

    it('should not call clarity when not available', () => {
      (window as any).clarity = undefined;
      trackClarityEvent('test_event', { test: true });
      expect(mockClarity).not.toHaveBeenCalled();
    });
  });

  describe('trackClarityFileUpload', () => {
    it('should track photo upload', () => {
      trackClarityFileUpload('photo');
      expect(mockClarity).toHaveBeenCalledWith('event', 'file_upload', {
        file_type: 'photo',
        file_size: undefined
      });
    });

    it('should track audio upload with size', () => {
      trackClarityFileUpload('audio', 1024000);
      expect(mockClarity).toHaveBeenCalledWith('event', 'file_upload', {
        file_type: 'audio',
        file_size: 1024000
      });
    });
  });

  describe('trackClarityCustomization', () => {
    it('should track customization action', () => {
      trackClarityCustomization('template_change', 'modern');
      expect(mockClarity).toHaveBeenCalledWith('event', 'customization', {
        action: 'template_change',
        value: 'modern'
      });
    });
  });

  describe('trackClarityPayment', () => {
    it('should track payment action', () => {
      trackClarityPayment('payment_initiated', 499);
      expect(mockClarity).toHaveBeenCalledWith('event', 'payment', {
        action: 'payment_initiated',
        value: 499
      });
    });
  });

  describe('trackClarityDownload', () => {
    it('should track download format', () => {
      trackClarityDownload('PDF');
      expect(mockClarity).toHaveBeenCalledWith('event', 'download', {
        format: 'PDF'
      });
    });
  });

  describe('trackClarityError', () => {
    it('should track error with location', () => {
      trackClarityError('Upload failed', 'UploadSection');
      expect(mockClarity).toHaveBeenCalledWith('event', 'error', {
        error: 'Upload failed',
        location: 'UploadSection'
      });
    });
  });

  describe('trackClarityEngagement', () => {
    it('should track engagement action', () => {
      trackClarityEngagement('button_click', 'preview_button');
      expect(mockClarity).toHaveBeenCalledWith('event', 'engagement', {
        action: 'button_click',
        details: 'preview_button'
      });
    });
  });

  describe('trackClaritySessionCreate', () => {
    it('should set session tag and track session creation', () => {
      trackClaritySessionCreate('session-123');
      expect(mockClarity).toHaveBeenCalledWith('set', 'session_id', 'session-123');
      expect(mockClarity).toHaveBeenCalledWith('event', 'session_created', {
        session_id: 'session-123'
      });
    });
  });

  describe('trackClarityTemplateSelect', () => {
    it('should track template selection', () => {
      trackClarityTemplateSelect('modern_template');
      expect(mockClarity).toHaveBeenCalledWith('event', 'template_selected', {
        template_id: 'modern_template'
      });
    });
  });

  describe('trackClarityBackgroundSelect', () => {
    it('should track background selection', () => {
      trackClarityBackgroundSelect('background_1');
      expect(mockClarity).toHaveBeenCalledWith('event', 'background_selected', {
        background_id: 'background_1'
      });
    });
  });

  describe('trackClarityConsentChange', () => {
    it('should track consent granted', () => {
      trackClarityConsentChange('analytics', true);
      expect(mockClarity).toHaveBeenCalledWith('event', 'consent_change', {
        consent_type: 'analytics',
        granted: true
      });
    });

    it('should track consent denied', () => {
      trackClarityConsentChange('analytics', false);
      expect(mockClarity).toHaveBeenCalledWith('event', 'consent_change', {
        consent_type: 'analytics',
        granted: false
      });
    });
  });
});
