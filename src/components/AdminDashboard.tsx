import React, { useState, useEffect } from 'react'
import {
  Settings,
  Type,
  FileText,
  Image,
  Edit,
  Trash2,
  Upload,
  Search,
  Filter,
  LogOut
} from 'lucide-react'
import { cn } from '../lib/utils'
import AdminLogin from './AdminLogin'

interface AdminStats {
  fonts: {
    total: number
    active: number
    premium: number
  }
  suggested_texts: {
    total: number
    active: number
    premium: number
  }
  backgrounds: {
    total: number
    active: number
    premium: number
  }
}

interface AdminFont {
  id: string
  name: string
  display_name: string
  file_path: string
  file_size?: number
  is_active: boolean
  is_premium: boolean
  description?: string
  created_at: string
  updated_at: string
}

interface AdminSuggestedText {
  id: string
  text: string
  category?: string
  is_active: boolean
  is_premium: boolean
  usage_count: number
  created_at: string
  updated_at: string
}

interface AdminBackground {
  id: string
  name: string
  display_name: string
  file_path: string
  file_size?: number
  is_active: boolean
  is_premium: boolean
  description?: string
  category?: string
  usage_count: number
  created_at: string
  updated_at: string
}

type ResourceType = 'fonts' | 'suggested-texts' | 'backgrounds'

