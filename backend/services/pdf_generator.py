from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter, A3
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import qrcode
from io import BytesIO
import tempfile
import os
from typing import Optional
from botocore.exceptions import ClientError

from ..config import settings
from ..models import SessionModel, Order
from .file_uploader import FileUploader
from .image_processor import ImageProcessor
from .visual_pdf_generator import VisualPDFGenerator

class PDFGenerator:
    """Generates poster PDFs with custom layouts and watermarks"""
    
    def __init__(self):
        self.file_uploader = FileUploader()
        self.image_processor = ImageProcessor()
        self.visual_generator = VisualPDFGenerator()
        self.page_sizes = {
            'A4': A4,
            'A4_Landscape': (A4[1], A4[0]),  # Swap width and height for landscape
            'Letter': letter,
            'Letter_Landscape': (letter[1], letter[0]),  # Swap width and height for landscape
            'A3': A3,
            'A3_Landscape': (A3[1], A3[0])  # Swap width and height for landscape
        }
        
    async def generate_preview_pdf(self, session: SessionModel) -> str:
        """Generate watermarked preview PDF"""
        # Check if visual template exists
        if self._has_visual_template(session.template_id):
            print(f"Using visual template for {session.template_id}")
            return await self.visual_generator.generate_pdf(session, add_watermark=True)
        else:
            print(f"Using code-based template for {session.template_id}")
            return await self._generate_pdf(session, add_watermark=True)
    
    async def generate_final_pdf(self, session: SessionModel, order: Order) -> str:
        """Generate final PDF without watermark"""
        # Check if visual template exists
        if self._has_visual_template(session.template_id):
            print(f"Using visual template for {session.template_id}")
            return await self.visual_generator.generate_pdf(session, add_watermark=False, order=order)
        else:
            print(f"Using code-based template for {session.template_id}")
            return await self._generate_pdf(session, add_watermark=False, order=order)
    
    async def _generate_pdf(self, session: SessionModel, add_watermark: bool = True, 
                           order: Optional[Order] = None) -> str:
        """Core PDF generation logic"""
        try:
            # Set up canvas
            buffer = BytesIO()
            page_size = self.page_sizes.get(session.pdf_size, A4)
            c = canvas.Canvas(buffer, pagesize=page_size)
            width, height = page_size
            
            # Get template configuration
            template_config = self._get_template_config(session.template_id)
            
            # Add background if template has one
            if template_config.get('background_color'):
                c.setFillColor(template_config['background_color'])
                c.rect(0, 0, width, height, fill=1, stroke=0)
            
            # Add custom text
            await self._add_text(c, session.custom_text, width, height, template_config)
            
            # Add photo
            await self._add_photo(c, session, template_config, width, height)
            
            # Add waveform
            await self._add_waveform(c, session, template_config, width, height)
            
            # Add QR code
            qr_url = self._generate_qr_url(session, order)
            await self._add_qr_code(c, qr_url, template_config, width, height)
            
            # Add watermark if needed
            if add_watermark:
                self._add_watermark(c, width, height)
            
            # Add template-specific decorations
            self._add_template_decorations(c, template_config, width, height)
            
            c.save()
            buffer.seek(0)
            
            # Upload PDF to storage
            pdf_key = f"pdfs/{'preview' if add_watermark else order.id if order else 'final'}.pdf"
            
            # Save buffer to temporary file for upload
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(buffer.getvalue())
            temp_file.close()
            
            try:
                if self.file_uploader.s3_client:
                    # Upload to S3
                    with open(temp_file.name, 'rb') as f:
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
                                f,
                                settings.s3_bucket,
                                pdf_key,
                                ExtraArgs=extra_args
                            )
                        except ClientError as e:
                            if 'AccessControlListNotSupported' in str(e):
                                # Retry without ACL if bucket doesn't support it
                                extra_args.pop('ACL', None)  # Remove ACL if present
                                self.file_uploader.s3_client.upload_fileobj(
                                    f,
                                    settings.s3_bucket,
                                    pdf_key,
                                    ExtraArgs=extra_args
                                )
                            else:
                                raise e
                    
                    # Return presigned URL for download
                    return self.file_uploader.generate_presigned_url(pdf_key, expiration=3600)
                else:
                    # Store locally
                    local_path = os.path.join(self.file_uploader.local_storage_path, pdf_key)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    
                    import shutil
                    shutil.copy2(temp_file.name, local_path)
                    
                    return f"{settings.base_url}/static/{pdf_key}"
                    
            finally:
                # Cleanup temporary file
                os.unlink(temp_file.name)
                
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def _get_template_config(self, template_id: str) -> dict:
        """Get template configuration"""
        templates = {
            'classic': {
                'text_y_offset': 0.90,  # Position text at top like in example
                'photo_y_offset': 0.70,  # Move photo higher up 
                'waveform_y_offset': 0.35,  # Position waveform below photo
                'qr_y_offset': 0.10,  # Center QR at bottom
                'text_font': 'Times-Italic',  # Handwritten-style font
                'text_size': 32,  # Larger text like in example
                'photo_size': 4.5,  # Larger photo (4.5 inches)
                'waveform_width': 7,  # Wider waveform (7 inches)
                'qr_size': 0.8,  # Smaller QR code (0.8 inches)
                'qr_position': 'center',  # Center QR instead of right
                'background_color': None,
                'accent_color': '#000000'  # Black text like in example
            },
            'modern': {
                'text_y_offset': 0.90,
                'photo_y_offset': 0.60,
                'waveform_y_offset': 0.30,
                'qr_y_offset': 0.05,
                'text_font': 'Helvetica',
                'text_size': 20,
                'photo_size': 3,
                'waveform_width': 6,
                'qr_size': 1,
                'qr_position': 'right',
                'background_color': '#f8fafc',
                'accent_color': '#6d28d9'
            },
            'vintage': {
                'text_y_offset': 0.88,
                'photo_y_offset': 0.58,
                'waveform_y_offset': 0.28,
                'qr_y_offset': 0.08,
                'text_font': 'Times-Roman',
                'text_size': 22,
                'photo_size': 3,
                'waveform_width': 6,
                'qr_size': 1,
                'qr_position': 'right',
                'background_color': '#fef7e0',
                'accent_color': '#92400e'
            },
            'elegant': {
                'text_y_offset': 0.87,
                'photo_y_offset': 0.57,
                'waveform_y_offset': 0.27,
                'qr_y_offset': 0.06,
                'text_font': 'Times-Italic',
                'text_size': 26,
                'photo_size': 3,
                'waveform_width': 6,
                'qr_size': 1,
                'qr_position': 'right',
                'background_color': None,
                'accent_color': '#1e293b'
            }
        }
        
        return templates.get(template_id, templates['classic'])
    
    async def _add_text(self, canvas_obj: canvas.Canvas, text: str, width: float, 
                       height: float, template_config: dict):
        """Add custom text to PDF"""
        if not text:
            return
            
        # Set font and size
        font_name = template_config.get('text_font', 'Helvetica-Bold')
        font_size = template_config.get('text_size', 24)
        
        canvas_obj.setFont(font_name, font_size)
        canvas_obj.setFillColor(template_config.get('accent_color', '#000000'))
        
        # Calculate position
        text_width = canvas_obj.stringWidth(text, font_name, font_size)
        x = (width - text_width) / 2  # Center horizontally
        y = height * template_config.get('text_y_offset', 0.85)
        
        # Add text
        canvas_obj.drawString(x, y, text)
    
    async def _add_photo(self, canvas_obj: canvas.Canvas, session: SessionModel, 
                        template_config: dict, width: float, height: float):
        """Add photo to PDF"""
        if not session.photo_s3_key:
            return
            
        try:
            # Get processed image in the right shape  
            photo_size_px = int(template_config.get('photo_size', 3) * 120)  # Convert inches to pixels (120 DPI)
            image = self.image_processor.create_shaped_image(
                session.photo_s3_key,
                session.photo_shape,
                (photo_size_px, photo_size_px)  # Dynamic size based on template
            )
            
            # Save image to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            if session.photo_shape == 'circle':
                image.save(temp_file.name, 'PNG')
            else:
                image.save(temp_file.name, 'JPEG', quality=95)
            temp_file.close()
            
            try:
                # Calculate position and size
                img_size = template_config.get('photo_size', 3) * inch  # Use template photo size
                x = (width - img_size) / 2  # Center horizontally
                y = height * template_config.get('photo_y_offset', 0.55) - img_size / 2
                
                # Add image to canvas
                canvas_obj.drawImage(temp_file.name, x, y, width=img_size, height=img_size, 
                                   mask='auto' if session.photo_shape == 'circle' else None)
                
            finally:
                # Cleanup temporary file
                os.unlink(temp_file.name)
                
        except Exception as e:
            print(f"Error adding photo: {e}")
            # Continue without photo rather than failing
    
    async def _add_waveform(self, canvas_obj: canvas.Canvas, session: SessionModel,
                           template_config: dict, width: float, height: float):
        """Add waveform to PDF"""
        if not session.waveform_s3_key:
            return
            
        try:
            # Download waveform image
            if self.file_uploader.s3_client:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                self.file_uploader.s3_client.download_fileobj(
                    settings.s3_bucket,
                    session.waveform_s3_key,
                    temp_file
                )
                temp_file.close()
                waveform_path = temp_file.name
            else:
                waveform_path = os.path.join(
                    self.file_uploader.local_storage_path, 
                    session.waveform_s3_key
                )
            
            try:
                # Calculate position and size
                waveform_width = template_config.get('waveform_width', 6) * inch
                waveform_height = 1.5 * inch
                x = (width - waveform_width) / 2
                y = height * template_config.get('waveform_y_offset', 0.25)
                
                # Add waveform image
                canvas_obj.drawImage(waveform_path, x, y, 
                                   width=waveform_width, height=waveform_height)
                
            finally:
                # Cleanup if we downloaded from S3
                if self.file_uploader.s3_client:
                    os.unlink(waveform_path)
                    
        except Exception as e:
            print(f"Error adding waveform: {e}")
            # Continue without waveform rather than failing
    
    async def _add_qr_code(self, canvas_obj: canvas.Canvas, url: str, 
                          template_config: dict, width: float, height: float):
        """Add QR code to PDF"""
        try:
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            qr_image.save(temp_file.name)
            temp_file.close()
            
            try:
                # Calculate position and size
                qr_size = template_config.get('qr_size', 1) * inch
                qr_position = template_config.get('qr_position', 'right')
                
                if qr_position == 'center':
                    x = (width - qr_size) / 2  # Center horizontally
                else:
                    x = width - qr_size - 0.5 * inch  # Right side with margin
                    
                y = height * template_config.get('qr_y_offset', 0.05)
                
                # Add QR code
                canvas_obj.drawImage(temp_file.name, x, y, width=qr_size, height=qr_size)
                
            finally:
                # Cleanup temporary file
                os.unlink(temp_file.name)
                
        except Exception as e:
            print(f"Error adding QR code: {e}")
            # Continue without QR code rather than failing
    
    def _add_watermark(self, canvas_obj: canvas.Canvas, width: float, height: float):
        """Add diagonal watermark across the page"""
        canvas_obj.saveState()
        
        # Set watermark properties according to specifications
        canvas_obj.setFont("Helvetica", 24)  # 24pt font
        canvas_obj.setFillColorRGB(0.8, 0.8, 0.8, 0.2)  # Light gray #CCCCCC, 20% opacity
        
        # Rotate and position watermark diagonally across entire poster
        canvas_obj.translate(width / 2, height / 2)
        canvas_obj.rotate(45)
        
        # Draw watermark text
        text = "PREVIEW - AudioPoster.com"
        text_width = canvas_obj.stringWidth(text, "Helvetica", 24)
        canvas_obj.drawString(-text_width / 2, 0, text)
        
        canvas_obj.restoreState()
    
    def _add_template_decorations(self, canvas_obj: canvas.Canvas, template_config: dict,
                                 width: float, height: float):
        """Add template-specific decorative elements"""
        accent_color = template_config.get('accent_color', '#8b5cf6')
        
        if template_config.get('id') == 'modern':
            # Add subtle border lines
            canvas_obj.setStrokeColor(accent_color)
            canvas_obj.setLineWidth(2)
            
            # Top line
            canvas_obj.line(0.5 * inch, height - 0.5 * inch, 
                           width - 0.5 * inch, height - 0.5 * inch)
            
            # Bottom line
            canvas_obj.line(0.5 * inch, 0.5 * inch, 
                           width - 0.5 * inch, 0.5 * inch)
        
        elif template_config.get('id') == 'vintage':
            # Add corner decorations
            canvas_obj.setStrokeColor(accent_color)
            canvas_obj.setLineWidth(1)
            
            # Corner lines
            corner_size = 20
            margin = 0.3 * inch
            
            # Top left
            canvas_obj.line(margin, height - margin, margin + corner_size, height - margin)
            canvas_obj.line(margin, height - margin, margin, height - margin - corner_size)
            
            # Top right
            canvas_obj.line(width - margin, height - margin, 
                           width - margin - corner_size, height - margin)
            canvas_obj.line(width - margin, height - margin, 
                           width - margin, height - margin - corner_size)
    
    def _generate_qr_url(self, session: SessionModel, order: Optional[Order] = None) -> str:
        """Generate direct audio file URL for QR code"""
        try:
            print(f"DEBUG: _generate_qr_url called with session.audio_s3_key: {session.audio_s3_key}")
            print(f"DEBUG: order: {order}")
            
            if order and order.permanent_audio_s3_key:
                # Paid version - use permanent audio URL
                print(f"DEBUG: Using permanent audio key: {order.permanent_audio_s3_key}")
                # First check if the file exists
                if self.file_uploader.file_exists(order.permanent_audio_s3_key):
                    return self.file_uploader.generate_presigned_url(
                        order.permanent_audio_s3_key,
                        expiration=86400 * 365 * 5  # 5 years expiration
                    )
                else:
                    raise Exception(f"Permanent audio file missing: {order.permanent_audio_s3_key}")
            elif session.audio_s3_key:
                # Preview version - use session audio URL
                print(f"DEBUG: Using session audio key: {session.audio_s3_key}")
                print(f"DEBUG: Checking if file exists...")
                
                # Check if it's a temporary file and handle accordingly
                if session.audio_s3_key.startswith('temp_'):
                    from .storage_manager import StorageManager
                    storage_manager = StorageManager()
                    temp_path = storage_manager.get_temp_file_path(session.audio_s3_key)
                    file_exists = temp_path and os.path.exists(temp_path)
                    print(f"DEBUG: Temporary file path: {temp_path}")
                    print(f"DEBUG: File exists check result: {file_exists}")
                    
                    if file_exists:
                        # For temporary files, we need to upload to S3 first or use a different approach
                        # For now, let's skip QR code generation for temporary files
                        print(f"DEBUG: Temporary audio file found, but QR code generation not supported for temp files")
                        return "https://audioposter.com"  # Fallback URL
                    else:
                        raise Exception(f"Temporary audio file missing: {session.audio_s3_key} (path: {temp_path})")
                else:
                    # Check S3 file
                    file_exists = self.file_uploader.file_exists(session.audio_s3_key)
                    print(f"DEBUG: S3 file exists check result: {file_exists}")
                    
                    if file_exists:
                        print(f"DEBUG: Generating presigned URL for session audio")
                        return self.file_uploader.generate_presigned_url(
                            session.audio_s3_key,
                            expiration=86400 * 7  # 7 days expiration
                        )
                    else:
                        raise Exception(f"Session audio file missing: {session.audio_s3_key}")
            else:
                raise Exception("No audio file available for QR code generation")
        except Exception as e:
            print(f"Error generating QR URL: {e}")
            raise Exception(f"Failed to generate QR code URL: {str(e)}")
    
    def _has_visual_template(self, template_id: str) -> bool:
        """Check if a visual template exists for the given template ID"""
        try:
            template = self.visual_generator.template_service.get_template(template_id)
            template_path = self.visual_generator.template_service.get_template_path(template_id)
            return template is not None and template_path is not None
        except Exception as e:
            print(f"Error checking visual template: {e}")
            return False
