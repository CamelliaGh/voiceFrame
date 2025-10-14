import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import LandingPage from '../LandingPage'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

const renderLandingPage = () => {
  return render(
    <BrowserRouter>
      <LandingPage />
    </BrowserRouter>
  )
}

describe('LandingPage Pricing Display', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {})) // Never resolves

    renderLandingPage()

    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('displays regular pricing when no discount is available', async () => {
    const mockPricingData = {
      price_cents: 299,
      original_price_cents: 299,
      price_dollars: 2.99,
      original_price_dollars: 2.99,
      formatted_price: '$2.99',
      formatted_original_price: '$2.99',
      discount_percentage: 0,
      discount_amount: 0,
      discount_enabled: false,
      has_discount: false
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPricingData
    })

    renderLandingPage()

    await waitFor(() => {
      expect(screen.getByText('$2.99')).toBeInTheDocument()
      expect(screen.getByText('per poster')).toBeInTheDocument()
    })

    // Should not show discount elements
    expect(screen.queryByText(/SAVE/)).not.toBeInTheDocument()
    expect(document.querySelector('.line-through')).not.toBeInTheDocument()
  })

  it('displays discounted pricing when discount is available', async () => {
    const mockPricingData = {
      price_cents: 199,
      original_price_cents: 299,
      price_dollars: 1.99,
      original_price_dollars: 2.99,
      formatted_price: '$1.99',
      formatted_original_price: '$2.99',
      discount_percentage: 33,
      discount_amount: 100,
      discount_enabled: true,
      has_discount: true
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPricingData
    })

    renderLandingPage()

    await waitFor(() => {
      expect(screen.getByText('$1.99')).toBeInTheDocument()
      expect(screen.getByText('$2.99')).toBeInTheDocument()
      expect(screen.getByText('SAVE 33%')).toBeInTheDocument()
    })
  })

  it('shows fallback pricing when API fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    renderLandingPage()

    await waitFor(() => {
      expect(screen.getByText('$2.99')).toBeInTheDocument()
      expect(screen.getByText('per poster')).toBeInTheDocument()
    })
  })

  it('shows fallback pricing when API returns non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500
    })

    renderLandingPage()

    await waitFor(() => {
      expect(screen.getByText('$2.99')).toBeInTheDocument()
      expect(screen.getByText('per poster')).toBeInTheDocument()
    })
  })

  it('includes all hero section elements', () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        price_cents: 299,
        formatted_price: '$2.99',
        has_discount: false
      })
    })

    renderLandingPage()

    expect(screen.getByText(/Transform Your Audio/)).toBeInTheDocument()
    expect(screen.getByText(/Into Beautiful/)).toBeInTheDocument()
    expect(screen.getByText(/Posters/)).toBeInTheDocument()
    expect(screen.getByText(/Create stunning visual representations/)).toBeInTheDocument()
    expect(screen.getByText('Create Your Poster')).toBeInTheDocument()
    expect(screen.getByText('See How It Works')).toBeInTheDocument()
  })
})
