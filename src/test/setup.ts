import '@testing-library/jest-dom'

// Mock window.Image for EXIF testing
Object.defineProperty(window, 'Image', {
  writable: true,
  value: class MockImage {
    src = ''
    onload: (() => void) | null = null
    onerror: (() => void) | null = null
    width = 0
    height = 0

    constructor() {
      // Simulate async loading
      setTimeout(() => {
        if (this.onload) {
          this.onload()
        }
      }, 0)
    }
  }
})

// Mock HTML5 Audio for audio duration testing
Object.defineProperty(window, 'Audio', {
  writable: true,
  value: class MockAudio {
    src = ''
    duration = 0
    onloadedmetadata: (() => void) | null = null
    onerror: (() => void) | null = null

    constructor() {
      // Simulate async loading
      setTimeout(() => {
        if (this.onloadedmetadata) {
          this.onloadedmetadata()
        }
      }, 0)
    }
  }
})

// Mock FileReader for file reading tests
Object.defineProperty(window, 'FileReader', {
  writable: true,
  value: class MockFileReader {
    result: string | ArrayBuffer | null = null
    onload: ((event: any) => void) | null = null
    onerror: ((event: any) => void) | null = null

    readAsDataURL(file: File) {
      // Simulate async reading
      setTimeout(() => {
        this.result = 'data:image/jpeg;base64,mock-data'
        if (this.onload) {
          this.onload({ target: this })
        }
      }, 0)
    }
  }
})

// Mock URL.createObjectURL and URL.revokeObjectURL
Object.defineProperty(URL, 'createObjectURL', {
  writable: true,
  value: () => 'mock-object-url'
})

Object.defineProperty(URL, 'revokeObjectURL', {
  writable: true,
  value: () => {}
})

// Mock EXIF library
import { vi } from 'vitest'

vi.mock('exif-js', () => ({
  default: {
    getData: vi.fn((img, callback) => {
      // Simulate EXIF data
      img.exifdata = { Orientation: 1 }
      callback.call(img)
    }),
    getTag: vi.fn((img, tag) => {
      return img.exifdata?.[tag] || 1
    })
  }
}))
