"""Add bulk upload tables

Revision ID: 002
Revises: 001
Create Date: 2025-07-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bulk_uploads table
    op.create_table('bulk_uploads',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('unique_id', sa.String(length=255), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('total_rows', sa.Integer(), nullable=True),
    sa.Column('valid_rows', sa.Integer(), nullable=True),
    sa.Column('invalid_rows', sa.Integer(), nullable=True),
    sa.Column('processed_rows', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('error_summary', sa.JSON(), nullable=True),
    sa.Column('company_id', sa.String(length=255), nullable=False),
    sa.Column('uploaded_by', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('unique_id')
    )
    op.create_index(op.f('ix_bulk_uploads_id'), 'bulk_uploads', ['id'], unique=False)
    
    # Create bulk_upload_items table
    op.create_table('bulk_upload_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('row_number', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('weight', sa.Float(), nullable=True),
    sa.Column('volume', sa.Float(), nullable=True),
    sa.Column('value', sa.Float(), nullable=True),
    sa.Column('hs_code', sa.String(length=50), nullable=True),
    sa.Column('country_of_origin', sa.String(length=100), nullable=True),
    sa.Column('destination_country', sa.String(length=100), nullable=True),
    sa.Column('validation_errors', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('bulk_upload_id', sa.Integer(), nullable=False),
    sa.Column('manifest_id', sa.Integer(), nullable=True),
    sa.Column('manifest_item_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['bulk_upload_id'], ['bulk_uploads.id'], ),
    sa.ForeignKeyConstraint(['manifest_id'], ['manifests.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bulk_upload_items_id'), 'bulk_upload_items', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_bulk_upload_items_id'), table_name='bulk_upload_items')
    op.drop_table('bulk_upload_items')
    op.drop_index(op.f('ix_bulk_uploads_id'), table_name='bulk_uploads')
    op.drop_table('bulk_uploads')