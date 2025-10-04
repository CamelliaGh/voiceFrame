import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock axios
const mockAxios = {
  post: vi.fn(),
  get: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  create: vi.fn(() => mockAxios),
  defaults: { baseURL: '' }
}

vi.mock('axios', () => ({
  default: mockAxios,
  create: vi.fn(() => mockAxios)
}))

describe('API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('API Module Structure', () => {
    it('should have uploadPhoto function available', async () => {
      // Test that the API module can be imported
      const apiModule = await import('../api')
      expect(apiModule.uploadPhoto).toBeDefined()
      expect(typeof apiModule.uploadPhoto).toBe('function')
    })

    it('should have uploadAudio function available', async () => {
      // Test that the API module can be imported
      const apiModule = await import('../api')
      expect(apiModule.uploadAudio).toBeDefined()
      expect(typeof apiModule.uploadAudio).toBe('function')
    })
  })
})
