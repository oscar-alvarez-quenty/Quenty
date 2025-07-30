"""Add tracking dashboard tables

Revision ID: 003
Revises: 002
Create Date: 2025-07-30 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tracking_events table
    op.create_table('tracking_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tracking_number', sa.String(length=255), nullable=False),
    sa.Column('event_timestamp', sa.DateTime(), nullable=False),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('carrier_code', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('manifest_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['manifest_id'], ['manifests.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tracking_events_id'), 'tracking_events', ['id'], unique=False)
    op.create_index(op.f('ix_tracking_events_tracking_number'), 'tracking_events', ['tracking_number'], unique=False)
    
    # Create bulk_tracking_dashboards table
    op.create_table('bulk_tracking_dashboards',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('unique_id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('tracking_numbers', sa.JSON(), nullable=True),
    sa.Column('status_filters', sa.JSON(), nullable=True),
    sa.Column('carrier_filters', sa.JSON(), nullable=True),
    sa.Column('date_range_start', sa.DateTime(), nullable=True),
    sa.Column('date_range_end', sa.DateTime(), nullable=True),
    sa.Column('refresh_interval', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('company_id', sa.String(length=255), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('unique_id')
    )
    op.create_index(op.f('ix_bulk_tracking_dashboards_id'), 'bulk_tracking_dashboards', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_bulk_tracking_dashboards_id'), table_name='bulk_tracking_dashboards')
    op.drop_table('bulk_tracking_dashboards')
    op.drop_index(op.f('ix_tracking_events_tracking_number'), table_name='tracking_events')
    op.drop_index(op.f('ix_tracking_events_id'), table_name='tracking_events')
    op.drop_table('tracking_events')