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
import Privacy from './components/Privacy'
import TermsOfService from './components/TermsOfService'
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
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50">
      <Header />

      {/* Progress Steps - Mobile Optimized */}
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8 sm:py-12">
        {/* Desktop Progress Stepper */}
        <div className="hidden md:flex items-center justify-center mb-12">
          {steps.map((step, index) => (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'flex items-center justify-center w-14 h-14 rounded-full text-base font-bold transition-all duration-300 shadow-md',
                    currentStep === step.id
                      ? 'bg-primary-600 text-white shadow-xl shadow-primary-200 scale-110 ring-4 ring-primary-100'
                      : step.enabled
                      ? 'bg-white text-primary-700 border-2 border-primary-300 cursor-pointer hover:bg-primary-50 hover:scale-110 active:scale-95'
                      : 'bg-gray-100 text-gray-400 border-2 border-gray-200'
                  )}
                  onClick={() => step.enabled && setCurrentStep(step.id)}
                >
                  {index + 1}
                </div>
                <span
                  className={cn(
                    'mt-3 text-sm font-semibold transition-colors',
                    currentStep === step.id
                      ? 'text-primary-700'
                      : step.enabled
                      ? 'text-gray-600'
                      : 'text-gray-400'
                  )}
                >
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'w-24 h-1.5 mx-6 rounded-full transition-all duration-300 mb-8',
                    step.enabled ? 'bg-primary-400' : 'bg-gray-200'
                  )}
                />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Mobile Progress Stepper */}
        <div className="md:hidden mb-8">
          <div className="bg-white rounded-xl shadow-md border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-gray-900">
                Step {steps.findIndex(s => s.id === currentStep) + 1} of {steps.length}
              </span>
              <span className="text-xs font-medium text-primary-600">
                {steps.find(s => s.id === currentStep)?.label}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${((steps.findIndex(s => s.id === currentStep) + 1) / steps.length) * 100}%` }}
              />
            </div>
            <div className="flex justify-between mt-2">
              {steps.map((step, index) => (
                <button
                  key={step.id}
                  onClick={() => step.enabled && setCurrentStep(step.id)}
                  disabled={!step.enabled}
                  className={cn(
                    'flex-1 py-2 text-xs font-medium transition-colors rounded-lg mx-0.5',
                    currentStep === step.id
                      ? 'text-primary-700 bg-primary-50'
                      : step.enabled
                      ? 'text-gray-600 hover:bg-gray-50'
                      : 'text-gray-400 cursor-not-allowed'
                  )}
                >
                  {index + 1}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Step Content */}
        <div className="space-y-10">
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
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<TermsOfService />} />
          </Routes>
        </Router>
      </SessionProvider>
    </Elements>
  )
}

export default App
