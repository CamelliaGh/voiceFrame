import { FileText, Shield, Clock, CreditCard, Download, AlertTriangle, Mail, Scale, Users, Globe } from 'lucide-react'
import Footer from './Footer'

export default function TermsOfService() {
  const lastUpdated = "December 2024"

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="flex items-center justify-center w-12 h-12 bg-purple-600 rounded-lg">
              <Scale className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Terms of Service</h1>
              <p className="text-gray-600">Legal terms and conditions for using our service</p>
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
                <h2 className="text-2xl font-semibold text-gray-900">Agreement to Terms</h2>
              </div>
              <div className="prose prose-gray max-w-none">
                <p className="text-gray-700 leading-relaxed">
                  Welcome to VoiceFrame (also referred to as "AudioPoster", "we", "us", or "our"). These Terms of Service
                  ("Terms") govern your use of our audio poster generation service, including our website, mobile applications,
                  and related services (collectively, the "Service").
                </p>
                <p className="text-gray-700 leading-relaxed">
                  By accessing or using our Service, you agree to be bound by these Terms. If you disagree with any part
                  of these terms, then you may not access the Service.
                </p>
              </div>
            </section>

            {/* Service Description */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Download className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Service Description</h2>
              </div>
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">What We Provide</h3>
                  <ul className="text-gray-700 space-y-1 text-sm">
                    <li>• Audio waveform visualization and poster generation</li>
                    <li>• Photo integration and customization tools</li>
                    <li>• Multiple design templates and formatting options</li>
                    <li>• High-quality PDF generation and download services</li>
                    <li>• Secure file processing and temporary storage</li>
                  </ul>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <h3 className="font-semibold text-purple-900 mb-2">Service Limitations</h3>
                  <ul className="text-purple-800 space-y-1 text-sm">
                    <li>• File size limits apply to uploads (photos and audio)</li>
                    <li>• Processing time may vary based on file complexity</li>
                    <li>• Service availability subject to maintenance windows</li>
                    <li>• Some features may require payment</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* User Accounts and Responsibilities */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Users className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">User Responsibilities</h2>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-semibold text-green-900 mb-2">Acceptable Use</h3>
                  <ul className="text-green-800 space-y-1 text-sm">
                    <li>• Use the service for lawful purposes only</li>
                    <li>• Upload only content you own or have rights to use</li>
                    <li>• Respect intellectual property rights</li>
                    <li>• Provide accurate information when required</li>
                  </ul>
                </div>
                <div className="bg-red-50 rounded-lg p-4">
                  <h3 className="font-semibold text-red-900 mb-2">Prohibited Activities</h3>
                  <ul className="text-red-800 space-y-1 text-sm">
                    <li>• Uploading copyrighted material without permission</li>
                    <li>• Sharing inappropriate, offensive, or illegal content</li>
                    <li>• Attempting to hack, disrupt, or abuse the service</li>
                    <li>• Using the service for commercial purposes without authorization</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Payment Terms */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <CreditCard className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Payment and Billing</h2>
              </div>
              <div className="space-y-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Pricing and Payments</h3>
                  <p className="text-gray-700 text-sm mb-2">
                    Our service operates on a pay-per-use model. Prices are clearly displayed before purchase and
                    include all applicable taxes. All payments are processed securely through Stripe.
                  </p>
                  <ul className="text-gray-700 space-y-1 text-sm">
                    <li>• Payments are due immediately upon order placement</li>
                    <li>• We accept major credit cards and digital payment methods</li>
                    <li>• All prices are in USD unless otherwise specified</li>
                    <li>• No recurring subscriptions or hidden fees</li>
                  </ul>
                </div>
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Refund Policy</h3>
                  <p className="text-gray-700 text-sm">
                    Due to the digital nature of our service and immediate delivery of products, all sales are final.
                    Refunds may be considered in exceptional circumstances, such as technical failures that prevent
                    service delivery, at our sole discretion.
                  </p>
                </div>
              </div>
            </section>

            {/* Data Retention and Links */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Clock className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Data Retention and Download Links</h2>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <div className="flex items-start space-x-3">
                  <Clock className="w-6 h-6 text-blue-600 mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-blue-900 mb-2">Important: Link Retention Policy</h3>
                    <p className="text-blue-800 text-sm mb-3">
                      <strong>We retain download links and associated order data for 5 years</strong> from the date of purchase.
                      This retention period serves multiple purposes:
                    </p>
                    <ul className="text-blue-800 space-y-1 text-sm">
                      <li>• Legal and tax compliance requirements</li>
                      <li>• Customer support and re-download requests</li>
                      <li>• Fraud prevention and dispute resolution</li>
                      <li>• Business record keeping obligations</li>
                    </ul>
                    <p className="text-blue-800 text-sm mt-3">
                      After 5 years, download links and associated data may be permanently deleted unless legally required to retain them longer.
                    </p>
                  </div>
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Temporary Data</h3>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                      <span>Session data: 2 hours</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                      <span>Temporary processing files: 24 hours</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                      <span>Unpaid session data: 7 days</span>
                    </li>
                  </ul>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Permanent Data</h3>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>Download links: 5 years</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>Order records: 5 years</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>Generated posters: 5 years</span>
                    </li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Intellectual Property */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Shield className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Intellectual Property Rights</h2>
              </div>
              <div className="space-y-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Your Content</h3>
                  <p className="text-gray-700 text-sm">
                    You retain all rights to the photos, audio files, and other content you upload to our service.
                    By using our service, you grant us a limited license to process your content solely for the
                    purpose of generating your audio poster.
                  </p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Our Service</h3>
                  <p className="text-gray-700 text-sm">
                    The VoiceFrame service, including our software, algorithms, templates, and website design,
                    are protected by copyright, trademark, and other intellectual property laws. You may not
                    copy, modify, or reverse engineer any part of our service.
                  </p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Generated Posters</h3>
                  <p className="text-gray-700 text-sm">
                    The audio posters generated using our service belong to you. You may use them for personal,
                    non-commercial purposes. Commercial use may require additional licensing.
                  </p>
                </div>
              </div>
            </section>

            {/* Disclaimers and Limitations */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Disclaimers and Limitations</h2>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-yellow-900 mb-2">Service Availability</h3>
                    <p className="text-yellow-800 text-sm">
                      We strive to maintain high service availability but cannot guarantee uninterrupted access.
                      The service may be temporarily unavailable due to maintenance, updates, or technical issues.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-yellow-900 mb-2">Limitation of Liability</h3>
                    <p className="text-yellow-800 text-sm">
                      To the maximum extent permitted by law, VoiceFrame shall not be liable for any indirect,
                      incidental, special, or consequential damages arising from your use of the service.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-yellow-900 mb-2">Data Loss</h3>
                    <p className="text-yellow-800 text-sm">
                      While we implement robust backup systems, we recommend keeping copies of your important
                      files. We are not responsible for any data loss that may occur.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Privacy and Data Protection */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Shield className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Privacy and Data Protection</h2>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <p className="text-purple-800 text-sm">
                  Your privacy is important to us. Our collection, use, and protection of your personal information
                  is governed by our{' '}
                  <a href="/privacy" className="underline hover:no-underline font-medium">
                    Privacy Policy
                  </a>
                  , which is incorporated into these Terms by reference. By using our service, you also agree to
                  our Privacy Policy.
                </p>
              </div>
            </section>

            {/* Termination */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Termination</h2>
              </div>
              <div className="space-y-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Termination by You</h3>
                  <p className="text-gray-700 text-sm">
                    You may stop using our service at any time. If you have purchased products, your download
                    links will remain active for the full 5-year retention period.
                  </p>
                </div>
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Termination by Us</h3>
                  <p className="text-gray-700 text-sm">
                    We may terminate or suspend your access to the service immediately if you violate these Terms
                    or engage in prohibited activities. Paid products will remain accessible unless the termination
                    is due to illegal activity.
                  </p>
                </div>
              </div>
            </section>

            {/* Governing Law */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Globe className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Governing Law and Disputes</h2>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700 text-sm mb-3">
                  These Terms shall be governed by and construed in accordance with the laws of the jurisdiction
                  where VoiceFrame is incorporated, without regard to its conflict of law provisions.
                </p>
                <p className="text-gray-700 text-sm">
                  Any disputes arising from these Terms or your use of the service shall be resolved through
                  binding arbitration or in the courts of competent jurisdiction in our home jurisdiction.
                </p>
              </div>
            </section>

            {/* Changes to Terms */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <FileText className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Changes to Terms</h2>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-800 text-sm">
                  We reserve the right to modify these Terms at any time. We will notify users of material changes
                  by email or through our service. Your continued use of the service after such modifications
                  constitutes acceptance of the updated Terms. The "Last updated" date at the top indicates when
                  these Terms were last revised.
                </p>
              </div>
            </section>

            {/* Contact Information */}
            <section>
              <div className="flex items-center space-x-2 mb-4">
                <Mail className="w-5 h-5 text-purple-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Contact Information</h2>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Legal Questions</h3>
                    <p className="text-gray-700 text-sm mb-2">
                      For questions about these Terms of Service:
                    </p>
                    <a
                      href="mailto:legal@audioposter.com"
                      className="text-purple-600 hover:underline font-medium"
                    >
                      legal@audioposter.com
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
                    By using VoiceFrame, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
                  </p>
                </div>
              </div>
            </section>

          </div>
        </div>

        {/* Navigation Links */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center space-y-2 sm:space-y-0 sm:space-x-6">
          <a
            href="/privacy"
            className="inline-flex items-center space-x-2 text-purple-600 hover:text-purple-700 font-medium"
          >
            <span>Privacy Policy</span>
          </a>
          <a
            href="/"
            className="inline-flex items-center space-x-2 text-purple-600 hover:text-purple-700 font-medium"
          >
            <span>← Back to VoiceFrame</span>
          </a>
        </div>
      </div>
      <Footer />
    </div>
  )
}
