import React, { useEffect, useState } from 'react'
import { useStripe, PaymentRequestButtonElement } from '@stripe/react-stripe-js'
import { PaymentRequest, PaymentRequestPaymentMethodEvent } from '@stripe/stripe-js'

interface PaymentRequestButtonProps {
  amount: number // in cents
  currency: string
  country: string
  email: string
  onPaymentSuccess: (paymentMethodId: string) => void
  onPaymentError: (error: string) => void
  disabled?: boolean
}

export default function PaymentRequestButton({
  amount,
  currency,
  country,
  email,
  onPaymentSuccess,
  onPaymentError,
  disabled = false
}: PaymentRequestButtonProps) {
  const stripe = useStripe()
  const [paymentRequest, setPaymentRequest] = useState<PaymentRequest | null>(null)
  const [canMakePayment, setCanMakePayment] = useState(false)

  useEffect(() => {
    if (!stripe || disabled) {
      return
    }

    // Create payment request
    const pr = stripe.paymentRequest({
      country,
      currency: currency.toLowerCase(),
      total: {
        label: 'Audio Poster',
        amount: amount,
      },
      requestPayerEmail: true,
      requestPayerName: false,
    })

    // Check if browser supports Apple Pay or Google Pay
    pr.canMakePayment().then((result) => {
      if (result) {
        setPaymentRequest(pr)
        setCanMakePayment(true)
      }
    })

    // Handle payment method event
    pr.on('paymentmethod', async (ev: PaymentRequestPaymentMethodEvent) => {
      try {
        // Call the success handler with payment method ID
        onPaymentSuccess(ev.paymentMethod.id)

        // Complete the payment request
        ev.complete('success')
      } catch (error) {
        console.error('Payment failed:', error)
        ev.complete('fail')
        onPaymentError(error instanceof Error ? error.message : 'Payment failed')
      }
    })

  }, [stripe, amount, currency, country, email, disabled, onPaymentSuccess, onPaymentError])

  // Update payment request amount when it changes
  useEffect(() => {
    if (paymentRequest) {
      paymentRequest.update({
        total: {
          label: 'Audio Poster',
          amount: amount,
        },
      })
    }
  }, [amount, paymentRequest])

  if (!canMakePayment || !paymentRequest) {
    return null
  }

  return (
    <div className="payment-request-button-wrapper" style={{ marginBottom: '0' }}>
      <PaymentRequestButtonElement
        options={{
          paymentRequest,
          style: {
            paymentRequestButton: {
              type: 'buy',
              theme: 'dark',
              height: '48px',
            },
          },
        }}
      />
      <style>{`
        .payment-request-button-wrapper {
          width: 100%;
        }
        .payment-request-button-wrapper > div {
          width: 100%;
        }
      `}</style>
    </div>
  )
}
