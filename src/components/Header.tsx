import { Music, AudioLines, Shield, Cookie } from 'lucide-react'
import { useState } from 'react'
import CookieConsentBanner from './CookieConsentBanner'

export default function Header() {
  const [, setShowCookieSettings] = useState(false)

  return (
    <>
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-primary-600 rounded-lg">
                <AudioLines className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">AudioPoster</h1>
                <p className="text-sm text-gray-500">Create beautiful audio memory posters</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="hidden sm:flex items-center space-x-2 text-sm text-gray-600">
                <Music className="w-4 h-4" />
                <span>Turn your memories into art</span>
              </div>

              {/* Privacy Links */}
              <div className="flex items-center space-x-3">
                <a
                  href="/privacy"
                  className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Shield className="w-4 h-4" />
                  <span className="hidden sm:inline">Privacy</span>
                </a>

                <button
                  onClick={() => setShowCookieSettings(true)}
                  className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                  title="Cookie Settings"
                >
                  <Cookie className="w-4 h-4" />
                  <span className="hidden sm:inline">Cookies</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Cookie Consent Banner */}
      <CookieConsentBanner
        onConsentChange={(consent) => {
          console.log('Cookie consent updated:', consent)
        }}
      />
    </>
  )
}
