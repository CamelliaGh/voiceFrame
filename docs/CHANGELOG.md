# AudioPoster Project - Change Log

## Overview
This document tracks all major decisions, changes, and technical implementations made during the development of the AudioPoster project. It serves as a comprehensive reference for future development and troubleshooting.

## Project Summary
AudioPoster is a web application that allows users to create beautiful audio memory posters by combining photos, audio files, and custom text. The system generates PDFs with embedded QR codes for audio playback and offers multiple design templates.

## Architecture Decisions

### Technology Stack
- **Backend**: FastAPI (Python) with async support
- **Frontend**: React 18 + TypeScript + Vite
- **Database**: PostgreSQL with Alembic migrations
- **Cache/Queue**: Redis + Celery for background tasks
- **File Storage**: AWS S3 (with local fallback)
- **Payment**: Stripe integration
- **Containerization**: Docker + Docker Compose
- **Styling**: Tailwind CSS with custom purple theme

### Key Design Principles
1. **Permanent Audio Storage**: Audio files linked via QR codes must remain accessible indefinitely
2. **Template-Based Design**: Support for both code-generated and visual templates (Canva/Figma)
3. **Fixed Pricing Model**: Single price point for all users and templates
4. **Secure File Access**: Permanent URLs for paid content, temporary for previews

## Major Changes & Implementations

### 1. Initial Project Setup & Docker Configuration
**Date**: Initial implementation
**Files Modified**: `docker-compose.yml`, `Dockerfile`, `requirements.txt`

**Changes Made**:
- Configured PostgreSQL, Redis, FastAPI, and Celery services
- Set up volume mounts for file storage
- Added environment variable configuration
- Fixed Alembic configuration issues (escaped % characters)

**Key Decisions**:
- Use `python3` command instead of `python` for Python scripts
- Mount local file storage at `/tmp/audioposter`
- Configure Celery worker to process all queues (audio, pdf, email)

### 2. Frontend UI & Theme Implementation
**Date**: Initial implementation
**Files Modified**: `src/components/Header.tsx`, `tailwind.config.js`

**Changes Made**:
- Implemented purple-based color theme (avoiding blue for primary components)
- Updated header with AudioLines icon from lucide-react
- Configured Tailwind CSS with custom purple palette

**Key Decisions**:
- Purple as primary brand color (avoid blue for primary components)
- Modern, clean UI design with lucide-react icons
- Responsive design using Tailwind CSS utilities

### 3. Audio Processing & Waveform Generation
**Date**: Initial implementation
**Files Modified**: `backend/services/audio_processor.py`, `backend/main.py`

**Changes Made**:
- Implemented audio file processing with librosa
- Added waveform generation and visualization
- Integrated Celery background tasks for audio processing
- Added task routing to specific queues (audio, pdf, email)

**Key Decisions**:
- Use librosa for audio analysis and waveform generation
- Process audio files asynchronously via Celery
- Store waveforms as PNG images for PDF integration

### 4. PDF Generation System
**Date**: Initial implementation
**Files Modified**: `backend/services/pdf_generator.py`, `backend/services/visual_pdf_generator.py`

**Changes Made**:
- Implemented code-based PDF generation using ReportLab
- Added support for multiple page sizes (A4, Letter, Square)
- Integrated photo, text, waveform, and QR code placement
- Created visual template system for external design tools

**Key Decisions**:
- Support both code-generated and visual templates
- Use ReportLab for programmatic PDF generation
- Implement placeholder system for dynamic content insertion

### 5. Visual Template System Implementation
**Date**: Recent implementation
**Files Modified**: `backend/services/visual_template_service.py`, `templates/modern/`

**Changes Made**:
- Created visual template service for external design integration
- Implemented template configuration via JSON files
- Added support for Canva/Figma-designed templates
- Created modern template with placeholder coordinates

**Key Decisions**:
- Use PNG images as template backgrounds
- Define placeholder coordinates in JSON configuration
- Support dynamic content overlay on visual templates
- Enable designers to create templates outside of code

### 6. Permanent Audio Storage System
**Date**: Critical implementation
**Files Modified**: `backend/services/permanent_audio_service.py`, `backend/main.py`

**Changes Made**:
- Implemented permanent audio storage service
- Added secure hash generation for audio files
- Created permanent audio access endpoints
- Integrated with order completion workflow

**Key Decisions**:
- Audio files must remain accessible indefinitely (critical for printed posters)
- Use secure hashes for permanent audio identification
- Implement both HTML player and direct file access
- Support both paid orders and preview sessions

### 7. Payment System & Stripe Integration
**Date**: Recent implementation
**Files Modified**: `backend/services/stripe_service.py`, `backend/main.py`

**Changes Made**:
- Integrated Stripe payment processing
- Implemented payment intent creation
- Added order completion workflow
- Connected payment to permanent audio storage

**Key Decisions**:
- Use Stripe for secure payment processing
- Implement single fixed price model ($2.99)
- Connect payment completion to permanent storage migration
- Generate secure access tokens for paid content

### 8. Premium Tier Removal & Pricing Simplification
**Date**: Most recent implementation
**Files Modified**: `src/components/PricingSection.tsx`, `backend/schemas.py`, `backend/services/stripe_service.py`

**Changes Made**:
- Removed premium tier concept entirely
- Simplified pricing to single fixed price ($2.99)
- Made all templates available to all users
- Updated frontend to reflect simplified pricing

**Key Decisions**:
- Single pricing tier for all users
- All templates available without restrictions
- Simplified user experience and decision-making
- Fixed price point for predictable revenue

### 9. File Storage & S3 Integration
**Date**: Ongoing implementation
**Files Modified**: `docker-compose.yml`, `backend/services/storage_service.py`

**Changes Made**:
- Configured AWS S3 integration
- Added local file storage fallback
- Implemented file upload and retrieval
- Added S3 lifecycle policies for cost optimization

**Key Decisions**:
- Use S3 for production file storage
- Implement local storage for development
- Use presigned URLs for secure temporary access
- Consider CloudFront for permanent public access

### 10. S3 Public Access Configuration for Preview Files
**Date**: Recent fix for 403 errors
**Files Modified**: `backend/services/file_uploader.py`, `backend/services/pdf_generator.py`, `backend/services/visual_pdf_generator.py`, `backend/services/audio_processor.py`, `backend/services/image_processor.py`

**Changes Made**:
- Added `ACL: public-read` for preview files (PDFs, photos, waveforms)
- Updated all file upload services to use public ACL for preview content
- Created comprehensive S3 bucket setup guide
- Added graceful ACL error handling and fallback to bucket policies

**Key Decisions**:
- Preview files must be publicly accessible for frontend display
- Use ACL-based access control for security when available
- Fallback to bucket policies when ACLs are not supported
- Maintain private access for final paid content
- Document S3 configuration requirements thoroughly

## Technical Implementation Details

### Database Schema
- **Sessions**: Store user uploads and processing state
- **Orders**: Track completed payments and permanent storage
- **Audio Files**: Store file metadata and S3 keys
- **Templates**: Store template configurations and metadata

### API Endpoints
- `/api/upload/photo`: Photo upload endpoint
- `/api/upload/audio`: Audio upload endpoint
- `/api/session/{token}/preview`: Generate preview PDF
- `/api/orders/create-payment-intent`: Create Stripe payment
- `/api/orders/{order_id}/complete`: Complete order and migrate to permanent storage
- `/listen/{identifier}`: Permanent audio playback
- `/api/templates`: Get available templates

### Background Tasks
- **Audio Processing**: Waveform generation and analysis
- **PDF Generation**: Create preview and final PDFs
- **File Migration**: Move files to permanent storage after payment

### Security Considerations
- **File Access**: Temporary URLs for previews, permanent for paid content
- **Audio Security**: Secure hashes for permanent audio identification
- **Payment Security**: Stripe integration with proper webhook handling
- **Template Security**: Validate template configurations and file paths

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://host:port

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=your_bucket_name
S3_REGION=us-east-2

# Stripe
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret

# Application
DEBUG=true
SECRET_KEY=your_secret_key
```

### Docker Services
- **api**: FastAPI backend service
- **db**: PostgreSQL database
- **redis**: Redis cache and message broker
- **celery-worker**: Background task processor

## Known Issues & Solutions

### 1. Celery Worker Queue Configuration
**Issue**: Worker not processing audio/PDF tasks
**Solution**: Ensure worker processes all queues or disable task routing for development

### 2. Alembic Configuration
**Issue**: Interpolation syntax errors with % characters
**Solution**: Escape % characters as %% in alembic.ini

### 3. File Storage Permissions
**Issue**: S3 access denied errors
**Solution**: Verify IAM policies and bucket permissions

### 4. PDF Preview Generation
**Issue**: 400 Bad Request errors
**Solution**: Ensure proper file paths and template loading

### 5. S3 403 Forbidden Errors (Preview Files)
**Issue**: Preview PDFs return 403 Forbidden when accessed directly from S3
**Solution**: 
- Upload preview files with `ACL: public-read`
- Disable S3 bucket block public access settings
- Apply bucket policy allowing public read for objects with public-read ACL
- See `docs/S3_BUCKET_SETUP.md` for complete configuration

### 6. S3 AccessControlListNotSupported Errors
**Issue**: File uploads fail with "The bucket does not allow ACLs" error
**Solution**:
- Change S3 bucket Object Ownership to "Bucket owner preferred"
- Enable ACLs in bucket settings
- Updated code to gracefully handle ACL errors and retry without ACLs
- See `docs/S3_BUCKET_SETUP.md` for detailed ACL configuration

### 7. Visual Template Preview Generation Issues
**Issue**: Preview PDFs showing placeholder text instead of actual content
**Solution**:
- Fixed template configuration coordinates to match actual template size (2000x1428)
- Added missing `get_image_from_s3` method to ImageProcessor
- Removed premium settings from template configuration
- Updated placeholder coordinates for proper content positioning
- Fixed waveform loading from S3 storage

### 8. File Storage Strategy Implementation
**Issue**: Files were being stored permanently in S3 before payment, causing unnecessary costs
**Solution**:
- Implemented temporary storage system for preview generation
- Created `StorageManager` service to handle temporary vs permanent storage
- Updated photo and audio upload endpoints to use temporary storage
- Modified order completion to migrate files to permanent storage only after payment
- Updated audio and image processors to work with temporary files
- Ensured QR codes point to permanent audio URLs for paid users

## Future Development Considerations

### 1. Template System Enhancements
- Support for more design tools (Figma, Adobe)
- Template marketplace for designers
- Dynamic template customization options

### 2. Audio Processing Improvements
- Support for more audio formats
- Advanced audio analysis features
- Custom waveform styles

### 3. Storage Optimization
- Implement CDN for global access
- Add file compression and optimization
- Implement intelligent caching strategies

### 4. User Experience
- Add template previews
- Implement drag-and-drop interface
- Add social sharing features

## Testing & Quality Assurance

### Manual Testing Checklist
- [ ] Photo upload and processing
- [ ] Audio upload and waveform generation
- [ ] Template selection and customization
- [ ] PDF preview generation
- [ ] Payment processing
- [ ] Order completion
- [ ] Permanent audio access
- [ ] Template system functionality

### Automated Testing
- Unit tests for core services
- Integration tests for API endpoints
- End-to-end testing for complete workflows

## Deployment & Production

### Production Considerations
- Use proper SSL certificates
- Implement rate limiting
- Add monitoring and logging
- Set up backup strategies
- Configure proper S3 lifecycle policies

### Scaling Considerations
- Horizontal scaling for API services
- Database connection pooling
- Redis clustering for high availability
- CDN integration for global performance

---

## Notes for Future Development

This change log serves as the authoritative source for understanding the current state of the AudioPoster project. When making changes or troubleshooting issues:

1. **Always reference this document** for context and decisions
2. **Update this document** when making significant changes
3. **Follow established patterns** for consistency
4. **Consider the permanent audio storage requirement** for all changes
5. **Maintain the simplified pricing model** unless explicitly requested to change

The project is designed to be maintainable and extensible, with clear separation of concerns and well-documented decision points.
