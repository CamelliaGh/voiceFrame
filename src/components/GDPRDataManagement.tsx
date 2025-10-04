import React, { useState } from 'react'
import {
  Download,
  Trash2,
  Edit,
  Eye,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  User,
  Mail,
  FileText,
  Database,
  X
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface GDPRDataManagementProps {
  userIdentifier?: string
  onClose?: () => void
}

interface UserData {
  sessions: any[]
  orders: any[]
  consents: any[]
  emailSubscribers: any[]
  personalInfo: {
    email?: string
    createdAt?: string
    lastActivity?: string
  }
}

export default function GDPRDataManagement({ userIdentifier, onClose }: GDPRDataManagementProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'data' | 'consent' | 'export' | 'delete'>('overview')
  const [userData, setUserData] = useState<UserData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [corrections, setCorrections] = useState<Record<string, any>>({})

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Eye },
    { id: 'data', label: 'My Data', icon: Database },
    { id: 'consent', label: 'Consent', icon: Shield },
    { id: 'export', label: 'Export', icon: Download },
    { id: 'delete', label: 'Delete', icon: Trash2 },
  ] as const

  const fetchUserData = async () => {
    if (!userIdentifier) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/gdpr/data/${userIdentifier}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch user data: ${response.statusText}`)
      }

      const data = await response.json()
      setUserData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user data')
    } finally {
      setLoading(false)
    }
  }

  const handleDataExport = async () => {
    if (!userIdentifier) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/gdpr/export/${userIdentifier}`)
      if (!response.ok) {
        throw new Error(`Failed to export data: ${response.statusText}`)
      }

      // Create download link
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audioposter_data_export_${userIdentifier}_${new Date().toISOString().split('T')[0]}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setSuccess('Data export completed successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export data')
    } finally {
      setLoading(false)
    }
  }

  const handleDataCorrection = async () => {
    if (!userIdentifier || Object.keys(corrections).length === 0) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/gdpr/data/${userIdentifier}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(corrections)
      })

      if (!response.ok) {
        throw new Error(`Failed to update data: ${response.statusText}`)
      }

      setSuccess('Data updated successfully')
      setCorrections({})
      fetchUserData() // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update data')
    } finally {
      setLoading(false)
    }
  }

  const handleDataDeletion = async () => {
    if (!userIdentifier) return

    const confirmed = window.confirm(
      'Are you sure you want to delete all your data? This action cannot be undone. ' +
      'Note: Some data may be retained for legal compliance (e.g., order records for 7 years).'
    )

    if (!confirmed) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/gdpr/data/${userIdentifier}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error(`Failed to delete data: ${response.statusText}`)
      }

      setSuccess('Data deletion request submitted successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete data')
    } finally {
      setLoading(false)
    }
  }

  const handleConsentWithdrawal = async (consentType: string) => {
    if (!userIdentifier) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/gdpr/consent', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          user_identifier: userIdentifier,
          consent_type: consentType
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to withdraw consent: ${response.statusText}`)
      }

      setSuccess(`Consent for ${consentType} withdrawn successfully`)
      fetchUserData() // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to withdraw consent')
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => {
    if (userIdentifier) {
      fetchUserData()
    }
  }, [userIdentifier])

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Management</h1>
          <p className="text-gray-600">Manage your personal data and privacy settings</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          <span className="text-red-800">{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className="text-green-800">{success}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm",
                  activeTab === tab.id
                    ? "border-primary-500 text-primary-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                )}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card">
                <div className="flex items-center space-x-3">
                  <Database className="w-8 h-8 text-blue-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900">Data Storage</h3>
                    <p className="text-sm text-gray-600">
                      {userData ? `${userData.sessions.length} sessions` : 'Loading...'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center space-x-3">
                  <Shield className="w-8 h-8 text-green-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900">Consent Status</h3>
                    <p className="text-sm text-gray-600">
                      {userData ? `${userData.consents.length} consents` : 'Loading...'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center space-x-3">
                  <Clock className="w-8 h-8 text-orange-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900">Data Retention</h3>
                    <p className="text-sm text-gray-600">90 days (sessions)</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Rights</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-start space-x-3">
                  <Eye className="w-5 h-5 text-blue-600 mt-1" />
                  <div>
                    <h4 className="font-medium text-gray-900">Right to Access</h4>
                    <p className="text-sm text-gray-600">View all personal data we hold about you</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <Download className="w-5 h-5 text-green-600 mt-1" />
                  <div>
                    <h4 className="font-medium text-gray-900">Right to Portability</h4>
                    <p className="text-sm text-gray-600">Export your data in a machine-readable format</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <Edit className="w-5 h-5 text-orange-600 mt-1" />
                  <div>
                    <h4 className="font-medium text-gray-900">Right to Rectification</h4>
                    <p className="text-sm text-gray-600">Correct inaccurate or incomplete data</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <Trash2 className="w-5 h-5 text-red-600 mt-1" />
                  <div>
                    <h4 className="font-medium text-gray-900">Right to Erasure</h4>
                    <p className="text-sm text-gray-600">Request deletion of your personal data</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'data' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h3>
              {userData?.personalInfo && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <Mail className="w-5 h-5 text-gray-400" />
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700">Email</label>
                      <input
                        type="email"
                        value={corrections.email || userData.personalInfo.email || ''}
                        onChange={(e) => setCorrections(prev => ({ ...prev, email: e.target.value }))}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <Clock className="w-5 h-5 text-gray-400" />
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Account Created</label>
                      <p className="text-sm text-gray-600">
                        {userData.personalInfo.createdAt ?
                          new Date(userData.personalInfo.createdAt).toLocaleDateString() :
                          'Unknown'
                        }
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <User className="w-5 h-5 text-gray-400" />
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Last Activity</label>
                      <p className="text-sm text-gray-600">
                        {userData.personalInfo.lastActivity ?
                          new Date(userData.personalInfo.lastActivity).toLocaleDateString() :
                          'Unknown'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {Object.keys(corrections).length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <button
                    onClick={handleDataCorrection}
                    disabled={loading}
                    className="btn-primary"
                  >
                    {loading ? 'Updating...' : 'Save Changes'}
                  </button>
                </div>
              )}
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Summary</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Sessions</span>
                  <span className="font-medium">{userData?.sessions.length || 0}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Orders</span>
                  <span className="font-medium">{userData?.orders.length || 0}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Email Subscriptions</span>
                  <span className="font-medium">{userData?.emailSubscribers.length || 0}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'consent' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Consent Management</h3>
              {userData?.consents && userData.consents.length > 0 ? (
                <div className="space-y-4">
                  {userData.consents.map((consent, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div>
                        <h4 className="font-medium text-gray-900 capitalize">
                          {consent.consent_type.replace('_', ' ')}
                        </h4>
                        <p className="text-sm text-gray-600">
                          Given: {new Date(consent.created_at).toLocaleDateString()}
                        </p>
                        <p className="text-sm text-gray-600">
                          Status: {consent.status}
                        </p>
                      </div>
                      <button
                        onClick={() => handleConsentWithdrawal(consent.consent_type)}
                        disabled={loading}
                        className="btn-secondary text-sm"
                      >
                        Withdraw
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No consent records found.</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'export' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Your Data</h3>
              <p className="text-gray-600 mb-4">
                Download a complete copy of all your personal data in a machine-readable format.
                The export will include all sessions, orders, consent records, and personal information.
              </p>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex items-start space-x-2">
                  <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900">Export Format</h4>
                    <p className="text-sm text-blue-800">
                      Your data will be exported as a ZIP file containing JSON files with all your information.
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={handleDataExport}
                disabled={loading}
                className="btn-primary flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>{loading ? 'Preparing Export...' : 'Download My Data'}</span>
              </button>
            </div>
          </div>
        )}

        {activeTab === 'delete' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete Your Data</h3>

              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-red-900">Warning: This action cannot be undone</h4>
                    <p className="text-sm text-red-800">
                      Deleting your data will permanently remove all your personal information, sessions, and preferences.
                      Some data may be retained for legal compliance (e.g., order records for 7 years).
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">What will be deleted:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li>All session data and uploaded files</li>
                  <li>Personal information and preferences</li>
                  <li>Consent records (after legal retention period)</li>
                  <li>Email subscription data</li>
                </ul>

                <h4 className="font-medium text-gray-900 mt-4">What will be retained:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li>Order records (7 years for legal compliance)</li>
                  <li>Payment transaction data (as required by law)</li>
                  <li>Anonymized usage statistics</li>
                </ul>
              </div>

              <button
                onClick={handleDataDeletion}
                disabled={loading}
                className="mt-6 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <Trash2 className="w-4 h-4" />
                <span>{loading ? 'Processing...' : 'Delete All My Data'}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
