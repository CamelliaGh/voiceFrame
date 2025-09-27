# Admin Dashboard

The Admin Dashboard provides a web interface for managing fonts, suggested texts, and background files used in the AudioPoster application.

## Features

### Font Management
- Upload font files (TTF, OTF, WOFF, WOFF2)
- Set display names and descriptions
- Mark fonts as premium or free
- Enable/disable fonts
- Track usage statistics

### Suggested Text Management
- Add suggested text templates
- Organize by categories (romantic, birthday, anniversary, etc.)
- Mark as premium or free
- Track usage count
- Enable/disable suggestions

### Background Management
- Upload background images (JPG, PNG, WebP)
- Set display names and descriptions
- Organize by categories (nature, abstract, patterns, etc.)
- Mark as premium or free
- Track usage statistics

## Access

The admin dashboard is available at `/admin` route and requires authentication using an admin API key.

### Authentication

1. **API Key Setup**: Set the `ADMIN_API_KEY` environment variable in your backend configuration
2. **Login**: Access `/admin` and enter your admin API key
3. **Session**: The API key is stored in browser localStorage for convenience

### Environment Configuration

Add to your `.env` file:
```env
ADMIN_API_KEY=your-secure-admin-api-key-here
```

## API Endpoints

### Admin Endpoints (Protected)
- `GET /api/admin/stats` - Get dashboard statistics
- `GET /api/admin/fonts` - List fonts with pagination
- `POST /api/admin/fonts` - Create new font entry
- `POST /api/admin/fonts/{id}/upload` - Upload font file
- `PUT /api/admin/fonts/{id}` - Update font
- `DELETE /api/admin/fonts/{id}` - Delete font
- Similar endpoints for `suggested-texts` and `backgrounds`

### Public Endpoints
- `GET /api/resources/fonts` - Get active fonts for frontend
- `GET /api/resources/suggested-texts` - Get suggested texts
- `GET /api/resources/backgrounds` - Get backgrounds
- `GET /api/resources/categories` - Get resource categories

## Database Schema

### AdminFont
- `id` (UUID) - Primary key
- `name` (String) - Unique font identifier
- `display_name` (String) - User-friendly name
- `file_path` (String) - Path to font file
- `file_size` (Integer) - File size in bytes
- `is_active` (Boolean) - Whether font is available
- `is_premium` (Boolean) - Whether font requires premium
- `description` (Text) - Font description
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp

### AdminSuggestedText
- `id` (UUID) - Primary key
- `text` (Text) - The suggested text content
- `category` (String) - Text category
- `is_active` (Boolean) - Whether text is available
- `is_premium` (Boolean) - Whether text requires premium
- `usage_count` (Integer) - How many times used
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp

### AdminBackground
- `id` (UUID) - Primary key
- `name` (String) - Unique background identifier
- `display_name` (String) - User-friendly name
- `file_path` (String) - Path to background image
- `file_size` (Integer) - File size in bytes
- `is_active` (Boolean) - Whether background is available
- `is_premium` (Boolean) - Whether background requires premium
- `description` (Text) - Background description
- `category` (String) - Background category
- `usage_count` (Integer) - How many times used
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp

## File Storage

### Font Files
- Stored in `fonts/admin/` directory
- Filename format: `{font_name}_{uuid}.{extension}`
- Supported formats: TTF, OTF, WOFF, WOFF2

### Background Images
- Stored in `backgrounds/admin/` directory
- Filename format: `{background_name}_{uuid}.{extension}`
- Supported formats: JPG, PNG, WebP

## Integration with PDF Generation

The admin-managed resources are integrated with the existing PDF generation system through the `AdminResourceService`:

1. **Font Integration**: Admin fonts are available for use in PDF generation
2. **Background Integration**: Admin backgrounds can be used as template backgrounds
3. **Suggested Text Integration**: Admin suggested texts are available in the frontend

## Security

- All admin endpoints require valid API key authentication
- API keys are validated on every request
- File uploads are validated for type and size
- Admin actions are logged for audit purposes

## Usage Statistics

The system tracks usage statistics for:
- How many times suggested texts are used
- How many times backgrounds are used
- Font usage (through PDF generation)

## Development

### Adding New Resource Types

1. Create database model in `backend/models.py`
2. Add Pydantic schemas in `backend/schemas.py`
3. Create API endpoints in `backend/routers/admin.py`
4. Update `AdminResourceService` in `backend/services/admin_resource_service.py`
5. Add frontend components in `src/components/AdminDashboard.tsx`

### Testing

The admin dashboard can be tested by:
1. Setting up the environment with `ADMIN_API_KEY`
2. Starting the backend server
3. Accessing `/admin` in the browser
4. Using the API key to authenticate
5. Testing CRUD operations for each resource type

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Check that `ADMIN_API_KEY` is set correctly
2. **File Upload Failed**: Verify file type and size limits
3. **Database Errors**: Ensure database migrations are run
4. **Permission Errors**: Check file system permissions for upload directories

### Logs

Admin actions are logged in the application logs. Check the backend logs for detailed error information.
