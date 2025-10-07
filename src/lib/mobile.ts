/**
 * Mobile device detection utilities
 */

export const isMobileDevice = (): boolean => {
  if (typeof window === 'undefined') return false

  // Check user agent for mobile devices
  const userAgent = navigator.userAgent || navigator.vendor || (window as any).opera

  // Common mobile device patterns
  const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i
  const isMobileUserAgent = mobileRegex.test(userAgent)

  // Check screen size (mobile devices typically have smaller screens)
  const isMobileScreen = window.innerWidth <= 768

  // Check for touch capability
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0

  // Consider it mobile if it matches user agent OR (small screen AND touch capable)
  return isMobileUserAgent || (isMobileScreen && isTouchDevice)
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
  // Use image preview for mobile devices, especially those known to have PDF iframe issues
  return isMobileDevice() || isMobileSafari() || isAndroidChrome()
}
