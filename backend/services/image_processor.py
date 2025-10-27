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
            shape: 'square', 'circle', or 'fullpage'
            size: Output dimensions
        """
        try:
            # All files are now in S3 (including temp files)
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
                # Fallback: Load from local storage for development
                local_path = os.path.join(self.file_uploader.local_storage_path, image_path)
                image = Image.open(local_path)

            # CRITICAL: Fix orientation based on EXIF data
            # This is essential because images from mobile devices often have EXIF orientation data
            # that needs to be applied to display correctly
            image = ImageOps.exif_transpose(image)
            print(f"DEBUG: Applied EXIF orientation fix to image, new size: {image.size}")

            print(f"DEBUG: create_shaped_image called with shape='{shape}', size={size}")
            if shape == 'circle':
                print(f"DEBUG: Using circular image processing")
                result = self._create_circular_image(image, size)
                print(f"DEBUG: Circular image processing returned: size={result.size}, mode={result.mode}")
                return result
            elif shape == 'fullpage':
                print(f"DEBUG: Using fullpage image processing")
                result = self._create_fullpage_image(image, size)
                print(f"DEBUG: Fullpage image processing returned: size={result.size}, mode={result.mode}")
                return result
            else:
                print(f"DEBUG: Using rectangle image processing (default)")
                # Default to rectangle (uses template dimensions)
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
        """Create circular masked image that fits within the template's rectangular area"""
        print(f"🔴 DEBUG: _create_circular_image ENTRY with size={size}")
        print(f"DEBUG: _create_circular_image called with size={size}")
        # For circular images, we need to fit a circle within the rectangular template area
        # Use the smaller dimension to ensure the circle fits
        width, height = size
        circle_diameter = min(width, height)
        print(f"DEBUG: Template size: {width}x{height}, circle diameter: {circle_diameter}")

        # Create square image with circle diameter
        square_size = (circle_diameter, circle_diameter)
        print(f"DEBUG: About to create square image with size={square_size}")
        square_image = self._create_square_image(image, square_size)
        print(f"DEBUG: Square image created: size={square_image.size}, mode={square_image.mode}")

        # Create circular mask
        mask = Image.new('L', square_size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, circle_diameter, circle_diameter), fill=255)
        print(f"DEBUG: Circular mask created: size={mask.size}")

        # Apply mask to create circular image
        print(f"DEBUG: About to apply mask to create circular image")
        output = Image.new('RGBA', square_size, (0, 0, 0, 0))
        print(f"DEBUG: Created RGBA output image: size={output.size}")
        output.paste(square_image, (0, 0))
        print(f"DEBUG: Pasted square image onto output")
        output.putalpha(mask)
        print(f"DEBUG: Applied alpha mask")
        print(f"DEBUG: Circular image created: size={output.size}, mode={output.mode}")

        # Check if the circular image has actual content
        try:
            bbox = output.getbbox()
            print(f"DEBUG: Circular image content bbox: {bbox}")
        except Exception as e:
            print(f"ERROR: Failed to get bbox: {e}")
            bbox = None

        # If the template area is rectangular, we need to center the circular image
        print(f"DEBUG: Checking if template is rectangular: width={width}, height={height}, width != height = {width != height}")
        try:
            if width != height:
                print(f"DEBUG: Template is rectangular, centering circle")
                # Create a new image with the template's rectangular dimensions
                final_output = Image.new('RGBA', size, (0, 0, 0, 0))
                # Calculate center position
                x_offset = (width - circle_diameter) // 2
                y_offset = (height - circle_diameter) // 2
                print(f"DEBUG: Center offset: x={x_offset}, y={y_offset}")
                # Paste the circular image centered in the rectangular area
                final_output.paste(output, (x_offset, y_offset), output)
                print(f"DEBUG: Final circular image: size={final_output.size}, mode={final_output.mode}")

                # Check if the final image has content
                final_bbox = final_output.getbbox()
                print(f"DEBUG: Final circular image content bbox: {final_bbox}")
                print(f"DEBUG: Returning centered circular image")
                return final_output

            print(f"DEBUG: Template is square, returning circular image directly")
            return output
        except Exception as e:
            print(f"ERROR in centering logic: {e}")
            import traceback
            traceback.print_exc()
            # Return the original circular image as fallback
            return output

    def _create_fullpage_image(self, image: Image.Image, size: tuple) -> Image.Image:
        """Create full page image that covers the entire template area"""
        print(f"DEBUG: _create_fullpage_image called with size={size}")

        # For full page, we want the image to cover the entire template area
        # This is similar to rectangle but optimized for full page coverage
        target_width, target_height = size

        # Calculate scaling factor to fill the entire area
        image_width, image_height = image.size
        scale_x = target_width / image_width
        scale_y = target_height / image_height

        # Use the larger scale to ensure the image fills the entire area
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

        print(f"DEBUG: Fullpage image created: size={cropped_image.size}, mode={cropped_image.mode}")
        return cropped_image

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
        """Download and return an image from S3 (all files now stored in S3)"""
        try:
            # All files are now in S3 (including temp files)
            if self.file_uploader.s3_client:
                # Download from S3
                response = self.file_uploader.s3_client.get_object(
                    Bucket=settings.s3_bucket,
                    Key=s3_key
                )
                image_data = response['Body'].read()
                return Image.open(BytesIO(image_data))
            else:
                # Fallback: Load from local storage for development
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
