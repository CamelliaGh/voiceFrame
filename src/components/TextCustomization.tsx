import { useState, useEffect, useCallback } from 'react'
import { Type } from 'lucide-react'
import { cn } from '@/lib/utils'
import { fontLoader, FontResource } from '@/lib/fontLoader'

interface TextCustomizationProps {
  value: string
  onChange: (text: string) => void
  onFontChange: (fontId: string) => void
  selectedFont: string
  maxLength?: number
  disabled?: boolean
  className?: string
}

// Interface for suggestion categories from API
interface SuggestionCategory {
  id: string
  name: string
  suggestions: string[]
}

const defaultFontOptions = [
  { id: 'script', name: 'Script', description: 'Handwritten style', preview: 'Love' },
  { id: 'elegant', name: 'Elegant', description: 'Sophisticated serif', preview: 'Forever' },
  { id: 'modern', name: 'Modern', description: 'Clean sans-serif', preview: 'Together' },
  { id: 'vintage', name: 'Vintage', description: 'Classic antique feel', preview: 'Always' },
  { id: 'classic', name: 'Classic', description: 'Traditional serif', preview: 'Cherish' }
]

// Font preview styles
const getFontStyle = (fontId: string) => {
  switch (fontId) {
    case 'script':
      return 'font-script'
    case 'elegant':
      return 'font-elegant'
    case 'modern':
      return 'font-modern'
    case 'vintage':
      return 'font-vintage'
    case 'classic':
      return 'font-classic'
    default:
      return 'font-sans'
  }
}

