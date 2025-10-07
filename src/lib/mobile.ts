/**
 * Mobile device detection utilities
 */

export const isMobileDevice = (): boolean => {
  if (typeof window === 'undefined') return false

  // Check user agent for mobile devices
  const userAgent = navigator.userAgent || navigator.vendor || (window as any).opera

  // Common mobile device patterns - more comprehensive
  const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile|tablet/i
  const isMobileUserAgent = mobileRegex.test(userAgent)

  // Check screen size (mobile devices typically have smaller screens)
  const isMobileScreen = window.innerWidth <= 768

  // Check for touch capability
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0

  // Check for mobile-specific features
  const hasMobileFeatures = 'orientation' in window || 'devicePixelRatio' in window

  // Consider it mobile if it matches user agent OR (small screen AND touch capable) OR has mobile features
  return isMobileUserAgent || (isMobileScreen && isTouchDevice) || (isMobileScreen && hasMobileFeatures)
}

export const isMobileSafari = (): boolean => {
  if (typeof window === 'undefined') return false

  const userAgent = navigator.userAgent
  return /iPad|iPhone|iPod/.test(userAgent) && /Safari/.test(userAgent) && !/CriOS|FxiOS|OPiOS|mercury/.test(userAgent)
}

export const isAndroidChrome = (): boolean => {
  if (typeof window === 'undefined') return false

  const userAgent = navigator.userAgent
  return /Android/.test(userAgent) && /Chrome/.test(userAgent)
}

export const shouldUseImagePreview = (): boolean => {
  if (typeof window === 'undefined') return false

  // Check for force image preview URL parameter
  const urlParams = new URLSearchParams(window.location.search)
  const forceImagePreview = urlParams.get('forceImagePreview') === 'true'

  if (forceImagePreview) {
    console.log('🔍 Force image preview mode enabled via URL parameter')
    return true
  }

  // Use image preview for mobile devices, especially those known to have PDF iframe issues
  const isMobile = isMobileDevice()
  const isSafari = isMobileSafari()
  const isAndroid = isAndroidChrome()
  const shouldUse = isMobile || isSafari || isAndroid

  // Debug logging
  console.log('🔍 Mobile Detection Debug:', {
    isMobile,
    isSafari,
    isAndroid,
    shouldUseImagePreview: shouldUse,
    forceImagePreview,
    userAgent: typeof window !== 'undefined' ? navigator.userAgent : 'N/A',
    screenWidth: typeof window !== 'undefined' ? window.innerWidth : 'N/A',
    hasTouch: typeof window !== 'undefined' ? 'ontouchstart' in window : 'N/A'
  })

  return shouldUse
}
