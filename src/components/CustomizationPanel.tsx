import { useState, useEffect } from 'react'
import { Type, FileText, ArrowLeft, ArrowRight } from 'lucide-react'
import { useSession } from '../contexts/SessionContext'
import { cn } from '../lib/utils'

interface CustomizationPanelProps {
  onNext: () => void
  onBack: () => void
}

const textSuggestions = [
  "Our Song ♪",
  "First Dance 💕",
  "Wedding Day",
  "Anniversary Memory",
  "I Love You",
  "Forever & Always",
  "Our Love Story",
  "Special Moment",
  "Together Forever",
  "You & Me",
  "My Heart",
  "Perfect Day"
]


// Framed template variants for different sizes
const getFramedTemplateId = (pdfSize: string) => {
  switch (pdfSize) {
    case 'A4_Landscape':
      return 'framed_a4_landscape'
    case 'A4':
      return 'framed_a4_portrait'
    case 'Letter_Landscape':
      return 'framed_letter_landscape'
    case 'Letter':
      return 'framed_letter_portrait'
    default:
      return 'framed_a4_landscape' // Default to A4 landscape
  }
}

export default function CustomizationPanel({ onNext, onBack }: CustomizationPanelProps) {
  const { session, updateSessionData } = useSession()
  const [customText, setCustomText] = useState(session?.custom_text || '')
  const [pdfSize, setPdfSize] = useState<'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape'>(session?.pdf_size || 'A4')
  const [characterCount, setCharacterCount] = useState(0)

  useEffect(() => {
    setCharacterCount(customText.length)
  }, [customText])

  const handleTextChange = (text: string) => {
    if (text.length <= 200) {
      setCustomText(text)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    if (suggestion.length <= 200) {
      setCustomText(suggestion)
    }
  }

  const handleSave = async () => {
    if (!session) return

    // Always use the appropriate framed template variant based on PDF size
    const finalTemplateId = getFramedTemplateId(pdfSize)

    await updateSessionData({
      custom_text: customText,
      pdf_size: pdfSize,
      template_id: finalTemplateId
    })
  }

  const handleNext = async () => {
    await handleSave()
    onNext()
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Customize Your Poster</h2>
        <p className="text-gray-600">
          Personalize your audio poster with custom text, shapes, and styling options.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Customization Options */}
        <div className="space-y-6">
          {/* Custom Text */}
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <Type className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold text-gray-900">Custom Text</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <textarea
                  value={customText}
                  onChange={(e) => handleTextChange(e.target.value)}
                  placeholder="Enter your custom message..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                  rows={3}
                />
                <div className="flex justify-between items-center mt-2">
                  <span className={cn(
                    "text-sm",
                    characterCount > 180 ? "text-red-600" : "text-gray-500"
                  )}>
                    {characterCount}/200 characters
                  </span>
                </div>
              </div>
              
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Suggestions:</p>
                <div className="flex flex-wrap gap-2">
                  {textSuggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors duration-200"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>


          {/* PDF Size */}
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <FileText className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold text-gray-900">PDF Size</h3>
            </div>
            
            <div className="space-y-2">
              {              [
                { value: 'A4', label: 'A4 Portrait (210 × 297 mm)' },
                { value: 'A4_Landscape', label: 'A4 Landscape (297 × 210 mm)' },
                { value: 'Letter', label: 'US Letter Portrait (8.5 × 11 in)' },
                { value: 'Letter_Landscape', label: 'US Letter Landscape (11 × 8.5 in)' },
                { value: 'A3', label: 'A3 Portrait (297 × 420 mm)' },
                { value: 'A3_Landscape', label: 'A3 Landscape (420 × 297 mm)' }
              ].map((size) => (
                <label
                  key={size.value}
                  className={cn(
                    'flex items-center justify-between p-3 border rounded-lg cursor-pointer transition-colors duration-200',
                    pdfSize === size.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                >
                  <div className="flex items-center space-x-3">
                    <input
                      type="radio"
                      name="pdfSize"
                      value={size.value}
                      checked={pdfSize === size.value}
                      onChange={(e) => setPdfSize(e.target.value as 'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape')}
                      className="text-primary-600 focus:ring-primary-500"
                    />
                    <span className="font-medium">{size.label}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

        </div>

        {/* Live Preview Placeholder */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Live Preview</h3>
          <div className="aspect-[3/4] bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-2" />
              <p>Preview will appear here</p>
              <p className="text-sm">Customize options to see changes</p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-6">
        <button
          onClick={onBack}
          className="btn-secondary flex items-center space-x-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Upload</span>
        </button>
        
        <button
          onClick={handleNext}
          className="btn-primary flex items-center space-x-2"
        >
          <span>Continue to Preview</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
