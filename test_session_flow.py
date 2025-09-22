#!/usr/bin/env python3
"""
Test script to verify the session update and preview generation flow
"""
import sys
import os
import asyncio
from pathlib import Path

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent / 'backend'))

async def test_session_flow():
    """Test the session update and preview generation flow"""
    
    # Import the necessary modules
    from backend.database import get_db
    from backend.models import SessionModel
    from backend.services.visual_pdf_generator import VisualPDFGenerator
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    from backend.config import settings
    
    print("Testing session flow...")
    
    # Create database connection
    engine = create_engine(settings.database_url)
    
    # Create a test session
    with Session(engine) as db:
        # Create a new session
        test_session = SessionModel(
            session_token="test_session_123",
            template_id="framed_template",
            custom_text="TEST CUSTOM TEXT FROM SESSION FLOW",
            font_id="script",
            photo_s3_key="temp_photos/test.jpg",
            waveform_s3_key="waveforms/test.png",
            audio_s3_key="temp_audio/test.mp3",
            background_id="none"
        )
        
        db.add(test_session)
        db.commit()
        db.refresh(test_session)
        
        print(f"Created test session: {test_session.session_token}")
        print(f"Session custom_text: '{test_session.custom_text}'")
        print(f"Session font_id: '{test_session.font_id}'")
        print(f"Session template_id: '{test_session.template_id}'")
        
        # Test the visual PDF generator
        visual_generator = VisualPDFGenerator()
        
        try:
            # Test generate_pdf method
            result = await visual_generator.generate_pdf(test_session, add_watermark=False)
            print(f"Preview generation result: {result}")
            
        except Exception as e:
            print(f"Error in preview generation: {e}")
            import traceback
            traceback.print_exc()
        
        # Clean up
        db.delete(test_session)
        db.commit()
        print("Cleaned up test session")

if __name__ == "__main__":
    asyncio.run(test_session_flow())
