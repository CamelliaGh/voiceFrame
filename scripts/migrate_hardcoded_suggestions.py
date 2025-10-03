#!/usr/bin/env python3
"""
Migration script to move hardcoded suggestions from TextCustomization.tsx to the database.
This script will add all hardcoded suggestions to the admin_suggested_texts table.
"""

import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models import Base, AdminSuggestedText

# Hardcoded suggestions from TextCustomization.tsx (without emojis)
HARDCODED_SUGGESTIONS = [
    # Romantic category
    {
        'text': "Our Song",
        'category': "romantic"
    },
    {
        'text': "I Love You",
        'category': "romantic"
    },
    {
        'text': "Forever & Always",
        'category': "romantic"
    },
    {
        'text': "Together Forever",
        'category': "romantic"
    },
    {
        'text': "My Heart",
        'category': "romantic"
    },
    {
        'text': "You & Me",
        'category': "romantic"
    },
    {
        'text': "Love Always",
        'category': "romantic"
    },
    {
        'text': "My Everything",
        'category': "romantic"
    },
    {
        'text': "Heart & Soul",
        'category': "romantic"
    },
    {
        'text': "True Love",
        'category': "romantic"
    },
    {
        'text': "Soulmates",
        'category': "romantic"
    },
    {
        'text': "Love Story",
        'category': "romantic"
    },

    # Wedding category
    {
        'text': "Wedding Day",
        'category': "wedding"
    },
    {
        'text': "First Dance",
        'category': "wedding"
    },
    {
        'text': "Mr. & Mrs.",
        'category': "wedding"
    },
    {
        'text': "Happily Ever After",
        'category': "wedding"
    },
    {
        'text': "Just Married",
        'category': "wedding"
    },
    {
        'text': "I Do",
        'category': "wedding"
    },
    {
        'text': "Our Vows",
        'category': "wedding"
    },
    {
        'text': "Wedding Song",
        'category': "wedding"
    },
    {
        'text': "Our Big Day",
        'category': "wedding"
    },
    {
        'text': "Husband & Wife",
        'category': "wedding"
    },

    # Anniversary category
    {
        'text': "Our Anniversary",
        'category': "anniversary"
    },
    {
        'text': "One Year Together",
        'category': "anniversary"
    },
    {
        'text': "5 Years Strong",
        'category': "anniversary"
    },
    {
        'text': "10 Years of Love",
        'category': "anniversary"
    },
    {
        'text': "Celebrating Us",
        'category': "anniversary"
    },
    {
        'text': "Anniversary Song",
        'category': "anniversary"
    },
    {
        'text': "Years of Happiness",
        'category': "anniversary"
    },
    {
        'text': "Our Milestone",
        'category': "anniversary"
    },

    # Baby & Family category
    {
        'text': "Baby's First Song",
        'category': "baby"
    },
    {
        'text': "Welcome Little One",
        'category': "baby"
    },
    {
        'text': "Our Family",
        'category': "baby"
    },
    {
        'text': "Sweet Dreams Baby",
        'category': "baby"
    },
    {
        'text': "Little Angel",
        'category': "baby"
    },
    {
        'text': "Family Love",
        'category': "baby"
    },
    {
        'text': "Baby Love",
        'category': "baby"
    },
    {
        'text': "Growing Family",
        'category': "baby"
    },

    # Special Moments category
    {
        'text': "Perfect Day",
        'category': "moments"
    },
    {
        'text': "Best Day Ever",
        'category': "moments"
    },
    {
        'text': "Unforgettable",
        'category': "moments"
    },
    {
        'text': "Precious Moments",
        'category': "moments"
    },
    {
        'text': "Sweet Memories",
        'category': "moments"
    },
    {
        'text': "Magical Moment",
        'category': "moments"
    },
    {
        'text': "Beautiful Memory",
        'category': "moments"
    },
    {
        'text': "Special Time",
        'category': "moments"
    }
]


def migrate_suggestions():
    """Migrate hardcoded suggestions to the database"""

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Starting migration of hardcoded suggestions...")

        # Check existing suggestions to avoid duplicates
        existing_texts = set()
        existing_suggestions = db.query(AdminSuggestedText).all()
        for suggestion in existing_suggestions:
            existing_texts.add(suggestion.text.lower().strip())

        print(f"Found {len(existing_suggestions)} existing suggestions in database")

        # Add new suggestions
        added_count = 0
        skipped_count = 0

        for suggestion_data in HARDCODED_SUGGESTIONS:
            text = suggestion_data['text']
            category = suggestion_data['category']

            # Check if this text already exists (case-insensitive)
            if text.lower().strip() in existing_texts:
                print(f"Skipping duplicate: '{text}'")
                skipped_count += 1
                continue

            # Create new suggestion
            suggestion = AdminSuggestedText(
                text=text,
                category=category,
                is_active=True,
                is_premium=False,
                usage_count=0
            )

            db.add(suggestion)
            existing_texts.add(text.lower().strip())
            added_count += 1
            print(f"Added: '{text}' (category: {category})")

        # Commit all changes
        db.commit()

        print(f"\nMigration completed!")
        print(f"Added: {added_count} new suggestions")
        print(f"Skipped: {skipped_count} duplicates")
        print(f"Total suggestions in database: {len(existing_suggestions) + added_count}")

        # Show summary by category
        print("\nSuggestions by category:")
        categories = db.query(AdminSuggestedText.category, db.func.count(AdminSuggestedText.id)).group_by(AdminSuggestedText.category).all()
        for category, count in categories:
            print(f"  {category or 'No category'}: {count}")

    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_suggestions()
