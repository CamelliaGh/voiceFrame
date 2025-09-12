import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Image, Music, CheckCircle, AlertCircle } from 'lucide-react'
import { useSession } from '../contexts/SessionContext'
import { uploadPhoto, uploadAudio } from '../lib/api'
// import { formatFileSize } from '../lib/utils'
import { cn } from '../lib/utils'

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

    setPhotoUploading(true)
    setUploadErrors(prev => ({ ...prev, photo: undefined }))

    try {
      await uploadPhoto(session.session_token, file)
      setPhotoUploaded(true)
      onPhotosUploaded()
    } catch (error: any) {
      console.error('Photo upload failed:', error)
      const errorMessage = error?.response?.data?.detail || 'Failed to upload photo. Please try again.'
      setUploadErrors(prev => ({ ...prev, photo: errorMessage }))
    } finally {
      setPhotoUploading(false)
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

    setAudioUploading(true)
    setUploadErrors(prev => ({ ...prev, audio: undefined }))

    try {
      await uploadAudio(session.session_token, file)
      setAudioUploaded(true)
      onAudioUploaded()
    } catch (error: any) {
      console.error('Audio upload failed:', error)
      const errorMessage = error?.response?.data?.detail || 'Failed to upload audio. Please try again.'
      setUploadErrors(prev => ({ ...prev, audio: errorMessage }))
    } finally {
      setAudioUploading(false)
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
              <div className="space-y-2">
                <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-sm text-gray-600">Uploading photo...</p>
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
            <div className="mt-2 flex items-center space-x-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <p className="text-sm">{uploadErrors.photo}</p>
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
              <div className="space-y-2">
                <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-sm text-gray-600">Uploading audio...</p>
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
            <div className="mt-2 flex items-center space-x-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <p className="text-sm">{uploadErrors.audio}</p>
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
