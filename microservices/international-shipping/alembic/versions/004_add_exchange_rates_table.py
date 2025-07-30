"""Add exchange rates table

Revision ID: 004_add_exchange_rates_table
Revises: 003_add_tracking_dashboard_tables
Create Date: 2025-07-30 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '004_add_exchange_rates_table'
down_revision = '003_add_tracking_dashboard_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Add exchange rates table for daily TRM storage"""
    op.create_table(
        'exchange_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('currency_from', sa.String(length=3), nullable=False),
        sa.Column('currency_to', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('currency_from', 'currency_to', 'date', name='uq_exchange_rate_date')
    )
    
    # Create indexes for efficient querying
    op.create_index('ix_exchange_rates_currency_from', 'exchange_rates', ['currency_from'])
    op.create_index('ix_exchange_rates_currency_to', 'exchange_rates', ['currency_to'])
    op.create_index('ix_exchange_rates_date', 'exchange_rates', ['date'])
    op.create_index('ix_exchange_rates_id', 'exchange_rates', ['id'])
    
    # Create composite index for common queries
    op.create_index(
        'ix_exchange_rates_currencies_date', 
        'exchange_rates', 
        ['currency_from', 'currency_to', 'date']
    )


def downgrade():
    """Remove exchange rates table"""
    op.drop_index('ix_exchange_rates_currencies_date', table_name='exchange_rates')
    op.drop_index('ix_exchange_rates_id', table_name='exchange_rates')
    op.drop_index('ix_exchange_rates_date', table_name='exchange_rates')
    op.drop_index('ix_exchange_rates_currency_to', table_name='exchange_rates')
    op.drop_index('ix_exchange_rates_currency_from', table_name='exchange_rates')
    op.drop_table('exchange_rates')