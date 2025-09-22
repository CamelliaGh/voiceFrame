import { useState, useEffect } from 'react'
import { Eye, RefreshCw } from 'lucide-react'
import { useSession } from '../contexts/SessionContext'
import { getPreviewUrl } from '../lib/api'

interface RealTimePreviewProps {
  className?: string
}

export default function RealTimePreview({ className = '' }: RealTimePreviewProps) {
  const { session } = useSession()
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Calculate aspect ratio based on PDF size
  const getAspectRatio = (pdfSize: string) => {
    switch (pdfSize) {
      case 'A4':
        return 'aspect-[3/4]' // A4 Portrait
      case 'A4_Landscape':
        return 'aspect-[4/3]' // A4 Landscape
      case 'Letter':
        return 'aspect-[3/4]' // Letter Portrait
      case 'Letter_Landscape':
        return 'aspect-[4/3]' // Letter Landscape
      case 'A3':
        return 'aspect-[2/3]' // A3 Portrait
      case 'A3_Landscape':
        return 'aspect-[3/2]' // A3 Landscape
      default:
        return 'aspect-[3/4]' // Default fallback
    }
  }

  const aspectRatio = session?.pdf_size ? getAspectRatio(session.pdf_size) : 'aspect-[3/4]'

  const generatePreview = async () => {
    if (!session) return

    setLoading(true)
    setError(null)

    try {
      const response = await getPreviewUrl(session.session_token)
      setPreviewUrl(response.preview_url)
    } catch (err: any) {
      console.error('Failed to generate preview:', err)
      
      // Extract specific error message from the response
      let errorMessage = 'Failed to generate preview'
      
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        if (detail.includes('Audio file is missing')) {
          errorMessage = 'Upload audio to see preview'
        } else if (detail.includes('Waveform file is missing')) {
          errorMessage = 'Processing audio...'
        } else if (detail.includes('Photo file is missing')) {
          errorMessage = 'Upload photo to see preview'
        } else {
          errorMessage = 'Preview unavailable'
        }
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // Auto-generate preview when session data changes
  useEffect(() => {
    generatePreview()
  }, [session?.custom_text, session?.pdf_size, session?.template_id, session?.background_id, session?.photo_s3_key, session?.waveform_s3_key])

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
          <Eye className="w-5 h-5 text-primary-600" />
          <span>Live Preview</span>
        </h3>
        <button
          onClick={generatePreview}
          disabled={loading}
          className="text-sm text-primary-600 hover:text-primary-700 flex items-center space-x-1"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
        {loading ? (
          <div className={`${aspectRatio} bg-gray-50 flex items-center justify-center`}>
            <div className="text-center">
              <div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-xs text-gray-600">Updating preview...</p>
            </div>
          </div>
        ) : error ? (
          <div className={`${aspectRatio} bg-gray-50 flex items-center justify-center`}>
            <div className="text-center text-gray-500">
              <Eye className="w-8 h-8 mx-auto mb-2" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          </div>
        ) : previewUrl ? (
          <iframe
            src={previewUrl}
            className={`w-full ${aspectRatio}`}
            title="Live Preview"
          />
        ) : (
          <div className={`${aspectRatio} bg-gray-100 flex items-center justify-center`}>
            <div className="text-center text-gray-500">
              <Eye className="w-8 h-8 mx-auto mb-2" />
              <p className="text-sm">Preview not available</p>
            </div>
          </div>
        )}
      </div>

      {previewUrl && (
        <div className="text-center">
          <p className="text-xs text-gray-500">
            This preview includes a watermark. Purchase to download the clean version.
          </p>
        </div>
      )}
    </div>
  )
}