export default function TextCustomization({
  value,
  onChange,
  onFontChange,
  selectedFont,
  maxLength = 200,
  disabled = false,
  className = ''
}: TextCustomizationProps) {
  const [characterCount, setCharacterCount] = useState(value.length)
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())
  const [isNearLimit, setIsNearLimit] = useState(false)
  const [suggestionCategories, setSuggestionCategories] = useState<SuggestionCategory[]>([])
  const [fontOptions, setFontOptions] = useState(defaultFontOptions)
  const [fontClasses, setFontClasses] = useState<Map<string, string>>(new Map())
  const [, setLoading] = useState(true)

  useEffect(() => {
    setCharacterCount(value.length)
    setIsNearLimit(value.length > maxLength * 0.8) // Warning at 80% of limit
  }, [value, maxLength])

  // Fetch admin-managed resources on component mount
  useEffect(() => {
    const fetchResources = async () => {
      try {
        setLoading(true)

        // Fetch suggested texts and organize by category
        const textsResponse = await fetch('/api/resources/suggested-texts')
        if (textsResponse.ok) {
          const textsData = await textsResponse.json()
          const suggestions = textsData.suggested_texts || []

          // Group suggestions by category
          const categoryMap = new Map<string, string[]>()

          suggestions.forEach((item: any) => {
            const category = item.category || 'other'
            if (!categoryMap.has(category)) {
              categoryMap.set(category, [])
            }
            categoryMap.get(category)!.push(item.text)
          })

          // Convert to category objects with proper names
          const categoryNames: Record<string, string> = {
            'romantic': 'Romantic',
            'wedding': 'Wedding',
            'anniversary': 'Anniversary',
            'baby': 'Baby & Family',
            'moments': 'Special Moments',
            'other': 'Other'
          }

          const categories: SuggestionCategory[] = []
          categoryMap.forEach((suggestions, categoryId) => {
            categories.push({
              id: categoryId,
              name: categoryNames[categoryId] || categoryId.charAt(0).toUpperCase() + categoryId.slice(1),
              suggestions: suggestions
            })
          })

          // Sort categories by priority
          const categoryOrder = ['romantic', 'wedding', 'anniversary', 'baby', 'moments', 'other']
          categories.sort((a, b) => {
            const aIndex = categoryOrder.indexOf(a.id)
            const bIndex = categoryOrder.indexOf(b.id)
            return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex)
          })

          setSuggestionCategories(categories)
        }

        // Fetch fonts
        const fontsResponse = await fetch('/api/resources/fonts')
        if (fontsResponse.ok) {
          const fontsData = await fontsResponse.json()
          const fonts: FontResource[] = fontsData.fonts || []

          if (fonts.length > 0) {
            // Map fonts to the expected format
            const mappedFonts = fonts.map((font: FontResource) => ({
              id: font.id,
              name: font.display_name,
              description: font.description || 'Custom font',
              preview: font.display_name
            }))
            setFontOptions(mappedFonts)

            // Load all fonts dynamically
            const loadedFontClasses = await fontLoader.loadFonts(fonts)
            setFontClasses(loadedFontClasses)
          }
        }
      } catch (error) {
        console.error('Failed to fetch resources:', error)
        // Keep using default data on error
      } finally {
        setLoading(false)
      }
    }

    fetchResources()
  }, [])

  const handleTextChange = useCallback((text: string) => {
    if (text.length <= maxLength) {
      onChange(text)
    }
  }, [onChange, maxLength])

  const handleSuggestionClick = useCallback((suggestion: string) => {
    if (suggestion.length <= maxLength) {
      onChange(suggestion)
    }
  }, [onChange, maxLength])

  const toggleCategory = useCallback((categoryId: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev)
      if (next.has(categoryId)) {
        next.delete(categoryId)
      } else {
        next.add(categoryId)
      }
      return next
    })
  }, [])

  const getCharacterCountColor = () => {
    if (characterCount > maxLength * 0.9) return "text-red-600"
    if (characterCount > maxLength * 0.8) return "text-amber-600"
    return "text-gray-500"
  }

  const getCharacterCountWeight = () => {
    if (characterCount > maxLength * 0.8) return "font-semibold"
    return "font-normal"
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Text Input Section */}
      <div className="space-y-3">
        <div className="relative">
          <textarea
            value={value}
            onChange={(e) => handleTextChange(e.target.value)}
            placeholder="Enter your custom message or choose from suggestions below..."
            className={cn(
              "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none transition-all duration-200",
              disabled && "opacity-50 cursor-not-allowed bg-gray-50",
              isNearLimit && "border-amber-300 focus:ring-amber-500"
            )}
            rows={3}
            disabled={disabled}
            maxLength={maxLength}
          />

          {/* Character count indicator */}
          <div className="flex justify-between items-center mt-2">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Characters:</span>
              <span className={cn("text-sm", getCharacterCountColor(), getCharacterCountWeight())}>
                {characterCount}/{maxLength}
              </span>
            </div>

            {/* Progress bar */}
            <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full transition-all duration-300",
                  characterCount > maxLength * 0.9 ? "bg-red-500" :
                  characterCount > maxLength * 0.8 ? "bg-amber-500" :
                  "bg-primary-500"
                )}
                style={{ width: `${Math.min((characterCount / maxLength) * 100, 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Text Suggestions - Categorized & Compact */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Quick suggestions:</p>

          <div className="space-y-1.5">
            {suggestionCategories.map((category) => {
              const isExpanded = expandedCategories.has(category.id)

              return (
                <div key={category.id} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* Category Header - Clickable */}
                  <button
                    onClick={() => toggleCategory(category.id)}
                    className="w-full flex items-center justify-between px-3 py-1.5 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-medium text-gray-900">{category.name}</span>
                      <span className="text-xs text-gray-500">({category.suggestions.length})</span>
                    </div>
                    <svg
                      className={cn(
                        "w-3.5 h-3.5 text-gray-500 transition-transform duration-200",
                        isExpanded && "rotate-180"
                      )}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Category Suggestions - Only show when expanded */}
                  {isExpanded && (
                    <div className="p-2 bg-white border-t border-gray-100">
                      <div className="flex flex-wrap gap-1.5">
                        {category.suggestions.map((suggestion) => (
                          <button
                            key={suggestion}
                            onClick={() => handleSuggestionClick(suggestion)}
                            disabled={disabled}
                            className={cn(
                              "px-2.5 py-1 text-xs bg-white hover:bg-primary-50 text-gray-700 hover:text-primary-700 rounded-md transition-colors duration-200 border border-gray-200 hover:border-primary-300",
                              disabled && "opacity-50 cursor-not-allowed",
                              suggestion.length > maxLength && "opacity-50 cursor-not-allowed"
                            )}
                            title={suggestion.length > maxLength ? `Too long (${suggestion.length}/${maxLength})` : suggestion}
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Font Selection */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Type className="w-4 h-4 text-primary-600" />
          <h4 className="text-sm font-medium text-gray-700">Font Style</h4>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {fontOptions.map((font) => (
            <label
              key={font.id}
              className={cn(
                "flex flex-col items-center p-2.5 border rounded-lg cursor-pointer transition-all duration-200 hover:shadow-sm",
                selectedFont === font.id
                  ? "border-primary-500 bg-primary-50 shadow-sm"
                  : "border-gray-200 hover:border-gray-300",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              <input
                type="radio"
                name="font"
                value={font.id}
                checked={selectedFont === font.id}
                onChange={(e) => onFontChange(e.target.value)}
                disabled={disabled}
                className="sr-only"
              />

              {/* Font preview word */}
              <div className={cn(
                "text-base text-gray-800 mb-1 text-center",
                fontClasses.get(font.id) || getFontStyle(font.id)
              )}>
                Love
              </div>

              {/* Font name */}
              <div className="text-xs font-medium text-gray-700">{font.name}</div>
            </label>
          ))}
        </div>
      </div>

    </div>
  )
}
