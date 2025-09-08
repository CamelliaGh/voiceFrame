import React, { useState, useEffect } from 'react'
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

  const generatePreview = async () => {
    if (!session) return

    setLoading(true)
    setError(null)

    try {
      const response = await getPreviewUrl(session.session_token)
      setPreviewUrl(response.preview_url)
    } catch (err) {
      console.error('Failed to generate preview:', err)
      setError('Failed to generate preview. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    generatePreview()
  }, [session])

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
              <h3 className="text-lg font-semibold text-gray-900">Poster Preview</h3>
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
                <div className="aspect-[3/4] bg-gray-50 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-sm text-gray-600">Generating preview...</p>
                  </div>
                </div>
              ) : error ? (
                <div className="aspect-[3/4] bg-red-50 flex items-center justify-center">
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
                  className="w-full aspect-[3/4]"
                  title="Poster Preview"
                />
              ) : (
                <div className="aspect-[3/4] bg-gray-100 flex items-center justify-center">
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
