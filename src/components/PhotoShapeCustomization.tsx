import React, { useCallback } from 'react'
import { Square, Circle, Image, Maximize } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PhotoShapeOption {
  id: 'square' | 'circle' | 'fullpage'
  name: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  preview: string
}

interface PhotoShapeCustomizationProps {
  value: 'square' | 'circle' | 'fullpage'
  onChange: (shape: 'square' | 'circle' | 'fullpage') => void
  disabled?: boolean
  className?: string
}

const photoShapeOptions: PhotoShapeOption[] = [
  {
    id: 'square',
    name: 'Rectangle',
    description: 'Standard rectangular photo',
    icon: Square,
    preview: 'rectangle'
  },
  {
    id: 'circle',
    name: 'Circle',
    description: 'Modern circular photo',
    icon: Circle,
    preview: 'circle'
  },
  {
    id: 'fullpage',
    name: 'Full Page',
    description: 'Photo covers entire page with gray elements',
    icon: Maximize,
    preview: 'fullpage'
  }
]

export default function PhotoShapeCustomization({
  value,
  onChange,
  disabled = false,
  className = ''
}: PhotoShapeCustomizationProps) {
  const handleShapeSelect = useCallback((shape: 'square' | 'circle' | 'fullpage') => {
    if (!disabled) {
      onChange(shape)
    }
  }, [onChange, disabled])

  return (
    <div className={cn("space-y-3", className)}>
      {/* Photo Shape Options - Compact */}
      <div className="grid grid-cols-3 gap-2">
        {photoShapeOptions.map((option) => {
          const IconComponent = option.icon
          const isSelected = value === option.id

          return (
            <div
              key={option.id}
              className={cn(
                "group relative border-2 rounded-lg overflow-hidden cursor-pointer transition-all duration-200",
                isSelected
                  ? "border-primary-500 bg-primary-50"
                  : "border-gray-200 hover:border-gray-300",
                disabled && "opacity-50 cursor-not-allowed"
              )}
              onClick={() => handleShapeSelect(option.id)}
            >
              {/* Compact Shape Preview */}
              <div className="aspect-[4/3] bg-gray-50 flex items-center justify-center relative p-3">
                {/* Photo placeholder with shape */}
                <div className={cn(
                  "relative w-16 h-12 bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center",
                  option.id === 'circle' ? 'rounded-full w-14 h-14' :
                  option.id === 'fullpage' ? 'w-full h-full rounded-none' : 'rounded-md'
                )}>
                  <Image className="w-6 h-6 text-primary-600" />
                </div>

                {/* Selection Indicator */}
                {isSelected && (
                  <div className="absolute top-1.5 right-1.5 w-5 h-5 bg-primary-500 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>

              {/* Shape Info - Compact */}
              <div className="p-2 bg-white border-t">
                <div className="flex items-center justify-center space-x-1.5">
                  <IconComponent className="w-3.5 h-3.5 text-gray-600" />
                  <h4 className="font-medium text-gray-900 text-sm">{option.name}</h4>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
