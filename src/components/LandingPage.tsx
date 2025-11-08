import { ArrowRight, Music, Heart, Gift, Sparkles, Check, Upload, Palette, Download, DollarSign, Quote } from 'lucide-react'
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

  const testimonials = [
    {
      emoji: '🌍',
      quote: "A voice from home he'll always have.",
      text: "My son is studying abroad, so I recorded a message telling him, 'I love you and I'm proud of you,' and turned it into a VocaFrame poster. Now he can scan it anytime and hear my voice from across the ocean. It's such a heartfelt way to stay connected.",
      author: 'Farah N.',
      location: 'San Diego, CA'
    },
    {
      emoji: '👩‍👧',
      quote: 'The sweetest surprise for my mom.',
      text: "I wanted to surprise my mother, she adores her granddaughter. I used VocaFrame to create a poster with my daughter's voice saying 'I love you, Grandma!' When my mom played it, she cried happy tears. It's such a unique and emotional gift.",
      author: 'Leila M.',
      location: 'Toronto, Canada'
    },
    {
      emoji: '💝',
      quote: 'An affordable gift that means so much.',
      text: "Using VocaFrame was super easy. I printed the poster myself and found a lovely frame at a dollar store. It turned out beautiful, a thoughtful, personal gift that didn't cost much but meant the world.",
      author: 'Sara J.',
      location: 'Vancouver, BC'
    },
    {
      emoji: '🕊️',
      quote: 'A way to keep his voice close.',
      text: "After my dad passed, I found an old voicemail of him saying he was proud of me. VocaFrame helped me preserve it in a way that feels timeless. It's comforting to see his words, not just hear them. Thank you for this beautiful idea.",
      author: 'Lila G.',
      location: 'Toronto, Canada'
    },
    {
      emoji: '💖',
      quote: "The most meaningful gift I've ever given.",
      text: "I turned my husband's voice message into a framed poster for our anniversary, and he actually teared up. It's so beautiful to see something that sounds like love, now hanging on our wall. VocaFrame made it in minutes and delivered instantly. Truly unforgettable.",
      author: 'Emily R.',
      location: 'Vancouver, Canada'
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
                <div className="inline-flex items-center space-x-4 bg-white border-2 border-primary-300 px-8 py-6 rounded-3xl shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-primary-500 to-blue-600 rounded-full shadow-lg">
                    <DollarSign className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex items-center space-x-4">
                    {pricingData.has_discount ? (
                      <>
                        <div className="flex flex-col items-start">
                          <span className="text-4xl font-bold text-primary-700 leading-none">
                            {pricingData.formatted_price}
                          </span>
                          <span className="text-sm text-gray-600 font-medium mt-1">per poster</span>
                        </div>
                        <div className="flex flex-col items-center space-y-1">
                          <span className="text-lg text-gray-400 line-through leading-none">
                            {pricingData.formatted_original_price}
                          </span>
                          <span className="bg-gradient-to-r from-green-500 to-emerald-600 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-md">
                            SAVE {pricingData.discount_percentage}%
                          </span>
                        </div>
                      </>
                    ) : (
                      <div className="flex flex-col items-start">
                        <span className="text-4xl font-bold text-primary-700 leading-none">
                          {pricingData.formatted_price}
                        </span>
                        <span className="text-sm text-gray-600 font-medium mt-1">per poster</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="inline-flex items-center space-x-4 bg-white border-2 border-primary-300 px-8 py-6 rounded-3xl shadow-xl">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-primary-500 to-blue-600 rounded-full shadow-lg">
                    <DollarSign className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex flex-col items-start">
                    <span className="text-4xl font-bold text-primary-700 leading-none">$2.99</span>
                    <span className="text-sm text-gray-600 font-medium mt-1">per poster</span>
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => navigate('/customize')}
                className="btn-primary flex items-center space-x-2 text-lg px-10"
              >
                <span>Create Your Poster instantly</span>
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
              onClick={() => navigate('/customize')}
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

      {/* Pricing Section */}
      <section className="py-20 bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="max-w-5xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-12">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-600">
              One price, unlimited possibilities. No subscriptions, no hidden fees.
            </p>
          </div>

          <div className="bg-white rounded-3xl shadow-2xl border-2 border-gray-200 overflow-hidden">
            <div className="bg-gradient-to-r from-primary-600 to-blue-600 p-8 text-center">
              {pricingLoading ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="bg-white/20 h-8 w-24 rounded animate-pulse"></div>
                </div>
              ) : pricingData ? (
                <div>
                  {pricingData.has_discount ? (
                    <div className="space-y-2">
                      <div className="flex items-center justify-center space-x-3">
                        <span className="text-6xl font-bold text-white">
                          {pricingData.formatted_price}
                        </span>
                        <div className="flex flex-col items-start">
                          <span className="text-2xl text-white/70 line-through">
                            {pricingData.formatted_original_price}
                          </span>
                          <span className="bg-white text-primary-700 text-sm font-bold px-3 py-1 rounded-full">
                            Save {pricingData.discount_percentage}%
                          </span>
                        </div>
                      </div>
                      <p className="text-primary-100 text-lg">per poster</p>
                    </div>
                  ) : (
                    <div>
                      <div className="text-6xl font-bold text-white mb-2">
                        {pricingData.formatted_price}
                      </div>
                      <p className="text-primary-100 text-lg">per poster</p>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <div className="text-6xl font-bold text-white mb-2">$2.99</div>
                  <p className="text-primary-100 text-lg">per poster</p>
                </div>
              )}
            </div>

            <div className="p-8 sm:p-12">
              <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
                Everything Included
              </h3>
              <div className="grid sm:grid-cols-2 gap-4 mb-8">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    <Check className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">High-Resolution PDF</p>
                    <p className="text-sm text-gray-600">300 DPI print-ready quality</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    <Check className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">Multiple Sizes</p>
                    <p className="text-sm text-gray-600">A3, A4, Letter formats</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    <Check className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">Custom Backgrounds</p>
                    <p className="text-sm text-gray-600">Choose from curated designs</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    <Check className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">Personal Text</p>
                    <p className="text-sm text-gray-600">Add your own message</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    <Check className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">QR Code Included</p>
                    <p className="text-sm text-gray-600">Scan to play audio</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    <Check className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">Instant Download</p>
                    <p className="text-sm text-gray-600">Get it in minutes</p>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-6 mb-8">
                <div className="flex items-start space-x-3">
                  <Sparkles className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                  <div>
                    <p className="font-semibold text-gray-900 mb-2">Professional Quality Guarantee</p>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      Your poster is created with professional-grade tools and exported at 300 DPI,
                      ensuring crisp, vibrant prints whether you choose to frame it yourself or have it
                      printed at your local print shop.
                    </p>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <button
                  onClick={() => navigate('/customize')}
                  className="btn-primary flex items-center space-x-2 text-lg px-12 mx-auto"
                >
                  <span>Create Your Poster Now</span>
                  <ArrowRight className="w-5 h-5" />
                </button>
                <p className="text-sm text-gray-500 mt-4">
                  No account required • Secure payment • Instant delivery
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 bg-white overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-12">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
              Stories From Our Community
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-6">
              Real people, real memories, real emotions preserved through VocaFrame
            </p>
            <p className="text-sm text-gray-500">
              Scroll to see more →
            </p>
          </div>

          <div className="relative">
            <div className="flex overflow-x-auto gap-6 pb-8 snap-x snap-mandatory scrollbar-hide">
              {testimonials.map((testimonial, index) => (
                <div
                  key={index}
                  className="flex-shrink-0 w-[85%] sm:w-[400px] bg-gradient-to-br from-gray-50 to-white border-2 border-gray-200 rounded-2xl p-8 hover:shadow-xl hover:border-primary-300 transition-all duration-300 snap-start"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="text-4xl">{testimonial.emoji}</div>
                    <Quote className="w-8 h-8 text-primary-200" />
                  </div>

                  <h3 className="text-xl font-bold text-gray-900 mb-4 leading-snug">
                    {testimonial.quote}
                  </h3>

                  <p className="text-gray-600 leading-relaxed mb-6">
                    {testimonial.text}
                  </p>

                  <div className="pt-4 border-t border-gray-200">
                    <p className="font-semibold text-gray-900">{testimonial.author}</p>
                    <p className="text-sm text-gray-500">{testimonial.location}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="absolute left-0 top-0 bottom-8 w-12 bg-gradient-to-r from-white to-transparent pointer-events-none" />
            <div className="absolute right-0 top-0 bottom-8 w-12 bg-gradient-to-l from-white to-transparent pointer-events-none" />
          </div>

          <div className="text-center mt-8">
            <button
              onClick={() => navigate('/customize')}
              className="btn-primary flex items-center space-x-2 text-lg px-10 mx-auto"
            >
              <span>Create Your Own Memory</span>
              <ArrowRight className="w-5 h-5" />
            </button>
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
            onClick={() => navigate('/customize')}
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
