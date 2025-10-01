# Admin Panel Setup Guide

## Overview

The voiceFrame application includes a comprehensive admin panel for managing fonts, backgrounds, and suggested text messages. This guide explains how to access and use the admin panel.

## Accessing the Admin Panel

### 1. Get the Admin API Key

The admin panel requires an API key for authentication. The API key is auto-generated on startup and can be found in the Docker logs:

```bash
docker-compose logs api | grep "admin API key"
```

**Current API Key:** `g_FuNtlAZ9_P3S3YcGinQi1FWTeN4BiyADDrgMm5R14`

⚠️ **Note:** The API key changes every time the API container restarts. For production, set a fixed API key using the `ADMIN_API_KEY` environment variable.

⚠️ **Note:** The API key changes every time the API container restarts. For production, set a fixed API key using the `ADMIN_API_KEY` environment variable.

### 2. Access the Admin Panel

1. Navigate to: `http://localhost:3000/admin`
2. Enter the admin API key when prompted
3. You'll be logged into the admin dashboard

## Admin Panel Features

### Dashboard Overview

The admin dashboard displays statistics for:
- **Fonts**: Total, active, and premium fonts
- **Backgrounds**: Total, active, and premium backgrounds
- **Suggested Texts**: Total, active, and premium text messages

### Managing Resources

#### Fonts Tab
- View all available fonts with file sizes and descriptions
- Upload new font files (.ttf, .otf, .woff, .woff2)
- Edit font metadata (display name, description, premium status)
- Delete fonts and their associated files

#### Backgrounds Tab
- View all background images with categories and file sizes
- Upload new background images (.jpg, .png, .webp)
- Edit background metadata (display name, description, category)
- Delete backgrounds and their associated files

#### Suggested Texts Tab
- View all suggested text messages organized by category
- Add new text messages with categories (romantic, birthday, anniversary, etc.)
- Edit existing messages and their premium status
- Delete unwanted text messages

### Current Data

The admin panel has been populated with your existing resources:

#### Fonts (5 total)
- **Script Handwriting** (script.ttf) - Script/handwriting style font
- **Modern Sans** (modern.ttf) - Open Sans for clean, modern sans-serif
- **Vintage Classic** (vintage.ttf) - Cinzel for classic serif with vintage feel
- **Elegant Display** (elegant.ttf) - Playfair Display for sophisticated designs
- **Classic Serif** (classic.ttf) - Lora font for elegant serif with excellent readability

#### Backgrounds (4 total)
- **Abstract Blurred** (237.jpg) - Abstract blurred background for modern designs
- **Roses on Wood** - Beautiful roses on white wooden background (romantic category)
- **Cute Hearts** - Copy space with cute hearts design (romantic category)
- **Flat Lay Hearts** - Flat lay design with small cute hearts (romantic category)

#### Suggested Texts (19 total)
- **Romantic messages** (7) - Love and relationship themed texts
- **Birthday messages** (3) - Birthday celebration texts
- **Anniversary messages** (3) - Anniversary celebration texts
- **Holiday messages** (3) - Christmas, New Year, Valentine's Day texts
- **General messages** (3) - Generic positive messages
- **Premium messages** (3) - Special romantic texts marked as premium

## API Endpoints

The admin panel uses these REST API endpoints:

### Authentication
All endpoints require the `Authorization: Bearer <api_key>` header.

### Statistics
- `GET /admin/stats` - Get dashboard statistics

### Fonts
- `GET /admin/fonts` - List all fonts
- `POST /admin/fonts` - Create new font entry
- `GET /admin/fonts/{id}` - Get specific font
- `PUT /admin/fonts/{id}` - Update font metadata
- `DELETE /admin/fonts/{id}` - Delete font
- `POST /admin/fonts/{id}/upload` - Upload font file

### Backgrounds
- `GET /admin/backgrounds` - List all backgrounds
- `POST /admin/backgrounds` - Create new background entry
- `GET /admin/backgrounds/{id}` - Get specific background
- `PUT /admin/backgrounds/{id}` - Update background metadata
- `DELETE /admin/backgrounds/{id}` - Delete background
- `POST /admin/backgrounds/{id}/upload` - Upload background image

### Suggested Texts
- `GET /admin/suggested-texts` - List all suggested texts
- `POST /admin/suggested-texts` - Create new text entry
- `GET /admin/suggested-texts/{id}` - Get specific text
- `PUT /admin/suggested-texts/{id}` - Update text
- `DELETE /admin/suggested-texts/{id}` - Delete text

## Troubleshooting

### Admin Panel Shows No Data

If the admin panel appears empty:

1. **Check if data exists in database:**
   ```bash
   docker-compose exec api python -c "
   from backend.database import SessionLocal
   from backend.models import AdminFont, AdminBackground, AdminSuggestedText
   db = SessionLocal()
   print(f'Fonts: {db.query(AdminFont).count()}')
   print(f'Backgrounds: {db.query(AdminBackground).count()}')
   print(f'Texts: {db.query(AdminSuggestedText).count()}')
   "
   ```

2. **Re-seed the data if needed:**
   ```bash
   # Copy the seeding script to container
   docker cp scripts/seed_admin_data.py voiceframe-api-1:/app/seed_admin_data.py

   # Run the seeding script
   docker-compose exec api python seed_admin_data.py
   ```

### API Key Issues

If you get "Invalid admin API key" errors:

1. **Get the current API key:**
   ```bash
   docker-compose logs api | grep "admin API key" | tail -1
   ```

2. **Set a fixed API key for production:**
   Add to your `.env` file:
   ```
   ADMIN_API_KEY=your-secure-api-key-here
   ```

### File Upload Issues

If file uploads fail:

1. **Check file permissions** - Ensure the API container can write to the upload directories
2. **Check file size** - Large files may timeout
3. **Check file format** - Only supported formats are accepted

## Security Notes

- The admin API key provides full access to manage all resources
- Keep the API key secure and don't commit it to version control
- In production, use a strong, randomly generated API key
- Consider implementing additional security measures like IP whitelisting

## Production Setup

For production deployment:

1. **Set a secure admin API key:**
   ```bash
   export ADMIN_API_KEY="your-secure-randomly-generated-key"
   ```

2. **Configure proper file storage:**
   - Use cloud storage (S3, etc.) for uploaded files
   - Implement proper backup strategies
   - Set up monitoring for admin activities

3. **Security hardening:**
   - Use HTTPS for admin panel access
   - Implement rate limiting on admin endpoints
   - Add audit logging for admin actions
   - Consider multi-factor authentication
