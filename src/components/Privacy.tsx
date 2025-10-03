import { Shield, Lock, Eye, Download, Trash2, Edit, Mail, FileText, Clock, Globe } from 'lucide-react'

export default function Privacy() {
  const lastUpdated = "December 2024"

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="flex items-center justify-center w-12 h-12 bg-purple-600 rounded-lg">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Privacy Policy</h1>
              <p className="text-gray-600">How we protect and handle your data</p>
            </div>
          </div>
          <p className="text-sm text-gray-500">Last updated: {lastUpdated}</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-8 space-y-8">

            {/* Introduction */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <FileText className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Introduction</h2>
              </div>
              <div className="prose prose-gray max-w-none">
                <p className="text-gray-700 leading-relaxed">
                  At AudioPoster, we are committed to protecting your privacy and ensuring the security of your personal information.
                  This Privacy Policy explains how we collect, use, store, and protect your data when you use our service to create
                  beautiful audio memory posters.
                </p>
                <p className="text-gray-700 leading-relaxed">
                  We believe in transparency and your right to control your personal data. This policy complies with the
                  General Data Protection Regulation (GDPR) and other applicable privacy laws.
                </p>
              </div>
            </section>

            {/* Data We Collect */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Eye className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Information We Collect</h2>
              </div>
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Files You Upload</h3>
                  <ul className="text-gray-700 space-y-1 text-sm">
                    <li>• Photos and images for your poster</li>
                    <li>• Audio files for waveform generation</li>
                    <li>• Custom text and design preferences</li>
                  </ul>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Contact Information</h3>
                  <ul className="text-gray-700 space-y-1 text-sm">
                    <li>• Email address (for order delivery and communication)</li>
                    <li>• Communication preferences</li>
                  </ul>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Technical Information</h3>
                  <ul className="text-gray-700 space-y-1 text-sm">
                    <li>• Session tokens for service functionality</li>
                    <li>• IP addresses and browser information</li>
                    <li>• Usage analytics and performance data</li>
                  </ul>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Payment Information</h3>
                  <ul className="text-gray-700 space-y-1 text-sm">
                    <li>• Payment details (processed securely by Stripe)</li>
                    <li>• Order history and transaction records</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* How We Use Data */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Lock className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">How We Use Your Information</h2>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-purple-50 rounded-lg p-4">
                  <h3 className="font-semibold text-purple-900 mb-2">Service Delivery</h3>
                  <ul className="text-purple-800 space-y-1 text-sm">
                    <li>• Process your uploaded files</li>
                    <li>• Generate audio waveforms</li>
                    <li>• Create custom posters</li>
                    <li>• Deliver your final products</li>
                  </ul>
                </div>
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="font-semibold text-blue-900 mb-2">Communication</h3>
                  <ul className="text-blue-800 space-y-1 text-sm">
                    <li>• Send download links</li>
                    <li>• Provide order updates</li>
                    <li>• Respond to support requests</li>
                    <li>• Share service improvements</li>
                  </ul>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-semibold text-green-900 mb-2">Legal Compliance</h3>
                  <ul className="text-green-800 space-y-1 text-sm">
                    <li>• Maintain transaction records</li>
                    <li>• Comply with tax obligations</li>
                    <li>• Respond to legal requests</li>
                    <li>• Prevent fraud and abuse</li>
                  </ul>
                </div>
                <div className="bg-orange-50 rounded-lg p-4">
                  <h3 className="font-semibold text-orange-900 mb-2">Service Improvement</h3>
                  <ul className="text-orange-800 space-y-1 text-sm">
                    <li>• Analyze usage patterns</li>
                    <li>• Improve performance</li>
                    <li>• Develop new features</li>
                    <li>• Enhance user experience</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Data Storage & Security */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Globe className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Data Storage & Security</h2>
              </div>
              <div className="space-y-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Secure Storage</h3>
                  <p className="text-gray-700 text-sm">
                    Your files are securely stored on Amazon Web Services (AWS) S3 with encryption at rest and in transit.
                    We use industry-standard security measures to protect your data from unauthorized access.
                  </p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Payment Security</h3>
                  <p className="text-gray-700 text-sm">
                    All payment processing is handled by Stripe, a PCI DSS compliant payment processor.
                    We never store your credit card information on our servers.
                  </p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Access Controls</h3>
                  <p className="text-gray-700 text-sm">
                    Access to your data is strictly limited to authorized personnel who need it to provide our services.
                    All access is logged and monitored for security purposes.
                  </p>
                </div>
              </div>
            </section>

            {/* Data Retention */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Clock className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Data Retention</h2>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Temporary Data</h3>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                        <span>Session data: 2 hours</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                        <span>Temporary files: 24 hours</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                        <span>Download links: 7 days</span>
                      </li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Permanent Data</h3>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>Order records: 7 years (legal requirement)</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>Purchased files: Permanent (your property)</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>Email preferences: Until unsubscribed</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Your Rights */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Shield className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Your Privacy Rights</h2>
              </div>
              <p className="text-gray-700 mb-4">
                Under GDPR and other privacy laws, you have the following rights regarding your personal data:
              </p>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-start space-x-3 p-4 bg-white border border-gray-200 rounded-lg">
                  <Download className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-gray-900">Right to Access</h3>
                    <p className="text-sm text-gray-600">Request a copy of all personal data we hold about you</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-4 bg-white border border-gray-200 rounded-lg">
                  <Edit className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-gray-900">Right to Rectification</h3>
                    <p className="text-sm text-gray-600">Correct any inaccurate or incomplete personal data</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-4 bg-white border border-gray-200 rounded-lg">
                  <Trash2 className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-gray-900">Right to Erasure</h3>
                    <p className="text-sm text-gray-600">Request deletion of your personal data (subject to legal requirements)</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-4 bg-white border border-gray-200 rounded-lg">
                  <Download className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-gray-900">Right to Portability</h3>
                    <p className="text-sm text-gray-600">Receive your data in a structured, machine-readable format</p>
                  </div>
                </div>
              </div>
              <div className="mt-6 p-4 bg-purple-50 rounded-lg">
                <p className="text-purple-800 text-sm">
                  <strong>To exercise your rights:</strong> Contact us at{' '}
                  <a href="mailto:privacy@audioposter.com" className="underline hover:no-underline">
                    privacy@audioposter.com
                  </a>{' '}
                  with your request. We will respond within 30 days.
                </p>
              </div>
            </section>

            {/* Third Parties */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Globe className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Third-Party Services</h2>
              </div>
              <div className="space-y-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <h3 className="font-semibold text-gray-900">Stripe (Payment Processing)</h3>
                  </div>
                  <p className="text-gray-700 text-sm">
                    Handles all payment transactions securely. View their privacy policy at{' '}
                    <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:underline">
                      stripe.com/privacy
                    </a>
                  </p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                    <h3 className="font-semibold text-gray-900">Amazon Web Services (File Storage)</h3>
                  </div>
                  <p className="text-gray-700 text-sm">
                    Provides secure cloud storage for your files. View their privacy policy at{' '}
                    <a href="https://aws.amazon.com/privacy/" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:underline">
                      aws.amazon.com/privacy
                    </a>
                  </p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <h3 className="font-semibold text-gray-900">SendGrid (Email Delivery)</h3>
                  </div>
                  <p className="text-gray-700 text-sm">
                    Delivers your order confirmations and download links. View their privacy policy at{' '}
                    <a href="https://sendgrid.com/policies/privacy/" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:underline">
                      sendgrid.com/policies/privacy
                    </a>
                  </p>
                </div>
              </div>
            </section>

            {/* Cookies */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Eye className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Cookies & Tracking</h2>
              </div>
              <div className="space-y-4">
                <p className="text-gray-700">
                  We use cookies and similar technologies to improve your experience and analyze usage patterns.
                </p>
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="bg-green-50 rounded-lg p-4">
                    <h3 className="font-semibold text-green-900 mb-2">Essential Cookies</h3>
                    <p className="text-green-800 text-sm">Required for basic functionality and security</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-900 mb-2">Analytics Cookies</h3>
                    <p className="text-blue-800 text-sm">Help us understand how you use our service</p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <h3 className="font-semibold text-purple-900 mb-2">Preference Cookies</h3>
                    <p className="text-purple-800 text-sm">Remember your settings and preferences</p>
                  </div>
                </div>
                <p className="text-gray-700 text-sm">
                  You can manage your cookie preferences through our cookie banner or your browser settings.
                </p>
              </div>
            </section>

            {/* Contact */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Mail className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Contact Us</h2>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Privacy Questions</h3>
                    <p className="text-gray-700 text-sm mb-2">
                      For any privacy-related questions or to exercise your rights:
                    </p>
                    <a
                      href="mailto:privacy@audioposter.com"
                      className="text-purple-600 hover:underline font-medium"
                    >
                      privacy@audioposter.com
                    </a>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">General Support</h3>
                    <p className="text-gray-700 text-sm mb-2">
                      For technical support or general inquiries:
                    </p>
                    <a
                      href="mailto:support@audioposter.com"
                      className="text-purple-600 hover:underline font-medium"
                    >
                      support@audioposter.com
                    </a>
                  </div>
                </div>
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <p className="text-gray-600 text-sm">
                    We are committed to resolving any privacy concerns promptly and will respond to your inquiries within 30 days.
                  </p>
                </div>
              </div>
            </section>

            {/* Updates */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <FileText className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Policy Updates</h2>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800 text-sm">
                  We may update this Privacy Policy from time to time to reflect changes in our practices or legal requirements.
                  We will notify you of any material changes by email or through our service. The "Last updated" date at the top
                  of this policy indicates when it was last revised.
                </p>
              </div>
            </section>

          </div>
        </div>

        {/* Navigation Links */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center space-y-2 sm:space-y-0 sm:space-x-6">
          <a
            href="/terms"
            className="inline-flex items-center space-x-2 text-purple-600 hover:text-purple-700 font-medium"
          >
            <span>Terms of Service</span>
          </a>
          <a
            href="/"
            className="inline-flex items-center space-x-2 text-purple-600 hover:text-purple-700 font-medium"
          >
            <span>← Back to VoiceFrame</span>
          </a>
        </div>
      </div>
    </div>
  )
}
