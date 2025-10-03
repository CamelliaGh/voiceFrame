#!/usr/bin/env python3
"""
Script to remove emojis from all suggested texts in the database.
"""

import sys
import os
import re

# Add the parent directory to Python path to enable absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models import Base, AdminSuggestedText

def remove_emojis(text):
    """Remove emojis from text using regex"""
    # Pattern to match most emojis and symbols
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "♪♫♬♩♭♮♯"              # musical symbols
        "❤💕💖💗💘💙💚💛💜🖤🤍🤎💝💞💟❣💔"  # hearts
        "✨⭐🌟💫⚡"              # stars and sparkles
        "🎉🎊🎈🎁🎂🎄🎃🎆🎇"      # celebration
        "]+",
        flags=re.UNICODE
    )

    # Remove emojis and clean up extra spaces
    cleaned = emoji_pattern.sub('', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Replace multiple spaces with single space
    cleaned = cleaned.strip()  # Remove leading/trailing spaces

    return cleaned

def clean_suggestions():
    """Remove emojis from all suggested texts"""

    db = SessionLocal()
    try:
        print("Starting emoji removal from suggested texts...")

        # Get all suggestions
        suggestions = db.query(AdminSuggestedText).all()
        print(f"Found {len(suggestions)} suggestions to check")

        updated_count = 0

        for suggestion in suggestions:
            original_text = suggestion.text
            cleaned_text = remove_emojis(original_text)

            if original_text != cleaned_text:
                print(f"Updating: '{original_text}' → '{cleaned_text}'")
                suggestion.text = cleaned_text
                updated_count += 1

        # Commit all changes
        if updated_count > 0:
            db.commit()
            print(f"\n✅ Successfully updated {updated_count} suggestions")
        else:
            print("\n✅ No emojis found - all suggestions are already clean")

        # Verify the cleanup
        print("\nVerifying cleanup...")
        suggestions_after = db.query(AdminSuggestedText).all()
        emoji_count = 0

        for suggestion in suggestions_after:
            if any(char in suggestion.text for char in ['♪', '💕', '💍', '🎊', '👶', '✨', '♥', '❤', '🎵', '🎶', '🎉', '🎂', '🎄', '🎃', '💖', '💗', '💘', '💙', '💚', '💛', '💜', '🖤', '🤍', '🤎', '💝', '💞', '💟', '❣', '💔', '⭐', '🌟', '💫', '⚡', '🎈', '🎁', '🎆', '🎇']):
                print(f"⚠️  Still has emoji: '{suggestion.text}'")
                emoji_count += 1

        if emoji_count == 0:
            print("✅ All emojis successfully removed!")
        else:
            print(f"⚠️  {emoji_count} suggestions still contain emojis")

    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clean_suggestions()
