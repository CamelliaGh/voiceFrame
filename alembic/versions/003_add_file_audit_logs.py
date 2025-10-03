"""Add file audit logs table

Revision ID: 003
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create file_audit_logs table
    op.create_table('file_audit_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),

        # Context information
        sa.Column('user_identifier', sa.String(255), nullable=True),
        sa.Column('session_token', sa.String(255), nullable=True),
        sa.Column('order_id', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(255), nullable=True),
        sa.Column('api_endpoint', sa.String(255), nullable=True),

        # File operation details
        sa.Column('source_path', sa.Text(), nullable=True),
        sa.Column('destination_path', sa.Text(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('encryption_status', sa.String(50), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Additional metadata
        sa.Column('additional_metadata', sa.Text(), nullable=True),
        sa.Column('additional_details', sa.Text(), nullable=True),

        # Compliance fields
        sa.Column('retention_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True),
        sa.Column('legal_basis', sa.String(100), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better query performance
    op.create_index('ix_file_audit_logs_timestamp', 'file_audit_logs', ['timestamp'])
    op.create_index('ix_file_audit_logs_user_identifier', 'file_audit_logs', ['user_identifier'])
    op.create_index('ix_file_audit_logs_session_token', 'file_audit_logs', ['session_token'])
    op.create_index('ix_file_audit_logs_operation_type', 'file_audit_logs', ['operation_type'])
    op.create_index('ix_file_audit_logs_file_type', 'file_audit_logs', ['file_type'])
    op.create_index('ix_file_audit_logs_status', 'file_audit_logs', ['status'])
    op.create_index('ix_file_audit_logs_order_id', 'file_audit_logs', ['order_id'])
    op.create_index('ix_file_audit_logs_retention_date', 'file_audit_logs', ['retention_date'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_file_audit_logs_retention_date', table_name='file_audit_logs')
    op.drop_index('ix_file_audit_logs_order_id', table_name='file_audit_logs')
    op.drop_index('ix_file_audit_logs_status', table_name='file_audit_logs')
    op.drop_index('ix_file_audit_logs_file_type', table_name='file_audit_logs')
    op.drop_index('ix_file_audit_logs_operation_type', table_name='file_audit_logs')
    op.drop_index('ix_file_audit_logs_session_token', table_name='file_audit_logs')
    op.drop_index('ix_file_audit_logs_user_identifier', table_name='file_audit_logs')
    op.drop_index('ix_file_audit_logs_timestamp', table_name='file_audit_logs')

    # Drop table
    op.drop_table('file_audit_logs')
