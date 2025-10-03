import { Music, AudioLines, Shield, Cookie, Scale } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import CookieConsentBanner from './CookieConsentBanner'

export default function Header() {
  const [showCookieSettings, setShowCookieSettings] = useState(false)

  return (
    <>
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 sm:h-20">
            {/* Logo and Title */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className="flex items-center justify-center w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl shadow-md">
                <AudioLines className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-bold text-gray-900 leading-tight">VoiceFrame</h1>
                <p className="hidden sm:block text-xs sm:text-sm text-gray-500 leading-tight">Create beautiful audio memory posters</p>
              </div>
            </div>

            {/* Right side navigation */}
            <div className="flex items-center space-x-2 sm:space-x-4">
              {/* Tagline - Hidden on mobile */}
              <div className="hidden lg:flex items-center space-x-2 text-sm text-gray-600 px-4 py-2 bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg">
                <Music className="w-4 h-4 text-primary-600" />
                <span className="font-medium text-gray-700">Turn your memories into art</span>
              </div>

              {/* Legal Links */}
              <div className="flex items-center space-x-1 sm:space-x-2">
                <Link
                  to="/privacy"
                  className="flex items-center space-x-1 px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-all"
                  title="Privacy Policy"
                >
                  <Shield className="w-4 h-4" />
                  <span className="hidden md:inline font-medium">Privacy</span>
                </Link>

                <Link
                  to="/terms"
                  className="flex items-center space-x-1 px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-all"
                  title="Terms of Service"
                >
                  <Scale className="w-4 h-4" />
                  <span className="hidden md:inline font-medium">Terms</span>
                </Link>

                <button
                  onClick={() => setShowCookieSettings(true)}
                  className="flex items-center space-x-1 px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-all"
                  title="Cookie Settings"
                >
                  <Cookie className="w-4 h-4" />
                  <span className="hidden md:inline font-medium">Cookies</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Cookie Consent Banner */}
      <CookieConsentBanner
        showSettings={showCookieSettings}
        onSettingsClose={() => setShowCookieSettings(false)}
        onConsentChange={(consent) => {
          console.log('Cookie consent updated:', consent)
        }}
      />
    </>
  )
}
