import React, { useState, useEffect } from 'react'
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js'
import { Check, ArrowLeft, CreditCard, Lock, Download, Star } from 'lucide-react'
import { useSession } from '../contexts/SessionContext'
import { createPaymentIntent, completeOrder } from '@/lib/api'
// import { cn } from '../lib/utils'

interface PricingSectionProps {
  onBack: () => void
}

interface PricingTier {
  id: string
  name: string
  price: number
  description: string
  features: string[]
  popular: boolean
}

const createPricingTiers = (price: number): PricingTier[] => [
  {
    id: 'standard',
    name: 'Download Your Poster',
    price: price,
    description: 'Get your high-quality audio poster PDF',
    features: [
      'Remove watermark',
      'High-resolution PDF (300 DPI)',
      'All template designs available',
      'Instant download',
      '7-day download link',
      'Personal use license'
    ],
    popular: true
  }
]

const cardStyle = {
  style: {
    base: {
      fontSize: '16px',
      color: '#424770',
      '::placeholder': {
        color: '#aab7c4',
      },
    },
    invalid: {
      color: '#9e2146',
    },
  },
  hidePostalCode: true, // We collect postal code separately for better international support
  wallets: {
    applePay: 'auto',
    googlePay: 'auto',
  },
}

export default function PricingSection({ onBack }: PricingSectionProps) {
  const { session } = useSession()
  const stripe = useStripe()
  const elements = useElements()

  const [selectedTier, setSelectedTier] = useState<'standard' | 'premium'>('standard')
  const [pricingTiers, setPricingTiers] = useState<PricingTier[]>(createPricingTiers(299))
  const [priceLoading, setPriceLoading] = useState<boolean>(true)
  const [email, setEmail] = useState('')
  const [zipCode, setZipCode] = useState('')
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)

  // Fetch current price from API
  useEffect(() => {
    const fetchPrice = async () => {
      try {
        setPriceLoading(true)
        const response = await fetch('/api/price')
        if (response.ok) {
          const priceData = await response.json()
          setPricingTiers(createPricingTiers(priceData.price_cents))
        } else {
          console.error('Failed to fetch price, using default')
        }
      } catch (error) {
        console.error('Error fetching price:', error)
        // Keep default price if fetch fails
      } finally {
        setPriceLoading(false)
      }
    }

    fetchPrice()
  }, [])

  const selectedPrice = pricingTiers.find(tier => tier.id === selectedTier)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()

    if (!stripe || !elements || !session) {
      return
    }

    setProcessing(true)
    setError(null)

    try {
      // Create payment intent
      const { client_secret, order_id } = await createPaymentIntent(
        session.session_token,
        email,
        'standard'
      )

      // Confirm payment
      const cardElement = elements.getElement(CardElement)
      if (!cardElement) {
        throw new Error('Card element not found')
      }

      const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(
        client_secret,
        {
          payment_method: {
            card: cardElement,
            billing_details: {
              email: email,
              address: {
                postal_code: zipCode,
              },
            },
          }
        }
      )

      if (stripeError) {
        throw new Error(stripeError.message)
      }

      if (paymentIntent?.status === 'succeeded') {
        // Complete the order
        const orderResult = await completeOrder(order_id, paymentIntent.id)
        setDownloadUrl(orderResult.download_url)
        setSuccess(true)
      }

    } catch (err) {
      console.error('Payment failed:', err)
      setError(err instanceof Error ? err.message : 'Payment failed. Please try again.')
    } finally {
      setProcessing(false)
    }
  }

  const handleDownload = () => {
    if (downloadUrl) {
      window.open(downloadUrl, '_blank')
    }
  }

  if (success) {
    return (
      <div className="max-w-md mx-auto">
        <div className="card text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-green-600" />
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h2>
          <p className="text-gray-600 mb-6">
            Your audio poster is ready for download. We've also sent the download link to your email.
          </p>

          <button
            onClick={handleDownload}
            className="btn-primary w-full flex items-center justify-center space-x-2 mb-4"
          >
            <Download className="w-4 h-4" />
            <span>Download Your Poster</span>
          </button>

          <p className="text-sm text-gray-500">
            Download link expires in 7 days
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Download Your Poster</h2>
        <p className="text-gray-600">
          Remove the watermark and get your high-quality audio poster PDF with any template design.
        </p>
      </div>

      <div className="max-w-md mx-auto">
        {pricingTiers.map((tier) => (
          <div
            key={tier.id}
            className="card relative border-primary-200"
          >
            {tier.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <div className="bg-primary-600 text-white px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-1">
                  <Star className="w-3 h-3" />
                  <span>Best Value</span>
                </div>
              </div>
            )}

            <div className="flex items-center space-x-3 mb-4">
              <input
                type="radio"
                name="tier"
                value={tier.id}
                checked={selectedTier === tier.id}
                onChange={(e) => setSelectedTier(e.target.value as 'standard' | 'premium')}
                className="text-primary-600 focus:ring-primary-500"
              />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{tier.name}</h3>
                <p className="text-sm text-gray-600">{tier.description}</p>
              </div>
            </div>

            <div className="mb-4">
              <div className="flex items-baseline space-x-2">
                <span className="text-3xl font-bold text-gray-900">
                  {priceLoading ? (
                    <div className="inline-flex items-center">
                      <div className="w-6 h-6 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin mr-2" />
                      Loading...
                    </div>
                  ) : (
                    `$${(tier.price / 100).toFixed(2)}`
                  )}
                </span>
                {/* Original price removed for simplicity */}
              </div>
            </div>

            <ul className="space-y-2">
              {tier.features.map((feature, index) => (
                <li key={index} className="flex items-center space-x-2 text-sm">
                  <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Payment Form */}
      <div className="max-w-md mx-auto">
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="your@email.com"
              />
              <p className="text-xs text-gray-500 mt-1">
                Required for PDF delivery and download link
              </p>
            </div>

            <div>
              <label htmlFor="zipCode" className="block text-sm font-medium text-gray-700 mb-1">
                Postal Code
              </label>
              <input
                type="text"
                id="zipCode"
                value={zipCode}
                onChange={(e) => setZipCode(e.target.value.toUpperCase())}
                minLength={3}
                maxLength={12}
                pattern="^[A-Z0-9][A-Z0-9\s\-]{1,10}[A-Z0-9]$"
                title="Enter your postal/ZIP code (e.g., 12345, V6K 2Y5, SW1A 1AA, 75008)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Enter postal code"
              />
              <p className="text-xs text-gray-500 mt-1">
                Any country postal/ZIP code accepted
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Card Information
              </label>
              <div className="border border-gray-300 rounded-lg p-3">
                <CardElement options={cardStyle} />
              </div>
            </div>

            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={!stripe || processing || !email || !zipCode}
              className="btn-primary w-full flex items-center justify-center space-x-2"
            >
              {processing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <CreditCard className="w-4 h-4" />
                  <span>
                    Pay {priceLoading ? '...' : `$${selectedPrice ? (selectedPrice.price / 100).toFixed(2) : '0.00'}`}
                  </span>
                </>
              )}
            </button>

            <div className="text-center">
              <div className="flex items-center justify-center space-x-1 text-xs text-gray-500">
                <Lock className="w-3 h-3" />
                <span>Secured by Stripe • SSL Encrypted</span>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Back Button */}
      <div className="flex justify-center pt-6">
        <button
          onClick={onBack}
          className="btn-secondary flex items-center space-x-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Preview</span>
        </button>
      </div>
    </div>
  )
}
