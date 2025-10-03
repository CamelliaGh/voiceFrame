"""add_orientation_to_backgrounds

Revision ID: e3f3b941e2d3
Revises: 006_add_admin_config_table
Create Date: 2025-10-03 11:36:54.579260

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3f3b941e2d3'
down_revision = '006_add_admin_config_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add orientation field to admin_backgrounds table
    op.add_column('admin_backgrounds', sa.Column('orientation', sa.String(20), nullable=True, default='both'))

    # Update existing records to have 'both' orientation (suitable for both portrait and landscape)
    op.execute("UPDATE admin_backgrounds SET orientation = 'both' WHERE orientation IS NULL")

    # Make the field non-nullable after setting default values
    op.alter_column('admin_backgrounds', 'orientation', nullable=False)


def downgrade() -> None:
    # Remove orientation field from admin_backgrounds table
    op.drop_column('admin_backgrounds', 'orientation')
