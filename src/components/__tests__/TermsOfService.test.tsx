import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import TermsOfService from '../TermsOfService'

// Wrapper component to provide router context
const TermsOfServiceWithRouter = () => (
  <BrowserRouter>
    <TermsOfService />
  </BrowserRouter>
)

describe('TermsOfService', () => {
  it('renders the terms of service page', () => {
    render(<TermsOfServiceWithRouter />)

    // Check for main heading
    expect(screen.getByText('Terms of Service')).toBeInTheDocument()
    expect(screen.getByText('Legal terms and conditions for using our service')).toBeInTheDocument()
  })

  it('displays the 5-year link retention policy', () => {
    render(<TermsOfServiceWithRouter />)

    // Check for the specific 5-year retention policy text
    expect(screen.getByText(/We retain download links and associated order data for 5 years/)).toBeInTheDocument()
    expect(screen.getByText('Download links: 5 years')).toBeInTheDocument()
  })

  it('includes all major sections', () => {
    render(<TermsOfServiceWithRouter />)

    // Check for key section headings
    expect(screen.getByText('Agreement to Terms')).toBeInTheDocument()
    expect(screen.getByText('Service Description')).toBeInTheDocument()
    expect(screen.getByText('User Responsibilities')).toBeInTheDocument()
    expect(screen.getByText('Payment and Billing')).toBeInTheDocument()
    expect(screen.getByText('Data Retention and Download Links')).toBeInTheDocument()
    expect(screen.getByText('Intellectual Property Rights')).toBeInTheDocument()
    expect(screen.getByText('Privacy and Data Protection')).toBeInTheDocument()
  })

  it('has navigation links', () => {
    render(<TermsOfServiceWithRouter />)

    // Check for navigation links - use getAllByText since there are multiple instances
    expect(screen.getAllByText('Privacy Policy')).toHaveLength(2)
    expect(screen.getByText('← Back to VoiceFrame')).toBeInTheDocument()
  })

  it('displays contact information', () => {
    render(<TermsOfServiceWithRouter />)

    // Check for contact email links
    expect(screen.getByText('legal@audioposter.com')).toBeInTheDocument()
    expect(screen.getByText('support@audioposter.com')).toBeInTheDocument()
  })

  it('shows the last updated date', () => {
    render(<TermsOfServiceWithRouter />)

    // Check for last updated information - use more flexible text matching
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
    expect(screen.getByText((content, element) => {
      return element?.textContent === 'Last updated: December 2024'
    })).toBeInTheDocument()
  })

  it('includes privacy policy reference', () => {
    render(<TermsOfServiceWithRouter />)

    // Check for privacy policy reference - use getAllByText since there are multiple instances
    expect(screen.getAllByText(/Privacy Policy/)).toHaveLength(3)
  })

  it('displays data retention periods correctly', () => {
    render(<TermsOfServiceWithRouter />)

    // Check for various retention periods
    expect(screen.getByText('Session data: 2 hours')).toBeInTheDocument()
    expect(screen.getByText('Temporary processing files: 24 hours')).toBeInTheDocument()
    expect(screen.getByText('Order records: 5 years')).toBeInTheDocument()
    expect(screen.getByText('Generated posters: 5 years')).toBeInTheDocument()
  })
})