const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ResourceType>('fonts')
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [fonts, setFonts] = useState<AdminFont[]>([])
  const [suggestedTexts, setSuggestedTexts] = useState<AdminSuggestedText[]>([])
  const [backgrounds, setBackgrounds] = useState<AdminBackground[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // Check for stored API key on component mount
  useEffect(() => {
    const storedApiKey = localStorage.getItem('admin_api_key')
    if (storedApiKey) {
      setApiKey(storedApiKey)
      setIsAuthenticated(true)
    }
  }, [])

  const handleLogin = (key: string) => {
    setApiKey(key)
    setIsAuthenticated(true)
    localStorage.setItem('admin_api_key', key)
  }

  const handleLogout = () => {
    setApiKey(null)
    setIsAuthenticated(false)
    localStorage.removeItem('admin_api_key')
  }

  const fetchStats = async () => {
    if (!apiKey) return

    try {
      const response = await fetch('/admin/stats', {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      } else if (response.status === 401 || response.status === 403) {
        // API key is invalid, logout
        handleLogout()
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const fetchFonts = async () => {
    if (!apiKey) return

    setLoading(true)
    try {
      const response = await fetch('/admin/fonts', {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setFonts(data.items)
      } else if (response.status === 401 || response.status === 403) {
        handleLogout()
      }
    } catch (error) {
      console.error('Failed to fetch fonts:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchSuggestedTexts = async () => {
    if (!apiKey) return

    setLoading(true)
    try {
      const response = await fetch('/admin/suggested-texts', {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setSuggestedTexts(data.items)
      } else if (response.status === 401 || response.status === 403) {
        handleLogout()
      }
    } catch (error) {
      console.error('Failed to fetch suggested texts:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchBackgrounds = async () => {
    if (!apiKey) return

    setLoading(true)
    try {
      const response = await fetch('/admin/backgrounds', {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setBackgrounds(data.items)
      } else if (response.status === 401 || response.status === 403) {
        handleLogout()
      }
    } catch (error) {
      console.error('Failed to fetch backgrounds:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchStats()
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (isAuthenticated) {
      switch (activeTab) {
        case 'fonts':
          fetchFonts()
          break
        case 'suggested-texts':
          fetchSuggestedTexts()
          break
        case 'backgrounds':
          fetchBackgrounds()
          break
      }
    }
  }, [activeTab, isAuthenticated])

  const handleDelete = async (type: ResourceType, id: string) => {
    if (!confirm('Are you sure you want to delete this item?') || !apiKey) return

    try {
      const response = await fetch(`/admin/${type}/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        // Refresh the current tab
        switch (activeTab) {
          case 'fonts':
            fetchFonts()
            break
          case 'suggested-texts':
            fetchSuggestedTexts()
            break
          case 'backgrounds':
            fetchBackgrounds()
            break
        }
        fetchStats()
      } else if (response.status === 401 || response.status === 403) {
        handleLogout()
      }
    } catch (error) {
      console.error('Failed to delete item:', error)
    }
  }

  const handleFileUpload = async (type: ResourceType, id: string, file: File) => {
    if (!apiKey) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`/admin/${type}/${id}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`
        },
        body: formData
      })

      if (response.ok) {
        // Refresh the current tab
        switch (activeTab) {
          case 'fonts':
            fetchFonts()
            break
          case 'backgrounds':
            fetchBackgrounds()
            break
        }
      } else if (response.status === 401 || response.status === 403) {
        handleLogout()
      }
    } catch (error) {
      console.error('Failed to upload file:', error)
    }
  }

  const filteredItems = () => {
    let items: any[] = []
    switch (activeTab) {
      case 'fonts':
        items = fonts
        break
      case 'suggested-texts':
        items = suggestedTexts
        break
      case 'backgrounds':
        items = backgrounds
        break
    }

    if (searchTerm) {
      items = items.filter(item =>
        item.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.display_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.text?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    return items
  }

  const tabs = [
    { id: 'fonts' as ResourceType, label: 'Fonts', icon: Type, count: stats?.fonts.total || 0 },
    { id: 'suggested-texts' as ResourceType, label: 'Suggested Texts', icon: FileText, count: stats?.suggested_texts.total || 0 },
    { id: 'backgrounds' as ResourceType, label: 'Backgrounds', icon: Image, count: stats?.backgrounds.total || 0 },
  ]

  // Show login form if not authenticated
  if (!isAuthenticated) {
    return <AdminLogin onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Settings className="h-8 w-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Type className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Fonts</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.fonts.total}</p>
                  <p className="text-sm text-gray-500">{stats.fonts.active} active, {stats.fonts.premium} premium</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <FileText className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Suggested Texts</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.suggested_texts.total}</p>
                  <p className="text-sm text-gray-500">{stats.suggested_texts.active} active, {stats.suggested_texts.premium} premium</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Image className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Backgrounds</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.backgrounds.total}</p>
                  <p className="text-sm text-gray-500">{stats.backgrounds.active} active, {stats.backgrounds.premium} premium</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      'flex items-center py-4 px-1 border-b-2 font-medium text-sm',
                      activeTab === tab.id
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    )}
                  >
                    <Icon className="h-5 w-5 mr-2" />
                    {tab.label}
                    <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                      {tab.count}
                    </span>
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Search and Filters */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder={`Search ${activeTab}...`}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <button className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredItems().map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-medium text-gray-900">
                          {item.display_name || item.name}
                        </h3>
                        {item.is_premium && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Premium
                          </span>
                        )}
                        {!item.is_active && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Inactive
                          </span>
                        )}
                      </div>
                      {item.description && (
                        <p className="text-sm text-gray-500 mt-1">{item.description}</p>
                      )}
                      {item.text && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">{item.text}</p>
                      )}
                      {item.category && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mt-2">
                          {item.category}
                        </span>
                      )}
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>Created: {new Date(item.created_at).toLocaleDateString()}</span>
                        {item.usage_count !== undefined && (
                          <span>Used: {item.usage_count} times</span>
                        )}
                        {item.file_size && (
                          <span>Size: {(item.file_size / 1024).toFixed(1)} KB</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {activeTab === 'fonts' && !item.file_path && (
                        <label className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer">
                          <Upload className="h-4 w-4 mr-2" />
                          Upload
                          <input
                            type="file"
                            accept=".ttf,.otf,.woff,.woff2"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0]
                              if (file) handleFileUpload(activeTab, item.id, file)
                            }}
                          />
                        </label>
                      )}
                      {activeTab === 'backgrounds' && !item.file_path && (
                        <label className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer">
                          <Upload className="h-4 w-4 mr-2" />
                          Upload
                          <input
                            type="file"
                            accept=".jpg,.jpeg,.png,.webp"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0]
                              if (file) handleFileUpload(activeTab, item.id, file)
                            }}
                          />
                        </label>
                      )}
                      <button
                        className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                      >
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(activeTab, item.id)}
                        className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
                {filteredItems().length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-500">No {activeTab} found.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard
