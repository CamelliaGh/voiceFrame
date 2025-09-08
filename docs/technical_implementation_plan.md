# Audio Poster Generator - Technical Implementation Plan

## 1. Technology Stack Overview

### 1.1 Backend Stack
- **Framework**: Flask (Python 3.9+) with Gunicorn WSGI server
- **Database**: PostgreSQL 14+ for order tracking, Redis for sessions/cache
- **File Processing**: 
  - Audio: `librosa` for waveform analysis, `pydub` for format conversion
  - Images: `Pillow` (PIL) for image processing and manipulation
  - PDF: `reportlab` for PDF generation, `qrcode` for QR codes
- **Task Queue**: Celery with Redis broker for background processing
- **File Storage**: AWS S3 for temporary file storage and generated PDFs
- **Email**: SendGrid or AWS SES for transactional emails
- **Payments**: Stripe API for anonymous checkout

### 1.2 Frontend Stack
- **Framework**: Vanilla JavaScript with modern ES6+ (keep it simple for MVP)
- **Styling**: Tailwind CSS with custom components
- **File Upload**: Dropzone.js for drag-and-drop functionality
- **Preview**: Canvas API for real-time poster preview
- **Payments**: Stripe Elements for secure checkout

### 1.3 Infrastructure
- **Hosting**: AWS EC2 or DigitalOcean Droplets
- **Load Balancer**: Nginx reverse proxy
- **CDN**: CloudFlare for static assets
- **Monitoring**: New Relic or DataDog for performance monitoring
- **Error Tracking**: Sentry for error logging

## 2. Database Schema Design

### 2.1 Core Tables

```sql
-- Orders table (minimal data for anonymous purchases)
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    amount_cents INTEGER NOT NULL,
    stripe_payment_intent_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed
    download_token VARCHAR(255) UNIQUE,
    download_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Session data (temporary file references)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    photo_s3_key VARCHAR(500),
    audio_s3_key VARCHAR(500),
    waveform_s3_key VARCHAR(500),
    custom_text TEXT,
    photo_shape VARCHAR(20) DEFAULT 'square',
    pdf_size VARCHAR(20) DEFAULT 'A4',
    template_id VARCHAR(50) DEFAULT 'classic',
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours'
);

-- Email marketing (post-purchase opt-ins)
CREATE TABLE email_subscribers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    subscribed BOOLEAN DEFAULT true,
    source VARCHAR(50) DEFAULT 'purchase', -- purchase, referral, etc
    first_purchase_date TIMESTAMP,
    total_purchases INTEGER DEFAULT 1,
    total_spent_cents INTEGER,
    last_campaign_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Templates (for future expansion)
CREATE TABLE templates (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_premium BOOLEAN DEFAULT false,
    layout_config JSONB, -- Store template positioning data
    preview_image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 3. API Design & Endpoints

### 3.1 Session Management
```python
# Create new session
POST /api/session
Response: {"session_token": "uuid", "expires_at": "timestamp"}

# Update session data
PUT /api/session/{token}
Body: {
    "custom_text": "Hi honey...",
    "photo_shape": "circle",
    "pdf_size": "A4",
    "template_id": "classic"
}
```

### 3.2 File Upload Endpoints
```python
# Upload photo
POST /api/session/{token}/photo
Content-Type: multipart/form-data
Body: photo file
Response: {"status": "success", "photo_url": "preview_url"}

# Upload audio
POST /api/session/{token}/audio  
Content-Type: multipart/form-data
Body: audio file
Response: {
    "status": "success", 
    "duration": 180.5,
    "waveform_processing": "started"
}

# Check processing status
GET /api/session/{token}/status
Response: {
    "photo_ready": true,
    "audio_ready": true,
    "waveform_ready": true,
    "preview_ready": true
}
```

### 3.3 Preview Generation
```python
# Generate watermarked preview
GET /api/session/{token}/preview
Response: {"preview_url": "signed_s3_url", "expires_at": "timestamp"}

# Get session data for preview
GET /api/session/{token}
Response: {
    "custom_text": "...",
    "photo_shape": "square",
    "photo_url": "...",
    "waveform_url": "...",
    "template": {...}
}
```

### 3.4 Payment & Download
```python
# Create payment intent
POST /api/session/{token}/payment
Body: {
    "email": "user@example.com",
    "tier": "standard" // or "premium"
}
Response: {
    "client_secret": "stripe_client_secret",
    "amount": 299
}

# Complete order after payment
POST /api/orders/{order_id}/complete
Body: {"payment_intent_id": "stripe_pi_xxx"}
Response: {
    "download_url": "signed_url",
    "expires_at": "timestamp",
    "email_sent": true
}

# Download PDF (with token validation)
GET /api/download/{download_token}
Response: PDF file stream
```

## 4. Core Processing Pipeline

### 4.1 Audio Processing Flow
```python
# app/services/audio_processor.py
import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from io import BytesIO

class AudioProcessor:
    def __init__(self, s3_client):
        self.s3 = s3_client
    
    def process_audio(self, audio_file_path, session_token):
        """Process uploaded audio file and generate waveform"""
        try:
            # Load audio file
            y, sr = librosa.load(audio_file_path, sr=44100)
            
            # Normalize audio
            y = librosa.util.normalize(y)
            
            # Trim silence
            y_trimmed, _ = librosa.effects.trim(y, top_db=20)
            
            # Generate waveform image
            waveform_buffer = self._generate_waveform_image(y_trimmed)
            
            # Upload to S3
            waveform_key = f"waveforms/{session_token}.png"
            self.s3.put_object(
                Bucket=settings.S3_BUCKET,
                Key=waveform_key,
                Body=waveform_buffer.getvalue(),
                ContentType='image/png'
            )
            
            return {
                'duration': len(y_trimmed) / sr,
                'waveform_s3_key': waveform_key,
                'sample_rate': sr
            }
            
        except Exception as e:
            raise AudioProcessingError(f"Failed to process audio: {str(e)}")
    
    def _generate_waveform_image(self, audio_data, width=1200, height=200):
        """Generate waveform visualization"""
        plt.figure(figsize=(width/100, height/100), facecolor='white')
        plt.plot(audio_data, color='black', linewidth=0.3)
        plt.axis('off')
        plt.tight_layout(pad=0)
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        buffer.seek(0)
        
        return buffer
```

### 4.2 Image Processing
```python
# app/services/image_processor.py
from PIL import Image, ImageDraw, ImageOps
import io

class ImageProcessor:
    def __init__(self, s3_client):
        self.s3 = s3_client
    
    def process_photo(self, photo_file, session_token, target_shape='square'):
        """Process uploaded photo for poster generation"""
        try:
            # Open and orient image
            image = Image.open(photo_file)
            image = ImageOps.exif_transpose(image)  # Fix rotation
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to standard dimensions
            max_size = (800, 800)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Create square crop if needed
            if target_shape == 'square':
                image = self._make_square(image)
            
            # Save processed image
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=95, optimize=True)
            buffer.seek(0)
            
            # Upload to S3
            photo_key = f"photos/{session_token}.jpg"
            self.s3.put_object(
                Bucket=settings.S3_BUCKET,
                Key=photo_key,
                Body=buffer.getvalue(),
                ContentType='image/jpeg'
            )
            
            return {
                'photo_s3_key': photo_key,
                'dimensions': image.size
            }
            
        except Exception as e:
            raise ImageProcessingError(f"Failed to process image: {str(e)}")
    
    def _make_square(self, image):
        """Crop image to square maintaining aspect ratio"""
        width, height = image.size
        size = min(width, height)
        
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        
        return image.crop((left, top, right, bottom))
    
    def create_circular_mask(self, image):
        """Apply circular mask to image"""
        size = min(image.size)
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        # Apply mask
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        output.paste(image, (0, 0))
        output.putalpha(mask)
        
        return output
```

### 4.3 PDF Generation
```python
# app/services/pdf_generator.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter, A3
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
import qrcode
from PIL import Image
import io

class PDFGenerator:
    def __init__(self, s3_client):
        self.s3 = s3_client
        self.page_sizes = {
            'A4': A4,
            'Letter': letter,
            'A3': A3
        }
    
    def generate_poster_pdf(self, session_data, order_data, add_watermark=True):
        """Generate final PDF poster"""
        try:
            # Set up canvas
            buffer = io.BytesIO()
            page_size = self.page_sizes[session_data['pdf_size']]
            c = canvas.Canvas(buffer, pagesize=page_size)
            width, height = page_size
            
            # Load template configuration
            template = self._get_template_config(session_data['template_id'])
            
            # Add custom text
            self._add_text(c, session_data['custom_text'], width, height, template)
            
            # Add photo
            self._add_photo(c, session_data, template, width, height)
            
            # Add waveform
            self._add_waveform(c, session_data, template, width, height)
            
            # Add QR code
            qr_url = self._generate_qr_url(order_data['id'])
            self._add_qr_code(c, qr_url, template, width, height)
            
            # Add watermark if needed
            if add_watermark:
                self._add_watermark(c, width, height)
            
            c.save()
            buffer.seek(0)
            
            # Upload to S3
            pdf_key = f"pdfs/{order_data['id']}.pdf"
            self.s3.put_object(
                Bucket=settings.S3_BUCKET,
                Key=pdf_key,
                Body=buffer.getvalue(),
                ContentType='application/pdf'
            )
            
            return pdf_key
            
        except Exception as e:
            raise PDFGenerationError(f"Failed to generate PDF: {str(e)}")
    
    def _add_watermark(self, canvas, width, height):
        """Add diagonal watermark across the page"""
        canvas.saveState()
        canvas.setFont("Helvetica", 24)
        canvas.setFillColorRGB(0.8, 0.8, 0.8, 0.3)  # Light gray, 30% opacity
        canvas.rotate(45)
        
        # Calculate position for centered diagonal text
        text = "PREVIEW - AudioPoster.com"
        text_width = canvas.stringWidth(text, "Helvetica", 24)
        
        # Position watermark across the page
        x = (width - text_width) / 2
        y = height / 4
        
        canvas.drawString(x, y, text)
        canvas.restoreState()
    
    def _generate_qr_url(self, order_id):
        """Generate URL for QR code - could link to audio playback page"""
        base_url = settings.BASE_URL
        return f"{base_url}/listen/{order_id}"
```

## 5. Celery Task Queue Setup

### 5.1 Background Tasks
```python
# app/tasks.py
from celery import Celery
from app.services.audio_processor import AudioProcessor
from app.services.image_processor import ImageProcessor
from app.services.pdf_generator import PDFGenerator

celery = Celery('audio_poster')

@celery.task(bind=True)
def process_audio_file(self, session_token, audio_s3_key):
    """Background task to process uploaded audio"""
    try:
        processor = AudioProcessor(s3_client)
        result = processor.process_audio_from_s3(audio_s3_key, session_token)
        
        # Update session with waveform data
        Session.update_waveform_data(session_token, result)
        
        return {"status": "completed", "result": result}
        
    except Exception as e:
        self.retry(countdown=60, max_retries=3)
        raise

@celery.task(bind=True)
def generate_pdf_task(self, session_token, order_id, watermarked=True):
    """Background task to generate PDF"""
    try:
        session_data = Session.get_by_token(session_token)
        order_data = Order.get_by_id(order_id)
        
        generator = PDFGenerator(s3_client)
        pdf_key = generator.generate_poster_pdf(
            session_data, order_data, add_watermark=watermarked
        )
        
        # Update order with PDF location
        Order.update_pdf_location(order_id, pdf_key)
        
        # Send email with download link
        if not watermarked:
            send_download_email.delay(order_id)
        
        return {"status": "completed", "pdf_key": pdf_key}
        
    except Exception as e:
        self.retry(countdown=60, max_retries=3)
        raise

@celery.task
def send_download_email(order_id):
    """Send email with download link"""
    order = Order.get_by_id(order_id)
    download_url = f"{settings.BASE_URL}/api/download/{order.download_token}"
    
    email_service.send_download_email(
        to_email=order.email,
        download_url=download_url,
        order_id=order_id
    )
```

## 6. Frontend Implementation

### 6.1 Core JavaScript Structure
```javascript
// static/js/app.js
class AudioPosterApp {
    constructor() {
        this.sessionToken = null;
        this.uploadedFiles = {
            photo: null,
            audio: null
        };
        this.previewData = {};
        
        this.initializeSession();
        this.setupEventListeners();
    }
    
    async initializeSession() {
        const response = await fetch('/api/session', {method: 'POST'});
        const data = await response.json();
        this.sessionToken = data.session_token;
    }
    
    setupEventListeners() {
        // File uploads
        const photoUpload = document.getElementById('photo-input');
        const audioUpload = document.getElementById('audio-input');
        
        photoUpload.addEventListener('change', (e) => this.handlePhotoUpload(e));
        audioUpload.addEventListener('change', (e) => this.handleAudioUpload(e));
        
        // Form updates
        document.getElementById('custom-text').addEventListener('input', 
            debounce(() => this.updatePreview(), 300));
        
        // Payment
        document.getElementById('generate-btn').addEventListener('click', 
            () => this.initiatePayment());
    }
    
    async handlePhotoUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        this.showUploadProgress('photo', 0);
        
        const formData = new FormData();
        formData.append('photo', file);
        
        try {
            const response = await fetch(`/api/session/${this.sessionToken}/photo`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            this.uploadedFiles.photo = result;
            this.updatePreview();
            this.checkGenerateButton();
            
        } catch (error) {
            this.showError('Failed to upload photo');
        }
    }
    
    async handleAudioUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        this.showUploadProgress('audio', 0);
        
        const formData = new FormData();
        formData.append('audio', file);
        
        try {
            const response = await fetch(`/api/session/${this.sessionToken}/audio`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            this.uploadedFiles.audio = result;
            
            // Poll for waveform processing completion
            this.pollProcessingStatus();
            
        } catch (error) {
            this.showError('Failed to upload audio');
        }
    }
    
    async pollProcessingStatus() {
        const checkStatus = async () => {
            const response = await fetch(`/api/session/${this.sessionToken}/status`);
            const status = await response.json();
            
            if (status.waveform_ready) {
                this.updatePreview();
                this.checkGenerateButton();
            } else {
                setTimeout(checkStatus, 1000); // Check every second
            }
        };
        
        checkStatus();
    }
    
    async updatePreview() {
        // Update session data
        const formData = {
            custom_text: document.getElementById('custom-text').value,
            photo_shape: document.querySelector('input[name="photo-shape"]:checked').value,
            pdf_size: document.getElementById('pdf-size').value
        };
        
        await fetch(`/api/session/${this.sessionToken}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        // Generate new preview
        this.generatePreview();
    }
    
    async initiatePayment() {
        const email = prompt('Enter your email to receive the PDF:');
        if (!email) return;
        
        const tier = document.querySelector('input[name="tier"]:checked')?.value || 'standard';
        
        try {
            // Create payment intent
            const response = await fetch(`/api/session/${this.sessionToken}/payment`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, tier})
            });
            
            const {client_secret, amount} = await response.json();
            
            // Initialize Stripe checkout
            this.processStripePayment(client_secret, amount);
            
        } catch (error) {
            this.showError('Payment initialization failed');
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new AudioPosterApp();
});
```

## 7. Deployment & Infrastructure

### 7.1 Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

### 7.2 AWS S3 Configuration
```python
# app/config.py
import os
import boto3

class Config:
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    # AWS S3
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET = os.environ.get('S3_BUCKET', 'audio-poster-files')
    S3_REGION = os.environ.get('S3_REGION', 'us-east-1')
    
    # Stripe
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    
    # Email
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@audioposter.com')
    
    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY')
    BASE_URL = os.environ.get('BASE_URL', 'https://audioposter.com')

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.S3_REGION
)
```

### 7.3 Nginx Configuration
```nginx
# nginx.conf
upstream app {
    server web:8000;
}

server {
    listen 80;
    server_name audioposter.com www.audioposter.com;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle large file uploads
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 8. Security & Performance Considerations

### 8.1 Security Measures
- **File Upload Validation**: Strict MIME type checking, file size limits
- **CSRF Protection**: CSRF tokens for all forms
- **Rate Limiting**: Prevent abuse of upload endpoints
- **Secure Downloads**: Time-limited signed URLs
- **Data Encryption**: All uploaded files encrypted at rest
- **PCI Compliance**: Stripe handles all payment data

### 8.2 Performance Optimizations
- **Async Processing**: All heavy tasks (audio/PDF processing) in background
- **CDN Integration**: Static assets served via CloudFlare
- **Database Indexing**: Proper indexes on frequently queried fields
- **File Compression**: Optimize image and PDF file sizes
- **Caching**: Redis for session data and frequently accessed templates

## 9. Monitoring & Analytics

### 9.1 Application Monitoring
```python
# app/monitoring.py
import logging
from datetime import datetime
import newrelic.agent

# Custom metrics tracking
class Metrics:
    @staticmethod
    def track_upload(file_type, file_size, processing_time):
        newrelic.agent.record_custom_metric(
            f'Upload/{file_type}/Size', file_size
        )
        newrelic.agent.record_custom_metric(
            f'Upload/{file_type}/ProcessingTime', processing_time
        )
    
    @staticmethod
    def track_conversion(session_token, conversion_type):
        # Track conversion funnel
        newrelic.agent.record_custom_event('Conversion', {
            'session': session_token,
            'type': conversion_type,
            'timestamp': datetime.utcnow().isoformat()
        })
```

## 10. Development Workflow

### 10.1 Local Development Setup
```bash
# Setup script
#!/bin/bash

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb audio_poster_dev
python migrate.py

# Start Redis
redis-server &

# Start Celery worker
celery -A app.tasks worker &

# Start development server
python app.py
```

### 10.2 Testing Strategy
```python
# tests/test_audio_processing.py
import pytest
from app.services.audio_processor import AudioProcessor

class TestAudioProcessor:
    def test_mp3_processing(self):
        processor = AudioProcessor(mock_s3_client)
        result = processor.process_audio('test.mp3', 'session_123')
        
        assert result['duration'] > 0
        assert result['waveform_s3_key'].endswith('.png')
    
    def test_invalid_audio_format(self):
        processor = AudioProcessor(mock_s3_client)
        
        with pytest.raises(AudioProcessingError):
            processor.process_audio('invalid.txt', 'session_123')
```

This technical implementation plan provides a complete roadmap for building the MVP with all the features outlined in the PRD. The architecture is designed to handle the anonymous user flow while collecting emails for marketing, and can scale as the business grows.

Would you like me to dive deeper into any specific component or start with the actual code implementation?