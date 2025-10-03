"""add_admin_config_table

Revision ID: 006_add_admin_config_table
Revises: 005_add_file_info_fields
Create Date: 2024-10-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '006_add_admin_config_table'
down_revision = '005_add_file_info_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create admin_config table
    op.create_table(
        'admin_config',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('value', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data_type', sa.String(20), nullable=False, server_default='string'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create unique index on key
    op.create_index('ix_admin_config_key', 'admin_config', ['key'], unique=True)

    # Insert default price configuration
    op.execute("""
        INSERT INTO admin_config (id, key, value, description, data_type, is_active, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'price_cents',
            '299',
            'Price for audio poster in cents (e.g., 299 = $2.99)',
            'integer',
            true,
            NOW(),
            NOW()
        )
    """)


def downgrade():
    # Drop admin_config table
    op.drop_index('ix_admin_config_key', 'admin_config')
    op.drop_table('admin_config')
