import React, { useState, useEffect } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { Elements } from '@stripe/react-stripe-js'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import UploadSection from './components/UploadSection'
import CustomizationPanel from './components/CustomizationPanel'
import PreviewSection from './components/PreviewSection'
import PricingSection from './components/PricingSection'
import AdminDashboard from './components/AdminDashboard'
import { SessionProvider } from './contexts/SessionContext'
import { cn } from './lib/utils'

// Initialize Stripe - replace with your publishable key
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || 'pk_test_...')

function MainApp() {
  const [currentStep, setCurrentStep] = useState<'upload' | 'customize' | 'preview' | 'payment'>('upload')
  const [hasPhotos, setHasPhotos] = useState(false)
  const [hasAudio, setHasAudio] = useState(false)
  // const [error, setError] = useState<string | null>(null)

  const canProceedToCustomize = hasPhotos && hasAudio
  const canProceedToPreview = canProceedToCustomize
  const canProceedToPayment = canProceedToPreview

  useEffect(() => {
    if (currentStep === 'customize' && !canProceedToCustomize) {
      setCurrentStep('upload')
    } else if (currentStep === 'preview' && !canProceedToPreview) {
      setCurrentStep('upload')
    } else if (currentStep === 'payment' && !canProceedToPayment) {
      setCurrentStep('upload')
    }
  }, [currentStep, canProceedToCustomize, canProceedToPreview, canProceedToPayment])

  const steps = [
    { id: 'upload', label: 'Upload Files', enabled: true },
    { id: 'customize', label: 'Customize', enabled: canProceedToCustomize },
    { id: 'preview', label: 'Preview', enabled: canProceedToPreview },
    { id: 'payment', label: 'Download', enabled: canProceedToPayment },
  ] as const

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Header />

      {/* Progress Steps */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-center mb-8">
          {steps.map((step, index) => (
            <React.Fragment key={step.id}>
              <div
                className={cn(
                  'flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium transition-all duration-200',
                  currentStep === step.id
                    ? 'bg-primary-600 text-white'
                    : step.enabled
                    ? 'bg-primary-100 text-primary-700 cursor-pointer hover:bg-primary-200'
                    : 'bg-gray-200 text-gray-500'
                )}
                onClick={() => step.enabled && setCurrentStep(step.id)}
              >
                {index + 1}
              </div>
              <span
                className={cn(
                  'mx-3 text-sm font-medium',
                  currentStep === step.id
                    ? 'text-primary-700'
                    : step.enabled
                    ? 'text-gray-700'
                    : 'text-gray-400'
                )}
              >
                {step.label}
              </span>
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'w-16 h-1 mx-4 rounded-full transition-colors duration-200',
                    step.enabled ? 'bg-primary-200' : 'bg-gray-200'
                  )}
                />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Step Content */}
        <div className="space-y-8">
          {currentStep === 'upload' && (
            <UploadSection
              onPhotosUploaded={() => setHasPhotos(true)}
              onAudioUploaded={() => setHasAudio(true)}
              canProceed={canProceedToCustomize}
              onNext={() => setCurrentStep('customize')}
            />
          )}

          {currentStep === 'customize' && (
            <CustomizationPanel
              onNext={() => setCurrentStep('preview')}
              onBack={() => setCurrentStep('upload')}
            />
          )}

          {currentStep === 'preview' && (
            <PreviewSection
              onNext={() => setCurrentStep('payment')}
              onBack={() => setCurrentStep('customize')}
            />
          )}

          {currentStep === 'payment' && (
            <PricingSection
              onBack={() => setCurrentStep('preview')}
            />
          )}
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <Elements stripe={stripePromise}>
      <SessionProvider>
        <Router>
          <Routes>
            <Route path="/" element={<MainApp />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
        </Router>
      </SessionProvider>
    </Elements>
  )
}

export default App
