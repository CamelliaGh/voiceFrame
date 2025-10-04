import { useState, useEffect } from 'react'
import { X, Cookie, Settings, Check, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CookieConsentBannerProps {
  onConsentChange?: (consent: CookieConsent) => void
  showSettings?: boolean
  onSettingsClose?: () => void
}

export interface CookieConsent {
  necessary: boolean
  analytics: boolean
  marketing: boolean
  preferences: boolean
  timestamp: string
  version: string
}

const COOKIE_CONSENT_KEY = 'audioposter_cookie_consent'
const CONSENT_VERSION = '1.0'

export default function CookieConsentBanner({ onConsentChange, showSettings, onSettingsClose }: CookieConsentBannerProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  // Handle external showSettings prop
  useEffect(() => {
    if (showSettings) {
      setShowDetails(true)
      setIsVisible(true)
    }
  }, [showSettings])
  const [consent, setConsent] = useState<CookieConsent>({
    necessary: true, // Always true - required for basic functionality
    analytics: false,
    marketing: false,
    preferences: false,
    timestamp: '',
    version: CONSENT_VERSION
  })

  useEffect(() => {
    // Check if consent has been given
    const savedConsent = localStorage.getItem(COOKIE_CONSENT_KEY)
    if (!savedConsent) {
      setIsVisible(true)
    } else {
      try {
        const parsedConsent = JSON.parse(savedConsent)
        if (parsedConsent.version !== CONSENT_VERSION) {
          // Show banner if consent version is outdated
          setIsVisible(true)
        }
      } catch (error) {
        // Invalid consent data, show banner
        setIsVisible(true)
      }
    }
  }, [])

  const saveConsent = (newConsent: CookieConsent) => {
    const consentWithTimestamp = {
      ...newConsent,
      timestamp: new Date().toISOString(),
      version: CONSENT_VERSION
    }

    localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(consentWithTimestamp))
    setConsent(consentWithTimestamp)
    setIsVisible(false)
    setShowDetails(false)
    onConsentChange?.(consentWithTimestamp)
    onSettingsClose?.()

    // Send consent to backend
    sendConsentToBackend(consentWithTimestamp)
  }

  const sendConsentToBackend = async (consentData: CookieConsent) => {
    try {
      const response = await fetch('/api/gdpr/consent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          user_identifier: 'anonymous', // For anonymous users
          consent_type: 'cookies',
          consent_data: JSON.stringify({
            necessary: consentData.necessary,
            analytics: consentData.analytics,
            marketing: consentData.marketing,
            preferences: consentData.preferences,
            timestamp: consentData.timestamp,
            version: consentData.version
          })
        })
      })

      if (!response.ok) {
        console.warn('Failed to send consent to backend:', response.statusText)
      }
    } catch (error) {
      console.warn('Error sending consent to backend:', error)
    }
  }

  const handleAcceptAll = () => {
    const allConsent = {
      necessary: true,
      analytics: true,
      marketing: true,
      preferences: true,
      timestamp: new Date().toISOString(),
      version: CONSENT_VERSION
    }
    saveConsent(allConsent)
  }

  const handleAcceptNecessary = () => {
    const necessaryConsent = {
      necessary: true,
      analytics: false,
      marketing: false,
      preferences: false,
      timestamp: new Date().toISOString(),
      version: CONSENT_VERSION
    }
    saveConsent(necessaryConsent)
  }

  const handleCustomSave = () => {
    saveConsent(consent)
  }

  const updateConsent = (key: keyof CookieConsent, value: boolean) => {
    if (key === 'necessary') return // Cannot change necessary cookies
    setConsent(prev => ({ ...prev, [key]: value }))
  }

  if (!isVisible) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-lg">
      <div className="max-w-7xl mx-auto p-4 sm:p-6">
        {!showDetails ? (
          // Simple consent banner
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start space-x-3 flex-1">
              <Cookie className="w-6 h-6 text-primary-600 mt-1 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  We use cookies to enhance your experience
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  We use cookies to provide essential functionality, analyze site usage, and personalize content.
                  By continuing to use our site, you consent to our use of cookies.{' '}
                  <a
                    href="/privacy"
                    className="text-primary-600 hover:text-primary-700 underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Learn more in our Privacy Policy
                  </a>
                </p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
              <button
                onClick={() => setShowDetails(true)}
                className="btn-secondary flex items-center justify-center space-x-2"
              >
                <Settings className="w-4 h-4" />
                <span>Customize</span>
              </button>
              <button
                onClick={handleAcceptNecessary}
                className="btn-secondary"
              >
                Necessary Only
              </button>
              <button
                onClick={handleAcceptAll}
                className="btn-primary"
              >
                Accept All
              </button>
            </div>
          </div>
        ) : (
          // Detailed consent settings
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                Cookie Preferences
              </h3>
              <button
                onClick={() => {
                  setShowDetails(false)
                  onSettingsClose?.()
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Necessary Cookies */}
              <div className="flex items-start justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h4 className="font-medium text-gray-900">Necessary Cookies</h4>
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                      Always Active
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Essential cookies required for the website to function properly. These cannot be disabled.
                  </p>
                </div>
                <div className="ml-4">
                  <div className="w-12 h-6 bg-green-500 rounded-full flex items-center justify-end px-1">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                </div>
              </div>

              {/* Analytics Cookies */}
              <div className="flex items-start justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h4 className="font-medium text-gray-900">Analytics Cookies</h4>
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                      Optional
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Help us understand how visitors interact with our website by collecting anonymous information.
                  </p>
                </div>
                <div className="ml-4">
                  <button
                    onClick={() => updateConsent('analytics', !consent.analytics)}
                    className={cn(
                      "w-12 h-6 rounded-full flex items-center transition-colors duration-200",
                      consent.analytics ? "bg-primary-500 justify-end" : "bg-gray-300 justify-start"
                    )}
                  >
                    <div className="w-4 h-4 bg-white rounded-full mx-1" />
                  </button>
                </div>
              </div>

              {/* Marketing Cookies */}
              <div className="flex items-start justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h4 className="font-medium text-gray-900">Marketing Cookies</h4>
                    <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                      Optional
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Used to deliver personalized advertisements and track the effectiveness of our marketing campaigns.
                  </p>
                </div>
                <div className="ml-4">
                  <button
                    onClick={() => updateConsent('marketing', !consent.marketing)}
                    className={cn(
                      "w-12 h-6 rounded-full flex items-center transition-colors duration-200",
                      consent.marketing ? "bg-primary-500 justify-end" : "bg-gray-300 justify-start"
                    )}
                  >
                    <div className="w-4 h-4 bg-white rounded-full mx-1" />
                  </button>
                </div>
              </div>

              {/* Preferences Cookies */}
              <div className="flex items-start justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h4 className="font-medium text-gray-900">Preference Cookies</h4>
                    <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
                      Optional
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Remember your preferences and settings to provide a personalized experience.
                  </p>
                </div>
                <div className="ml-4">
                  <button
                    onClick={() => updateConsent('preferences', !consent.preferences)}
                    className={cn(
                      "w-12 h-6 rounded-full flex items-center transition-colors duration-200",
                      consent.preferences ? "bg-primary-500 justify-end" : "bg-gray-300 justify-start"
                    )}
                  >
                    <div className="w-4 h-4 bg-white rounded-full mx-1" />
                  </button>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
              <button
                onClick={handleAcceptNecessary}
                className="btn-secondary flex-1"
              >
                Accept Necessary Only
              </button>
              <button
                onClick={handleCustomSave}
                className="btn-primary flex-1"
              >
                Save Preferences
              </button>
            </div>

            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <AlertCircle className="w-4 h-4" />
              <span>
                You can change your cookie preferences at any time by clicking the cookie icon in the footer.
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
