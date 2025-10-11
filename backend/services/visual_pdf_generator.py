import os
import tempfile
import re
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Tuple, List

import qrcode
from PIL import Image, ImageDraw, ImageFont

from ..config import settings
from ..models import Order, SessionModel
from .file_uploader import FileUploader
from .image_processor import ImageProcessor
from .visual_template_service import VisualTemplateService
from .admin_resource_service import admin_resource_service


class VisualPDFGenerator:
    """Generates PDFs using visual templates designed in Canva/Figma"""

    def __init__(self):
        self.template_service = VisualTemplateService()
        self.file_uploader = FileUploader()
        self.image_processor = ImageProcessor()
        self.admin_resource_service = admin_resource_service

    def _get_admin_font_path(self, font_name: str) -> Optional[str]:
        """Get the file path for an admin-managed font"""
        try:
            from ..database import get_db
            db = next(get_db())
            font_data = self.admin_resource_service.get_font_by_name(db, font_name)
            if font_data and font_data.get('file_path'):
                return font_data['file_path']
        except Exception as e:
            print(f"Error getting admin font path for {font_name}: {e}")
        return None

    async def generate_pdf(
        self,
        session: SessionModel,
        add_watermark: bool = True,
        order: Optional[Order] = None,
    ) -> str:
        """Generate PDF using visual template"""
        try:
            # Debug session data
            print(
                f"DEBUG: Session data - template_id: {session.template_id}, custom_text: '{session.custom_text}', font_id: {getattr(session, 'font_id', 'NOT_SET')}"
            )
            print(f"DEBUG: add_watermark parameter: {add_watermark}")
            print(f"🚀 DEBUG: VISUAL PDF GENERATION START - template_id: {session.template_id}")
            print(f"🚀 DEBUG: VISUAL PDF GENERATION START - custom_text: '{session.custom_text}'")
            print(f"🚀 DEBUG: VISUAL PDF GENERATION START - photo_s3_key: {session.photo_s3_key}")
            print(f"DEBUG: Starting visual PDF generation process...")

            # Get template configuration
            print(f"DEBUG: Looking for template with ID: {session.template_id}")
            template = self.template_service.get_template(session.template_id)
            if not template:
                raise ValueError(f"Template {session.template_id} not found")

            print(f"DEBUG: Template configuration: {template}")
            print(f"DEBUG: Template placeholders: {template.get('placeholders', {})}")

            # Load template image
            template_path = self.template_service.get_template_path(session.template_id)
            if not template_path:
                raise ValueError(f"Template file not found for {session.template_id}")

            print(f"Loading template from: {template_path}")

            # Create base image from template
            base_image = Image.open(template_path)
            print(f"Template loaded: {base_image.size}")

            # Apply background if specified
            if session.background_id and session.background_id != "none":
                base_image = self._apply_background(base_image, session.background_id)
                print(f"Background applied: {session.background_id}")

            # Add photo
            print(f"🔵 DEBUG: About to check photo condition - session.photo_s3_key: {session.photo_s3_key}")
            print(f"🔵 DEBUG: About to check photo condition - session.custom_text: '{session.custom_text}'")
            if session.photo_s3_key:
                print(f"🔵 DEBUG: Photo condition passed, calling _add_photo_to_template")
                await self._add_photo_to_template(base_image, session, template)
            else:
                print(f"🔵 DEBUG: Photo condition failed - no photo_s3_key")

            # Add waveform
            if session.waveform_s3_key:
                await self._add_waveform_to_template(base_image, session, template)

            # Add QR code
            qr_url = self._generate_qr_url(session, order)
            print(f"🔴🔴🔴 CRITICAL DEBUG: QR URL GENERATED: {qr_url} 🔴🔴🔴")
            await self._add_qr_to_template(base_image, qr_url, template)

            # Add text
            if session.custom_text:
                print(f"DEBUG: Adding text '{session.custom_text}' to template")
                print(f"DEBUG: Base image mode before text: {base_image.mode}")
                await self._add_text_to_template(
                    base_image, session.custom_text, template, session
                )
                print(f"DEBUG: Base image mode after text: {base_image.mode}")
            else:
                print(
                    f"DEBUG: No custom text to add (session.custom_text: {session.custom_text})"
                )

            # Add watermark if needed (LAST - on top of everything)
            if add_watermark:
                print("DEBUG: Adding watermark to image...")
                # Convert to RGBA BEFORE adding watermark to preserve transparency
                if base_image.mode != "RGBA":
                    print(
                        f"DEBUG: Converting base image from {base_image.mode} to RGBA before watermark"
                    )
                    base_image = base_image.convert("RGBA")
                base_image = self._add_watermark_to_image(base_image)
                print("DEBUG: Watermark added successfully!")
            else:
                print("DEBUG: No watermark requested (add_watermark=False)")

            # Convert to PDF
            pdf_path = await self._convert_image_to_pdf(base_image, template)

            # Upload to storage
            if add_watermark:
                # Add timestamp to preview filename to prevent caching
                import time
                timestamp = int(time.time())
                pdf_key = f"pdfs/preview_{timestamp}.pdf"
            else:
                pdf_key = f"pdfs/{order.id if order else 'final'}.pdf"

            if self.file_uploader.s3_client:
                with open(pdf_path, "rb") as f:
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
                    except Exception as e:
                        if "AccessControlListNotSupported" in str(e):
                            # Retry without ACL if bucket doesn't support it
                            extra_args.pop("ACL", None)  # Remove ACL if present
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

    async def _add_photo_to_template(
        self, base_image: Image.Image, session: SessionModel, template: Dict
    ):
        """Add photo to template at specified coordinates"""
        print(f"🟢 DEBUG: _add_photo_to_template ENTRY - session.photo_s3_key: {session.photo_s3_key}")
        print(f"🟢 DEBUG: _add_photo_to_template ENTRY - session.photo_shape: {session.photo_shape}")
        print(f"🟢 DEBUG: _add_photo_to_template ENTRY - session.custom_text: '{session.custom_text}'")
        placeholder = template["placeholders"]["photo"]

        try:
            # Get processed photo
            photo_size = (placeholder["width"], placeholder["height"])
            # Simple debug log to verify photo shape
            print(f"🔍 PHOTO SHAPE DEBUG: session.photo_shape = '{session.photo_shape}'")

            # DEBUG MODE: Draw red circle instead of actual photo
            debug_mode = settings.debug_photo_circle

            if debug_mode:
                print("🔴 DEBUG MODE: Drawing red circle instead of photo")
                # Create a red circle image
                photo = Image.new('RGBA', photo_size, (0, 0, 0, 0))  # Transparent background
                draw = ImageDraw.Draw(photo)

                # Draw a red circle
                margin = 20
                circle_bbox = [margin, margin, photo_size[0] - margin, photo_size[1] - margin]
                draw.ellipse(circle_bbox, fill='red', outline='darkred', width=5)

                # Add text label
                draw.text((photo_size[0]//2 - 30, photo_size[1]//2 - 10), "CIRCLE", fill='white')
                print(f"🔴 DEBUG: Created red circle image with size {photo_size}")
            else:
                photo = self.image_processor.create_shaped_image(
                    session.photo_s3_key,
                    session.photo_shape,  # Use the session's photo shape preference
                    photo_size,
                )

            # Paste photo onto template
            print(f"🔴 DEBUG: PHOTO PASTE #{id(photo)} - About to paste photo. Base image mode: {base_image.mode}, Photo mode: {photo.mode}")
            print(f"🔴 DEBUG: PHOTO PASTE #{id(photo)} - Photo size: {photo.size}, Paste position: ({placeholder['x']}, {placeholder['y']})")
            print(f"🔴 DEBUG: PHOTO PASTE #{id(photo)} - Photo shape being used: {session.photo_shape}")

            # Handle transparency for circular images using PIL's mask-based paste
            # PIL can paste RGBA onto RGB using the alpha channel as a mask
            if photo.mode == 'RGBA':
                print(f"DEBUG: Photo has RGBA mode with transparency")
                print(f"DEBUG: Photo size: {photo.size}, position: ({placeholder['x']}, {placeholder['y']})")
                print(f"DEBUG: Base image mode: {base_image.mode} (keeping as RGB)")

                # Use PIL's built-in mask paste - the third parameter uses the alpha channel as mask
                # This works even when pasting RGBA onto RGB - transparent areas show the base image
                base_image.paste(photo, (placeholder["x"], placeholder["y"]), photo)
                print("DEBUG: Photo pasted with alpha mask successfully!")
            else:
                print(f"DEBUG: Photo has no alpha channel (mode: {photo.mode}), using regular paste")
                base_image.paste(photo, (placeholder["x"], placeholder["y"]))

            print(f"DEBUG: Photo pasted successfully. Final base image mode: {base_image.mode}")

        except Exception as e:
            print(f"Error adding photo: {e}")

    async def _add_waveform_to_template(
        self, base_image: Image.Image, session: SessionModel, template: Dict
    ):
        """Add waveform to template at specified coordinates"""
        placeholder = template["placeholders"]["waveform"]

        try:
            # Get waveform image
            waveform = self.image_processor.get_image_from_s3(session.waveform_s3_key)
            waveform = waveform.resize((placeholder["width"], placeholder["height"]))

            # Handle waveform with transparency
            if waveform.mode == "RGBA":
                # If waveform has alpha channel, use it for transparency
                base_image.paste(
                    waveform, (placeholder["x"], placeholder["y"]), waveform
                )
            else:
                # Convert to RGBA and make white pixels transparent
                waveform = waveform.convert("RGBA")
                data = waveform.getdata()
                new_data = []
                for item in data:
                    # Change all white pixels to transparent
                    if item[0] > 250 and item[1] > 250 and item[2] > 250:
                        new_data.append((255, 255, 255, 0))  # Transparent
                    else:
                        new_data.append(
                            (item[0], item[1], item[2], 255)
                        )  # Keep original

                waveform.putdata(new_data)
                base_image.paste(
                    waveform, (placeholder["x"], placeholder["y"]), waveform
                )
            print(
                f"Waveform added at ({placeholder['x']}, {placeholder['y']}) with size ({placeholder['width']}, {placeholder['height']}) in black with matching background"
            )

        except Exception as e:
            print(f"Error adding waveform: {e}")

    async def _add_qr_to_template(
        self, base_image: Image.Image, qr_url: str, template: Dict
    ):
        """Add QR code to template at specified coordinates"""
        placeholder = template["placeholders"]["qr_code"]

        try:
            # Generate QR code
            print(f"🟡🟡🟡 ABOUT TO ADD TO QR CODE: '{qr_url}' (length: {len(qr_url)}) 🟡🟡🟡")
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            print(f"🟡🟡🟡 QR CODE DATA ADDED SUCCESSFULLY 🟡🟡🟡")

            # Create QR code with white background first
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_image = qr_image.resize((placeholder["width"], placeholder["height"]))

            # Convert to RGBA and make white pixels transparent
            qr_image = qr_image.convert("RGBA")

            # Create transparent version
            data = qr_image.getdata()
            new_data = []
            for item in data:
                # Change all white (255, 255, 255) pixels to transparent
                if item[0] > 250 and item[1] > 250 and item[2] > 250:
                    new_data.append((255, 255, 255, 0))  # Make white pixels transparent
                else:
                    new_data.append(
                        (item[0], item[1], item[2], 255)
                    )  # Keep black pixels opaque

            qr_image.putdata(new_data)

            # Paste QR code with transparency mask
            base_image.paste(qr_image, (placeholder["x"], placeholder["y"]), qr_image)
            print(
                f"QR code added at ({placeholder['x']}, {placeholder['y']}) with size ({placeholder['width']}, {placeholder['height']}) and matching background"
            )

        except Exception as e:
            print(f"Error adding QR code: {e}")

    def _detect_emojis(self, text: str) -> List[Tuple[str, int, int]]:
        """Detect emojis in text and return list of (emoji, start_pos, end_pos)"""
        emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F]'  # Emoticons
            r'|[\U0001F300-\U0001F5FF]'  # Misc Symbols and Pictographs
            r'|[\U0001F680-\U0001F6FF]'  # Transport and Map
            r'|[\U0001F1E0-\U0001F1FF]'  # Regional indicator symbols
            r'|[\U00002600-\U000026FF]'  # Misc symbols
            r'|[\U00002700-\U000027BF]'  # Dingbats
            r'|[\U0001F900-\U0001F9FF]'  # Supplemental Symbols and Pictographs
            r'|[\U0001FA70-\U0001FAFF]'  # Symbols and Pictographs Extended-A
        )

        emojis = []
        for match in emoji_pattern.finditer(text):
            emojis.append((match.group(), match.start(), match.end()))

        return emojis

    def _render_text_with_emojis(self, draw: ImageDraw.Draw, text: str, font: ImageFont.ImageFont,
                                emoji_font: ImageFont.ImageFont, position: Tuple[int, int],
                                color: str) -> None:
        """Render text with emoji support by splitting text and emojis"""
        x, y = position
        emojis = self._detect_emojis(text)

        if not emojis:
            # No emojis, render normally
            draw.text((x, y), text, font=font, fill=color)
            return

        # Get font metrics for proper alignment
        font_bbox = draw.textbbox((0, 0), "Ay", font=font)  # Use "Ay" to get proper height
        font_height = font_bbox[3] - font_bbox[1]
        font_baseline = -font_bbox[1]  # Distance from top to baseline

        emoji_bbox = draw.textbbox((0, 0), "😀", font=emoji_font)
        emoji_height = emoji_bbox[3] - emoji_bbox[1]
        emoji_baseline = -emoji_bbox[1]

        # Calculate emoji scaling and positioning
        emoji_scale = font_height / emoji_height
        emoji_y_offset = (font_baseline - emoji_baseline * emoji_scale)

        # Split text around emojis and render each part
        current_x = x
        last_end = 0

        for emoji, start, end in emojis:
            # Render text before emoji
            if start > last_end:
                text_before = text[last_end:start]
                draw.text((current_x, y), text_before, font=font, fill=color)
                # Get width of rendered text
                bbox = draw.textbbox((0, 0), text_before, font=font)
                current_x += bbox[2] - bbox[0]

            # Render emoji with proper scaling and positioning
            emoji_y = y + emoji_y_offset
            # Create a temporary image for the emoji to scale it
            emoji_img = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
            emoji_draw = ImageDraw.Draw(emoji_img)
            emoji_draw.text((0, 0), emoji, font=emoji_font, fill=color)

            # Scale the emoji to match the text size
            new_size = (int(200 * emoji_scale), int(200 * emoji_scale))
            emoji_img = emoji_img.resize(new_size, Image.Resampling.LANCZOS)

            # Paste the scaled emoji onto the main image
            draw._image.paste(emoji_img, (int(current_x), int(emoji_y)), emoji_img)

            # Update current_x position (approximate emoji width)
            current_x += int(200 * emoji_scale * 0.8)  # 0.8 is a rough width/height ratio for emojis

            last_end = end

        # Render remaining text after last emoji
        if last_end < len(text):
            text_after = text[last_end:]
            draw.text((current_x, y), text_after, font=font, fill=color)

    async def _add_text_to_template(
        self, base_image: Image.Image, text: str, template: Dict, session: SessionModel
    ):
        """Add text to template at specified coordinates"""
        print(f"DEBUG: _add_text_to_template called with text: '{text}'")
        print(f"DEBUG: Template placeholders: {template.get('placeholders', {})}")

        placeholder = template["placeholders"]["text"]
        print(f"DEBUG: Text placeholder: {placeholder}")

        try:
            # Create drawing context
            draw = ImageDraw.Draw(base_image)

            # Try to load custom font with fallback options
            font = None
            # Use session font_id if available, otherwise fall back to template font
            font_name = (
                session.font_id
                if hasattr(session, "font_id") and session.font_id
                else placeholder.get("font", "script")
            )
            font_size = placeholder.get("font_size", 32)
            print(f"DEBUG: Using font_name: {font_name}, font_size: {font_size}")

            # First try to load admin-managed font
            font_path = self._get_admin_font_path(font_name)
            if font_path and os.path.exists(font_path):
                try:
                    print(f"Loading admin-managed font: {font_path}")
                    font = ImageFont.truetype(font_path, font_size)
                    print(f"Successfully loaded admin font: {font_name} at size {font_size}")
                except Exception as e:
                    print(f"Failed to load admin font {font_name}: {e}")
                    font_path = None

            # If admin font failed, try system fonts
            if not font_path:
                # Map font names to system fonts or font files
                font_mapping = {
                    "script": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "elegant": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                    "modern": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "vintage": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                    "classic": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                    "Arial": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "Helvetica": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "Times": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                    "Courier": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                }

                font_path = font_mapping.get(font_name, font_name)

                try:
                    print(f"Loading system font: {font_path}")
                    font = ImageFont.truetype(font_path, font_size)
                    print(f"Successfully loaded system font: {font_name} at size {font_size}")
                except Exception as e:
                    print(f"Failed to load font {font_name}: {e}")
                    # Try alternative fonts
                    alt_fonts = [
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
                    ]
                    for alt_font in alt_fonts:
                        try:
                            font = ImageFont.truetype(alt_font, font_size)
                            print(f"Successfully loaded alternative font: {alt_font}")
                            break
                        except:
                            continue
                    else:
                        # Last resort - use default font
                        font = ImageFont.load_default()
                        print(f"Using default font as fallback")

            # Calculate text position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            if placeholder.get("alignment", "center") == "center":
                x = placeholder["x"] + (placeholder["width"] - text_width) // 2
            else:
                x = placeholder["x"]

            y = placeholder["y"] + (placeholder["height"] - text_height) // 2

            # Draw text with the specified color from template
            text_color = placeholder.get("color", "#000000")
            print(
                f"DEBUG: Drawing text at position ({x}, {y}) with font {font_name} size {font_size}"
            )
            print(f"DEBUG: Using color: {text_color}")

            # Check if text contains emojis and load emoji font if needed
            emojis = self._detect_emojis(text)
            if emojis:
                print(f"DEBUG: Detected {len(emojis)} emojis in text: {[e[0] for e in emojis]}")
                try:
                    # Load emoji font with fixed size (Noto Color Emoji requires specific size)
                    emoji_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
                    print("DEBUG: Loaded Noto Color Emoji font for emoji rendering")
                    # Use emoji-aware rendering
                    self._render_text_with_emojis(draw, text, font, emoji_font, (x, y), text_color)
                    print("DEBUG: Text with emojis rendered successfully")
                except Exception as e:
                    print(f"DEBUG: Failed to load emoji font, falling back to regular rendering: {e}")
                    draw.text((x, y), text, font=font, fill=text_color)
            else:
                # No emojis, render normally
                draw.text((x, y), text, font=font, fill=text_color)

            print(
                f"DEBUG: Text successfully added at ({x}, {y}): '{text}' with font {font_name} size {font_size}"
            )

        except Exception as e:
            print(f"Error adding text: {e}")

    def _add_watermark_to_image(self, image: Image.Image) -> Image.Image:
        """Add diagonal watermark to image according to specifications"""
        try:
            print(
                f"DEBUG: Starting watermark - image mode: {image.mode}, size: {image.size}"
            )

            # Create a rotated watermark image
            watermark_img = Image.new("RGBA", image.size, (0, 0, 0, 0))
            watermark_draw = ImageDraw.Draw(watermark_img)

            # Watermark text - back to working version
            text = "vocaframe.com"

            # Use a larger font size for better visibility
            # Scale font size based on image dimensions
            base_font_size = 48  # Larger base size
            # Scale font size based on image diagonal (hypotenuse)
            image_diagonal = (image.width**2 + image.height**2) ** 0.5
            # Scale factor: for 800x600 image (diagonal ~1000), use base size
            # For 2480x3507 image (diagonal ~4300), scale up proportionally
            scale_factor = image_diagonal / 1000.0
            font_size = int(base_font_size * scale_factor)
            # Ensure minimum and maximum font sizes - bigger for visibility
            font_size = max(48, min(font_size, 150))
            try:
                # Try to use DejaVu Sans (available in most Linux containers)
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
                )
                print(
                    f"DEBUG: Successfully loaded DejaVu Sans Bold font at size {font_size}"
                )
            except:
                try:
                    # Try Arial
                    font = ImageFont.truetype("Arial", font_size)
                    print(f"DEBUG: Successfully loaded Arial font at size {font_size}")
                except:
                    try:
                        # Try Helvetica
                        font = ImageFont.truetype("Helvetica", font_size)
                        print(
                            f"DEBUG: Successfully loaded Helvetica font at size {font_size}"
                        )
                    except:
                        # Last resort: use default font but with a smaller size that works
                        font = ImageFont.load_default()
                        print(
                            f"DEBUG: Using default font (size may not be {font_size})"
                        )
                        # For default font, use a much smaller size that actually works
                        font_size = 24  # Default font works better with smaller sizes
                        print(
                            f"DEBUG: Adjusted font size to {font_size} for default font"
                        )

            print(
                f"DEBUG: Using scaled font size: {font_size} (image size: {image.width}x{image.height}, diagonal: {image_diagonal:.0f}, scale factor: {scale_factor:.2f})"
            )

            # Calculate text dimensions
            bbox = watermark_draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Position text in center
            x = (image.width - text_width) // 2
            y = (image.height - text_height) // 2

            print(
                f"DEBUG: Watermark position: ({x}, {y}), text size: {text_width}x{text_height}"
            )

            # Draw a large gray rectangle first for watermark background
            rect_width = min(text_width + 100, image.width - 200)
            rect_height = min(text_height + 50, image.height - 200)
            rect_x = max(100, x - 50)
            rect_y = max(100, y - 25)
            watermark_draw.rectangle(
                [rect_x, rect_y, rect_x + rect_width, rect_y + rect_height],
                fill=(128, 128, 128, 128),
            )  # Semi-transparent gray background
            print(
                f"DEBUG: Drew gray rectangle at ({rect_x}, {rect_y}) with size {rect_width}x{rect_height}"
            )

            # Draw watermark text with SOLID GRAY color for watermark
            # RGB(128, 128, 128) with alpha 255 (100% opaque) - SOLID GRAY
            watermark_draw.text((x, y), text, font=font, fill=(128, 128, 128, 255))
            print("DEBUG: Watermark text drawn on watermark layer")

            # No rotation - keep it horizontal

            # Use PIL's alpha_composite for proper transparency blending
            original_mode = image.mode
            if image.mode != "RGBA":
                image = image.convert("RGBA")
                print(f"DEBUG: Converted image from {original_mode} to RGBA")

            # Use alpha_composite instead of paste for better transparency handling
            image = Image.alpha_composite(image, watermark_img)
            print("DEBUG: Watermark alpha-composited onto base image")
            print(
                f"Horizontal watermark added with specifications: {font_size}px font, gray background, center position"
            )

            return image

        except Exception as e:
            print(f"Error adding watermark: {e}")
            import traceback

            traceback.print_exc()
            return image  # Return original image on error

    async def _convert_image_to_pdf(self, image: Image.Image, template: Dict) -> str:
        """Convert image to PDF"""
        try:
            # Convert to RGB if needed
            print(f"DEBUG: Converting image to PDF - current mode: {image.mode}")
            if image.mode == "RGBA":
                print("DEBUG: Image has alpha channel - compositing onto white background")
                # Create white background and composite (for watermark)
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
                image = rgb_image
                print("DEBUG: Conversion completed")
            elif image.mode != "RGB":
                print(f"DEBUG: Converting from {image.mode} to RGB")
                image = image.convert("RGB")

            # Handle different page sizes and orientations
            page_size = template.get("page_size", "A4")

            # Define target sizes for different page formats (width, height in pixels at 300 DPI)
            if page_size == "A4_Landscape":
                target_size = (3507, 2480)  # A4 landscape
            elif page_size == "A4":
                target_size = (2480, 3507)  # A4 portrait
            elif page_size == "Letter_Landscape":
                target_size = (3300, 2550)  # Letter landscape
            elif page_size == "Letter":
                target_size = (2550, 3300)  # Letter portrait
            elif page_size == "A3_Landscape":
                target_size = (4961, 3507)  # A3 landscape
            elif page_size == "A3":
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
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.close()

            # Convert to PDF
            image.save(temp_file.name, "PDF", resolution=300.0)
            print(f"PDF created: {temp_file.name}")

            return temp_file.name

        except Exception as e:
            print(f"Error converting to PDF: {e}")
            raise

    def _apply_background(
        self, base_image: Image.Image, background_id: str
    ) -> Image.Image:
        """Apply background image to the base template - all backgrounds are managed through admin panel"""
        try:
            background_path = None

            # Get background from admin resource service (all backgrounds are now admin-managed)
            try:
                from ..database import get_db
                db = next(get_db())
                background_data = self.admin_resource_service.get_background_by_name(db, background_id)
                if background_data and background_data.get('file_path'):
                    background_path = Path(background_data['file_path'])
                    print(f"Using admin-managed background: {background_path}")
                db.close()
            except Exception as e:
                print(f"Error getting admin background {background_id}: {e}")

            if not background_path:
                print(f"Unknown background ID: {background_id} - Please add it through the admin panel")
                return base_image

            if not background_path.exists():
                print(f"Background file not found: {background_path} - File may have been deleted")
                return base_image

            background = Image.open(background_path)
            print(f"Background loaded: {background.size}")

            # Resize background to match base image
            background = background.resize(base_image.size, Image.Resampling.LANCZOS)

            # Convert both images to RGBA if needed
            if base_image.mode != "RGBA":
                base_image = base_image.convert("RGBA")
            if background.mode != "RGBA":
                background = background.convert("RGBA")

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
            result = Image.new("RGBA", base_image.size, (255, 255, 255, 255))

            # Paste background first
            result.paste(background, (0, 0))

            # Paste base image on top with alpha blending
            result = Image.alpha_composite(result, base_image)

            # Convert back to RGB for PDF generation
            result = result.convert("RGB")

            print(f"Background applied successfully")
            return result

        except Exception as e:
            print(f"Error applying background: {e}")
            return base_image

    def _generate_qr_url(
        self, session: SessionModel, order: Optional[Order] = None
    ) -> str:
        """Generate permanent URL for QR code that uses /listen/ endpoint

        This generates URLs like: https://yoursite.com/listen/{identifier}
        The /listen/ endpoint generates fresh presigned URLs on-demand, avoiding
        AWS S3's 7-day maximum expiration limit for presigned URLs with SigV4.

        This approach ensures QR codes work for years as long as:
        - The domain remains active
        - The backend is running
        - The audio file exists in storage
        """
        try:
            print(
                f"DEBUG: Visual PDF _generate_qr_url called with session.audio_s3_key: {session.audio_s3_key if session else 'None'}"
            )
            print(f"DEBUG: order: {order}")

            if order:
                # Paid version - use order ID for permanent access
                print(f"DEBUG: Using order ID for permanent access: {order.id}")

                # Verify the audio file exists before generating URL
                if order.permanent_audio_s3_key and self.file_uploader.file_exists(order.permanent_audio_s3_key):
                    generated_url = f"{settings.base_url}/listen/{order.id}"
                    print(f"🔴🔴🔴 RETURNING QR URL (PAID): {generated_url} 🔴🔴🔴")
                    return generated_url
                else:
                    raise Exception(
                        f"Permanent audio file missing: {order.permanent_audio_s3_key if order.permanent_audio_s3_key else 'No key set'}"
                    )
            elif session and session.audio_s3_key:
                # Preview version - use session token for temporary access
                print(f"DEBUG: Using session token for preview access: {session.session_token}")

                # Verify the audio file exists before generating URL
                file_exists = self.file_uploader.file_exists(session.audio_s3_key)
                print(f"DEBUG: S3 file exists check result: {file_exists}")

                if file_exists:
                    generated_url = f"{settings.base_url}/listen/{session.session_token}"
                    print(f"🔴🔴🔴 RETURNING QR URL: {generated_url} 🔴🔴🔴")
                    return generated_url
                else:
                    raise Exception(
                        f"Session audio file missing: {session.audio_s3_key}"
                    )
            else:
                raise Exception("No audio file available for QR code generation")
        except Exception as e:
            print(f"Error generating QR URL: {e}")
            raise Exception(f"Failed to generate QR code URL: {str(e)}")
