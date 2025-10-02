"""add_file_info_fields

Revision ID: 005_add_file_info_fields
Revises: 004_increase_background_font_id_lengths
Create Date: 2024-10-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_file_info_fields'
down_revision = '004_increase_background_font_id_lengths'
branch_labels = None
depends_on = None


def upgrade():
    # Add file information fields to sessions table
    op.add_column('sessions', sa.Column('photo_filename', sa.String(255), nullable=True))
    op.add_column('sessions', sa.Column('photo_size', sa.Integer(), nullable=True))
    op.add_column('sessions', sa.Column('audio_filename', sa.String(255), nullable=True))
    op.add_column('sessions', sa.Column('audio_size', sa.Integer(), nullable=True))


def downgrade():
    # Remove file information fields from sessions table
    op.drop_column('sessions', 'audio_size')
    op.drop_column('sessions', 'audio_filename')
    op.drop_column('sessions', 'photo_size')
    op.drop_column('sessions', 'photo_filename')
