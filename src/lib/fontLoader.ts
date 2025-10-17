/**
 * Dynamic Font Loader
 *
 * Loads fonts dynamically from admin-managed resources
 * and applies them to the DOM for preview purposes
 */

interface FontResource {
  id: string
  name: string
  display_name: string
  file_path: string
  is_premium: boolean
  description: string
}

class FontLoader {
  private loadedFonts = new Set<string>()
  private fontStyles = new Map<string, string>()

  /**
   * Load a font dynamically and create CSS class for it
   */
  async loadFont(font: FontResource): Promise<string> {
    const fontId = font.id
    const fontName = `Font_${fontId.replace(/[^a-zA-Z0-9]/g, '_')}`

    // If already loaded, return existing class
    if (this.loadedFonts.has(fontId)) {
      return this.fontStyles.get(fontId) || 'font-sans'
    }

    try {
      // Create font face CSS
      const fontFaceCSS = `
        @font-face {
          font-family: '${fontName}';
          src: url('/api/resources/fonts/${fontId}/file') format('truetype');
          font-weight: normal;
          font-style: normal;
          font-display: swap;
        }
      `

      // Create CSS class for the font
      const fontClass = `font-${fontId}`
      const fontClassCSS = `
        .${fontClass} {
          font-family: '${fontName}', cursive;
        }
      `

      // Inject CSS into the document
      const styleId = `font-style-${fontId}`
      let styleElement = document.getElementById(styleId) as HTMLStyleElement

      if (!styleElement) {
        styleElement = document.createElement('style')
        styleElement.id = styleId
        styleElement.textContent = fontFaceCSS + fontClassCSS
        document.head.appendChild(styleElement)
      }

      // Store the font class
      this.fontStyles.set(fontId, fontClass)
      this.loadedFonts.add(fontId)

      // Wait for font to load
      await this.waitForFontLoad(fontName)

      return fontClass
    } catch (error) {
      console.error(`Failed to load font ${fontId}:`, error)
      return 'font-sans' // Fallback
    }
  }

  /**
   * Load multiple fonts at once
   */
  async loadFonts(fonts: FontResource[]): Promise<Map<string, string>> {
    const fontClasses = new Map<string, string>()

    const loadPromises = fonts.map(async (font) => {
      const fontClass = await this.loadFont(font)
      fontClasses.set(font.id, fontClass)
    })

    await Promise.all(loadPromises)
    return fontClasses
  }

  /**
   * Get the CSS class for a font ID
   */
  getFontClass(fontId: string): string {
    return this.fontStyles.get(fontId) || 'font-sans'
  }

  /**
   * Check if a font is loaded
   */
  isFontLoaded(fontId: string): boolean {
    return this.loadedFonts.has(fontId)
  }

  /**
   * Wait for a font to load
   */
  private waitForFontLoad(fontFamily: string): Promise<void> {
    return new Promise((resolve) => {
      if ('fonts' in document) {
        // Use FontFace API if available
        document.fonts.load(`16px ${fontFamily}`).then(() => {
          resolve()
        }).catch(() => {
          // Fallback: resolve after a short delay
          setTimeout(resolve, 100)
        })
      } else {
        // Fallback: resolve after a short delay
        setTimeout(resolve, 100)
      }
    })
  }

  /**
   * Clean up loaded fonts (useful for testing or memory management)
   */
  cleanup(): void {
    this.loadedFonts.forEach((fontId) => {
      const styleElement = document.getElementById(`font-style-${fontId}`)
      if (styleElement) {
        styleElement.remove()
      }
    })
    this.loadedFonts.clear()
    this.fontStyles.clear()
  }
}

// Export singleton instance
export const fontLoader = new FontLoader()
export type { FontResource }
