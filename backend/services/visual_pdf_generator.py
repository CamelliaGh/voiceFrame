from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO
import tempfile
import os
from typing import Optional, Tuple, Dict
from pathlib import Path

from ..config import settings
from ..models import SessionModel, Order
from .visual_template_service import VisualTemplateService
from .file_uploader import FileUploader
from .image_processor import ImageProcessor

class VisualPDFGenerator:
    """Generates PDFs using visual templates designed in Canva/Figma"""
    
    def __init__(self):
        self.template_service = VisualTemplateService()
        self.file_uploader = FileUploader()
        self.image_processor = ImageProcessor()
    
    async def generate_pdf(self, session: SessionModel, add_watermark: bool = True, 
                          order: Optional[Order] = None) -> str:
        """Generate PDF using visual template"""
        try:
            # Get template configuration
            template = self.template_service.get_template(session.template_id)
            if not template:
                raise ValueError(f"Template {session.template_id} not found")
            
            print(f"Template configuration: {template}")
            
            # Load template image
            template_path = self.template_service.get_template_path(session.template_id)
            if not template_path:
                raise ValueError(f"Template file not found for {session.template_id}")
            
            print(f"Loading template from: {template_path}")
            
            # Create base image from template
            base_image = Image.open(template_path)
            print(f"Template loaded: {base_image.size}")
            
            # Apply background if specified
            if session.background_id and session.background_id != 'none':
                base_image = self._apply_background(base_image, session.background_id)
                print(f"Background applied: {session.background_id}")
            
            # Add photo
            if session.photo_s3_key:
                await self._add_photo_to_template(base_image, session, template)
            
            # Add waveform
            if session.waveform_s3_key:
                await self._add_waveform_to_template(base_image, session, template)
            
            # Add QR code
            qr_url = self._generate_qr_url(session, order)
            await self._add_qr_to_template(base_image, qr_url, template)
            
            # Add text
            if session.custom_text:
                await self._add_text_to_template(base_image, session.custom_text, template)
            
            # Add watermark if needed
            if add_watermark:
                self._add_watermark_to_image(base_image)
            
            # Convert to PDF
            pdf_path = await self._convert_image_to_pdf(base_image, template)
            
            # Upload to storage
            pdf_key = f"pdfs/{'preview' if add_watermark else order.id if order else 'final'}.pdf"
            
            if self.file_uploader.s3_client:
                with open(pdf_path, 'rb') as f:
                    # Determine if this should be public (preview PDFs)
                    is_public = 'preview' in pdf_key.lower()
                    
                    extra_args = {
                        'ContentType': 'application/pdf',
                        'ServerSideEncryption': 'AES256'
                    }
                    
                    # Try to make preview PDFs publicly readable
                    if is_public:
                        try:
                            extra_args['ACL'] = 'public-read'
                        except Exception:
                            # If ACL is not supported, we'll rely on bucket policy
                            pass
                    
                    try:
                        self.file_uploader.s3_client.upload_fileobj(
                            f, settings.s3_bucket, pdf_key, ExtraArgs=extra_args
                        )
                    except Exception as e:
                        if 'AccessControlListNotSupported' in str(e):
                            # Retry without ACL if bucket doesn't support it
                            extra_args.pop('ACL', None)  # Remove ACL if present
                            self.file_uploader.s3_client.upload_fileobj(
                                f, settings.s3_bucket, pdf_key, ExtraArgs=extra_args
                            )
                        else:
                            raise e
                pdf_url = f"https://{settings.s3_bucket}.s3.amazonaws.com/{pdf_key}"
            else:
                # Local storage
                local_path = f"/tmp/audioposter/{pdf_key}"
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                os.rename(pdf_path, local_path)
                pdf_url = f"/static/{pdf_key}"
            
            # Cleanup
            os.unlink(pdf_path)
            
            return pdf_url
            
        except Exception as e:
            print(f"Error generating visual PDF: {e}")
            raise
    
    async def _add_photo_to_template(self, base_image: Image.Image, session: SessionModel, template: Dict):
        """Add photo to template at specified coordinates"""
        placeholder = template['placeholders']['photo']
        
        try:
            # Get processed photo
            photo_size = (placeholder['width'], placeholder['height'])
            photo = self.image_processor.create_shaped_image(
                session.photo_s3_key,
                'rectangle',  # Always use rectangle for framed templates
                photo_size
            )
            
            # Paste photo onto template
            base_image.paste(photo, (placeholder['x'], placeholder['y']))
            print(f"Photo added at ({placeholder['x']}, {placeholder['y']}) with size {photo_size}")
            
        except Exception as e:
            print(f"Error adding photo: {e}")
    
    async def _add_waveform_to_template(self, base_image: Image.Image, session: SessionModel, template: Dict):
        """Add waveform to template at specified coordinates"""
        placeholder = template['placeholders']['waveform']
        
        try:
            # Get waveform image
            waveform = self.image_processor.get_image_from_s3(session.waveform_s3_key)
            waveform = waveform.resize((placeholder['width'], placeholder['height']))
            
            # Handle waveform with transparency
            if waveform.mode == 'RGBA':
                # If waveform has alpha channel, use it for transparency
                base_image.paste(waveform, (placeholder['x'], placeholder['y']), waveform)
            else:
                # Convert to RGBA and make white pixels transparent
                waveform = waveform.convert('RGBA')
                data = waveform.getdata()
                new_data = []
                for item in data:
                    # Change all white pixels to transparent
                    if item[0] > 250 and item[1] > 250 and item[2] > 250:
                        new_data.append((255, 255, 255, 0))  # Transparent
                    else:
                        new_data.append((item[0], item[1], item[2], 255))  # Keep original
                
                waveform.putdata(new_data)
                base_image.paste(waveform, (placeholder['x'], placeholder['y']), waveform)
            print(f"Waveform added at ({placeholder['x']}, {placeholder['y']}) with size ({placeholder['width']}, {placeholder['height']}) in black with matching background")
            
        except Exception as e:
            print(f"Error adding waveform: {e}")
    
    async def _add_qr_to_template(self, base_image: Image.Image, qr_url: str, template: Dict):
        """Add QR code to template at specified coordinates"""
        placeholder = template['placeholders']['qr_code']
        
        try:
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            # Create QR code with white background first
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_image = qr_image.resize((placeholder['width'], placeholder['height']))
            
            # Convert to RGBA and make white pixels transparent
            qr_image = qr_image.convert('RGBA')
            
            # Create transparent version
            data = qr_image.getdata()
            new_data = []
            for item in data:
                # Change all white (255, 255, 255) pixels to transparent
                if item[0] > 250 and item[1] > 250 and item[2] > 250:
                    new_data.append((255, 255, 255, 0))  # Make white pixels transparent
                else:
                    new_data.append((item[0], item[1], item[2], 255))  # Keep black pixels opaque
            
            qr_image.putdata(new_data)
            
            # Paste QR code with transparency mask
            base_image.paste(qr_image, (placeholder['x'], placeholder['y']), qr_image)
            print(f"QR code added at ({placeholder['x']}, {placeholder['y']}) with size ({placeholder['width']}, {placeholder['height']}) and matching background")
            
        except Exception as e:
            print(f"Error adding QR code: {e}")
    
    async def _add_text_to_template(self, base_image: Image.Image, text: str, template: Dict):
        """Add text to template at specified coordinates"""
        placeholder = template['placeholders']['text']
        
        try:
            # Create drawing context
            draw = ImageDraw.Draw(base_image)
            
            # Try to load custom font with fallback options
            font = None
            font_name = placeholder.get('font', 'Arial')
            font_size = placeholder.get('font_size', 32)
            
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent
            
            # Map font names to system fonts or font files
            font_mapping = {
                'script': project_root / 'fonts' / 'script.ttf',  # Handwritten/script style
                'elegant': project_root / 'fonts' / 'elegant.ttf',  # Elegant serif
                'modern': project_root / 'fonts' / 'modern.ttf',  # Modern sans-serif
                'Arial': 'Arial',
                'Helvetica': 'Helvetica',
                'Times': 'Times New Roman',
                'Courier': 'Courier New'
            }
            
            font_path = font_mapping.get(font_name, font_name)
            
            try:
                if isinstance(font_path, Path) and font_path.exists():
                    # Try to load from fonts directory
                    print(f"Loading font from: {font_path}")
                    font = ImageFont.truetype(str(font_path), font_size)
                    print(f"Successfully loaded font: {font_name} at size {font_size}")
                elif isinstance(font_path, str) and font_path.endswith('.ttf'):
                    # Try to load from fonts directory with string path
                    full_path = project_root / 'fonts' / font_path
                    if full_path.exists():
                        print(f"Loading font from: {full_path}")
                        font = ImageFont.truetype(str(full_path), font_size)
                        print(f"Successfully loaded font: {font_name} at size {font_size}")
                else:
                    # Try system font
                    print(f"Loading system font: {font_path}")
                    font = ImageFont.truetype(font_path, font_size)
                    print(f"Successfully loaded system font: {font_name} at size {font_size}")
            except Exception as e:
                print(f"Failed to load font {font_name}: {e}")
                # Try alternative script fonts
                if font_name == 'script':
                    try:
                        # Try some common script fonts on macOS
                        script_fonts = [
                            'Bradley Hand',
                            'Brush Script MT',
                            'Chalkduster',
                            'Marker Felt',
                            'Papyrus'
                        ]
                        for alt_font in script_fonts:
                            try:
                                font = ImageFont.truetype(alt_font, font_size)
                                print(f"Successfully loaded alternative script font: {alt_font}")
                                break
                            except:
                                continue
                        else:
                            # If no script font works, use a serif font
                            font = ImageFont.truetype('Times New Roman', font_size)
                            print(f"Using Times New Roman as script fallback")
                    except:
                        # Last resort - use default font
                        font = ImageFont.load_default()
                        print(f"Using default font as last resort")
                else:
                    try:
                        # Fallback to default font with size
                        font = ImageFont.load_default()
                        print(f"Using default font as fallback")
                    except:
                        # Last resort - use default
                        font = ImageFont.load_default()
                        print(f"Using default font as last resort")
            
            # Calculate text position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if placeholder.get('alignment', 'center') == 'center':
                x = placeholder['x'] + (placeholder['width'] - text_width) // 2
            else:
                x = placeholder['x']
            
            y = placeholder['y'] + (placeholder['height'] - text_height) // 2
            
            # Draw text
            draw.text((x, y), text, font=font, fill=placeholder.get('color', '#000000'))
            print(f"Text added at ({x}, {y}): {text} with font {font_name} size {font_size}")
            
        except Exception as e:
            print(f"Error adding text: {e}")
    
    def _add_watermark_to_image(self, image: Image.Image):
        """Add diagonal watermark to image"""
        try:
            # Create a rotated watermark image
            watermark_img = Image.new('RGBA', image.size, (0, 0, 0, 0))
            watermark_draw = ImageDraw.Draw(watermark_img)
            
            # Watermark text
            text = "PRELIMINARY"
            try:
                # Scale font size based on image dimensions
                font_size = min(image.width, image.height) // 10
                font = ImageFont.truetype("Arial", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text dimensions
            bbox = watermark_draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position text in center
            x = (image.width - text_width) // 2
            y = (image.height - text_height) // 2
            
            # Draw watermark text with light gray color
            watermark_draw.text((x, y), text, font=font, fill=(200, 200, 200, 180))
            
            # Rotate the watermark image 45 degrees
            rotated_watermark = watermark_img.rotate(45, expand=False, fillcolor=(0, 0, 0, 0))
            
            # Paste the rotated watermark onto the original image
            image.paste(rotated_watermark, (0, 0), rotated_watermark)
            print("Diagonal watermark added")
            
        except Exception as e:
            print(f"Error adding watermark: {e}")
    
    async def _convert_image_to_pdf(self, image: Image.Image, template: Dict) -> str:
        """Convert image to PDF"""
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Handle different page sizes and orientations
            page_size = template.get('page_size', 'A4')
            
            # Define target sizes for different page formats (width, height in pixels at 300 DPI)
            if page_size == 'A4_Landscape':
                target_size = (3507, 2480)  # A4 landscape
            elif page_size == 'A4':
                target_size = (2480, 3507)  # A4 portrait
            elif page_size == 'Letter_Landscape':
                target_size = (3300, 2550)  # Letter landscape
            elif page_size == 'Letter':
                target_size = (2550, 3300)  # Letter portrait
            elif page_size == 'A3_Landscape':
                target_size = (4961, 3507)  # A3 landscape
            elif page_size == 'A3':
                target_size = (3507, 4961)  # A3 portrait
            else:
                # Default to A4 landscape if unknown
                target_size = (3507, 2480)
            
            # Resize image to target dimensions
            if image.size != target_size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)
                print(f"Resized image to {page_size}: {target_size}")
            else:
                print(f"Image already correct size for {page_size}: {target_size}")
            
            # Create temporary PDF file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            # Convert to PDF
            image.save(temp_file.name, 'PDF', resolution=300.0)
            print(f"PDF created: {temp_file.name}")
            
            return temp_file.name
            
        except Exception as e:
            print(f"Error converting to PDF: {e}")
            raise
    
    def _apply_background(self, base_image: Image.Image, background_id: str) -> Image.Image:
        """Apply background image to the base template"""
        try:
            # Map background IDs to file paths
            background_mapping = {
                'abstract-blurred': '237.jpg',
                'roses-wooden': 'beautiful-roses-great-white-wooden-background-with-space-right.jpg',
                'cute-hearts': 'copy-space-with-cute-hearts.jpg',
                'flat-lay-hearts': 'flat-lay-small-cute-hearts.jpg'
            }
            
            if background_id not in background_mapping:
                print(f"Unknown background ID: {background_id}")
                return base_image
            
            # Load background image
            background_path = Path(settings.project_root) / 'backgrounds' / background_mapping[background_id]
            if not background_path.exists():
                print(f"Background file not found: {background_path}")
                return base_image
            
            background = Image.open(background_path)
            print(f"Background loaded: {background.size}")
            
            # Resize background to match base image
            background = background.resize(base_image.size, Image.Resampling.LANCZOS)
            
            # Convert both images to RGBA if needed
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')
            if background.mode != 'RGBA':
                background = background.convert('RGBA')
            
            # Make white areas of the template transparent
            # This allows the background to show through
            base_data = base_image.getdata()
            new_data = []
            
            for item in base_data:
                # If pixel is white or very light, make it transparent
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    new_data.append((item[0], item[1], item[2], 0))  # Transparent
                else:
                    new_data.append(item)  # Keep original
            
            base_image.putdata(new_data)
            
            # Create a new image with background
            result = Image.new('RGBA', base_image.size, (255, 255, 255, 255))
            
            # Paste background first
            result.paste(background, (0, 0))
            
            # Paste base image on top with alpha blending
            result = Image.alpha_composite(result, base_image)
            
            # Convert back to RGB for PDF generation
            result = result.convert('RGB')
            
            print(f"Background applied successfully")
            return result
            
        except Exception as e:
            print(f"Error applying background: {e}")
            return base_image
    
    def _generate_qr_url(self, session: SessionModel, order: Optional[Order] = None) -> str:
        """Generate direct audio file URL for QR code"""
        try:
            if order and order.permanent_audio_s3_key:
                # Paid version - use permanent audio URL
                # First check if the file exists
                if self.file_uploader.file_exists(order.permanent_audio_s3_key):
                    return self.file_uploader.generate_presigned_url(
                        order.permanent_audio_s3_key,
                        expiration=86400 * 365  # 1 year expiration
                    )
                else:
                    print(f"WARNING: Permanent audio file missing: {order.permanent_audio_s3_key}")
                    return f"{settings.base_url}/audio-not-found"
            elif session.audio_s3_key:
                # Preview version - use session audio URL
                # First check if the file exists
                if self.file_uploader.file_exists(session.audio_s3_key):
                    return self.file_uploader.generate_presigned_url(
                        session.audio_s3_key,
                        expiration=86400 * 7  # 7 days expiration
                    )
                else:
                    print(f"WARNING: Session audio file missing: {session.audio_s3_key}")
                    return f"{settings.base_url}/audio-not-found"
            else:
                # Fallback - return a placeholder
                return f"{settings.base_url}/audio-not-found"
        except Exception as e:
            print(f"Error generating QR URL: {e}")
            return f"{settings.base_url}/audio-error"
