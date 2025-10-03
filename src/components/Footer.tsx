import { Mail, Heart } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-white border-t border-gray-200 mt-16">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8 sm:py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-gray-900">VocaFrame</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              Transform your precious audio memories into beautiful, tangible posters that you can cherish forever.
            </p>
          </div>

          {/* Quick Links */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">Quick Links</h4>
            <nav className="flex flex-col space-y-2">
              <Link
                to="/privacy"
                className="text-sm text-gray-600 hover:text-primary-600 transition-colors"
              >
                Privacy Policy
              </Link>
              <Link
                to="/terms"
                className="text-sm text-gray-600 hover:text-primary-600 transition-colors"
              >
                Terms of Service
              </Link>
            </nav>
          </div>

          {/* Contact Section */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">Contact Us</h4>
            <a
              href="mailto:contact@vocaframe.com"
              className="flex items-center space-x-2 text-sm text-gray-600 hover:text-primary-600 transition-colors group"
            >
              <Mail className="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span>contact@vocaframe.com</span>
            </a>
            <p className="text-xs text-gray-500 leading-relaxed">
              We'd love to hear from you! Send us your questions, feedback, or just say hello.
            </p>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-200 mt-8 pt-8">
          <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
            {/* Copyright */}
            <p className="text-sm text-gray-600 text-center sm:text-left">
              © {currentYear} VocaFrame. All rights reserved.
            </p>

            {/* Made with love */}
            <p className="flex items-center space-x-1 text-sm text-gray-600">
              <span>Made with</span>
              <Heart className="w-4 h-4 text-red-500 fill-current" />
              <span>for preserving memories</span>
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}
