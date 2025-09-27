import React, { useCallback } from 'react'
import { Square, Circle, Image } from 'lucide-react'
import { cn } from '../lib/utils'

interface PhotoShapeOption {
  id: 'square' | 'circle'
  name: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  preview: string
}

interface PhotoShapeCustomizationProps {
  value: 'square' | 'circle'
  onChange: (shape: 'square' | 'circle') => void
  disabled?: boolean
  className?: string
}

const photoShapeOptions: PhotoShapeOption[] = [
  {
    id: 'square',
    name: 'Rectangle',
    description: 'Standard rectangular photo using template dimensions',
    icon: Square,
    preview: 'rectangle'
  },
  {
    id: 'circle',
    name: 'Circle',
    description: 'Modern circular photo with rounded edges',
    icon: Circle,
    preview: 'circle'
  }
]

export default function PhotoShapeCustomization({
  value,
  onChange,
  disabled = false,
  className = ''
}: PhotoShapeCustomizationProps) {
  const handleShapeSelect = useCallback((shape: 'square' | 'circle') => {
    if (!disabled) {
      onChange(shape)
    }
  }, [onChange, disabled])

  return (
    <div className={cn("space-y-4", className)}>
      {/* Photo Shape Options */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {photoShapeOptions.map((option) => {
          const IconComponent = option.icon
          const isSelected = value === option.id

          return (
            <div
              key={option.id}
              className={cn(
                "group relative border-2 rounded-lg overflow-hidden cursor-pointer transition-all duration-200",
                isSelected
                  ? "border-primary-500 ring-2 ring-primary-200"
                  : "border-gray-200 hover:border-gray-300 hover:shadow-md",
                disabled && "opacity-50 cursor-not-allowed"
              )}
              onClick={() => handleShapeSelect(option.id)}
            >
              {/* Shape Preview */}
              <div className="aspect-square bg-gray-50 flex items-center justify-center relative">
                {/* Background pattern to show shape effect */}
                <div className="absolute inset-2 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg" />

                {/* Photo placeholder with shape */}
                <div className={cn(
                  "relative w-24 h-16 bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center",
                  option.id === 'circle' ? 'rounded-full' : 'rounded-lg'
                )}>
                  <Image className="w-8 h-8 text-primary-600" />
                </div>

                {/* Selection Indicator */}
                {isSelected && (
                  <div className="absolute top-2 right-2 w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}

                {/* Hover Overlay */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all duration-200" />
              </div>

              {/* Shape Info */}
              <div className="p-3 bg-white">
                <div className="flex items-center space-x-2 mb-1">
                  <IconComponent className="w-4 h-4 text-gray-600" />
                  <h4 className="font-medium text-gray-900 text-sm">{option.name}</h4>
                </div>
                <p className="text-xs text-gray-500">{option.description}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Shape Preview with Example */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-gray-700">Preview:</p>
        <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <div className="relative">
            {/* Example photo with selected shape */}
            <div className={cn(
              "w-16 h-12 bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center relative overflow-hidden",
              value === 'circle' ? 'rounded-full' : 'rounded-lg'
            )}>
              <Image className="w-6 h-6 text-blue-600" />
            </div>

            {/* Shape indicator */}
            <div className={cn(
              "absolute -inset-1 border-2 border-dashed border-gray-300",
              value === 'circle' ? 'rounded-full' : 'rounded-lg'
            )} />
          </div>

          <div className="flex-1">
            <p className="text-sm text-gray-600">
              Your photo will be displayed as a{' '}
              <span className="font-medium text-gray-900">
                {value === 'circle' ? 'circle' : 'rectangle'}
              </span>{' '}
              in the final poster.
            </p>
          </div>
        </div>
      </div>

      {/* Shape Information */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-medium text-blue-900">Photo Shape Tips</h4>
            <ul className="text-xs text-blue-700 mt-1 space-y-1">
              <li>• <strong>Rectangle:</strong> Uses the template's dimensions for optimal fit</li>
              <li>• <strong>Circle:</strong> Creates a modern, elegant look centered in the photo area</li>
              <li>• Both shapes work well with all background options</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
