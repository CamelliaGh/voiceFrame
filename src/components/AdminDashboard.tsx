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
  LogOut,
  Plus,
  Cog
} from 'lucide-react'
import { cn } from '@/lib/utils'
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
  orientation: string
  usage_count: number
  created_at: string
  updated_at: string
}

interface AdminConfig {
  id: string
  key: string
  value: string
  description?: string
  data_type: string
  is_active: boolean
  created_at: string
  updated_at: string
}

type ResourceType = 'fonts' | 'suggested-texts' | 'backgrounds' | 'config'

const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ResourceType>('fonts')
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [fonts, setFonts] = useState<AdminFont[]>([])
  const [suggestedTexts, setSuggestedTexts] = useState<AdminSuggestedText[]>([])
  const [backgrounds, setBackgrounds] = useState<AdminBackground[]>([])
  const [configs, setConfigs] = useState<AdminConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [adminPassword, setAdminPassword] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingItem, setEditingItem] = useState<any>(null)
  const [addFormData, setAddFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    category: 'general',
    orientation: 'both',
    text: '',
    file: null as File | null
  })
  const [editFormData, setEditFormData] = useState({
    display_name: '',
    description: '',
    category: 'general',
    orientation: 'both',
    text: '',
    file: null as File | null
  })

  // Check for stored admin password on component mount
  useEffect(() => {
    const storedPassword = localStorage.getItem('admin_password')
    if (storedPassword) {
      setAdminPassword(storedPassword)
      setIsAuthenticated(true)
    }
  }, [])

  const handleLogin = (password: string) => {
    setAdminPassword(password)
    setIsAuthenticated(true)
    localStorage.setItem('admin_password', password)
  }

  const handleLogout = () => {
    setAdminPassword(null)
    setIsAuthenticated(false)
    localStorage.removeItem('admin_password')
  }

  const fetchStats = async () => {
    if (!adminPassword) return

    try {
      const response = await fetch('/admin/stats', {
        headers: {
          'Authorization': `Bearer ${adminPassword}`,
          'Content-Type': 'application/json'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      } else if (response.status === 401 || response.status === 403) {
        // Password is invalid, logout
        handleLogout()
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const fetchFonts = async () => {
    if (!adminPassword) return

    setLoading(true)
    try {
      const response = await fetch('/admin/fonts', {
        headers: {
          'Authorization': `Bearer ${adminPassword}`,
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
    if (!adminPassword) return

    setLoading(true)
    try {
      const response = await fetch('/admin/suggested-texts', {
        headers: {
          'Authorization': `Bearer ${adminPassword}`,
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
    if (!adminPassword) return

    setLoading(true)
    try {
      const response = await fetch('/admin/backgrounds', {
        headers: {
          'Authorization': `Bearer ${adminPassword}`,
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

  const fetchConfigs = async () => {
    if (!adminPassword) return

    setLoading(true)
    try {
      const response = await fetch('/admin/config', {
        headers: {
          'Authorization': `Bearer ${adminPassword}`,
          'Content-Type': 'application/json'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setConfigs(data.items)
      } else if (response.status === 401 || response.status === 403) {
        handleLogout()
      }
    } catch (error) {
      console.error('Failed to fetch configurations:', error)
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
        case 'config':
          fetchConfigs()
          break
      }
    }
  }, [activeTab, isAuthenticated])

  const handleDelete = async (type: ResourceType, id: string) => {
    if (!confirm('Are you sure you want to delete this item?') || !adminPassword) return

    try {
      const response = await fetch(`/admin/${type}/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${adminPassword}`,
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
          case 'config':
            fetchConfigs()
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
    if (!adminPassword) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`/admin/${type}/${id}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminPassword}`
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

  const handleAddNew = () => {
    // Reset form data
    setAddFormData({
      name: '',
      display_name: '',
      description: '',
      category: 'general',
      orientation: 'both',
      text: '',
      file: null
    })
    setShowAddModal(true)
  }

  const handleSubmitAdd = async () => {
    if (!adminPassword) return

    try {
      let endpoint = ''
      let body = {}

      switch (activeTab) {
        case 'fonts':
          if (!addFormData.name || !addFormData.display_name) {
            alert('Name and display name are required')
            return
          }
          if (!addFormData.file) {
            alert('Font file is required')
            return
          }
          endpoint = '/admin/fonts'
          body = {
            name: addFormData.name,
            display_name: addFormData.display_name,
            description: addFormData.description,
            is_premium: false
          }
          break
        case 'backgrounds':
          if (!addFormData.name || !addFormData.display_name) {
            alert('Name and display name are required')
            return
          }
          if (!addFormData.file) {
            alert('Background image is required')
            return
          }
          endpoint = '/admin/backgrounds'
          body = {
            name: addFormData.name,
            display_name: addFormData.display_name,
            description: addFormData.description,
            category: addFormData.category,
            orientation: addFormData.orientation,
            is_premium: false
          }
          break
        case 'suggested-texts':
          if (!addFormData.text) {
            alert('Text message is required')
            return
          }
          endpoint = '/admin/suggested-texts'
          body = {
            text: addFormData.text,
            category: addFormData.category,
            is_premium: false
          }
          break
        case 'config':
          if (!addFormData.name || !addFormData.display_name) {
            alert('Key and value are required')
            return
          }
          endpoint = '/admin/config'
          body = {
            key: addFormData.name,
            value: addFormData.display_name,
            description: addFormData.description,
            data_type: addFormData.category || 'string'
          }
          break
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminPassword}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      })

      if (response.ok) {
        const newItem = await response.json()

        // If there's a file to upload, upload it
        if (addFormData.file && (activeTab === 'fonts' || activeTab === 'backgrounds')) {
          await handleFileUpload(activeTab, newItem.id, addFormData.file)
        }

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
          case 'config':
            fetchConfigs()
            break
        }
        fetchStats()
        setShowAddModal(false)
        alert(`${activeTab.slice(0, -1)} created successfully!`)
      } else if (response.status === 401 || response.status === 403) {
        handleLogout()
      } else {
        const error = await response.json()
        alert(`Failed to create ${activeTab.slice(0, -1)}: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to create item:', error)
      alert(`Failed to create ${activeTab.slice(0, -1)}: ${error}`)
    }
  }

  const handleEdit = (item: any) => {
    setEditingItem(item)
    setEditFormData({
      display_name: item.display_name || item.name || item.value || '',
      description: item.description || '',
      category: item.category || item.data_type || 'general',
      orientation: item.orientation || 'both',
      text: item.text || '',
      file: null
    })
    setShowEditModal(true)
  }

  const handleSubmitEdit = async () => {
    if (!adminPassword || !editingItem) return

    try {
      let endpoint = ''
      let body = {}

      switch (activeTab) {
        case 'fonts':
          if (!editFormData.display_name) {
            alert('Display name is required')
            return
          }
          endpoint = `/admin/fonts/${editingItem.id}`
          body = {
            display_name: editFormData.display_name,
            description: editFormData.description
          }
          break
        case 'backgrounds':
          if (!editFormData.display_name) {
            alert('Display name is required')
            return
          }
          endpoint = `/admin/backgrounds/${editingItem.id}`
          body = {
            display_name: editFormData.display_name,
            description: editFormData.description,
            category: editFormData.category,
            orientation: editFormData.orientation
          }
          break
        case 'suggested-texts':
          if (!editFormData.text) {
            alert('Text message is required')
            return
          }
          endpoint = `/admin/suggested-texts/${editingItem.id}`
          body = {
            text: editFormData.text,
            category: editFormData.category
          }
          break
        case 'config':
          if (!editFormData.display_name) {
            alert('Value is required')
            return
          }
          endpoint = `/admin/config/${editingItem.id}`
          body = {
            value: editFormData.display_name,
            description: editFormData.description
          }
          break
      }

      const response = await fetch(endpoint, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${adminPassword}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      })

      if (response.ok) {
        // If there's a new file to upload, upload it
        if (editFormData.file && (activeTab === 'fonts' || activeTab === 'backgrounds')) {
          await handleFileUpload(activeTab, editingItem.id, editFormData.file)
        }

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
          case 'config':
            fetchConfigs()
            break
        }
        setShowEditModal(false)
        setEditingItem(null)
        alert(`${activeTab.slice(0, -1)} updated successfully!`)
      } else if (response.status === 401 || response.status === 403) {
        handleLogout()
      } else {
        const error = await response.json()
        alert(`Failed to update ${activeTab.slice(0, -1)}: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to update item:', error)
      alert(`Failed to update ${activeTab.slice(0, -1)}: ${error}`)
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
      case 'config':
        items = configs
        break
    }

    if (searchTerm) {
      items = items.filter(item =>
        item.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.display_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.text?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.key?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.value?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    return items
  }

  const tabs = [
    { id: 'fonts' as ResourceType, label: 'Fonts', icon: Type, count: stats?.fonts.total || 0 },
    { id: 'suggested-texts' as ResourceType, label: 'Suggested Texts', icon: FileText, count: stats?.suggested_texts.total || 0 },
    { id: 'backgrounds' as ResourceType, label: 'Backgrounds', icon: Image, count: stats?.backgrounds.total || 0 },
    { id: 'config' as ResourceType, label: 'Configuration', icon: Cog, count: configs.length },
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
              <button
                onClick={handleAddNew}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add New {activeTab.slice(0, -1)}
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
                          {activeTab === 'config' ? item.key : (item.display_name || item.name)}
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
                      {activeTab === 'config' && (
                        <div className="mt-1">
                          <p className="text-sm text-gray-600">
                            <span className="font-medium">Value:</span> {item.value}
                          </p>
                          <p className="text-xs text-gray-500">
                            <span className="font-medium">Type:</span> {item.data_type}
                          </p>
                        </div>
                      )}
                      <div className="flex items-center space-x-2 mt-2">
                        {item.category && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {item.category}
                          </span>
                        )}
                        {activeTab === 'backgrounds' && item.orientation && (
                          <span className={cn(
                            "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium",
                            item.orientation === 'portrait' ? "bg-green-100 text-green-800" :
                            item.orientation === 'landscape' ? "bg-orange-100 text-orange-800" :
                            "bg-gray-100 text-gray-800"
                          )}>
                            {item.orientation === 'both' ? 'Any Orientation' :
                             item.orientation === 'portrait' ? 'Portrait' : 'Landscape'}
                          </span>
                        )}
                      </div>
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
                        onClick={() => handleEdit(item)}
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

      {/* Add New Item Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Add New {activeTab.slice(0, -1)}
            </h3>

            <div className="space-y-4">
              {activeTab === 'fonts' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Font Name *
                    </label>
                    <input
                      type="text"
                      value={addFormData.name}
                      onChange={(e) => setAddFormData({...addFormData, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      placeholder="e.g., my-custom-font"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Display Name *
                    </label>
                    <input
                      type="text"
                      value={addFormData.display_name}
                      onChange={(e) => setAddFormData({...addFormData, display_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      placeholder="e.g., My Custom Font"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={addFormData.description}
                      onChange={(e) => setAddFormData({...addFormData, description: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      rows={3}
                      placeholder="Describe this font..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Font File *
                    </label>
                    <input
                      type="file"
                      accept=".ttf,.otf,.woff,.woff2"
                      onChange={(e) => setAddFormData({...addFormData, file: e.target.files?.[0] || null})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </>
              )}

              {activeTab === 'backgrounds' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Background Name *
                    </label>
                    <input
                      type="text"
                      value={addFormData.name}
                      onChange={(e) => setAddFormData({...addFormData, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      placeholder="e.g., my-background"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Display Name *
                    </label>
                    <input
                      type="text"
                      value={addFormData.display_name}
                      onChange={(e) => setAddFormData({...addFormData, display_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      placeholder="e.g., My Beautiful Background"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category
                    </label>
                    <select
                      value={addFormData.category}
                      onChange={(e) => setAddFormData({...addFormData, category: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="general">General</option>
                      <option value="romantic">Romantic</option>
                      <option value="birthday">Birthday</option>
                      <option value="anniversary">Anniversary</option>
                      <option value="memorial">Memorial</option>
                      <option value="abstract">Abstract</option>
                      <option value="baby">Baby</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Orientation
                    </label>
                    <select
                      value={addFormData.orientation}
                      onChange={(e) => setAddFormData({...addFormData, orientation: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="both">Both (Portrait & Landscape)</option>
                      <option value="portrait">Portrait Only</option>
                      <option value="landscape">Landscape Only</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">Choose which orientations this background works best for</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={addFormData.description}
                      onChange={(e) => setAddFormData({...addFormData, description: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      rows={3}
                      placeholder="Describe this background..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Background Image *
                    </label>
                    <input
                      type="file"
                      accept=".jpg,.jpeg,.png,.webp"
                      onChange={(e) => setAddFormData({...addFormData, file: e.target.files?.[0] || null})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </>
              )}

              {activeTab === 'suggested-texts' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Text Message *
                    </label>
                    <textarea
                      value={addFormData.text}
                      onChange={(e) => setAddFormData({...addFormData, text: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      rows={3}
                      placeholder="Enter the text message..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category
                    </label>
                    <select
                      value={addFormData.category}
                      onChange={(e) => setAddFormData({...addFormData, category: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="general">General</option>
                      <option value="romantic">Romantic</option>
                      <option value="birthday">Birthday</option>
                      <option value="anniversary">Anniversary</option>
                      <option value="holiday">Holiday</option>
                      <option value="congratulations">Congratulations</option>
                      <option value="thank_you">Thank You</option>
                    </select>
                  </div>
                </>
              )}

              {activeTab === 'config' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Configuration Key *
                    </label>
                    <select
                      value={addFormData.name}
                      onChange={(e) => {
                        const key = e.target.value
                        setAddFormData({
                          ...addFormData,
                          name: key,
                          category: key === 'price_cents' ? 'integer' :
                                   key === 'discount_percentage' ? 'integer' :
                                   key === 'discount_enabled' ? 'boolean' : 'string',
                          description: key === 'price_cents' ? 'Price in cents (e.g., 299 for $2.99)' :
                                      key === 'discount_percentage' ? 'Discount percentage (e.g., 20 for 20% off)' :
                                      key === 'discount_enabled' ? 'Enable or disable discount' : ''
                        })
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Select a configuration key</option>
                      <option value="price_cents">price_cents</option>
                      <option value="discount_percentage">discount_percentage</option>
                      <option value="discount_enabled">discount_enabled</option>
                      <option value="custom">Custom Key</option>
                    </select>
                    {addFormData.name === 'custom' && (
                      <input
                        type="text"
                        value={addFormData.display_name}
                        onChange={(e) => setAddFormData({...addFormData, name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 mt-2"
                        placeholder="Enter custom key name"
                      />
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Value *
                    </label>
                    {addFormData.name === 'discount_enabled' ? (
                      <select
                        value={addFormData.display_name}
                        onChange={(e) => setAddFormData({...addFormData, display_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      >
                        <option value="false">Disabled</option>
                        <option value="true">Enabled</option>
                      </select>
                    ) : (
                      <input
                        type={addFormData.name === 'price_cents' || addFormData.name === 'discount_percentage' ? 'number' : 'text'}
                        value={addFormData.display_name}
                        onChange={(e) => setAddFormData({...addFormData, display_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                        placeholder={
                          addFormData.name === 'price_cents' ? 'e.g., 299' :
                          addFormData.name === 'discount_percentage' ? 'e.g., 20' :
                          'Enter value'
                        }
                        min={addFormData.name === 'discount_percentage' ? '0' : undefined}
                        max={addFormData.name === 'discount_percentage' ? '100' : undefined}
                      />
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data Type
                    </label>
                    <select
                      value={addFormData.category}
                      onChange={(e) => setAddFormData({...addFormData, category: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      disabled={!!(addFormData.name && addFormData.name !== 'custom')}
                    >
                      <option value="string">String</option>
                      <option value="integer">Integer</option>
                      <option value="float">Float</option>
                      <option value="boolean">Boolean</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={addFormData.description}
                      onChange={(e) => setAddFormData({...addFormData, description: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      rows={3}
                      placeholder="Describe this configuration setting..."
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitAdd}
                className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
              >
                Add {activeTab.slice(0, -1)}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Item Modal */}
      {showEditModal && editingItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Edit {activeTab.slice(0, -1)}
            </h3>

            <div className="space-y-4">
              {activeTab === 'fonts' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Font Name
                    </label>
                    <input
                      type="text"
                      value={editingItem.name}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Font name cannot be changed</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Display Name *
                    </label>
                    <input
                      type="text"
                      value={editFormData.display_name}
                      onChange={(e) => setEditFormData({...editFormData, display_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={editFormData.description}
                      onChange={(e) => setEditFormData({...editFormData, description: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Replace Font File
                    </label>
                    <input
                      type="file"
                      accept=".ttf,.otf,.woff,.woff2"
                      onChange={(e) => setEditFormData({...editFormData, file: e.target.files?.[0] || null})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Leave empty to keep current file</p>
                  </div>
                </>
              )}

              {activeTab === 'backgrounds' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Background Name
                    </label>
                    <input
                      type="text"
                      value={editingItem.name}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Background name cannot be changed</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Display Name *
                    </label>
                    <input
                      type="text"
                      value={editFormData.display_name}
                      onChange={(e) => setEditFormData({...editFormData, display_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category
                    </label>
                    <select
                      value={editFormData.category}
                      onChange={(e) => setEditFormData({...editFormData, category: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="general">General</option>
                      <option value="romantic">Romantic</option>
                      <option value="birthday">Birthday</option>
                      <option value="anniversary">Anniversary</option>
                      <option value="holiday">Holiday</option>
                      <option value="abstract">Abstract</option>
                      <option value="nature">Nature</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Orientation
                    </label>
                    <select
                      value={editFormData.orientation}
                      onChange={(e) => setEditFormData({...editFormData, orientation: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="both">Both (Portrait & Landscape)</option>
                      <option value="portrait">Portrait Only</option>
                      <option value="landscape">Landscape Only</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">Choose which orientations this background works best for</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={editFormData.description}
                      onChange={(e) => setEditFormData({...editFormData, description: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Replace Background Image
                    </label>
                    <input
                      type="file"
                      accept=".jpg,.jpeg,.png,.webp"
                      onChange={(e) => setEditFormData({...editFormData, file: e.target.files?.[0] || null})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Leave empty to keep current image</p>
                  </div>
                </>
              )}

              {activeTab === 'suggested-texts' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Text Message *
                    </label>
                    <textarea
                      value={editFormData.text}
                      onChange={(e) => setEditFormData({...editFormData, text: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category
                    </label>
                    <select
                      value={editFormData.category}
                      onChange={(e) => setEditFormData({...editFormData, category: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="general">General</option>
                      <option value="romantic">Romantic</option>
                      <option value="birthday">Birthday</option>
                      <option value="anniversary">Anniversary</option>
                      <option value="holiday">Holiday</option>
                      <option value="congratulations">Congratulations</option>
                      <option value="thank_you">Thank You</option>
                    </select>
                  </div>
                </>
              )}

              {activeTab === 'config' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Configuration Key
                    </label>
                    <input
                      type="text"
                      value={editingItem.key}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Configuration key cannot be changed</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Value *
                    </label>
                    {editingItem.key === 'discount_enabled' ? (
                      <select
                        value={editFormData.display_name}
                        onChange={(e) => setEditFormData({...editFormData, display_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      >
                        <option value="false">Disabled</option>
                        <option value="true">Enabled</option>
                      </select>
                    ) : (
                      <input
                        type={editingItem.key === 'price_cents' || editingItem.key === 'discount_percentage' ? 'number' : 'text'}
                        value={editFormData.display_name}
                        onChange={(e) => setEditFormData({...editFormData, display_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                        min={editingItem.key === 'discount_percentage' ? '0' : undefined}
                        max={editingItem.key === 'discount_percentage' ? '100' : undefined}
                      />
                    )}
                    {editingItem.key === 'price_cents' && (
                      <p className="text-xs text-gray-500 mt-1">Price in cents (e.g., 299 for $2.99)</p>
                    )}
                    {editingItem.key === 'discount_percentage' && (
                      <p className="text-xs text-gray-500 mt-1">Percentage from 0-100 (e.g., 20 for 20% off)</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data Type
                    </label>
                    <input
                      type="text"
                      value={editingItem.data_type}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Data type cannot be changed</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={editFormData.description}
                      onChange={(e) => setEditFormData({...editFormData, description: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                      rows={3}
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setEditingItem(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitEdit}
                className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
              >
                Update {activeTab.slice(0, -1)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminDashboard
