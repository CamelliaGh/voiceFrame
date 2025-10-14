import { ArrowRight, Music, Heart, Gift, Sparkles, Check, Upload, Palette, Download, DollarSign } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Header from './Header'
import Footer from './Footer'

interface PricingData {
  price_cents: number
  original_price_cents: number
  price_dollars: number
  original_price_dollars: number
  formatted_price: string
  formatted_original_price: string
  discount_percentage: number
  discount_amount: number
  discount_enabled: boolean
  has_discount: boolean
}

export default function LandingPage() {
  const navigate = useNavigate()
  const [pricingData, setPricingData] = useState<PricingData | null>(null)
  const [pricingLoading, setPricingLoading] = useState(true)

  const features = [
    {
      icon: Music,
      title: 'Audio Waveform Art',
      description: 'Transform your favorite songs and voice messages into stunning visual waveforms'
    },
    {
      icon: Heart,
      title: 'Personal Touch',
      description: 'Add your own photos and custom text to create something truly unique'
    },
    {
      icon: Gift,
      title: 'Perfect Gift',
      description: 'Create memorable gifts for weddings, anniversaries, birthdays, or any special occasion'
    },
    {
      icon: Sparkles,
      title: 'Print Ready',
      description: 'High-resolution PDFs ready for professional printing in multiple sizes'
    }
  ]

  const steps = [
    {
      icon: Upload,
      title: 'Upload',
      description: 'Upload your audio file and photo'
    },
    {
      icon: Palette,
      title: 'Customize',
      description: 'Choose size, background, and add text'
    },
    {
      icon: Download,
      title: 'Download',
      description: 'Get your high-quality PDF poster'
    }
  ]

  const useCases = [
    {
      title: 'Wedding Songs',
      description: 'Immortalize your first dance or wedding song',
      emoji: '💒'
    },
    {
      title: 'Voice Messages',
      description: 'Preserve precious voice recordings from loved ones',
      emoji: '🎤'
    },
    {
      title: 'Anniversary Gifts',
      description: 'Celebrate years together with your special song',
      emoji: '💝'
    },
    {
      title: 'Memorial Tributes',
      description: 'Honor memories with meaningful audio',
      emoji: '🕊️'
    },
    {
      title: 'Baby Sounds',
      description: "Capture baby's first words or laughter forever",
      emoji: '👶'
    },
    {
      title: 'Favorite Songs',
      description: 'Turn your anthem into wall art',
      emoji: '🎵'
    }
  ]

  // Fetch pricing data
  useEffect(() => {
    const fetchPricing = async () => {
      try {
        setPricingLoading(true)
        const response = await fetch('/api/price')
        if (response.ok) {
          const data = await response.json()
          setPricingData(data)
        } else {
          console.error('Failed to fetch pricing data')
        }
      } catch (error) {
        console.error('Error fetching pricing data:', error)
      } finally {
        setPricingLoading(false)
      }
    }

    fetchPricing()
  }, [])

  return (
    <div className="min-h-screen bg-white">
      <Header />

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-sky-50">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-20 sm:py-28 relative">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center space-x-2 bg-primary-100 text-primary-700 px-4 py-2 rounded-full text-sm font-semibold mb-8">
              <Sparkles className="w-4 h-4" />
              <span>Turn Audio Into Art</span>
            </div>

            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              Transform Your Audio
              <br />
              Into Beautiful
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-blue-600"> Posters</span>
            </h1>

            <p className="text-xl sm:text-2xl text-gray-600 mb-10 leading-relaxed">
              Create stunning visual representations of your favorite songs, voice messages, and audio memories.
              Perfect for gifts, décor, and preserving precious moments.
            </p>

            {/* Pricing Display */}
            <div className="mb-10">
              {pricingLoading ? (
                <div className="inline-flex items-center space-x-2 bg-gray-100 px-6 py-3 rounded-2xl animate-pulse">
                  <div className="bg-gray-300 h-6 w-6 rounded-full"></div>
                  <div className="bg-gray-300 h-6 w-20 rounded"></div>
                </div>
              ) : pricingData ? (
                <div className="inline-flex items-center space-x-3 bg-gradient-to-r from-purple-100 via-purple-50 to-purple-100 border-2 border-purple-200 px-8 py-5 rounded-3xl shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 backdrop-blur-sm">
                  <div className="flex items-center justify-center w-10 h-10 bg-purple-600 rounded-full shadow-md">
                    <DollarSign className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex items-center space-x-3">
                    {pricingData.has_discount ? (
                      <>
                        <div className="flex flex-col items-start">
                          <span className="text-3xl font-bold text-purple-700 leading-none">
                            {pricingData.formatted_price}
                          </span>
                          <span className="text-sm text-purple-600 font-medium">per poster</span>
                        </div>
                        <div className="flex flex-col items-center">
                          <span className="text-lg text-gray-500 line-through leading-none">
                            {pricingData.formatted_original_price}
                          </span>
                          <span className="bg-gradient-to-r from-red-500 to-red-600 text-white text-xs font-bold px-3 py-1 rounded-full shadow-md mt-1">
                            SAVE {pricingData.discount_percentage}%
                          </span>
                        </div>
                      </>
                    ) : (
                      <div className="flex flex-col items-start">
                        <span className="text-3xl font-bold text-purple-700 leading-none">
                          {pricingData.formatted_price}
                        </span>
                        <span className="text-sm text-purple-600 font-medium">per poster</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="inline-flex items-center space-x-3 bg-gradient-to-r from-purple-100 via-purple-50 to-purple-100 border-2 border-purple-200 px-8 py-5 rounded-3xl shadow-lg">
                  <div className="flex items-center justify-center w-10 h-10 bg-purple-600 rounded-full shadow-md">
                    <DollarSign className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex flex-col items-start">
                    <span className="text-3xl font-bold text-purple-700 leading-none">$2.99</span>
                    <span className="text-sm text-purple-600 font-medium">per poster</span>
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="btn-primary flex items-center space-x-2 text-lg px-10"
              >
                <span>Create Your Poster</span>
                <ArrowRight className="w-5 h-5" />
              </button>
              <button
                onClick={() => {
                  const element = document.getElementById('how-it-works')
                  element?.scrollIntoView({ behavior: 'smooth' })
                }}
                className="btn-secondary flex items-center space-x-2 text-lg px-10"
              >
                <span>See How It Works</span>
              </button>
            </div>

            <div className="mt-12 flex items-center justify-center space-x-8 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <Check className="w-5 h-5 text-green-600" />
                <span>High Quality PDF</span>
              </div>
              <div className="flex items-center space-x-2">
                <Check className="w-5 h-5 text-green-600" />
                <span>Print Ready</span>
              </div>
              <div className="flex items-center space-x-2">
                <Check className="w-5 h-5 text-green-600" />
                <span>Instant Download</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
              Why Choose VoiceFrame?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Create meaningful, personalized art that captures the essence of your audio memories
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="card text-center hover:shadow-xl transition-all duration-300"
              >
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary-100 to-blue-100 mb-6">
                  <feature.icon className="w-8 h-8 text-primary-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
              Create Your Poster in 3 Easy Steps
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              From upload to download in just a few minutes
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                <div className="card text-center">
                  <div className="relative inline-flex items-center justify-center mb-6">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary-400 to-blue-500 rounded-full blur-xl opacity-30" />
                    <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-primary-500 to-blue-600 flex items-center justify-center">
                      <step.icon className="w-10 h-10 text-white" />
                    </div>
                    <div className="absolute -top-2 -right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg">
                      <span className="text-sm font-bold text-primary-600">{index + 1}</span>
                    </div>
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-3">
                    {step.title}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    {step.description}
                  </p>
                </div>
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-1/3 -right-6 w-12">
                    <ArrowRight className="w-8 h-8 text-primary-400" />
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <button
              onClick={() => navigate('/')}
              className="btn-primary flex items-center space-x-2 text-lg px-10 mx-auto"
            >
              <span>Get Started Now</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
              Perfect For Every Occasion
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Create meaningful gifts and keepsakes for life's special moments
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {useCases.map((useCase, index) => (
              <div
                key={index}
                className="bg-white border-2 border-gray-200 rounded-2xl p-6 hover:border-primary-400 hover:shadow-lg transition-all duration-300"
              >
                <div className="text-4xl mb-4">{useCase.emoji}</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {useCase.title}
                </h3>
                <p className="text-gray-600">
                  {useCase.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-primary-600 to-blue-700 text-white">
        <div className="max-w-4xl mx-auto px-6 sm:px-8 lg:px-12 text-center">
          <h2 className="text-4xl sm:text-5xl font-bold mb-6">
            Ready to Create Your Audio Poster?
          </h2>
          <p className="text-xl text-primary-100 mb-10">
            Join thousands of people preserving their precious audio memories as beautiful art
          </p>
          <button
            onClick={() => navigate('/')}
            className="bg-white text-primary-600 hover:bg-gray-50 font-bold py-4 px-10 text-lg rounded-xl shadow-xl hover:shadow-2xl transition-all duration-300 inline-flex items-center space-x-2"
          >
            <span>Start Creating Now</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      <Footer />
    </div>
  )
}
