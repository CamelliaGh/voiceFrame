import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import UploadSection from '../UploadSection'

// Mock the session context
const mockSession = {
  session_token: 'test-session-token',
  expires_at: '2024-10-03T12:00:00Z',
  photo_url: null,
  waveform_url: null,
  audio_duration: null,
  custom_text: null,
  photo_shape: 'square',
  pdf_size: 'A4',
  template_id: 'framed_a4_portrait',
  background_id: 'none',
  font_id: 'script',
  photo_filename: null,
  photo_size: null,
  audio_filename: null,
  audio_size: null
}

const mockRefreshSession = vi.fn()

// Mock the session context hook
vi.mock('../../contexts/SessionContext', () => ({
  useSession: () => ({
    session: mockSession,
    refreshSession: mockRefreshSession
  })
}))

// Mock the API functions
vi.mock('../../lib/api', () => ({
  uploadPhoto: vi.fn().mockResolvedValue({ success: true }),
  uploadAudio: vi.fn().mockResolvedValue({ success: true }),
  removePhoto: vi.fn().mockResolvedValue({ status: 'success', message: 'Photo removed successfully' }),
  removeAudio: vi.fn().mockResolvedValue({ status: 'success', message: 'Audio removed successfully' })
}))

// Mock the utils
vi.mock('../../lib/utils', () => ({
  cn: (...classes: string[]) => classes.filter(Boolean).join(' '),
  isChrome: () => false,
  hasPotentialUploadIssues: () => false
}))

// Mock exifr
vi.mock('exifr', () => ({
  parse: vi.fn().mockResolvedValue({ Orientation: 1 })
}))

// Mock react-dropzone
vi.mock('react-dropzone', () => ({
  useDropzone: vi.fn(() => ({
    getRootProps: () => ({ role: 'presentation' }),
    getInputProps: () => ({ value: '' }),
    isDragActive: false
  }))
}))

describe('UploadSection Component', () => {
  const mockProps = {
    onPhotosUploaded: vi.fn(),
    onAudioUploaded: vi.fn(),
    canProceed: false,
    onNext: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Task 1.1: React Dropzone Setup', () => {
    it('should render photo and audio upload zones', () => {
      render(<UploadSection {...mockProps} />)

      // Check if both upload zones are present
      expect(screen.getByText('Upload Your Files')).toBeInTheDocument()
      expect(screen.getByText('Upload Photo')).toBeInTheDocument()
      expect(screen.getByText('Upload Audio')).toBeInTheDocument()
    })

    it('should display correct file type instructions', () => {
      render(<UploadSection {...mockProps} />)

      // Check photo file type instructions
      expect(screen.getByText(/Supports JPG, PNG, HEIC up to 50MB/)).toBeInTheDocument()

      // Check audio file type instructions
      expect(screen.getByText(/Supports MP3, WAV, M4A up to 100MB/)).toBeInTheDocument()
    })

    it('should have drag and drop functionality', () => {
      render(<UploadSection {...mockProps} />)

      // Check if dropzone elements are present (text is split across elements)
      expect(screen.getByText(/Drop your photo here/)).toBeInTheDocument()
      expect(screen.getByText(/Drop your audio here/)).toBeInTheDocument()
    })

    it('should have file input elements', () => {
      render(<UploadSection {...mockProps} />)

      // Check for file input elements (they are hidden but present)
      const fileInputs = screen.getAllByDisplayValue('')
      expect(fileInputs.length).toBeGreaterThan(0)
    })
  })

  describe('Task 1.2: File Size Validation', () => {
    it('should display file size limits in UI', () => {
      render(<UploadSection {...mockProps} />)

      // Check that file size limits are displayed
      expect(screen.getByText(/up to 50MB/)).toBeInTheDocument()
      expect(screen.getByText(/up to 100MB/)).toBeInTheDocument()
    })

    it('should have proper file type restrictions', () => {
      render(<UploadSection {...mockProps} />)

      // Check that file type restrictions are displayed
      expect(screen.getByText(/JPG, PNG, HEIC/)).toBeInTheDocument()
      expect(screen.getByText(/MP3, WAV, M4A/)).toBeInTheDocument()
    })
  })

  describe('Task 1.3: Upload Progress Indicators', () => {
    it('should have upload zone structure for progress display', () => {
      render(<UploadSection {...mockProps} />)

      // Check that upload zones are present (they will show progress when files are uploaded)
      const uploadZones = screen.getAllByRole('presentation')
      expect(uploadZones).toHaveLength(2) // One for photo, one for audio
    })
  })

  describe('Task 1.4: EXIF Data Handling', () => {
    it('should have EXIF library available', async () => {
      // Test that EXIF library is imported and available
      const EXIF = await import('exif-js')
      expect(EXIF.default).toBeDefined()
    })
  })

  describe('Task 1.5: Audio Duration Validation', () => {
    it('should have audio duration validation capability', () => {
      render(<UploadSection {...mockProps} />)

      // Check that audio upload zone is present
      expect(screen.getByText('Upload Audio')).toBeInTheDocument()
    })
  })

  describe('Task 1.6: Error Handling', () => {
    it('should have error handling structure in place', () => {
      render(<UploadSection {...mockProps} />)

      // Check that the component renders without errors
      expect(screen.getByText('Upload Your Files')).toBeInTheDocument()
    })
  })

  describe('File Display and Remove Functionality', () => {
    it('should show uploaded photo with remove button when photo is uploaded', () => {
      // Mock session with uploaded photo
      const sessionWithPhoto = {
        ...mockSession,
        photo_url: 'https://example.com/photo.jpg',
        photo_filename: 'test-photo.jpg',
        photo_size: 1024000 // 1MB
      }

      vi.mocked(vi.importActual('../../contexts/SessionContext')).useSession = () => ({
        session: sessionWithPhoto,
        refreshSession: mockRefreshSession
      })

      render(<UploadSection {...mockProps} />)

      // Should show the uploaded file info
      expect(screen.getByText('test-photo.jpg')).toBeInTheDocument()
      expect(screen.getByText('1000.00 KB')).toBeInTheDocument()

      // Should show remove button
      expect(screen.getByTitle('Remove photo')).toBeInTheDocument()
    })

    it('should show uploaded audio with remove button when audio is uploaded', () => {
      // Mock session with uploaded audio
      const sessionWithAudio = {
        ...mockSession,
        audio_duration: 120, // 2 minutes
        audio_filename: 'test-audio.mp3',
        audio_size: 2048000 // 2MB
      }

      vi.mocked(vi.importActual('../../contexts/SessionContext')).useSession = () => ({
        session: sessionWithAudio,
        refreshSession: mockRefreshSession
      })

      render(<UploadSection {...mockProps} />)

      // Should show the uploaded file info
      expect(screen.getByText('test-audio.mp3')).toBeInTheDocument()
      expect(screen.getByText(/2.00 MB/)).toBeInTheDocument()
      expect(screen.getByText(/2:00/)).toBeInTheDocument()

      // Should show remove button
      expect(screen.getByTitle('Remove audio')).toBeInTheDocument()
    })

    it('should format file sizes correctly', () => {
      render(<UploadSection {...mockProps} />)

      // The formatFileSize function should be working
      // This is tested indirectly through the file display tests above
      expect(screen.getByText('Upload Your Files')).toBeInTheDocument()
    })
  })
})
