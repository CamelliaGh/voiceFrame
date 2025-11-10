#!/usr/bin/env python3
"""
Debug script to investigate QR code access issues
Run this to check session data and S3 file status
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
from backend.models import SessionModel, Order
from backend.config import settings
from backend.services.file_uploader import FileUploader

def debug_qr_access(identifier: str):
    """Debug QR code access for a given identifier"""
    db = SessionLocal()
    file_uploader = FileUploader()

    try:
        print(f"\n{'='*80}")
        print(f"🔍 DEBUGGING QR CODE ACCESS")
        print(f"{'='*80}\n")
        print(f"Identifier: {identifier}")
        print(f"Base URL: {settings.base_url}")
        print(f"Preview expiration: {settings.qr_code_preview_expiration} seconds ({settings.qr_code_preview_expiration / 86400:.1f} days)")
        print(f"\n{'='*80}\n")

        # Try as UUID (order)
        import uuid
        try:
            uuid.UUID(identifier)
            print("✅ Identifier is a valid UUID - checking orders...")
            order = db.query(Order).filter(
                Order.id == identifier,
                Order.status == "completed"
            ).first()

            if order:
                print(f"✅ Found completed order:")
                print(f"   - Order ID: {order.id}")
                print(f"   - Email: {order.email}")
                print(f"   - Status: {order.status}")
                print(f"   - Permanent audio key: {order.permanent_audio_s3_key}")

                if order.permanent_audio_s3_key:
                    exists = file_uploader.file_exists(order.permanent_audio_s3_key)
                    print(f"   - Audio file exists in S3: {'✅ YES' if exists else '❌ NO'}")
                    if exists:
                        print(f"\n{'='*80}")
                        print(f"✅ QR CODE SHOULD WORK - Order found with audio file")
                        print(f"{'='*80}\n")
                        return
                    else:
                        print(f"\n{'='*80}")
                        print(f"❌ PROBLEM: Order found but audio file missing from S3")
                        print(f"{'='*80}\n")
                        return
                else:
                    print(f"❌ Order has no permanent audio key")
            else:
                print(f"⚠️  No completed order found with this UUID")
        except ValueError:
            print("⚠️  Identifier is not a UUID - skipping order check")

        print(f"\n{'-'*80}\n")

        # Try as session token
        print("🔍 Checking sessions...")

        # Check with session_manager logic (expires_at > now)
        session_active = db.query(SessionModel).filter(
            SessionModel.session_token == identifier,
            SessionModel.expires_at > datetime.utcnow()
        ).first()

        print(f"Active session (expires_at > now): {'✅ Found' if session_active else '❌ Not found'}")

        # Check for any session regardless of expiration
        session_any = db.query(SessionModel).filter(
            SessionModel.session_token == identifier
        ).first()

        if session_any:
            print(f"\n✅ Found session in database:")
            print(f"   - Session token: {session_any.session_token}")
            print(f"   - Created at: {session_any.created_at}")
            print(f"   - Expires at: {session_any.expires_at}")
            print(f"   - Audio S3 key: {session_any.audio_s3_key}")
            print(f"   - Photo S3 key: {session_any.photo_s3_key}")
            print(f"   - Waveform S3 key: {session_any.waveform_s3_key}")

            now = datetime.utcnow()
            preview_expires_at = (session_any.created_at or now) + timedelta(
                seconds=settings.qr_code_preview_expiration
            )

            print(f"\n🕒 Time analysis:")
            print(f"   - Current time (UTC): {now}")
            print(f"   - Session created: {session_any.created_at}")
            print(f"   - Session expires_at: {session_any.expires_at}")
            print(f"   - Preview window expires: {preview_expires_at}")

            if session_any.expires_at:
                time_until_expires = session_any.expires_at - now
                print(f"   - Time until expires_at: {time_until_expires}")

            time_until_preview_expires = preview_expires_at - now
            print(f"   - Time until preview expires: {time_until_preview_expires}")

            print(f"\n📊 Status:")
            is_active = session_any.expires_at and session_any.expires_at > now
            within_preview = now <= preview_expires_at

            print(f"   - Session is active (expires_at > now): {'✅ YES' if is_active else '❌ NO'}")
            print(f"   - Within preview window: {'✅ YES' if within_preview else '❌ NO'}")

            # Check audio file
            if session_any.audio_s3_key:
                print(f"\n🔍 Checking audio file in S3...")
                exists = file_uploader.file_exists(session_any.audio_s3_key)
                print(f"   - Audio file exists: {'✅ YES' if exists else '❌ NO'}")

                if exists:
                    if within_preview:
                        print(f"\n{'='*80}")
                        print(f"✅ QR CODE SHOULD WORK - Session found within preview window with audio")
                        print(f"{'='*80}\n")
                    else:
                        print(f"\n{'='*80}")
                        print(f"❌ PROBLEM: Session expired beyond preview window")
                        print(f"{'='*80}\n")
                else:
                    print(f"\n{'='*80}")
                    print(f"❌ PROBLEM: Session found but audio file missing from S3")
                    print(f"   Key: {session_any.audio_s3_key}")
                    print(f"{'='*80}\n")
            else:
                print(f"\n{'='*80}")
                print(f"❌ PROBLEM: Session has no audio_s3_key")
                print(f"{'='*80}\n")
        else:
            print(f"\n{'='*80}")
            print(f"❌ PROBLEM: No session found with this token in database")
            print(f"   Token: {identifier}")
            print(f"{'='*80}\n")

            # List recent sessions to help debug
            print("\n🔍 Recent sessions in database:")
            recent = db.query(SessionModel).order_by(SessionModel.created_at.desc()).limit(5).all()
            for s in recent:
                print(f"   - {s.session_token[:20]}... (created: {s.created_at}, expires: {s.expires_at})")

    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_qr_access.py <session_token_or_order_id>")
        print("\nExample:")
        print("  python debug_qr_access.py abc123def456...")
        sys.exit(1)

    identifier = sys.argv[1]
    debug_qr_access(identifier)
