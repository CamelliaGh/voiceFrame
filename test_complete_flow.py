#!/usr/bin/env python3
"""
Test script to simulate the complete preview generation flow
"""
import sys
import os
from pathlib import Path

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent / 'backend'))

def test_complete_flow():
    """Test the complete flow from session update to PDF generation"""
    
    # Import the necessary modules
    from backend.services.visual_pdf_generator import VisualPDFGenerator
    from backend.services.visual_template_service import VisualTemplateService
    from backend.models import SessionModel
    from backend.database import get_db
    from sqlalchemy.orm import Session
    
    print("Testing complete flow...")
    
    # Create a mock session object
    class MockSession:
        def __init__(self):
            self.template_id = 'framed_template'
            self.custom_text = 'TEST TEXT FROM MOCK SESSION'
            self.font_id = 'script'
            self.photo_s3_key = 'temp_photos/test.jpg'
            self.waveform_s3_key = 'waveforms/test.png'
            self.audio_s3_key = 'temp_audio/test.mp3'
            self.background_id = 'none'
    
    mock_session = MockSession()
    
    # Test template service
    template_service = VisualTemplateService()
    template = template_service.get_template('framed_template')
    print(f"Template loaded: {template is not None}")
    if template:
        print(f"Template placeholders: {template.get('placeholders', {})}")
    
    # Test template path
    template_path = template_service.get_template_path('framed_template')
    print(f"Template path: {template_path}")
    print(f"Template file exists: {template_path.exists() if template_path else False}")
    
    # Test visual PDF generator
    visual_generator = VisualPDFGenerator()
    
    # Test the text rendering method directly
    try:
        from PIL import Image
        import tempfile
        
        # Load the template image
        if template_path and template_path.exists():
            base_image = Image.open(template_path)
            print(f"Template image loaded: {base_image.size}")
            
            # Test text rendering
            import asyncio
            asyncio.run(visual_generator._add_text_to_template(
                base_image, 
                mock_session.custom_text, 
                template, 
                mock_session
            ))
            
            # Save test result
            test_output = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            base_image.save(test_output.name)
            print(f"Test image saved to: {test_output.name}")
            
        else:
            print("Template file not found!")
            
    except Exception as e:
        print(f"Error in text rendering test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_flow()
