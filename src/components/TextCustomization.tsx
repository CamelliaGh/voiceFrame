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

// Default fallback data in case API fails
const defaultTextSuggestions = [
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
  "Love Story",
  "Made for Each Other",
  "In Love",
  "Love You More",
  "Wedding Day",
  "First Dance 💕",
  "Mr. & Mrs.",
  "Happily Ever After",
  "Just Married",
  "Wedding Memories",
  "Our Big Day",
  "I Do",
  "Married Life",
  "Husband & Wife",
  "Wedding Song",
  "Our Vows",
  "Wedding Day Magic",
  "Anniversary Memory",
  "One Year Together",
  "5 Years Strong",
  "10 Years of Love",
  "Golden Anniversary",
  "Our Anniversary",
  "Celebrating Us",
  "Years of Happiness",
  "Anniversary Song",
  "Special Date",
  "Our Milestone",
  "Baby's First Song",
  "Welcome Little One",
  "Our Family",
  "Mommy & Daddy Love You",
  "Sweet Dreams Baby",
  "Little Angel",
  "Family Love",
  "Our Child",
  "Growing Family",
  "Baby Love",
  "Family Song",
  "Special Moment",
  "Perfect Day",
  "Our Memories",
  "Best Day Ever",
  "Unforgettable",
  "Precious Moments",
  "Sweet Memories",
  "Amazing Day",
  "Wonderful Time",
  "Happy Times",
  "Beautiful Memory",
  "Magical Moment",
  "Cherished Memory",
  "Special Time",
  "Incredible Day"
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
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [isNearLimit, setIsNearLimit] = useState(false)
  const [textSuggestions, setTextSuggestions] = useState<string[]>(defaultTextSuggestions)
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

        // Fetch suggested texts
        const textsResponse = await fetch('/api/resources/suggested-texts')
        if (textsResponse.ok) {
          const textsData = await textsResponse.json()
          const suggestions = textsData.suggested_texts?.map((item: any) => item.text) || []
          if (suggestions.length > 0) {
            setTextSuggestions(suggestions)
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
      setShowSuggestions(false)
    }
  }, [onChange, maxLength])

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
            placeholder="Enter your custom message..."
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

        {/* Text Suggestions */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-700">Suggestions:</p>
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="text-xs text-primary-600 hover:text-primary-700 font-medium transition-colors"
            >
              {showSuggestions ? 'Hide' : 'Show all'}
            </button>
          </div>

          <div className={cn(
            "flex flex-wrap gap-2 transition-all duration-200",
            showSuggestions ? "max-h-96 overflow-y-auto" : "max-h-20 overflow-hidden"
          )}>
            {textSuggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={disabled}
                className={cn(
                  "px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors duration-200 border border-transparent hover:border-gray-300",
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
      </div>

      {/* Font Selection */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Type className="w-4 h-4 text-primary-600" />
          <h4 className="text-sm font-medium text-gray-700">Font Style</h4>
        </div>

        <div className="grid grid-cols-1 gap-2">
          {fontOptions.map((font) => (
            <label
              key={font.id}
              className={cn(
                "flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-all duration-200 hover:shadow-sm",
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
                className="text-primary-600 focus:ring-primary-500"
              />

              <div className="flex-1 flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900">{font.name}</div>
                  <div className="text-xs text-gray-500">{font.description}</div>
                </div>

                {/* Font preview */}
                <div className={cn(
                  "text-sm text-gray-600 px-2 py-1 rounded border bg-white",
                  getFontStyle(font.id)
                )}>
                  {font.preview}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Current text preview with selected font */}
      {value && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Preview:</p>
          <div className={cn(
            "p-4 border rounded-lg bg-gray-50 text-center",
            getFontStyle(selectedFont),
            "text-lg"
          )}>
            {value}
          </div>
        </div>
      )}
    </div>
  )
}
