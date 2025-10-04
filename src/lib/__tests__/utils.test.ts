import { describe, it, expect } from 'vitest'
import { cn } from '../utils'

describe('Utility Functions', () => {
  describe('cn function', () => {
    it('should combine class names correctly', () => {
      expect(cn('class1', 'class2')).toBe('class1 class2')
    })

    it('should filter out falsy values', () => {
      expect(cn('class1', null, 'class2', undefined, 'class3')).toBe('class1 class2 class3')
    })

    it('should handle empty strings', () => {
      expect(cn('class1', '', 'class2')).toBe('class1 class2')
    })

    it('should handle conditional classes', () => {
      const isActive = true
      const isDisabled = false
      expect(cn('base', isActive && 'active', isDisabled && 'disabled')).toBe('base active')
    })
  })
})
