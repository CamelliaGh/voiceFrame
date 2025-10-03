import os
import tempfile
from io import BytesIO
from typing import Optional

import qrcode
from botocore.exceptions import ClientError
from PIL import Image
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A3, A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from ..config import settings
from ..models import Order, SessionModel
from .file_uploader import FileUploader
from .image_processor import ImageProcessor
from .visual_pdf_generator import VisualPDFGenerator
from .admin_resource_service import admin_resource_service


class PDFGenerator:
    """Generates poster PDFs with custom layouts and watermarks"""

    def __init__(self):
        self.file_uploader = FileUploader()
        self.image_processor = ImageProcessor()
        self.visual_generator = VisualPDFGenerator()
        self.admin_resource_service = admin_resource_service
        self.page_sizes = {
            "A4": A4,
            "A4_Landscape": (A4[1], A4[0]),  # Swap width and height for landscape
            "Letter": letter,
            "Letter_Landscape": (
                letter[1],
                letter[0],
            ),  # Swap width and height for landscape
            "A3": A3,
            "A3_Landscape": (A3[1], A3[0]),  # Swap width and height for landscape
        }

    async def generate_preview_pdf(self, session: SessionModel) -> str:
        """Generate watermarked preview PDF"""
        # Always use visual generator since we only use visual templates now
        print(f"🎯 DEBUG: Using visual generator for {session.template_id}")
        return await self.visual_generator.generate_pdf(session, add_watermark=True)

    async def generate_final_pdf(self, session: SessionModel, order: Order) -> str:
        """Generate final PDF without watermark"""
        # Always use visual generator since we only use visual templates now
        print(f"🎯 DEBUG: Using visual generator for final PDF {session.template_id}")
        return await self.visual_generator.generate_pdf(
            session, add_watermark=False, order=order
        )

    async def _generate_pdf(
        self,
        session: SessionModel,
        add_watermark: bool = True,
        order: Optional[Order] = None,
    ) -> str:
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
            if template_config.get("background_color"):
                c.setFillColor(template_config["background_color"])
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

            # Add template-specific decorations
            self._add_template_decorations(c, template_config, width, height)

            # Add watermark if needed (LAST - on top of everything)
            if add_watermark:
                self._add_watermark(c, width, height)

            c.save()
            buffer.seek(0)

            # Upload PDF to storage
            if add_watermark:
                # Add timestamp to preview filename to prevent caching
                import time
                timestamp = int(time.time())
                pdf_key = f"pdfs/preview_{timestamp}.pdf"
            else:
                pdf_key = f"pdfs/{order.id if order else 'final'}.pdf"

            # Save buffer to temporary file for upload
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(buffer.getvalue())
            temp_file.close()

            try:
                if self.file_uploader.s3_client:
                    # Upload to S3
                    with open(temp_file.name, "rb") as f:
                        # Determine if this should be public (preview PDFs)
                        is_public = "preview" in pdf_key.lower()

                        extra_args = {
                            "ContentType": "application/pdf",
                            "ServerSideEncryption": "AES256",
                        }

                        # Try to make preview PDFs publicly readable
                        if is_public:
                            try:
                                extra_args["ACL"] = "public-read"
                            except Exception:
                                # If ACL is not supported, we'll rely on bucket policy
                                pass

                        try:
                            self.file_uploader.s3_client.upload_fileobj(
                                f, settings.s3_bucket, pdf_key, ExtraArgs=extra_args
                            )
                        except ClientError as e:
                            if "AccessControlListNotSupported" in str(e):
                                # Retry without ACL if bucket doesn't support it
                                extra_args.pop("ACL", None)  # Remove ACL if present
                                self.file_uploader.s3_client.upload_fileobj(
                                    f, settings.s3_bucket, pdf_key, ExtraArgs=extra_args
                                )
                            else:
                                raise e

                    # Return presigned URL for download
                    return self.file_uploader.generate_presigned_url(
                        pdf_key, expiration=3600
                    )
                else:
                    # Store locally
                    local_path = os.path.join(
                        self.file_uploader.local_storage_path, pdf_key
                    )
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)

                    import shutil

                    shutil.copy2(temp_file.name, local_path)

                    return f"{settings.base_url}/static/{pdf_key}"

            finally:
                # Cleanup temporary file
                os.unlink(temp_file.name)

        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")

    # Legacy method - no longer used since we only use visual templates
    def _get_template_config(self, template_id: str) -> dict:
        """Legacy method - no longer used"""
        return {}

    async def _add_text(
        self,
        canvas_obj: canvas.Canvas,
        text: str,
        width: float,
        height: float,
        template_config: dict,
    ):
        """Add custom text to PDF"""
        if not text:
            return

        # Set font and size
        font_name = template_config.get("text_font", "Helvetica-Bold")
        font_size = template_config.get("text_size", 24)

        canvas_obj.setFont(font_name, font_size)
        canvas_obj.setFillColor(template_config.get("accent_color", "#000000"))

        # Calculate position
        text_width = canvas_obj.stringWidth(text, font_name, font_size)
        x = (width - text_width) / 2  # Center horizontally
        y = height * template_config.get("text_y_offset", 0.85)

        # Add text
        canvas_obj.drawString(x, y, text)

    async def _add_photo(
        self,
        canvas_obj: canvas.Canvas,
        session: SessionModel,
        template_config: dict,
        width: float,
        height: float,
    ):
        """Add photo to PDF"""
        if not session.photo_s3_key:
            return

        try:
            # Get processed image in the right shape
            photo_size_px = int(
                template_config.get("photo_size", 3) * 120
            )  # Convert inches to pixels (120 DPI)
            image = self.image_processor.create_shaped_image(
                session.photo_s3_key,
                session.photo_shape,
                (photo_size_px, photo_size_px),  # Dynamic size based on template
            )

            # Save image to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            if session.photo_shape == "circle":
                image.save(temp_file.name, "PNG")
            else:
                image.save(temp_file.name, "JPEG", quality=95)
            temp_file.close()

            try:
                # Calculate position and size
                img_size = (
                    template_config.get("photo_size", 3) * inch
                )  # Use template photo size
                x = (width - img_size) / 2  # Center horizontally
                y = height * template_config.get("photo_y_offset", 0.55) - img_size / 2

                # Add image to canvas
                canvas_obj.drawImage(
                    temp_file.name,
                    x,
                    y,
                    width=img_size,
                    height=img_size,
                    mask="auto" if session.photo_shape == "circle" else None,
                )

            finally:
                # Cleanup temporary file
                os.unlink(temp_file.name)

        except Exception as e:
            print(f"Error adding photo: {e}")
            # Continue without photo rather than failing

    async def _add_waveform(
        self,
        canvas_obj: canvas.Canvas,
        session: SessionModel,
        template_config: dict,
        width: float,
        height: float,
    ):
        """Add waveform to PDF"""
        if not session.waveform_s3_key:
            return

        try:
            # Download waveform image
            if self.file_uploader.s3_client:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                self.file_uploader.s3_client.download_fileobj(
                    settings.s3_bucket, session.waveform_s3_key, temp_file
                )
                temp_file.close()
                waveform_path = temp_file.name
            else:
                waveform_path = os.path.join(
                    self.file_uploader.local_storage_path, session.waveform_s3_key
                )

            try:
                # Calculate position and size
                waveform_width = template_config.get("waveform_width", 6) * inch
                waveform_height = 1.5 * inch
                x = (width - waveform_width) / 2
                y = height * template_config.get("waveform_y_offset", 0.25)

                # Add waveform image
                canvas_obj.drawImage(
                    waveform_path, x, y, width=waveform_width, height=waveform_height
                )

            finally:
                # Cleanup if we downloaded from S3
                if self.file_uploader.s3_client:
                    os.unlink(waveform_path)

        except Exception as e:
            print(f"Error adding waveform: {e}")
            # Continue without waveform rather than failing

    async def _add_qr_code(
        self,
        canvas_obj: canvas.Canvas,
        url: str,
        template_config: dict,
        width: float,
        height: float,
    ):
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
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            qr_image.save(temp_file.name)
            temp_file.close()

            try:
                # Calculate position and size
                qr_size = template_config.get("qr_size", 1) * inch
                qr_position = template_config.get("qr_position", "right")

                if qr_position == "center":
                    x = (width - qr_size) / 2  # Center horizontally
                else:
                    x = width - qr_size - 0.5 * inch  # Right side with margin

                y = height * template_config.get("qr_y_offset", 0.05)

                # Add QR code
                canvas_obj.drawImage(
                    temp_file.name, x, y, width=qr_size, height=qr_size
                )

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
        # Light gray #CCCCCC with 40% opacity for better visibility
        canvas_obj.setFillColorRGB(0.8, 0.8, 0.8)  # Light gray #CCCCCC
        canvas_obj.setFillAlpha(0.4)  # 40% opacity for better visibility

        # Rotate and position watermark diagonally across entire poster
        canvas_obj.translate(width / 2, height / 2)
        canvas_obj.rotate(45)

        # Draw watermark text
        text = "PREVIEW - VocaFrame.com"
        text_width = canvas_obj.stringWidth(text, "Helvetica", 24)
        canvas_obj.drawString(-text_width / 2, 0, text)

        canvas_obj.restoreState()

    def _add_template_decorations(
        self,
        canvas_obj: canvas.Canvas,
        template_config: dict,
        width: float,
        height: float,
    ):
        """Add template-specific decorative elements"""
        accent_color = template_config.get("accent_color", "#8b5cf6")

        if template_config.get("id") == "modern":
            # Add subtle border lines
            canvas_obj.setStrokeColor(accent_color)
            canvas_obj.setLineWidth(2)

            # Top line
            canvas_obj.line(
                0.5 * inch, height - 0.5 * inch, width - 0.5 * inch, height - 0.5 * inch
            )

            # Bottom line
            canvas_obj.line(0.5 * inch, 0.5 * inch, width - 0.5 * inch, 0.5 * inch)

        elif template_config.get("id") == "vintage":
            # Add corner decorations
            canvas_obj.setStrokeColor(accent_color)
            canvas_obj.setLineWidth(1)

            # Corner lines
            corner_size = 20
            margin = 0.3 * inch

            # Top left
            canvas_obj.line(
                margin, height - margin, margin + corner_size, height - margin
            )
            canvas_obj.line(
                margin, height - margin, margin, height - margin - corner_size
            )

            # Top right
            canvas_obj.line(
                width - margin,
                height - margin,
                width - margin - corner_size,
                height - margin,
            )
            canvas_obj.line(
                width - margin,
                height - margin,
                width - margin,
                height - margin - corner_size,
            )

    def _generate_qr_url(
        self, session: SessionModel, order: Optional[Order] = None
    ) -> str:
        """Generate direct audio file URL for QR code"""
        try:
            print(
                f"DEBUG: _generate_qr_url called with session.audio_s3_key: {session.audio_s3_key if session else 'None'}"
            )
            print(f"DEBUG: order: {order}")

            if order and order.permanent_audio_s3_key:
                # Paid version - use permanent audio URL
                print(
                    f"DEBUG: Using permanent audio key: {order.permanent_audio_s3_key}"
                )
                # First check if the file exists
                if self.file_uploader.file_exists(order.permanent_audio_s3_key):
                    return self.file_uploader.generate_presigned_url(
                        order.permanent_audio_s3_key,
                        expiration=settings.qr_code_permanent_expiration
                    )
                else:
                    raise Exception(
                        f"Permanent audio file missing: {order.permanent_audio_s3_key}"
                    )
            elif session and session.audio_s3_key:
                # Preview version - use session audio URL
                print(f"DEBUG: Using session audio key: {session.audio_s3_key}")
                print(f"DEBUG: Checking if file exists...")

                # All audio files are now in S3, so check S3 directly
                file_exists = self.file_uploader.file_exists(session.audio_s3_key)
                print(f"DEBUG: S3 file exists check result: {file_exists}")

                if file_exists:
                    print(f"DEBUG: Generating presigned URL for session audio")
                    return self.file_uploader.generate_presigned_url(
                        session.audio_s3_key, expiration=settings.qr_code_preview_expiration
                    )
                else:
                    raise Exception(
                        f"Session audio file missing: {session.audio_s3_key}"
                    )
            else:
                raise Exception("No audio file available for QR code generation")
        except Exception as e:
            print(f"Error generating QR URL: {e}")
            raise Exception(f"Failed to generate QR code URL: {str(e)}")

    # Legacy method - no longer used since we only use visual templates
    def _has_visual_template(self, template_id: str) -> bool:
        """Legacy method - no longer used"""
        return True
