import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Privacy from '../Privacy'

// Wrapper component to provide router context
const PrivacyWithRouter = () => (
  <BrowserRouter>
    <Privacy />
  </BrowserRouter>
)

describe('Privacy Component', () => {
  it('should render privacy policy header', () => {
    render(<PrivacyWithRouter />)

    expect(screen.getByText('Privacy Policy')).toBeInTheDocument()
    expect(screen.getByText('How we protect and handle your data')).toBeInTheDocument()
  })

  it('should display main privacy sections', () => {
    render(<PrivacyWithRouter />)

    // Check for key sections
    expect(screen.getByText('Introduction')).toBeInTheDocument()
    expect(screen.getByText('Information We Collect')).toBeInTheDocument()
    expect(screen.getByText('How We Use Your Information')).toBeInTheDocument()
    expect(screen.getByText('Data Storage & Security')).toBeInTheDocument()
    expect(screen.getByText('Your Privacy Rights')).toBeInTheDocument()
  })

  it('should display GDPR rights information', () => {
    render(<PrivacyWithRouter />)

    expect(screen.getByText('Right to Access')).toBeInTheDocument()
    expect(screen.getByText('Right to Rectification')).toBeInTheDocument()
    expect(screen.getByText('Right to Erasure')).toBeInTheDocument()
    expect(screen.getByText('Right to Portability')).toBeInTheDocument()
  })

  it('should display third-party services information', () => {
    render(<PrivacyWithRouter />)

    expect(screen.getByText('Third-Party Services')).toBeInTheDocument()
    expect(screen.getByText('Stripe (Payment Processing)')).toBeInTheDocument()
    expect(screen.getByText('Amazon Web Services (File Storage)')).toBeInTheDocument()
    expect(screen.getByText('SendGrid (Email Delivery)')).toBeInTheDocument()
  })

  it('should display contact information', () => {
    render(<PrivacyWithRouter />)

    expect(screen.getByText('Contact Us')).toBeInTheDocument()
    expect(screen.getAllByText('privacy@audioposter.com')).toHaveLength(2) // Appears in footer and contact section
    expect(screen.getByText('support@audioposter.com')).toBeInTheDocument()
  })

  it('should have proper navigation links', () => {
    render(<PrivacyWithRouter />)

    // Check for back to home link
    const backLink = screen.getByText('← Back to VocaFrame')
    expect(backLink).toBeInTheDocument()
    expect(backLink.closest('a')).toHaveAttribute('href', '/')
  })

  it('should display data retention information', () => {
    render(<PrivacyWithRouter />)

    expect(screen.getByText('Data Retention')).toBeInTheDocument()
    expect(screen.getByText('Temporary Data')).toBeInTheDocument()
    expect(screen.getByText('Permanent Data')).toBeInTheDocument()
  })

  it('should display cookies and tracking information', () => {
    render(<PrivacyWithRouter />)

    expect(screen.getByText('Cookies & Tracking')).toBeInTheDocument()
    expect(screen.getByText('Essential Cookies')).toBeInTheDocument()
    expect(screen.getByText('Analytics Cookies')).toBeInTheDocument()
    expect(screen.getByText('Preference Cookies')).toBeInTheDocument()
  })
})
