import { Music, AudioLines, Shield, Cookie, Scale } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import CookieConsentBanner from './CookieConsentBanner'

export default function Header() {
  const [showCookieSettings, setShowCookieSettings] = useState(false)

  return (
    <>
      <header className="bg-white border-b border-gray-200 shadow-md sticky top-0 z-50 backdrop-blur-sm bg-white/95">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex items-center justify-between h-18 sm:h-24">
            {/* Logo and Title */}
            <div className="flex items-center space-x-3 sm:space-x-4">
              <div className="flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                <AudioLines className="w-6 h-6 sm:w-7 sm:h-7 text-white" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900 leading-tight tracking-tight">VocaFrame</h1>
                <p className="hidden sm:block text-sm text-gray-600 leading-tight font-medium">Create beautiful audio memory posters</p>
              </div>
            </div>

            {/* Right side navigation */}
            <div className="flex items-center space-x-2 sm:space-x-4">
              {/* Tagline - Hidden on mobile */}
              <div className="hidden lg:flex items-center space-x-2 text-sm text-gray-700 px-5 py-2.5 bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl border border-primary-100 shadow-sm">
                <Music className="w-5 h-5 text-primary-600" />
                <span className="font-semibold">Turn your memories into art</span>
              </div>

              {/* Legal Links */}
              <div className="flex items-center space-x-1 sm:space-x-2">
                <Link
                  to="/privacy"
                  className="flex items-center space-x-1.5 px-3 sm:px-4 py-2.5 text-xs sm:text-sm text-gray-600 hover:text-primary-700 hover:bg-primary-50 rounded-xl transition-all hover:scale-105 font-medium"
                  title="Privacy Policy"
                >
                  <Shield className="w-4 h-4" />
                  <span className="hidden md:inline">Privacy</span>
                </Link>

                <Link
                  to="/terms"
                  className="flex items-center space-x-1.5 px-3 sm:px-4 py-2.5 text-xs sm:text-sm text-gray-600 hover:text-primary-700 hover:bg-primary-50 rounded-xl transition-all hover:scale-105 font-medium"
                  title="Terms of Service"
                >
                  <Scale className="w-4 h-4" />
                  <span className="hidden md:inline">Terms</span>
                </Link>

                <button
                  onClick={() => setShowCookieSettings(true)}
                  className="flex items-center space-x-1.5 px-3 sm:px-4 py-2.5 text-xs sm:text-sm text-gray-600 hover:text-primary-700 hover:bg-primary-50 rounded-xl transition-all hover:scale-105 font-medium"
                  title="Cookie Settings"
                >
                  <Cookie className="w-4 h-4" />
                  <span className="hidden md:inline">Cookies</span>
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
