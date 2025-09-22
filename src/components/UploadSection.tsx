import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Image, Music, CheckCircle, AlertCircle, RotateCcw } from 'lucide-react'
import { useSession } from '../contexts/SessionContext'
import { uploadPhoto, uploadAudio } from '../lib/api'
// import { formatFileSize } from '../lib/utils'
import { cn } from '../lib/utils'
import EXIF from 'exif-js'

interface UploadSectionProps {
  onPhotosUploaded: () => void
  onAudioUploaded: () => void
  canProceed: boolean
  onNext: () => void
}

export default function UploadSection({
  onPhotosUploaded,
  onAudioUploaded,
  canProceed,
  onNext
}: UploadSectionProps) {
  const { session } = useSession()
  const [photoUploading, setPhotoUploading] = useState(false)
  const [audioUploading, setAudioUploading] = useState(false)
  const [photoUploaded, setPhotoUploaded] = useState(false)
  const [audioUploaded, setAudioUploaded] = useState(false)
  const [uploadErrors, setUploadErrors] = useState<{ photo?: string; audio?: string }>({})
  const [uploadProgress, setUploadProgress] = useState<{ photo?: number; audio?: number }>({})
  const [uploadSpeed, setUploadSpeed] = useState<{ photo?: string; audio?: string }>({})
  const [uploadTimeRemaining, setUploadTimeRemaining] = useState<{ photo?: string; audio?: string }>({})
  const [previewImages, setPreviewImages] = useState<{ photo?: string; audio?: string }>({})
  const [retryCount, setRetryCount] = useState<{ photo?: number; audio?: number }>({})
  const [lastUploadAttempt, setLastUploadAttempt] = useState<{ photo?: File; audio?: File }>({})

  // Function to handle and categorize errors
  const handleUploadError = (error: any, fileType: 'photo' | 'audio'): string => {
    console.error(`${fileType} upload failed:`, error)

    // Network errors
    if (!navigator.onLine) {
      return 'No internet connection. Please check your network and try again.'
    }

    // Server errors
    if (error?.response) {
      const status = error.response.status
      const detail = error.response.data?.detail || error.response.data?.message

      switch (status) {
        case 400:
          return detail || 'Invalid file format or corrupted file. Please try a different file.'
        case 401:
          return 'Session expired. Please refresh the page and try again.'
        case 413:
          return 'File too large. Please choose a smaller file.'
        case 415:
          return 'Unsupported file type. Please use a supported format.'
        case 429:
          return 'Too many upload attempts. Please wait a moment and try again.'
        case 500:
          return 'Server error. Please try again in a few moments.'
        case 503:
          return 'Service temporarily unavailable. Please try again later.'
        default:
          return detail || `Upload failed (Error ${status}). Please try again.`
      }
    }

    // Client-side errors
    if (error?.code === 'NETWORK_ERROR') {
      return 'Network error. Please check your connection and try again.'
    }

    if (error?.message?.includes('timeout')) {
      return 'Upload timed out. Please try again with a smaller file or better connection.'
    }

    if (error?.message?.includes('abort')) {
      return 'Upload was cancelled.'
    }

    // Generic fallback
    return error?.message || `Failed to upload ${fileType}. Please try again.`
  }

  // Function to retry upload
  const retryUpload = async (fileType: 'photo' | 'audio') => {
    const file = lastUploadAttempt[fileType]
    if (!file) return

    const currentRetryCount = retryCount[fileType] || 0
    if (currentRetryCount >= 3) {
      setUploadErrors(prev => ({
        ...prev,
        [fileType]: 'Maximum retry attempts reached. Please try a different file.'
      }))
      return
    }

    setRetryCount(prev => ({ ...prev, [fileType]: currentRetryCount + 1 }))
    setUploadErrors(prev => ({ ...prev, [fileType]: undefined }))

    if (fileType === 'photo') {
      await handlePhotoUpload([file])
    } else {
      await handleAudioUpload([file])
    }
  }

  // Function to get audio duration from file
  const getAudioDuration = (file: File): Promise<number> => {
    return new Promise((resolve, reject) => {
      const audio = new Audio()
      const url = URL.createObjectURL(file)

      audio.addEventListener('loadedmetadata', () => {
        URL.revokeObjectURL(url)
        resolve(audio.duration)
      })

      audio.addEventListener('error', () => {
        URL.revokeObjectURL(url)
        reject(new Error('Failed to load audio metadata'))
      })

      audio.src = url
    })
  }

  // Function to handle EXIF data and auto-rotate image
  const handleImageOrientation = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const img = new window.Image()
        img.onload = () => {
          // Get EXIF data
          EXIF.getData(img, function() {
            const orientation = EXIF.getTag(this, 'Orientation')

            // Create canvas to handle rotation
            const canvas = document.createElement('canvas')
            const ctx = canvas.getContext('2d')

            if (!ctx) {
              resolve(e.target?.result as string)
              return
            }

            // Set canvas size based on orientation
            if (orientation === 6 || orientation === 8) {
              canvas.width = img.height
              canvas.height = img.width
            } else {
              canvas.width = img.width
              canvas.height = img.height
            }

            // Apply rotation based on EXIF orientation
            switch (orientation) {
              case 2:
                ctx.transform(-1, 0, 0, 1, canvas.width, 0)
                break
              case 3:
                ctx.transform(-1, 0, 0, -1, canvas.width, canvas.height)
                break
              case 4:
                ctx.transform(1, 0, 0, -1, 0, canvas.height)
                break
              case 5:
                ctx.transform(0, 1, 1, 0, 0, 0)
                break
              case 6:
                ctx.transform(0, 1, -1, 0, canvas.height, 0)
                break
              case 7:
                ctx.transform(0, -1, -1, 0, canvas.height, canvas.width)
                break
              case 8:
                ctx.transform(0, -1, 1, 0, 0, canvas.width)
                break
              default:
                break
            }

            // Draw the image
            ctx.drawImage(img, 0, 0)

            // Convert to data URL
            const correctedDataUrl = canvas.toDataURL('image/jpeg', 0.9)
            resolve(correctedDataUrl)
          })
        }
        img.src = e.target?.result as string
      }
      reader.readAsDataURL(file)
    })
  }

  const handlePhotoUpload = async (files: File[]) => {
    const file = files[0]
    if (!file || !session) return

    // Client-side validation
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
    const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    const maxSize = 50 * 1024 * 1024 // 50MB
    const minSize = 1024 // 1KB

    // Validate file type
    if (!allowedTypes.includes(file.type)) {
      setUploadErrors(prev => ({
        ...prev,
        photo: 'Invalid file type. Please upload a JPEG, PNG, GIF, BMP, or WebP image.'
      }))
      return
    }

    // Validate file extension
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (!allowedExtensions.includes(fileExtension)) {
      setUploadErrors(prev => ({
        ...prev,
        photo: 'Invalid file extension. Please upload a JPEG, PNG, GIF, BMP, or WebP image.'
      }))
      return
    }

    // Validate file size
    if (file.size === 0) {
      setUploadErrors(prev => ({ ...prev, photo: 'File is empty. Please select a valid image.' }))
      return
    }

    if (file.size < minSize) {
      setUploadErrors(prev => ({ ...prev, photo: 'File too small. Please select an image larger than 1KB.' }))
      return
    }

    if (file.size > maxSize) {
      setUploadErrors(prev => ({ ...prev, photo: 'File too large. Please select an image smaller than 50MB.' }))
      return
    }

    // Generate preview image with EXIF correction
    try {
      const correctedImageUrl = await handleImageOrientation(file)
      setPreviewImages(prev => ({ ...prev, photo: correctedImageUrl }))
    } catch (error) {
      console.warn('EXIF correction failed, using original image:', error)
      // Fallback to original image if EXIF correction fails
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreviewImages(prev => ({ ...prev, photo: e.target?.result as string }))
      }
      reader.readAsDataURL(file)
    }

    // Store file for potential retry
    setLastUploadAttempt(prev => ({ ...prev, photo: file }))

    // Reset states and start upload
    setPhotoUploading(true)
    setUploadErrors(prev => ({ ...prev, photo: undefined }))
    setUploadProgress(prev => ({ ...prev, photo: 0 }))

    const startTime = Date.now()
    const fileSize = file.size

    try {
      // Simulate progress updates (in real implementation, this would come from axios onUploadProgress)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const current = prev.photo || 0
          if (current < 90) {
            const newProgress = current + Math.random() * 20
            const elapsed = (Date.now() - startTime) / 1000
            const uploaded = (newProgress / 100) * fileSize
            const speed = uploaded / elapsed
            const remaining = ((100 - newProgress) / 100) * fileSize / speed

            setUploadSpeed(prev => ({
              ...prev,
              photo: `${(speed / 1024 / 1024).toFixed(1)} MB/s`
            }))
            setUploadTimeRemaining(prev => ({
              ...prev,
              photo: `${remaining.toFixed(0)}s`
            }))

            return { ...prev, photo: Math.min(newProgress, 90) }
          }
          return prev
        })
      }, 200)

      await uploadPhoto(session.session_token, file)

      clearInterval(progressInterval)
      setUploadProgress(prev => ({ ...prev, photo: 100 }))
      setPhotoUploaded(true)
      onPhotosUploaded()
    } catch (error: any) {
      const errorMessage = handleUploadError(error, 'photo')
      setUploadErrors(prev => ({ ...prev, photo: errorMessage }))
    } finally {
      setPhotoUploading(false)
      setUploadSpeed(prev => ({ ...prev, photo: undefined }))
      setUploadTimeRemaining(prev => ({ ...prev, photo: undefined }))
    }
  }

  const handleAudioUpload = async (files: File[]) => {
    const file = files[0]
    if (!file || !session) return

    // Client-side validation
    const allowedTypes = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/aac', 'audio/ogg', 'audio/flac']
    const allowedExtensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']
    const maxSize = 100 * 1024 * 1024 // 100MB
    const minSize = 1024 // 1KB

    // Validate file type
    if (!allowedTypes.includes(file.type)) {
      setUploadErrors(prev => ({
        ...prev,
        audio: 'Invalid file type. Please upload an MP3, WAV, M4A, AAC, OGG, or FLAC audio file.'
      }))
      return
    }

    // Validate file extension
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (!allowedExtensions.includes(fileExtension)) {
      setUploadErrors(prev => ({
        ...prev,
        audio: 'Invalid file extension. Please upload an MP3, WAV, M4A, AAC, OGG, or FLAC audio file.'
      }))
      return
    }

    // Validate file size
    if (file.size === 0) {
      setUploadErrors(prev => ({ ...prev, audio: 'File is empty. Please select a valid audio file.' }))
      return
    }

    if (file.size < minSize) {
      setUploadErrors(prev => ({ ...prev, audio: 'File too small. Please select an audio file larger than 1KB.' }))
      return
    }

    if (file.size > maxSize) {
      setUploadErrors(prev => ({ ...prev, audio: 'File too large. Please select an audio file smaller than 100MB.' }))
      return
    }

    // Validate audio duration (max 10 minutes = 600 seconds)
    try {
      const duration = await getAudioDuration(file)
      if (duration > 600) { // 10 minutes
        setUploadErrors(prev => ({
          ...prev,
          audio: `Audio too long (${Math.floor(duration / 60)}:${Math.floor(duration % 60).toString().padStart(2, '0')}). Maximum duration is 10 minutes.`
        }))
        return
      }

      // Generate audio preview with duration info
      setPreviewImages(prev => ({
        ...prev,
        audio: `Audio file: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB, ${Math.floor(duration / 60)}:${Math.floor(duration % 60).toString().padStart(2, '0')})`
      }))
    } catch (error) {
      console.warn('Failed to get audio duration:', error)
      // Continue with upload if duration check fails (backend will validate)
      setPreviewImages(prev => ({
        ...prev,
        audio: `Audio file: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`
      }))
    }

    // Store file for potential retry
    setLastUploadAttempt(prev => ({ ...prev, audio: file }))

    // Reset states and start upload
    setAudioUploading(true)
    setUploadErrors(prev => ({ ...prev, audio: undefined }))
    setUploadProgress(prev => ({ ...prev, audio: 0 }))

    const startTime = Date.now()
    const fileSize = file.size

    try {
      // Simulate progress updates (in real implementation, this would come from axios onUploadProgress)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const current = prev.audio || 0
          if (current < 90) {
            const newProgress = current + Math.random() * 15
            const elapsed = (Date.now() - startTime) / 1000
            const uploaded = (newProgress / 100) * fileSize
            const speed = uploaded / elapsed
            const remaining = ((100 - newProgress) / 100) * fileSize / speed

            setUploadSpeed(prev => ({
              ...prev,
              audio: `${(speed / 1024 / 1024).toFixed(1)} MB/s`
            }))
            setUploadTimeRemaining(prev => ({
              ...prev,
              audio: `${remaining.toFixed(0)}s`
            }))

            return { ...prev, audio: Math.min(newProgress, 90) }
          }
          return prev
        })
      }, 300)

      await uploadAudio(session.session_token, file)

      clearInterval(progressInterval)
      setUploadProgress(prev => ({ ...prev, audio: 100 }))
      setAudioUploaded(true)
      onAudioUploaded()
    } catch (error: any) {
      const errorMessage = handleUploadError(error, 'audio')
      setUploadErrors(prev => ({ ...prev, audio: errorMessage }))
    } finally {
      setAudioUploading(false)
      setUploadSpeed(prev => ({ ...prev, audio: undefined }))
      setUploadTimeRemaining(prev => ({ ...prev, audio: undefined }))
    }
  }

  const photoDropzone = useDropzone({
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.heic']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
    onDrop: handlePhotoUpload,
    disabled: photoUploading || photoUploaded
  })

  const audioDropzone = useDropzone({
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.aac']
    },
    maxFiles: 1,
    maxSize: 100 * 1024 * 1024, // 100MB
    onDrop: handleAudioUpload,
    disabled: audioUploading || audioUploaded
  })

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Your Files</h2>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Start by uploading a photo and an audio file. We'll create a beautiful poster combining
          your image with the audio waveform and any custom text you add.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Photo Upload */}
        <div className="card">
          <div className="flex items-center space-x-2 mb-4">
            <Image className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">Upload Photo</h3>
          </div>

          <div
            {...photoDropzone.getRootProps()}
            className={cn(
              'upload-zone',
              photoDropzone.isDragActive && 'active',
              photoUploaded && 'border-green-300 bg-green-50'
            )}
          >
            <input {...photoDropzone.getInputProps()} />

            {photoUploading ? (
              <div className="space-y-3">
                {previewImages.photo && (
                  <div className="w-16 h-16 mx-auto rounded-lg overflow-hidden border-2 border-gray-200">
                    <img
                      src={previewImages.photo}
                      alt="Preview"
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <div className="space-y-1">
                  <p className="text-sm text-gray-600">Uploading photo...</p>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress.photo || 0}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{uploadProgress.photo?.toFixed(0) || 0}%</span>
                    {uploadSpeed.photo && <span>{uploadSpeed.photo}</span>}
                    {uploadTimeRemaining.photo && <span>{uploadTimeRemaining.photo} remaining</span>}
                  </div>
                </div>
              </div>
            ) : photoUploaded ? (
              <div className="space-y-2">
                <CheckCircle className="w-8 h-8 text-green-600 mx-auto" />
                <p className="text-sm text-green-700 font-medium">Photo uploaded successfully!</p>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload className="w-8 h-8 text-gray-400 mx-auto" />
                <p className="text-sm text-gray-600">
                  Drop your photo here or <span className="text-primary-600 font-medium">browse</span>
                </p>
                <p className="text-xs text-gray-500">
                  Supports JPG, PNG, HEIC up to 50MB
                </p>
              </div>
            )}
          </div>

          {uploadErrors.photo && (
            <div className="mt-2 space-y-2">
              <div className="flex items-center space-x-2 text-red-600">
                <AlertCircle className="w-4 h-4" />
                <p className="text-sm flex-1">{uploadErrors.photo}</p>
              </div>
              {lastUploadAttempt.photo && (retryCount.photo || 0) < 3 && (
                <button
                  onClick={() => retryUpload('photo')}
                  className="flex items-center space-x-1 text-sm text-primary-600 hover:text-primary-700 transition-colors"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Retry upload</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Audio Upload */}
        <div className="card">
          <div className="flex items-center space-x-2 mb-4">
            <Music className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">Upload Audio</h3>
          </div>

          <div
            {...audioDropzone.getRootProps()}
            className={cn(
              'upload-zone',
              audioDropzone.isDragActive && 'active',
              audioUploaded && 'border-green-300 bg-green-50'
            )}
          >
            <input {...audioDropzone.getInputProps()} />

            {audioUploading ? (
              <div className="space-y-3">
                {previewImages.audio && (
                  <div className="text-center">
                    <Music className="w-8 h-8 text-primary-600 mx-auto mb-2" />
                    <p className="text-xs text-gray-600">{previewImages.audio}</p>
                  </div>
                )}
                <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <div className="space-y-1">
                  <p className="text-sm text-gray-600">Uploading audio...</p>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress.audio || 0}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{uploadProgress.audio?.toFixed(0) || 0}%</span>
                    {uploadSpeed.audio && <span>{uploadSpeed.audio}</span>}
                    {uploadTimeRemaining.audio && <span>{uploadTimeRemaining.audio} remaining</span>}
                  </div>
                </div>
              </div>
            ) : audioUploaded ? (
              <div className="space-y-2">
                <CheckCircle className="w-8 h-8 text-green-600 mx-auto" />
                <p className="text-sm text-green-700 font-medium">Audio uploaded successfully!</p>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload className="w-8 h-8 text-gray-400 mx-auto" />
                <p className="text-sm text-gray-600">
                  Drop your audio here or <span className="text-primary-600 font-medium">browse</span>
                </p>
                <p className="text-xs text-gray-500">
                  Supports MP3, WAV, M4A up to 100MB
                </p>
              </div>
            )}
          </div>

          {uploadErrors.audio && (
            <div className="mt-2 space-y-2">
              <div className="flex items-center space-x-2 text-red-600">
                <AlertCircle className="w-4 h-4" />
                <p className="text-sm flex-1">{uploadErrors.audio}</p>
              </div>
              {lastUploadAttempt.audio && (retryCount.audio || 0) < 3 && (
                <button
                  onClick={() => retryUpload('audio')}
                  className="flex items-center space-x-1 text-sm text-primary-600 hover:text-primary-700 transition-colors"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Retry upload</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Continue Button */}
      {canProceed && (
        <div className="flex justify-center pt-6">
          <button
            onClick={onNext}
            className="btn-primary px-8 py-3 text-lg"
          >
            Continue to Customize
          </button>
        </div>
      )}
    </div>
  )
}
