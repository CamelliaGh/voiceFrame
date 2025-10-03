#!/usr/bin/env python3
"""
VoiceFrame Data Cleanup Script
Cleans up data for unpaid users and old sessions
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import SessionModel, Order
from config import DATABASE_URL

async def cleanup_unpaid_sessions(days_old=7):
    """
    Clean up sessions that are older than specified days and have no paid orders
    """
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as db:
        # Find sessions older than X days with no paid orders
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Get sessions that are old and have no paid orders
        old_unpaid_sessions = db.execute(text("""
            SELECT s.id, s.session_token, s.photo_s3_key, s.audio_s3_key, s.waveform_s3_key
            FROM sessions s
            LEFT JOIN orders o ON s.session_token = o.session_token AND o.status = 'paid'
            WHERE s.created_at < :cutoff_date
            AND o.id IS NULL
        """), {"cutoff_date": cutoff_date}).fetchall()

        print(f"Found {len(old_unpaid_sessions)} unpaid sessions older than {days_old} days")

        if old_unpaid_sessions:
            # Delete the sessions
            session_ids = [row.id for row in old_unpaid_sessions]
            db.execute(text("DELETE FROM sessions WHERE id = ANY(:session_ids)"),
                      {"session_ids": session_ids})
            db.commit()

            print(f"Deleted {len(session_ids)} unpaid sessions")

            # Note: S3 files will be cleaned up by S3 lifecycle policies
            # or you can add S3 cleanup logic here if needed

        else:
            print("No unpaid sessions to clean up")

async def cleanup_expired_sessions():
    """
    Clean up sessions that have passed their expiration date
    """
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as db:
        # Find expired sessions
        expired_sessions = db.execute(text("""
            SELECT id, session_token FROM sessions
            WHERE expires_at < NOW()
        """)).fetchall()

        print(f"Found {len(expired_sessions)} expired sessions")

        if expired_sessions:
            session_ids = [row.id for row in expired_sessions]
            db.execute(text("DELETE FROM sessions WHERE id = ANY(:session_ids)"),
                      {"session_ids": session_ids})
            db.commit()

            print(f"Deleted {len(session_ids)} expired sessions")

async def get_database_stats():
    """
    Get current database statistics
    """
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as db:
        # Count sessions
        total_sessions = db.execute(text("SELECT COUNT(*) FROM sessions")).scalar()
        paid_sessions = db.execute(text("""
            SELECT COUNT(DISTINCT s.id) FROM sessions s
            JOIN orders o ON s.session_token = o.session_token
            WHERE o.status = 'paid'
        """)).scalar()
        unpaid_sessions = total_sessions - paid_sessions

        # Count orders
        total_orders = db.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        paid_orders = db.execute(text("SELECT COUNT(*) FROM orders WHERE status = 'paid'")).scalar()

        # Old unpaid sessions
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        old_unpaid = db.execute(text("""
            SELECT COUNT(s.id) FROM sessions s
            LEFT JOIN orders o ON s.session_token = o.session_token AND o.status = 'paid'
            WHERE s.created_at < :cutoff_date AND o.id IS NULL
        """), {"cutoff_date": cutoff_date}).scalar()

        print("📊 Database Statistics:")
        print(f"  Total Sessions: {total_sessions}")
        print(f"  Paid Sessions: {paid_sessions}")
        print(f"  Unpaid Sessions: {unpaid_sessions}")
        print(f"  Total Orders: {total_orders}")
        print(f"  Paid Orders: {paid_orders}")
        print(f"  Old Unpaid Sessions (>7 days): {old_unpaid}")

async def main():
    print("🧹 VoiceFrame Data Cleanup")
    print("=" * 40)

    # Show current stats
    await get_database_stats()
    print()

    # Clean up expired sessions first
    print("🗑️  Cleaning up expired sessions...")
    await cleanup_expired_sessions()
    print()

    # Clean up old unpaid sessions
    print("🗑️  Cleaning up old unpaid sessions...")
    await cleanup_unpaid_sessions(days_old=7)
    print()

    # Show stats after cleanup
    print("📊 After cleanup:")
    await get_database_stats()

if __name__ == "__main__":
    asyncio.run(main())
