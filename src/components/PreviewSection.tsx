import { useState, useEffect } from 'react'
import { Download, Eye, ArrowLeft, ArrowRight, RefreshCw } from 'lucide-react'
import { useSession } from '../contexts/SessionContext'
import { getPreviewUrl } from '../lib/api'

interface PreviewSectionProps {
  onNext: () => void
  onBack: () => void
}

export default function PreviewSection({ onNext, onBack }: PreviewSectionProps) {
  const { session } = useSession()
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Calculate aspect ratio based on PDF size (adjusted for better viewport fit)
  const getAspectRatio = (pdfSize: string) => {
    switch (pdfSize) {
      case 'A4':
        return 'aspect-[3/4]' // A4 Portrait: adjusted for viewport
      case 'A4_Landscape':
        return 'aspect-[4/3]' // A4 Landscape: adjusted for viewport
      case 'Letter':
        return 'aspect-[3/4]' // Letter Portrait: adjusted for viewport
      case 'Letter_Landscape':
        return 'aspect-[4/3]' // Letter Landscape: adjusted for viewport
      case 'A3':
        return 'aspect-[2/3]' // A3 Portrait: adjusted for viewport
      case 'A3_Landscape':
        return 'aspect-[3/2]' // A3 Landscape: adjusted for viewport
      default:
        return 'aspect-[3/4]' // Default fallback
    }
  }

  const aspectRatio = session?.pdf_size ? getAspectRatio(session.pdf_size) : 'aspect-[3/4]'

  const generatePreview = async () => {
    if (!session) return

    console.log('🎯 PreviewSection: generatePreview called for photo_shape:', session.photo_shape)
    setLoading(true)
    setError(null)

    try {
      console.log('🎯 PreviewSection: Making preview request...')
      const response = await getPreviewUrl(session.session_token)
      console.log('🎯 PreviewSection: Preview response received:', response)
      // Add cache-busting parameter to prevent browser caching
      const cacheBustingUrl = `${response}?t=${Date.now()}`
      console.log('🎯 PreviewSection: Using cache-busting URL:', cacheBustingUrl)
      setPreviewUrl(cacheBustingUrl)
    } catch (err: any) {
      console.error('Failed to generate preview:', err)

      // Extract specific error message from the response
      let errorMessage = 'Failed to generate preview. Please try again.'

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        if (detail.includes('Audio file is missing')) {
          errorMessage = 'Audio file is missing. Please upload your audio file again.'
        } else if (detail.includes('Waveform file is missing')) {
          errorMessage = 'Audio is still processing. Please wait a moment and try again.'
        } else if (detail.includes('Photo file is missing')) {
          errorMessage = 'Photo file is missing. Please upload your photo again.'
        } else if (detail.includes('Failed to upload audio to S3')) {
          errorMessage = 'Failed to upload audio file. Please check your connection and try again.'
        } else if (detail.includes('Session audio file missing')) {
          errorMessage = 'Audio file was not properly uploaded. Please try uploading your audio again.'
        } else {
          errorMessage = detail
        }
      } else if (err.message) {
        errorMessage = `Error: ${err.message}`
      }

      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    console.log('🎯 PreviewSection: useEffect triggered, session photo_shape:', session?.photo_shape)
    generatePreview()
  }, [session?.custom_text, session?.pdf_size, session?.template_id, session?.background_id, session?.photo_shape, session?.photo_url, session?.waveform_url])

  const handleDownloadPreview = () => {
    if (previewUrl) {
      const link = document.createElement('a')
      link.href = previewUrl
      link.download = 'audio-poster-preview.pdf'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Preview Your Poster</h2>
        <p className="text-gray-600">
          Here's how your audio poster will look. The watermarked version shows the final layout.
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Preview */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Poster Preview</h3>
                {session?.pdf_size && (
                  <p className="text-sm text-gray-600 mt-1">
                    Size: {session.pdf_size.replace('_', ' ')}
                  </p>
                )}
              </div>
              <button
                onClick={generatePreview}
                disabled={loading}
                className="btn-secondary flex items-center space-x-2 text-sm"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>

            <div className="border border-gray-200 rounded-lg overflow-hidden">
              {loading ? (
                <div className={`${aspectRatio} bg-gray-50 flex items-center justify-center`}>
                  <div className="text-center">
                    <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-sm text-gray-600">Generating preview...</p>
                  </div>
                </div>
              ) : error ? (
                <div className={`${aspectRatio} bg-red-50 flex items-center justify-center`}>
                  <div className="text-center text-red-600">
                    <p className="font-medium">{error}</p>
                    <button
                      onClick={generatePreview}
                      className="mt-2 text-sm underline hover:no-underline"
                    >
                      Try again
                    </button>
                  </div>
                </div>
              ) : previewUrl ? (
                <iframe
                  src={previewUrl}
                  className={`w-full ${aspectRatio}`}
                  title="Poster Preview"
                />
              ) : (
                <div className={`${aspectRatio} bg-gray-100 flex items-center justify-center`}>
                  <div className="text-center text-gray-500">
                    <Eye className="w-12 h-12 mx-auto mb-2" />
                    <p>Preview not available</p>
                  </div>
                </div>
              )}
            </div>

            {previewUrl && (
              <div className="mt-4 flex justify-center">
                <button
                  onClick={handleDownloadPreview}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Watermarked Preview</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Summary & Details */}
        <div className="space-y-6">
          {/* Poster Details */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Poster Details</h3>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Custom Text:</span>
                <span className="font-medium max-w-32 text-right truncate">
                  {session?.custom_text || 'None'}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-600">Photo Shape:</span>
                <span className="font-medium capitalize">
                  {session?.photo_shape || 'Square'}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-600">PDF Size:</span>
                <span className="font-medium">
                  {session?.pdf_size || 'A4'}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-600">Template:</span>
                <span className="font-medium capitalize">
                  {session?.template_id || 'Classic'}
                </span>
              </div>

              {session?.audio_duration && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Audio Duration:</span>
                  <span className="font-medium">
                    {Math.floor(session.audio_duration / 60)}:
                    {Math.floor(session.audio_duration % 60).toString().padStart(2, '0')}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Watermark Notice */}
          <div className="card bg-amber-50 border-amber-200">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <Eye className="w-5 h-5 text-amber-600 mt-0.5" />
              </div>
              <div>
                <h4 className="font-medium text-amber-900 mb-1">Preview Version</h4>
                <p className="text-sm text-amber-700">
                  This preview includes a watermark. Purchase to download the clean,
                  high-resolution version without watermarks.
                </p>
              </div>
            </div>
          </div>

          {/* Features Included */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">What's Included</h3>

            <div className="space-y-2 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span>High-resolution PDF (300 DPI)</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span>Audio waveform visualization</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span>QR code for audio playback</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span>Professional poster layout</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span>Print-ready format</span>
              </div>
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
          <span>Back to Customize</span>
        </button>

        <button
          onClick={onNext}
          className="btn-primary flex items-center space-x-2"
        >
          <span>Purchase & Download</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
