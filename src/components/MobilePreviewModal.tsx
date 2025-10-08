import { useState, useRef, useEffect } from 'react'
import { X, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'

interface MobilePreviewModalProps {
  imageUrl: string
  onClose: () => void
  pdfSize?: string
}

export default function MobilePreviewModal({ imageUrl, onClose, pdfSize }: MobilePreviewModalProps) {
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const lastTouchDistance = useRef(0)

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = ''
    }
  }, [])

  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      const distance = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      )
      lastTouchDistance.current = distance
    } else if (e.touches.length === 1) {
      setIsDragging(true)
      setDragStart({
        x: e.touches[0].clientX - position.x,
        y: e.touches[0].clientY - position.y
      })
    }
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    e.preventDefault()

    if (e.touches.length === 2) {
      const distance = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      )

      if (lastTouchDistance.current > 0) {
        const delta = distance / lastTouchDistance.current
        const newScale = Math.max(1, Math.min(4, scale * delta))
        setScale(newScale)
      }
      lastTouchDistance.current = distance
    } else if (e.touches.length === 1 && isDragging && scale > 1) {
      setPosition({
        x: e.touches[0].clientX - dragStart.x,
        y: e.touches[0].clientY - dragStart.y
      })
    }
  }

  const handleTouchEnd = () => {
    setIsDragging(false)
    lastTouchDistance.current = 0
  }

  const handleZoomIn = () => {
    setScale(prev => Math.min(4, prev + 0.5))
  }

  const handleZoomOut = () => {
    const newScale = Math.max(1, scale - 0.5)
    setScale(newScale)
    if (newScale === 1) {
      setPosition({ x: 0, y: 0 })
    }
  }

  const handleReset = () => {
    setScale(1)
    setPosition({ x: 0, y: 0 })
  }

  return (
    <div className="fixed inset-0 z-50 bg-black">
      <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/80 to-transparent z-10 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={onClose}
            className="p-2 rounded-full bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 transition-colors"
            aria-label="Close preview"
          >
            <X className="w-6 h-6" />
          </button>
          {pdfSize && (
            <span className="text-white text-sm font-medium">
              {pdfSize.replace('_', ' ')}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleZoomOut}
            disabled={scale <= 1}
            className="p-2 rounded-full bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 disabled:opacity-50 disabled:hover:bg-white/10 transition-colors"
            aria-label="Zoom out"
          >
            <ZoomOut className="w-5 h-5" />
          </button>

          <span className="text-white text-sm font-medium min-w-[3rem] text-center">
            {Math.round(scale * 100)}%
          </span>

          <button
            onClick={handleZoomIn}
            disabled={scale >= 4}
            className="p-2 rounded-full bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 disabled:opacity-50 disabled:hover:bg-white/10 transition-colors"
            aria-label="Zoom in"
          >
            <ZoomIn className="w-5 h-5" />
          </button>

          {scale > 1 && (
            <button
              onClick={handleReset}
              className="p-2 rounded-full bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 transition-colors"
              aria-label="Reset zoom"
            >
              <Maximize2 className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      <div
        ref={containerRef}
        className="w-full h-full flex items-center justify-center overflow-hidden touch-none"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <img
          ref={imageRef}
          src={imageUrl}
          alt="Poster Preview"
          className="max-w-full max-h-full object-contain select-none"
          style={{
            transform: `scale(${scale}) translate(${position.x / scale}px, ${position.y / scale}px)`,
            transition: isDragging ? 'none' : 'transform 0.2s ease-out',
            cursor: scale > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default'
          }}
          draggable={false}
        />
      </div>

      {scale === 1 && (
        <div className="absolute bottom-8 left-0 right-0 text-center">
          <p className="text-white/70 text-sm">
            Pinch to zoom • Drag to pan
          </p>
        </div>
      )}
    </div>
  )
}
