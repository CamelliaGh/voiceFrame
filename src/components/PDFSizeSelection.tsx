import React, { useState, useCallback } from 'react'
import { FileText, Maximize2, RotateCcw, Monitor } from 'lucide-react'
import { cn } from '../lib/utils'

interface PDFSizeOption {
  value: 'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape'
  label: string
  dimensions: string
  category: 'A4' | 'Letter' | 'A3'
  orientation: 'Portrait' | 'Landscape'
  description: string
  icon: React.ComponentType<{ className?: string }>
}

interface PDFSizeSelectionProps {
  value: 'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape'
  onChange: (size: 'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape') => void
  disabled?: boolean
  className?: string
}

const pdfSizeOptions: PDFSizeOption[] = [
  {
    value: 'A4',
    label: 'A4 Portrait',
    dimensions: '210 × 297 mm',
    category: 'A4',
    orientation: 'Portrait',
    description: 'Standard portrait format',
    icon: FileText
  },
  {
    value: 'A4_Landscape',
    label: 'A4 Landscape',
    dimensions: '297 × 210 mm',
    category: 'A4',
    orientation: 'Landscape',
    description: 'Wide landscape format',
    icon: Maximize2
  },
  {
    value: 'Letter',
    label: 'US Letter Portrait',
    dimensions: '8.5 × 11 in',
    category: 'Letter',
    orientation: 'Portrait',
    description: 'US standard portrait',
    icon: FileText
  },
  {
    value: 'Letter_Landscape',
    label: 'US Letter Landscape',
    dimensions: '11 × 8.5 in',
    category: 'Letter',
    orientation: 'Landscape',
    description: 'US standard landscape',
    icon: Maximize2
  },
  {
    value: 'A3',
    label: 'A3 Portrait',
    dimensions: '297 × 420 mm',
    category: 'A3',
    orientation: 'Portrait',
    description: 'Large portrait format',
    icon: Monitor
  },
  {
    value: 'A3_Landscape',
    label: 'A3 Landscape',
    dimensions: '420 × 297 mm',
    category: 'A3',
    orientation: 'Landscape',
    description: 'Large landscape format',
    icon: Monitor
  }
]

const categories = ['A4', 'Letter', 'A3']

export default function PDFSizeSelection({
  value,
  onChange,
  disabled = false,
  className = ''
}: PDFSizeSelectionProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>(
    pdfSizeOptions.find(option => option.value === value)?.category || 'A4'
  )

  const filteredOptions = selectedCategory === 'All'
    ? pdfSizeOptions
    : pdfSizeOptions.filter(option => option.category === selectedCategory)

  const handleSizeSelect = useCallback((sizeValue: 'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape') => {
    if (!disabled) {
      onChange(sizeValue)
      // Update category when selection changes
      const selectedOption = pdfSizeOptions.find(option => option.value === sizeValue)
      if (selectedOption) {
        setSelectedCategory(selectedOption.category)
      }
    }
  }, [onChange, disabled])

  const getSizePreview = (option: PDFSizeOption) => {
    const isLandscape = option.orientation === 'Landscape'
    return (
      <div className={cn(
        "w-12 h-8 border-2 border-gray-300 bg-white flex items-center justify-center",
        isLandscape ? "rounded-lg" : "rounded-sm"
      )}>
        <option.icon className={cn(
          "text-gray-600",
          isLandscape ? "w-4 h-3" : "w-3 h-4"
        )} />
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Category Filter */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-gray-700">Paper Size:</p>
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

      {/* Size Options */}
      <div className="space-y-2">
        {filteredOptions.map((option) => {
          const isSelected = value === option.value

          return (
            <div
              key={option.value}
              className={cn(
                "group relative border-2 rounded-lg overflow-hidden cursor-pointer transition-all duration-200",
                isSelected
                  ? "border-primary-500 ring-2 ring-primary-200"
                  : "border-gray-200 hover:border-gray-300 hover:shadow-md",
                disabled && "opacity-50 cursor-not-allowed"
              )}
              onClick={() => handleSizeSelect(option.value)}
            >
              <div className="flex items-center justify-between p-4">
                <div className="flex items-center space-x-4">
                  {/* Size Preview */}
                  {getSizePreview(option)}

                  {/* Size Info */}
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">{option.label}</h4>
                      {option.orientation === 'Landscape' && (
                        <RotateCcw className="w-4 h-4 text-gray-400" />
                      )}
                    </div>
                    <p className="text-sm text-gray-500">{option.dimensions}</p>
                    <p className="text-xs text-gray-400">{option.description}</p>
                  </div>
                </div>

                {/* Selection Indicator */}
                {isSelected && (
                  <div className="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Size Comparison Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-medium text-blue-900">Size Guide</h4>
            <ul className="text-xs text-blue-700 mt-1 space-y-1">
              <li>• <strong>A4:</strong> International standard (210 × 297 mm)</li>
              <li>• <strong>Letter:</strong> US standard (8.5 × 11 in)</li>
              <li>• <strong>A3:</strong> Large format, twice the size of A4</li>
              <li>• <strong>Landscape:</strong> Wide format, great for panoramic photos</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Current Selection Preview */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-gray-700">Selected Format:</p>
        <div className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
          {(() => {
            const selectedOption = pdfSizeOptions.find(option => option.value === value)
            if (!selectedOption) return null

            return (
              <>
                {getSizePreview(selectedOption)}
                <div>
                  <p className="text-sm font-medium text-gray-900">{selectedOption.label}</p>
                  <p className="text-xs text-gray-500">{selectedOption.dimensions}</p>
                </div>
              </>
            )
          })()}
        </div>
      </div>
    </div>
  )
}
