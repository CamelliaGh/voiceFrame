import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import tempfile

class VisualTemplateService:
    """Manages visual templates designed in Canva/Figma"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent.parent / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._load_templates()
    
    def _load_templates(self):
        """Load visual template configurations from templates directory"""
        self.templates = {}
        
        # Scan templates directory for template configurations
        for template_dir in self.templates_dir.iterdir():
            if template_dir.is_dir():
                template_id = template_dir.name
                config_file = template_dir / f"{template_id}_template.json"
                
                if config_file.exists():
                    try:
                        print(f"Loading template from: {config_file}")
                        with open(config_file, 'r') as f:
                            template_config = json.load(f)
                            print(f"Loaded template config: {template_config}")
                            self.templates[template_id] = template_config
                    except Exception as e:
                        print(f"Error loading template {template_id}: {e}")
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get template configuration by ID"""
        # Reload templates to get latest configuration
        self._load_templates()
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> Dict[str, Dict]:
        """Get all available templates"""
        return self.templates
    
    def get_template_path(self, template_id: str) -> Optional[Path]:
        """Get the file path for a template image"""
        template = self.get_template(template_id)
        if template and template.get('template_file'):
            template_path = self.templates_dir / template_id / template['template_file']
            if template_path.exists():
                return template_path
        return None
    
    def get_placeholder_coordinates(self, template_id: str, element: str) -> Optional[Dict]:
        """Get placeholder coordinates for a specific element"""
        template = self.get_template(template_id)
        if template and 'placeholders' in template:
            return template['placeholders'].get(element)
        return None
    
    def list_available_templates(self) -> List[str]:
        """List all available template IDs"""
        return list(self.templates.keys())
    

    
    def create_watermarked_preview(self, template_id: str, output_path: str) -> str:
        """Create a watermarked preview of a template"""
        template_path = self.get_template_path(template_id)
        if not template_path:
            raise ValueError(f"Template {template_id} not found")
        
        # Load the template image
        with Image.open(template_path) as img:
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create a copy for watermarking
            watermarked = img.copy()
            draw = ImageDraw.Draw(watermarked)
            
            # Try to load a font, fall back to default if not available
            try:
                font_size = max(24, min(img.width, img.height) // 20)
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Add watermark text
            watermark_text = "PREVIEW - WATERMARKED"
            text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Position watermark in center
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
            
            # Add semi-transparent background for watermark
            padding = 20
            draw.rectangle(
                [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
                fill=(255, 255, 255, 180)
            )
            
            # Add watermark text
            draw.text((x, y), watermark_text, fill=(128, 128, 128, 255), font=font)
            
            # Save watermarked image
            watermarked.save(output_path, "PNG")
            
        return output_path
