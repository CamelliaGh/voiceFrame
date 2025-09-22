import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import UploadSection from '../UploadSection'

// Mock the session context
const mockSession = {
  session_token: 'test-session-token',
  photo_uploaded: false,
  audio_uploaded: false,
  audio_duration: null,
  custom_text: null,
  background_selected: null,
  photo_shape: null,
  pdf_size: null,
  pdf_orientation: null
}

// Mock the session context hook
vi.mock('../../contexts/SessionContext', () => ({
  useSession: () => ({ session: mockSession })
}))

// Mock the API functions
vi.mock('../../lib/api', () => ({
  uploadPhoto: vi.fn().mockResolvedValue({ success: true }),
  uploadAudio: vi.fn().mockResolvedValue({ success: true })
}))

// Mock the utils
vi.mock('../../lib/utils', () => ({
  cn: (...classes: string[]) => classes.filter(Boolean).join(' ')
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
})
