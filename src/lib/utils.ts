import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export function generateSessionToken(): string {
  return crypto.randomUUID()
}

// Browser detection utilities
export function isChrome(): boolean {
  return /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor)
}

export function getBrowserInfo(): { name: string; version: string } {
  const userAgent = navigator.userAgent

  if (userAgent.includes('Chrome') && userAgent.includes('Google Inc')) {
    const match = userAgent.match(/Chrome\/(\d+)/)
    return { name: 'Chrome', version: match ? match[1] : 'Unknown' }
  } else if (userAgent.includes('Firefox')) {
    const match = userAgent.match(/Firefox\/(\d+)/)
    return { name: 'Firefox', version: match ? match[1] : 'Unknown' }
  } else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
    const match = userAgent.match(/Version\/(\d+)/)
    return { name: 'Safari', version: match ? match[1] : 'Unknown' }
  } else if (userAgent.includes('Edge')) {
    const match = userAgent.match(/Edge\/(\d+)/)
    return { name: 'Edge', version: match ? match[1] : 'Unknown' }
  }

  return { name: 'Unknown', version: 'Unknown' }
}

// Check if browser might have upload issues
export function hasPotentialUploadIssues(): boolean {
  const browser = getBrowserInfo()

  // Chrome versions that commonly have upload issues
  if (browser.name === 'Chrome') {
    const version = parseInt(browser.version)
    // Recent Chrome versions sometimes have stricter security policies
    return version >= 120
  }

  return false
}
