import { useState, useCallback, useEffect } from 'react'
import { Image, Eye, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BackgroundOption {
  id: string
  name: string
  description: string
  preview: string | null
  category?: string
  tags?: string[]
}

interface BackgroundSelectionProps {
  value: string
  onChange: (backgroundId: string) => void
  disabled?: boolean
  className?: string
  pdfSize?: 'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape'
}

// Default fallback option - only "none" is hardcoded as it's a special case
// All actual backgrounds come from the admin panel
const defaultBackgroundOptions: BackgroundOption[] = [
  {
    id: 'none',
    name: 'No Background',
    description: 'Clean white background',
    preview: null,
    category: 'Minimal',
    tags: ['clean', 'minimal', 'white']
  }
]

const defaultCategories = ['All']

// Helper function to determine orientation from PDF size
const getOrientationFromPdfSize = (pdfSize: string): 'portrait' | 'landscape' => {
  return pdfSize.includes('Landscape') ? 'landscape' : 'portrait'
}

export default function BackgroundSelection({
  value,
  onChange,
  disabled = false,
  className = '',
  pdfSize = 'A4'
}: BackgroundSelectionProps) {
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [previewBackground, setPreviewBackground] = useState<BackgroundOption | null>(null)
  const [backgroundOptions, setBackgroundOptions] = useState<BackgroundOption[]>(defaultBackgroundOptions)
  const [categories, setCategories] = useState<string[]>(defaultCategories)
  const [, setLoading] = useState(true)
  const [showAll, setShowAll] = useState(false)

  // Fetch admin-managed backgrounds on component mount and when pdfSize changes
  useEffect(() => {
    const fetchBackgrounds = async () => {
      try {
        setLoading(true)

        // Determine orientation from PDF size
        const orientation = getOrientationFromPdfSize(pdfSize)

        // Fetch backgrounds filtered by orientation
        const response = await fetch(`/api/resources/backgrounds?orientation=${orientation}`)
        if (response.ok) {
          const data = await response.json()
          const backgrounds = data.backgrounds?.map((bg: any) => {
            // Create preview URL based on file path
            let preview = null
            if (bg.file_path) {
              if (bg.file_path.includes('/admin/') || bg.file_path.includes('admin/')) {
                // Admin-managed background: handle both absolute and relative paths
                let relativePath
                if (bg.file_path.startsWith('/app/')) {
                  relativePath = bg.file_path.replace('/app/', '/')
                } else if (bg.file_path.startsWith('backgrounds/')) {
                  relativePath = `/${bg.file_path}`
                } else {
                  relativePath = bg.file_path
                }
                preview = relativePath.startsWith('/') ? relativePath : `/${relativePath}`
              } else {
                // Default background: just use the filename
                preview = `/backgrounds/${bg.file_path.split('/').pop()}`
              }
            }

            return {
              id: bg.id,
              name: bg.display_name,
              description: bg.description || 'Custom background',
              preview: preview,
              category: bg.category || 'General',
              tags: [bg.category || 'general']
            }
          }) || []

          if (backgrounds.length > 0) {
            // Add the "none" option at the beginning
            setBackgroundOptions([defaultBackgroundOptions[0], ...backgrounds])

            // Update categories
            const uniqueCategories = ['All', ...new Set(backgrounds.map((bg: any) => bg.category).filter(Boolean))] as string[]
            setCategories(uniqueCategories)
          }
        }
      } catch (error) {
        console.error('Failed to fetch backgrounds:', error)
        // Keep using default data on error
      } finally {
        setLoading(false)
      }
    }

    fetchBackgrounds()
  }, [pdfSize])

  const filteredBackgrounds = selectedCategory === 'All'
    ? backgroundOptions
    : backgroundOptions.filter(bg => bg.category === selectedCategory)

  const handleBackgroundSelect = useCallback((backgroundId: string) => {
    if (!disabled) {
      onChange(backgroundId)
    }
  }, [onChange, disabled])

  const handlePreview = useCallback((background: BackgroundOption) => {
    setPreviewBackground(background)
  }, [])

  const handleClosePreview = useCallback(() => {
    setPreviewBackground(null)
  }, [])

  return (
    <div className={cn("space-y-4", className)}>
      {/* Category Filter */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-gray-700">Background Style:</p>
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              disabled={disabled}
              className={cn(
                "px-3 py-1 text-sm rounded-full border transition-all duration-200",
                selectedCategory === category
                  ? "bg-primary-100 border-primary-500 text-primary-700 font-medium"
                  : "bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Background Grid */}
      <div className="relative">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 max-h-[400px] overflow-y-auto pb-2 pr-2">
          {(showAll ? filteredBackgrounds : filteredBackgrounds.slice(0, 8)).map((background) => (
          <div
            key={background.id}
            className={cn(
              "group relative border-2 rounded-lg overflow-hidden cursor-pointer transition-all duration-200",
              value === background.id
                ? "border-primary-500 ring-2 ring-primary-200"
                : "border-gray-200 hover:border-gray-300 hover:shadow-md",
              disabled && "opacity-50 cursor-not-allowed"
            )}
            onClick={() => handleBackgroundSelect(background.id)}
          >
            {/* Background Preview */}
            <div className="aspect-[3/4] bg-gray-100 relative">
              {background.preview ? (
                <img
                  src={background.preview}
                  alt={background.name}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="w-full h-full bg-white flex items-center justify-center">
                  <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                    <Image className="w-6 h-6 text-gray-400" />
                  </div>
                </div>
              )}

              {/* Selection Indicator */}
              {value === background.id && (
                <div className="absolute top-2 right-2 w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}

              {/* Hover Overlay */}
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handlePreview(background)
                  }}
                  disabled={disabled}
                  className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-white bg-opacity-90 hover:bg-opacity-100 rounded-full p-2 shadow-lg"
                  title="Preview background"
                >
                  <Eye className="w-4 h-4 text-gray-700" />
                </button>
              </div>
            </div>

            {/* Background Info */}
            <div className="p-2 bg-white">
              <h4 className="font-medium text-gray-900 text-xs truncate" title={background.name}>{background.name}</h4>
            </div>
          </div>
        ))}
        </div>

        {/* Show More/Less Button */}
        {filteredBackgrounds.length > 8 && (
          <div className="text-center mt-4">
            <button
              onClick={() => setShowAll(!showAll)}
              disabled={disabled}
              className="text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {showAll ? 'Show Less' : `Show All (${filteredBackgrounds.length} backgrounds)`}
            </button>
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {previewBackground && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{previewBackground.name}</h3>
                <p className="text-sm text-gray-500">{previewBackground.description}</p>
              </div>
              <button
                onClick={handleClosePreview}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-4">
              {previewBackground.preview ? (
                <div className="max-h-[50vh] bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
                  <img
                    src={previewBackground.preview}
                    alt={previewBackground.name}
                    className="max-w-full max-h-full object-contain"
                  />
                </div>
              ) : (
                <div className="aspect-[3/4] bg-white border-2 border-gray-200 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <Image className="w-16 h-16 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-500">No background preview</p>
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  {previewBackground.tags && previewBackground.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {previewBackground.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 text-xs bg-white text-gray-600 rounded-full border"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => {
                    handleBackgroundSelect(previewBackground.id)
                    handleClosePreview()
                  }}
                  disabled={disabled}
                  className={cn(
                    "px-4 py-2 rounded-lg font-medium transition-colors",
                    value === previewBackground.id
                      ? "bg-primary-500 text-white"
                      : "bg-primary-600 hover:bg-primary-700 text-white",
                    disabled && "opacity-50 cursor-not-allowed"
                  )}
                >
                  {value === previewBackground.id ? 'Selected' : 'Select Background'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
