# AudioPoster - Create Beautiful Audio Memory Posters

Transform your favorite songs and voice messages into beautiful, personalized poster PDFs with custom photos and audio waveforms.

## Features

- 🎵 **Audio Waveform Visualization**: Convert any audio into stunning waveform art
- 📷 **Photo Integration**: Combine your memories with audio visualizations
- ✨ **Custom Text**: Add personal messages and dedications
- 🎨 **Multiple Templates**: Choose from Classic, Modern, Vintage, and Elegant designs
- 💳 **Anonymous Checkout**: No account required - pay and download instantly
- 📱 **Mobile Responsive**: Works perfectly on all devices
- 🔗 **QR Code Integration**: Links to audio playback for interactive posters

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Stripe Elements** for payments
- **React Dropzone** for file uploads
- **Lucide React** for icons

### Backend
- **FastAPI** with Python 3.11
- **PostgreSQL** for data persistence
- **Redis** for caching and task queues
- **Celery** for background processing
- **Stripe** for payment processing
- **SendGrid** for email delivery
- **AWS S3** for file storage

### Audio/Image Processing
- **librosa** for audio analysis and waveform generation
- **PIL (Pillow)** for image processing
- **ReportLab** for PDF generation
- **matplotlib** for waveform visualization

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** 15+
- **Redis** 7+
- **Docker** (optional, for containerized setup)

### Environment Setup

1. Copy the environment template:
```bash
cp env.example .env
```

2. Update the `.env` file with your configuration:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/audioposter
REDIS_URL=redis://localhost:6379

# Stripe (get keys from dashboard)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# SendGrid (for email delivery)
SENDGRID_API_KEY=SG....

# AWS S3 (for file storage)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=audioposter-files
```

### Development Setup

#### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f api
```

The application will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- Database: localhost:5432

#### Option 2: Local Development

1. **Backend Setup**:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis locally
# Run database migrations
alembic upgrade head

# Start the API server
uvicorn backend.main:app --reload --port 8000

# Start Celery worker (in another terminal)
celery -A backend.tasks worker --loglevel=info

# Start Celery beat (in another terminal)
celery -A backend.tasks beat --loglevel=info
```

2. **Frontend Setup**:
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Production Deployment

1. **Build the frontend**:
```bash
npm run build
```

2. **Deploy with Docker**:
```bash
# Production build
docker-compose -f docker-compose.yml --profile production up -d
```

3. **Set up SSL** (recommended):
   - Use Let's Encrypt with Certbot
   - Update nginx.conf for HTTPS

## Project Structure

```
voiceFrame/
├── src/                    # React frontend
│   ├── components/         # React components
│   ├── contexts/          # React contexts
│   ├── lib/               # Utilities and API client
│   └── main.tsx           # App entry point
├── backend/               # FastAPI backend
│   ├── services/          # Business logic
│   ├── models.py          # Database models
│   ├── schemas.py         # Pydantic schemas
│   ├── main.py            # FastAPI app
│   └── tasks.py           # Celery tasks
├── alembic/               # Database migrations
├── docs/                  # Documentation
├── docker-compose.yml     # Development environment
├── Dockerfile             # Container definition
├── nginx.conf             # Production web server
└── requirements.txt       # Python dependencies
```

## API Endpoints

### Session Management
- `POST /api/session` - Create new session
- `GET /api/session/{token}` - Get session data
- `PUT /api/session/{token}` - Update session

### File Upload
- `POST /api/session/{token}/photo` - Upload photo
- `POST /api/session/{token}/audio` - Upload audio
- `GET /api/session/{token}/status` - Check processing status

### Preview & Generation
- `GET /api/session/{token}/preview` - Generate watermarked preview

### Payment & Download
- `POST /api/session/{token}/payment` - Create payment intent
- `POST /api/orders/{order_id}/complete` - Complete order
- `GET /api/download/{token}` - Download final PDF

## Features Overview

### User Flow
1. **Upload**: Drag and drop photo + audio files
2. **Customize**: Add text, choose shape/size/template
3. **Preview**: See watermarked version
4. **Purchase**: Anonymous checkout with Stripe
5. **Download**: Instant PDF delivery via email

### Payment Tiers
- **Standard ($2.99)**: Remove watermark, high-res PDF, 24h download
- **Premium ($4.99)**: Everything + premium templates, commercial license, 7-day download

### Templates
- **Classic**: Clean, timeless design
- **Modern**: Contemporary minimalist style  
- **Vintage**: Retro-inspired aesthetic
- **Elegant**: Sophisticated and refined

## Contributing

This project is optimized for use with **Lovable** and **Bolt** for easy frontend modifications and improvements.

### Frontend Development
- Built with modern React patterns
- Fully typed with TypeScript
- Tailwind CSS for easy styling
- Component-based architecture

### Backend Development
- RESTful API design
- Async/await patterns
- Comprehensive error handling
- Background task processing

## License

Private project - All rights reserved.

## Support

For questions or issues:
- Check the docs/ folder for detailed documentation
- Review the technical implementation plan
- Create an issue in the repository
