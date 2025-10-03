import { useState, useEffect, useCallback } from 'react'
import { Type } from 'lucide-react'
import { cn } from '../lib/utils'

interface TextCustomizationProps {
  value: string
  onChange: (text: string) => void
  onFontChange: (fontId: string) => void
  selectedFont: string
  maxLength?: number
  disabled?: boolean
  className?: string
}

// Default fallback data in case API fails - organized by category
interface SuggestionCategory {
  id: string
  name: string
  emoji: string
  suggestions: string[]
}

const defaultSuggestionCategories: SuggestionCategory[] = [
  {
    id: 'romantic',
    name: 'Romantic',
    emoji: '💕',
    suggestions: [
      "Our Song ♪",
      "I Love You",
      "Forever & Always",
      "Together Forever",
      "My Heart",
      "You & Me",
      "Love Always",
      "My Everything",
      "Heart & Soul",
      "True Love",
      "Soulmates",
      "Love Story"
    ]
  },
  {
    id: 'wedding',
    name: 'Wedding',
    emoji: '💍',
    suggestions: [
      "Wedding Day",
      "First Dance 💕",
      "Mr. & Mrs.",
      "Happily Ever After",
      "Just Married",
      "I Do",
      "Our Vows",
      "Wedding Song",
      "Our Big Day",
      "Husband & Wife"
    ]
  },
  {
    id: 'anniversary',
    name: 'Anniversary',
    emoji: '🎊',
    suggestions: [
      "Our Anniversary",
      "One Year Together",
      "5 Years Strong",
      "10 Years of Love",
      "Celebrating Us",
      "Anniversary Song",
      "Years of Happiness",
      "Our Milestone"
    ]
  },
  {
    id: 'baby',
    name: 'Baby & Family',
    emoji: '👶',
    suggestions: [
      "Baby's First Song",
      "Welcome Little One",
      "Our Family",
      "Sweet Dreams Baby",
      "Little Angel",
      "Family Love",
      "Baby Love",
      "Growing Family"
    ]
  },
  {
    id: 'moments',
    name: 'Special Moments',
    emoji: '✨',
    suggestions: [
      "Perfect Day",
      "Best Day Ever",
      "Unforgettable",
      "Precious Moments",
      "Sweet Memories",
      "Magical Moment",
      "Beautiful Memory",
      "Special Time"
    ]
  }
]

const defaultFontOptions = [
  { id: 'script', name: 'Script', description: 'Handwritten style', preview: 'Script Font' },
  { id: 'elegant', name: 'Elegant', description: 'Sophisticated serif', preview: 'Elegant Font' },
  { id: 'modern', name: 'Modern', description: 'Clean sans-serif', preview: 'Modern Font' },
  { id: 'vintage', name: 'Vintage', description: 'Classic antique feel', preview: 'Vintage Font' },
  { id: 'classic', name: 'Classic', description: 'Traditional serif', preview: 'Classic Font' }
]

// Font preview styles
const getFontStyle = (fontId: string) => {
  switch (fontId) {
    case 'script':
      return 'font-script'
    case 'elegant':
      return 'font-serif'
    case 'modern':
      return 'font-sans'
    case 'vintage':
      return 'font-serif italic'
    case 'classic':
      return 'font-serif'
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
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['romantic']))
  const [isNearLimit, setIsNearLimit] = useState(false)
  const [suggestionCategories, setSuggestionCategories] = useState<SuggestionCategory[]>(defaultSuggestionCategories)
  const [fontOptions, setFontOptions] = useState(defaultFontOptions)
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

        // Fetch suggested texts (keep existing API, but organize by category if available)
        const textsResponse = await fetch('/api/resources/suggested-texts')
        if (textsResponse.ok) {
          const textsData = await textsResponse.json()
          const suggestions = textsData.suggested_texts?.map((item: any) => item.text) || []
          // If API returns suggestions, add them to the "Popular" category
          if (suggestions.length > 0) {
            const popularCategory: SuggestionCategory = {
              id: 'popular',
              name: 'Popular',
              emoji: '⭐',
              suggestions: suggestions.slice(0, 12)
            }
            setSuggestionCategories([popularCategory, ...defaultSuggestionCategories])
          }
        }

        // Fetch fonts
        const fontsResponse = await fetch('/api/resources/fonts')
        if (fontsResponse.ok) {
          const fontsData = await fontsResponse.json()
          const fonts = fontsData.fonts?.map((font: any) => ({
            id: font.id,
            name: font.display_name,
            description: font.description || 'Custom font',
            preview: font.display_name
          })) || []
          if (fonts.length > 0) {
            setFontOptions(fonts)
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

        {/* Text Suggestions - Categorized */}
        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-700">Quick suggestions:</p>

          <div className="space-y-2">
            {suggestionCategories.map((category) => {
              const isExpanded = expandedCategories.has(category.id)
              const visibleSuggestions = isExpanded ? category.suggestions : category.suggestions.slice(0, 4)

              return (
                <div key={category.id} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* Category Header */}
                  <button
                    onClick={() => toggleCategory(category.id)}
                    className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-base">{category.emoji}</span>
                      <span className="text-sm font-medium text-gray-900">{category.name}</span>
                      <span className="text-xs text-gray-500">({category.suggestions.length})</span>
                    </div>
                    <svg
                      className={cn(
                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                        isExpanded && "rotate-180"
                      )}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Category Suggestions */}
                  <div className="p-2 bg-white">
                    <div className="flex flex-wrap gap-1.5">
                      {visibleSuggestions.map((suggestion) => (
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

                    {!isExpanded && category.suggestions.length > 4 && (
                      <button
                        onClick={() => toggleCategory(category.id)}
                        className="mt-2 text-xs text-primary-600 hover:text-primary-700 font-medium"
                      >
                        +{category.suggestions.length - 4} more
                      </button>
                    )}
                  </div>
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
                getFontStyle(font.id)
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
