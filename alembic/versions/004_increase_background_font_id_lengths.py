"""Increase background_id and font_id field lengths for admin resources

Revision ID: 004
Revises: 003
Create Date: 2025-10-01 20:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Increase background_id field length from 50 to 255 characters
    op.alter_column('sessions', 'background_id',
                    existing_type=sa.String(50),
                    type_=sa.String(255),
                    existing_nullable=True)

    # Increase font_id field length from 50 to 255 characters
    op.alter_column('sessions', 'font_id',
                    existing_type=sa.String(50),
                    type_=sa.String(255),
                    existing_nullable=True)


def downgrade():
    # Revert background_id field length back to 50 characters
    op.alter_column('sessions', 'background_id',
                    existing_type=sa.String(255),
                    type_=sa.String(50),
                    existing_nullable=True)

    # Revert font_id field length back to 50 characters
    op.alter_column('sessions', 'font_id',
                    existing_type=sa.String(255),
                    type_=sa.String(50),
                    existing_nullable=True)
