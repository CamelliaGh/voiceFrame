import { useState } from 'react'
import { Shield, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ConsentCollectionProps {
  onConsentGiven: (consent: ConsentData) => void
  onConsentDeclined: () => void
  userIdentifier?: string
}

export interface ConsentData {
  dataProcessing: boolean
  emailMarketing: boolean
  analytics: boolean
  fileStorage: boolean
  thirdPartySharing: boolean
  timestamp: string
}

export default function ConsentCollection({
  onConsentGiven,
  onConsentDeclined,
  userIdentifier
}: ConsentCollectionProps) {
  const [consent, setConsent] = useState<ConsentData>({
    dataProcessing: true, // Required for service functionality
    emailMarketing: false,
    analytics: false,
    fileStorage: true, // Required for file uploads
    thirdPartySharing: false,
    timestamp: new Date().toISOString()
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const updateConsent = (key: keyof ConsentData, value: boolean) => {
    if (key === 'dataProcessing' || key === 'fileStorage') {
      // These are required for basic functionality
      return
    }
    setConsent(prev => ({ ...prev, [key]: value }))
  }

  const handleConsentSubmit = async () => {
    setLoading(true)
    setError(null)

    try {
      // Send consent to backend
      const response = await fetch('/api/gdpr/consent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          user_identifier: userIdentifier || 'anonymous',
          consent_type: 'data_processing',
          consent_data: JSON.stringify({
            dataProcessing: consent.dataProcessing,
            emailMarketing: consent.emailMarketing,
            analytics: consent.analytics,
            fileStorage: consent.fileStorage,
            thirdPartySharing: consent.thirdPartySharing,
            timestamp: consent.timestamp,
            version: '1.0'
          })
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to save consent: ${response.statusText}`)
      }

      onConsentGiven(consent)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save consent')
    } finally {
      setLoading(false)
    }
  }

  const consentItems = [
    {
      key: 'dataProcessing' as keyof ConsentData,
      title: 'Data Processing',
      description: 'Process your personal data to provide our service',
      required: true,
      icon: Shield
    },
    {
      key: 'fileStorage' as keyof ConsentData,
      title: 'File Storage',
      description: 'Store your uploaded photos and audio files securely',
      required: true,
      icon: Shield
    },
    {
      key: 'emailMarketing' as keyof ConsentData,
      title: 'Email Marketing',
      description: 'Send you promotional emails and updates about our service',
      required: false,
      icon: Info
    },
    {
      key: 'analytics' as keyof ConsentData,
      title: 'Analytics',
      description: 'Collect anonymous usage data using Google Analytics and Microsoft Clarity to improve our service',
      required: false,
      icon: Info
    },
    {
      key: 'thirdPartySharing' as keyof ConsentData,
      title: 'Third-Party Sharing',
      description: 'Share data with trusted partners for payment processing and email delivery',
      required: false,
      icon: Info
    }
  ]

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mx-auto mb-4">
          <Shield className="w-8 h-8 text-primary-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Privacy & Consent</h2>
        <p className="text-gray-600">
          We need your consent to process your data and provide our service.
          Please review and select your preferences below.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-800">{error}</span>
        </div>
      )}

      <div className="space-y-4">
        {consentItems.map((item) => {
          const Icon = item.icon
          const isChecked = consent[item.key]
          const isRequired = item.required

          return (
            <div
              key={item.key}
              className={cn(
                "p-4 border rounded-lg transition-colors",
                isRequired
                  ? "bg-green-50 border-green-200"
                  : "bg-white border-gray-200 hover:border-gray-300"
              )}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {isRequired ? (
                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-4 h-4 text-white" />
                    </div>
                  ) : (
                    <button
                      onClick={() => updateConsent(item.key, !isChecked)}
                      className={cn(
                        "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors",
                        isChecked
                          ? "bg-primary-500 border-primary-500"
                          : "border-gray-300 hover:border-primary-400"
                      )}
                    >
                      {isChecked && <CheckCircle className="w-4 h-4 text-white" />}
                    </button>
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <Icon className="w-5 h-5 text-gray-600" />
                    <h3 className="font-medium text-gray-900">{item.title}</h3>
                    {isRequired && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                        Required
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">{item.description}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Info className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900">Your Rights</h4>
            <p className="text-sm text-blue-800 mt-1">
              You can withdraw your consent at any time by visiting our{' '}
              <a href="/privacy" className="underline hover:text-blue-900" target="_blank" rel="noopener noreferrer">
                Privacy Policy
              </a>{' '}
              or contacting us. Required consents are necessary for our service to function properly.
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 pt-4">
        <button
          onClick={onConsentDeclined}
          className="btn-secondary flex-1"
        >
          Decline & Exit
        </button>
        <button
          onClick={handleConsentSubmit}
          disabled={loading}
          className="btn-primary flex-1"
        >
          {loading ? 'Saving...' : 'Accept & Continue'}
        </button>
      </div>

      <div className="text-center text-xs text-gray-500">
        By continuing, you agree to our{' '}
        <a href="/privacy" className="text-primary-600 hover:text-primary-700 underline" target="_blank" rel="noopener noreferrer">
          Privacy Policy
        </a>{' '}
        and{' '}
        <a href="/terms" className="text-primary-600 hover:text-primary-700 underline" target="_blank" rel="noopener noreferrer">
          Terms of Service
        </a>
      </div>
    </div>
  )
}
