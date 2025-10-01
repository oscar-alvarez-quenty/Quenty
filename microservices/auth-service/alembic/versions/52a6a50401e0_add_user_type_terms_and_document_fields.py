"""add_user_type_terms_and_document_fields

Revision ID: 52a6a50401e0
Revises: 
Create Date: 2025-10-01 16:26:44.740939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52a6a50401e0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to users table
    op.add_column('users', sa.Column('user_type', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('document_type_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('document_number', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('terms_accepted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('terms_accepted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('privacy_policy_accepted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('privacy_policy_accepted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('marketing_consent', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('marketing_consent_at', sa.DateTime(), nullable=True))

    # Create indexes
    op.create_index('ix_users_user_type', 'users', ['user_type'])
    op.create_index('ix_users_document_number', 'users', ['document_number'])

    # Create foreign key constraint for document_type_id
    op.create_foreign_key('fk_users_document_type_id', 'users', 'document_types', ['document_type_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint('fk_users_document_type_id', 'users', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_users_document_number', 'users')
    op.drop_index('ix_users_user_type', 'users')

    # Drop columns
    op.drop_column('users', 'marketing_consent_at')
    op.drop_column('users', 'marketing_consent')
    op.drop_column('users', 'privacy_policy_accepted_at')
    op.drop_column('users', 'privacy_policy_accepted')
    op.drop_column('users', 'terms_accepted_at')
    op.drop_column('users', 'terms_accepted')
    op.drop_column('users', 'document_number')
    op.drop_column('users', 'document_type_id')
    op.drop_column('users', 'user_type')
