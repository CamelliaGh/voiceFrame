"""Add email_subscribers table

Revision ID: 007
Revises: e3f3b941e2d3
Create Date: 2025-01-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = 'e3f3b941e2d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_subscribers table
    op.create_table('email_subscribers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('subscribed_at', sa.DateTime(), nullable=True, default=sa.text('now()')),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('consent_data', sa.Text(), nullable=True),
        sa.Column('consent_updated_at', sa.DateTime(), nullable=True),
        sa.Column('data_processing_consent', sa.Boolean(), nullable=True, default=False),
        sa.Column('marketing_consent', sa.Boolean(), nullable=True, default=False),
        sa.Column('analytics_consent', sa.Boolean(), nullable=True, default=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_email_subscribers_email', 'email_subscribers', ['email'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_email_subscribers_email', table_name='email_subscribers')

    # Drop table
    op.drop_table('email_subscribers')
