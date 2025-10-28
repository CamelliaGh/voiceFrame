import { useState, useEffect, useCallback } from 'react'
import { Type, ArrowLeft, ArrowRight, Image, FileText, RefreshCw, Eye, Maximize2 } from 'lucide-react'
import { useSession } from '../contexts/SessionContext'
import { SessionData, getProcessingStatus, getPreviewUrl, getPreviewImageUrl } from '@/lib/api'
import { trackCustomization, trackEngagement } from '@/lib/analytics'
import { shouldUseImagePreview } from '@/lib/mobile'
import TextCustomization from './TextCustomization'
import BackgroundSelection from './BackgroundSelection'
import PhotoShapeCustomization from './PhotoShapeCustomization'
import PDFSizeSelection from './PDFSizeSelection'
import MobilePreviewModal from './MobilePreviewModal'

interface CustomizationPanelProps {
  onNext: () => void
  onBack: () => void
}




// Framed template variants for different sizes
const getFramedTemplateId = (pdfSize: string) => {
  switch (pdfSize) {
    case 'A4_Landscape':
      return 'framed_a4_landscape'
    case 'A4':
      return 'framed_a4_portrait'
    case 'A3_Landscape':
      return 'framed_a3_landscape'
    case 'A3':
      return 'framed_a3_portrait'
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
  const [customText, setCustomText] = useState(session?.custom_text || 'Our Song ♪')
  const [pdfSize, setPdfSize] = useState<'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape'>((session?.pdf_size as any) || 'A4')
  const [backgroundId, setBackgroundId] = useState(session?.background_id || 'none')
  const [fontId, setFontId] = useState(session?.font_id || 'script')
  const [photoShape, setPhotoShape] = useState<'square' | 'circle'>((session?.photo_shape as any) || 'square')
  const [isUpdating, setIsUpdating] = useState(false)
  const [processingStatus, setProcessingStatus] = useState<{
    photo_ready: boolean
    audio_ready: boolean
    waveform_ready: boolean
    preview_ready: boolean
  } | null>(null)

  // Preview state
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [showMobileModal, setShowMobileModal] = useState(false)
  const [useImagePreview, setUseImagePreview] = useState(shouldUseImagePreview())
  const [updateError, setUpdateError] = useState<string | null>(null)

  const handleUpdateError = (error: any, operation: string) => {
    console.error(`Failed to ${operation}:`, error)

    if (error.response?.status === 429) {
      setUpdateError('Too many requests. Please wait a moment and try again.')
    } else if (error.response?.status >= 500) {
      setUpdateError('Server error. Please try again in a few moments.')
    } else if (error.response?.status === 400) {
      // Handle specific 400 errors (like audio processing not complete)
      if (error.message?.includes('Audio processing not complete')) {
        setUpdateError('Audio is still processing. Please wait a moment and try again.')
      } else {
        setUpdateError('Invalid request. Please check your settings and try again.')
      }
    } else {
      setUpdateError(`Failed to ${operation}. Please try again.`)
    }
  }

  const clearUpdateError = () => {
    setUpdateError(null)
  }

  // Check processing status when component mounts and periodically
  useEffect(() => {
    const checkProcessingStatus = async () => {
      if (!session) return

      try {
        const status = await getProcessingStatus(session.session_token)
        setProcessingStatus({
          photo_ready: status.photo_ready || false,
          audio_ready: status.audio_ready || false,
          waveform_ready: status.waveform_ready || false,
          preview_ready: status.preview_ready || false,
        })
      } catch (error) {
        console.error('Failed to get processing status:', error)
      }
    }

    checkProcessingStatus()

    // Check periodically, but stop once everything is ready
    const interval = setInterval(async () => {
      if (!session) return

      try {
        const status = await getProcessingStatus(session.session_token)
        setProcessingStatus({
          photo_ready: status.photo_ready || false,
          audio_ready: status.audio_ready || false,
          waveform_ready: status.waveform_ready || false,
          preview_ready: status.preview_ready || false,
        })

        // Stop polling if everything is ready
        if (status.audio_ready && status.waveform_ready && status.preview_ready) {
          clearInterval(interval)
        }
      } catch (error) {
        console.error('Failed to get processing status:', error)
      }
    }, 5000) // Check every 5 seconds (reduced frequency)

    return () => clearInterval(interval)
  }, [session]) // Removed processingStatus from dependencies

  // Initialize default custom text if not set
  useEffect(() => {
    if (session && !session.custom_text && customText === 'Our Song ♪') {
      // Update session with default custom text - but only if audio processing is complete
      if (processingStatus && processingStatus.waveform_ready) {
        updateSessionData({ custom_text: customText }).catch(error => {
          handleUpdateError(error, 'set default text')
        })
      }
    }
  }, [session, customText, updateSessionData, processingStatus])

  // Debounced update function for real-time preview
  const debouncedUpdate = useCallback(
    (() => {
      let timeoutId: ReturnType<typeof setTimeout>
      return (data: Partial<SessionData>) => {
        console.log('⏱️ debouncedUpdate called with data:', data)
        clearTimeout(timeoutId)
        timeoutId = setTimeout(async () => {
          console.log('🚀 debouncedUpdate timeout triggered')
          console.log('📊 Session exists:', !!session)
          console.log('📊 Processing status:', processingStatus)

          if (!session) {
            console.log('❌ No session, returning')
            return
          }

          // Allow photo shape updates even if audio processing isn't complete
          // Check if audio processing is complete before updating (except for photo_shape-only updates)
          const isPhotoShapeOnlyUpdate = Object.keys(data).length === 1 && 'photo_shape' in data
          if (processingStatus && !processingStatus.waveform_ready && !isPhotoShapeOnlyUpdate) {
            console.warn('Audio processing not complete, skipping session update')
            return
          }

          console.log('✅ Proceeding with session update:', data)

          try {
            setIsUpdating(true)
            clearUpdateError() // Clear any previous errors
            console.log('📡 Calling updateSessionData with:', data)
            await updateSessionData(data)
            console.log('✅ updateSessionData completed successfully')
          } catch (error) {
            handleUpdateError(error, 'update session')
            // If it's a 400 error about audio processing, refresh the processing status
            if (error instanceof Error && (error.message.includes('Audio processing not complete') || error.message.includes('Request failed with status code 400'))) {
              try {
                const status = await getProcessingStatus(session.session_token)
                setProcessingStatus({
                  photo_ready: status.photo_ready || false,
                  audio_ready: status.audio_ready || false,
                  waveform_ready: status.waveform_ready || false,
                  preview_ready: status.preview_ready || false,
                })
              } catch (statusError) {
                console.error('Failed to refresh processing status:', statusError)
              }
            }
          } finally {
            setIsUpdating(false)
          }
        }, 500) // 500ms delay
      }
    })(),
    [session, updateSessionData, processingStatus]
  )

  const handleTextChange = (text: string) => {
    if (text.length <= 200) {
      setCustomText(text)
      // Update session in real-time for preview
      debouncedUpdate({
        custom_text: text.trim(),
        pdf_size: pdfSize,
        template_id: getFramedTemplateId(pdfSize),
        background_id: backgroundId,
        font_id: fontId,
        photo_shape: photoShape
      })
    }
  }


  const handlePdfSizeChange = (newPdfSize: 'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape') => {
    setPdfSize(newPdfSize)
    // Update session in real-time for preview
    debouncedUpdate({
      custom_text: customText.trim(),
      pdf_size: newPdfSize,
      template_id: getFramedTemplateId(newPdfSize),
      background_id: backgroundId,
      font_id: fontId,
      photo_shape: photoShape
    })
  }

  const handleBackgroundChange = (newBackgroundId: string) => {
    setBackgroundId(newBackgroundId)
    // Update session in real-time for preview
    debouncedUpdate({
      custom_text: customText.trim(),
      pdf_size: pdfSize,
      template_id: getFramedTemplateId(pdfSize),
      background_id: newBackgroundId,
      font_id: fontId,
      photo_shape: photoShape
    })
  }

  const handleFontChange = (newFontId: string) => {
    setFontId(newFontId)
    // Update session in real-time for preview
    debouncedUpdate({
      custom_text: customText.trim(),
      pdf_size: pdfSize,
      template_id: getFramedTemplateId(pdfSize),
      background_id: backgroundId,
      font_id: newFontId,
      photo_shape: photoShape
    })
  }

  const handlePhotoShapeChange = (newPhotoShape: 'square' | 'circle') => {
    console.log('🔄 Photo shape change triggered:', newPhotoShape)
    setPhotoShape(newPhotoShape)
    // Update session in real-time for preview - send only photo_shape for immediate update
    console.log('📤 Calling debouncedUpdate with photo_shape:', newPhotoShape)
    debouncedUpdate({
      photo_shape: newPhotoShape
    })
  }

  const handleSave = async () => {
    if (!session) return

    // Validate custom text
    if (customText && customText.trim().length > 0 && customText.length > 200) {
      throw new Error('Text is too long. Please keep it under 200 characters')
    }

    // Check if audio processing is complete before saving
    if (processingStatus && !processingStatus.waveform_ready) {
      throw new Error('Audio processing is not complete yet. Please wait a moment and try again.')
    }

    // Always use the appropriate framed template variant based on PDF size
    const finalTemplateId = getFramedTemplateId(pdfSize)

    await updateSessionData({
      custom_text: customText.trim(),
      pdf_size: pdfSize,
      template_id: finalTemplateId,
      background_id: backgroundId,
      font_id: fontId,
      photo_shape: photoShape
    })
  }

  const handleNext = async () => {
    try {
      await handleSave()
      clearUpdateError() // Clear any errors on successful save
      trackEngagement('step_progression', 'customize_to_preview')
      onNext()
    } catch (error: any) {
      handleUpdateError(error, 'save settings')
      // Don't throw error - let the error display in the UI
    }
  }

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

  const aspectRatio = getAspectRatio(pdfSize)

  // Manual preview generation function
  const generatePreview = async () => {
    if (!session) return

    setPreviewLoading(true)
    setPreviewError(null)

    // Wait a moment to ensure any pending session updates have completed
    if (isUpdating) {
      console.log('⏳ Waiting for session update to complete before generating preview...')
      await new Promise(resolve => {
        const checkUpdate = () => {
          if (!isUpdating) {
            resolve(void 0)
          } else {
            setTimeout(checkUpdate, 100)
          }
        }
        checkUpdate()
      })
    }

    try {
      const response = useImagePreview
        ? await getPreviewImageUrl(session.session_token)
        : await getPreviewUrl(session.session_token)

      const previewUrl = response.preview_url
      const cacheBustingUrl = `${previewUrl}?t=${Date.now()}`
      setPreviewUrl(cacheBustingUrl)
    } catch (err: any) {
      if (useImagePreview && shouldUseImagePreview()) {
        try {
          setUseImagePreview(false)
          const response = await getPreviewUrl(session.session_token)
          const previewUrl = response.preview_url
          const cacheBustingUrl = `${previewUrl}?t=${Date.now()}`
          setPreviewUrl(cacheBustingUrl)
          return
        } catch (fallbackErr: any) {
          console.error('Fallback PDF preview also failed:', fallbackErr)
        }
      }
      console.error('Failed to generate preview:', err)

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

      setPreviewError(errorMessage)
    } finally {
      setPreviewLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Error Display */}
      {updateError && (
        <div className="mx-4 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{updateError}</p>
            </div>
            <div className="ml-auto pl-3">
              <div className="-mx-1.5 -my-1.5">
                <button
                  onClick={clearUpdateError}
                  className="inline-flex bg-red-50 rounded-md p-1.5 text-red-500 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-red-50 focus:ring-red-600"
                >
                  <span className="sr-only">Dismiss</span>
                  <svg className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="text-center px-4 animate-slide-in-bottom">
        <h2 className="section-title">Customize Your Poster</h2>
        <p className="section-subtitle">
          Personalize your audio poster with custom text, size, and background options.
        </p>
        {isUpdating && (
          <div className="mt-3 flex items-center justify-center space-x-2 text-sm text-primary-600 bg-primary-50 py-2 px-4 rounded-lg">
            <div className="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
            <span className="font-medium">Updating preview...</span>
          </div>
        )}
        {processingStatus && !processingStatus.waveform_ready && (
          <div className="mt-3 flex items-center justify-center space-x-2 text-sm text-amber-600 bg-amber-50 py-2 px-4 rounded-lg">
            <div className="w-4 h-4 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
            <span className="font-medium">Processing audio... Please wait before customizing.</span>
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-2 gap-6 sm:gap-8 max-w-6xl mx-auto">
        {/* Customization Options */}
        <div className={`space-y-4 sm:space-y-6 stagger-children ${processingStatus && !processingStatus.waveform_ready ? 'opacity-50 pointer-events-none' : ''}`}>
          {/* Custom Text */}
          <div className="card animate-slide-in-left">
            <div className="flex items-center space-x-2 mb-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-100">
                <Type className="w-5 h-5 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Custom Text</h3>
            </div>

            <TextCustomization
              value={customText}
              onChange={handleTextChange}
              onFontChange={handleFontChange}
              selectedFont={fontId}
              maxLength={200}
              disabled={processingStatus ? !processingStatus.waveform_ready : false}
            />
          </div>


          {/* PDF Size */}
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-100">
                <FileText className="w-5 h-5 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">PDF Size & Orientation</h3>
            </div>

            <PDFSizeSelection
              value={pdfSize}
              onChange={handlePdfSizeChange}
              disabled={processingStatus ? !processingStatus.waveform_ready : false}
            />
          </div>

          {/* Background Selection */}
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-100">
                <Image className="w-5 h-5 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Background</h3>
            </div>

            <BackgroundSelection
              value={backgroundId}
              onChange={handleBackgroundChange}
              disabled={processingStatus ? !processingStatus.waveform_ready : false}
              pdfSize={pdfSize}
            />
          </div>

          {/* Photo Shape Selection */}
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-100">
                <Image className="w-5 h-5 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Photo Shape</h3>
            </div>

            <PhotoShapeCustomization
              value={photoShape}
              onChange={handlePhotoShapeChange}
              disabled={processingStatus ? !processingStatus.waveform_ready : false}
            />
          </div>


        </div>

        {/* Manual Preview Section */}
        <div className="lg:sticky lg:top-8 lg:h-fit animate-slide-in-right">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Poster Preview</h3>
                {pdfSize && (
                  <p className="text-sm text-gray-600 mt-1">
                    Size: {pdfSize.replace('_', ' ')}
                  </p>
                )}
              </div>
              <div className="flex items-center space-x-2">
                {shouldUseImagePreview() && previewUrl && !previewLoading && !previewError && (
                  <button
                    onClick={() => setShowMobileModal(true)}
                    className="btn-secondary flex items-center space-x-2 text-sm px-3 py-2"
                    title="View fullscreen"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={generatePreview}
                  disabled={previewLoading || !session}
                  className="btn-secondary flex items-center space-x-2 text-sm"
                >
                  <RefreshCw className={`w-4 h-4 ${previewLoading ? 'animate-spin' : ''}`} />
                  <span className="hidden sm:inline">Refresh</span>
                </button>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg overflow-hidden">
              {previewLoading ? (
                <div className={`${aspectRatio} bg-gray-50 flex items-center justify-center`}>
                  <div className="text-center">
                    <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-sm text-gray-600">Generating preview...</p>
                  </div>
                </div>
              ) : previewError ? (
                <div className={`${aspectRatio} bg-red-50 flex items-center justify-center p-4`}>
                  <div className="text-center text-red-600">
                    <p className="font-medium text-sm">{previewError}</p>
                    <button
                      onClick={generatePreview}
                      className="mt-2 text-sm underline hover:no-underline"
                    >
                      Try again
                    </button>
                  </div>
                </div>
              ) : previewUrl ? (
                useImagePreview ? (
                  <div className="relative">
                    <img
                      src={previewUrl}
                      alt="Poster Preview"
                      className={`w-full ${aspectRatio} object-contain`}
                    />
                    {shouldUseImagePreview() && (
                      <button
                        onClick={() => setShowMobileModal(true)}
                        className="absolute inset-0 flex items-center justify-center bg-black/0 hover:bg-black/10 transition-colors group"
                      >
                        <div className="bg-white/90 backdrop-blur-sm rounded-full p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Maximize2 className="w-6 h-6 text-gray-900" />
                        </div>
                      </button>
                    )}
                  </div>
                ) : (
                  <iframe
                    src={previewUrl}
                    className={`w-full ${aspectRatio}`}
                    title="Poster Preview"
                  />
                )
              ) : (
                <div className={`${aspectRatio} bg-gray-100 flex items-center justify-center`}>
                  <div className="text-center text-gray-500">
                    <Eye className="w-12 h-12 mx-auto mb-2" />
                    <p>Preview not available</p>
                    <p className="text-xs mt-1">Click "Refresh" to generate preview</p>
                  </div>
                </div>
              )}
            </div>

            {previewUrl && (
              <div className="mt-4 text-center">
                <p className="text-xs text-gray-500">
                  This preview includes a watermark. Purchase to download the clean version.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex flex-col sm:flex-row gap-4 sm:justify-between pt-6 px-4 sm:px-0">
        <button
          onClick={() => {
            trackEngagement('step_progression', 'customize_to_upload')
            onBack()
          }}
          className="btn-secondary flex items-center justify-center space-x-2 w-full sm:w-auto"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Upload</span>
        </button>

        <button
          onClick={handleNext}
          disabled={processingStatus ? !processingStatus.waveform_ready : false}
          className={`btn-primary flex items-center justify-center space-x-2 w-full sm:w-auto ${
            processingStatus && !processingStatus.waveform_ready
              ? 'opacity-50 cursor-not-allowed'
              : ''
          }`}
        >
          <span>Continue to Preview</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {showMobileModal && previewUrl && (
        <MobilePreviewModal
          imageUrl={previewUrl}
          onClose={() => setShowMobileModal(false)}
          pdfSize={pdfSize}
        />
      )}
    </div>
  )
}
