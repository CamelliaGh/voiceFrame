from PIL import Image, ImageDraw, ImageOps, ImageEnhance
from io import BytesIO
import tempfile
import os
from fastapi import UploadFile, HTTPException

from ..config import settings
from .file_uploader import FileUploader

class ImageProcessor:
    """Processes and optimizes images for poster generation"""
    
    def __init__(self):
        self.file_uploader = FileUploader()
    
    async def process_photo(self, photo: UploadFile, session_token: str) -> str:
        """
        Process uploaded photo: validate, resize, optimize, and store
        Returns the S3 key for the processed image
        """
        try:
            # Validate file size
            if photo.size > settings.max_photo_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Photo too large (max {settings.max_photo_size // (1024*1024)}MB)"
                )
            
            # Read and process image
            image_content = await photo.read()
            image = Image.open(BytesIO(image_content))
            
            # Process the image
            processed_image = self._process_image(image)
            
            # Save to temporary file for upload
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            processed_image.save(temp_file.name, 'JPEG', quality=95, optimize=True)
            temp_file.close()
            
            try:
                # Upload processed image
                photo_key = f"photos/{session_token}.jpg"
                
                if self.file_uploader.s3_client:
                    # Upload to S3
                    with open(temp_file.name, 'rb') as f:
                        # Photos should be publicly readable for preview PDFs
                        extra_args = {
                            'ContentType': 'image/jpeg',
                            'ServerSideEncryption': 'AES256'
                        }
                        
                        # Try to make photos publicly readable
                        try:
                            extra_args['ACL'] = 'public-read'
                        except Exception:
                            # If ACL is not supported, we'll rely on bucket policy
                            pass
                        
                        try:
                            self.file_uploader.s3_client.upload_fileobj(
                                f,
                                settings.s3_bucket,
                                photo_key,
                                ExtraArgs=extra_args
                            )
                        except Exception as e:
                            if 'AccessControlListNotSupported' in str(e):
                                # Retry without ACL if bucket doesn't support it
                                extra_args.pop('ACL', None)  # Remove ACL if present
                                self.file_uploader.s3_client.upload_fileobj(
                                    f,
                                    settings.s3_bucket,
                                    photo_key,
                                    ExtraArgs=extra_args
                                )
                            else:
                                raise e
                else:
                    # Store locally
                    local_path = os.path.join(self.file_uploader.local_storage_path, photo_key)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    
                    import shutil
                    shutil.copy2(temp_file.name, local_path)
                
                return photo_key
                
            finally:
                # Cleanup temporary file
                os.unlink(temp_file.name)
                
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
    
    def _process_image(self, image: Image.Image) -> Image.Image:
        """Apply image processing pipeline"""
        try:
            # Fix orientation based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'LA'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to standard dimensions while maintaining aspect ratio
            max_size = (1200, 1200)  # High quality for PDF generation
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Enhance image quality
            image = self._enhance_image(image)
            
            return image
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image processing error: {str(e)}")
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Apply subtle image enhancements"""
        try:
            # Slight contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            # Slight color saturation enhancement
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.05)
            
            # Slight sharpness enhancement
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            return image
            
        except Exception:
            # Return original image if enhancement fails
            return image
    
    def create_shaped_image(self, image_path: str, shape: str = 'square', size: tuple = (400, 400)) -> Image.Image:
        """
        Create shaped version of image for PDF generation
        
        Args:
            image_path: Path to source image (can be S3 key or temporary file key)
            shape: 'square' or 'circle'
            size: Output dimensions
        """
        try:
            # Check if this is a temporary file
            if image_path.startswith('temp_'):
                # This is a temporary file, get the local path
                from .storage_manager import StorageManager
                storage_manager = StorageManager()
                temp_path = storage_manager.get_temp_file_path(image_path)
                if temp_path and os.path.exists(temp_path):
                    image = Image.open(temp_path)
                else:
                    raise HTTPException(status_code=404, detail="Temporary image file not found")
            elif self.file_uploader.s3_client:
                # Download from S3
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                self.file_uploader.s3_client.download_fileobj(
                    settings.s3_bucket,
                    image_path,
                    temp_file
                )
                temp_file.close()
                image = Image.open(temp_file.name)
                os.unlink(temp_file.name)
            else:
                # Load from local storage
                local_path = os.path.join(self.file_uploader.local_storage_path, image_path)
                image = Image.open(local_path)
            
            if shape == 'square':
                return self._create_square_image(image, size)
            elif shape == 'circle':
                return self._create_circular_image(image, size)
            elif shape == 'rectangle':
                return self._create_rectangle_image(image, size)
            else:
                return self._create_rectangle_image(image, size)
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Shape creation failed: {str(e)}")
    
    def _create_square_image(self, image: Image.Image, size: tuple) -> Image.Image:
        """Create square cropped image"""
        # Make square crop maintaining aspect ratio
        width, height = image.size
        min_dimension = min(width, height)
        
        left = (width - min_dimension) // 2
        top = (height - min_dimension) // 2
        right = left + min_dimension
        bottom = top + min_dimension
        
        square_image = image.crop((left, top, right, bottom))
        
        # Resize to target size
        square_image = square_image.resize(size, Image.Resampling.LANCZOS)
        
        return square_image
    
    def _create_rectangle_image(self, image: Image.Image, size: tuple) -> Image.Image:
        """Create rectangular image that fills the entire placeholder"""
        # Resize image to fill the entire rectangle, maintaining aspect ratio
        # This will crop the image if necessary to fit the exact dimensions
        target_width, target_height = size
        
        # Calculate scaling factor to fill the rectangle
        image_width, image_height = image.size
        scale_x = target_width / image_width
        scale_y = target_height / image_height
        
        # Use the larger scale to ensure the image fills the entire rectangle
        scale = max(scale_x, scale_y)
        
        # Resize the image
        new_width = int(image_width * scale)
        new_height = int(image_height * scale)
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to exact target size from center
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        cropped_image = resized_image.crop((left, top, right, bottom))
        
        return cropped_image
    
    def _create_circular_image(self, image: Image.Image, size: tuple) -> Image.Image:
        """Create circular masked image"""
        # First create square version
        square_image = self._create_square_image(image, size)
        
        # Create circular mask
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)
        
        # Apply mask to create circular image
        output = Image.new('RGBA', size, (0, 0, 0, 0))
        output.paste(square_image, (0, 0))
        output.putalpha(mask)
        
        return output
    
    def create_thumbnail(self, image_path: str, size: tuple = (200, 200)) -> BytesIO:
        """Create thumbnail for preview purposes"""
        try:
            if self.file_uploader.s3_client:
                # Download from S3
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                self.file_uploader.s3_client.download_fileobj(
                    settings.s3_bucket,
                    image_path,
                    temp_file
                )
                temp_file.close()
                image = Image.open(temp_file.name)
                os.unlink(temp_file.name)
            else:
                # Load from local storage
                local_path = os.path.join(self.file_uploader.local_storage_path, image_path)
                image = Image.open(local_path)
            
            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save to buffer
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Thumbnail creation failed: {str(e)}")
    
    def get_image_from_s3(self, s3_key: str) -> Image.Image:
        """Download and return an image from S3 or temporary storage"""
        try:
            # Check if this is a temporary file
            if s3_key.startswith('temp_'):
                # This is a temporary file, get the local path
                from .storage_manager import StorageManager
                storage_manager = StorageManager()
                temp_path = storage_manager.get_temp_file_path(s3_key)
                if temp_path and os.path.exists(temp_path):
                    return Image.open(temp_path)
                else:
                    raise HTTPException(status_code=404, detail="Temporary image file not found")
            
            # Handle permanent S3 files
            if self.file_uploader.s3_client:
                # Download from S3
                response = self.file_uploader.s3_client.get_object(
                    Bucket=settings.s3_bucket,
                    Key=s3_key
                )
                image_data = response['Body'].read()
                return Image.open(BytesIO(image_data))
            else:
                # Load from local storage
                local_path = os.path.join(self.file_uploader.local_storage_path, s3_key)
                return Image.open(local_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load image from S3: {str(e)}")
    
    def validate_image_file(self, file: UploadFile) -> bool:
        """Validate that uploaded file is a valid image"""
        try:
            # Check content type
            if not file.content_type.startswith('image/'):
                return False
            
            # Try to open the image
            content = file.file.read()
            file.file.seek(0)  # Reset file pointer
            
            image = Image.open(BytesIO(content))
            image.verify()  # Verify it's a valid image
            
            return True
            
        except Exception:
            return False
