"""Add international mailbox tables for Pasarex and Aeropost

Revision ID: 9b3c24948a8e
Revises: 
Create Date: 2025-08-20 19:12:54.029634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b3c24948a8e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create international_mailboxes table
    op.create_table('international_mailboxes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=False),
        sa.Column('carrier', sa.Enum('DHL', 'FedEx', 'UPS', 'Servientrega', 'Interrapidisimo', 'Pasarex', 'Aeropost', name='carriertype'), nullable=False),
        sa.Column('mailbox_id', sa.String(length=100), nullable=False),
        sa.Column('mailbox_number', sa.String(length=50), nullable=False),
        sa.Column('miami_address', sa.JSON(), nullable=False),
        sa.Column('spain_address', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('membership_type', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_international_mailboxes_customer_id'), 'international_mailboxes', ['customer_id'], unique=False)
    op.create_index(op.f('ix_international_mailboxes_mailbox_id'), 'international_mailboxes', ['mailbox_id'], unique=True)
    
    # Create package_prealerts table
    op.create_table('package_prealerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mailbox_id', sa.String(length=100), nullable=False),
        sa.Column('carrier', sa.Enum('DHL', 'FedEx', 'UPS', 'Servientrega', 'Interrapidisimo', 'Pasarex', 'Aeropost', name='carriertype'), nullable=False),
        sa.Column('tracking_number', sa.String(length=100), nullable=False),
        sa.Column('origin_carrier', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('declared_value', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('weight_lb', sa.Float(), nullable=False),
        sa.Column('dimensions', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('expected_arrival', sa.DateTime(), nullable=True),
        sa.Column('arrived_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_package_prealerts_mailbox_id'), 'package_prealerts', ['mailbox_id'], unique=False)
    op.create_index(op.f('ix_package_prealerts_tracking_number'), 'package_prealerts', ['tracking_number'], unique=False)
    
    # Create package_consolidations table
    op.create_table('package_consolidations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consolidation_id', sa.String(length=100), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=False),
        sa.Column('carrier', sa.Enum('DHL', 'FedEx', 'UPS', 'Servientrega', 'Interrapidisimo', 'Pasarex', 'Aeropost', name='carriertype'), nullable=False),
        sa.Column('package_ids', sa.JSON(), nullable=False),
        sa.Column('master_tracking', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('packages_count', sa.Integer(), nullable=False),
        sa.Column('total_weight_lb', sa.Float(), nullable=False),
        sa.Column('volumetric_weight', sa.Float(), nullable=True),
        sa.Column('billable_weight', sa.Float(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('savings_amount', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_package_consolidations_consolidation_id'), 'package_consolidations', ['consolidation_id'], unique=True)
    
    # Create customs_declarations table
    op.create_table('customs_declarations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.String(length=100), nullable=False),
        sa.Column('declaration_id', sa.String(length=100), nullable=False),
        sa.Column('carrier', sa.Enum('DHL', 'FedEx', 'UPS', 'Servientrega', 'Interrapidisimo', 'Pasarex', 'Aeropost', name='carriertype'), nullable=False),
        sa.Column('items', sa.JSON(), nullable=False),
        sa.Column('total_value', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('invoice_number', sa.String(length=100), nullable=True),
        sa.Column('purchase_date', sa.DateTime(), nullable=True),
        sa.Column('merchant', sa.String(length=200), nullable=True),
        sa.Column('customs_form_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customs_declarations_declaration_id'), 'customs_declarations', ['declaration_id'], unique=True)
    op.create_index(op.f('ix_customs_declarations_package_id'), 'customs_declarations', ['package_id'], unique=False)
    
    # Create import_cost_calculations table
    op.create_table('import_cost_calculations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.String(length=100), nullable=False),
        sa.Column('carrier', sa.Enum('DHL', 'FedEx', 'UPS', 'Servientrega', 'Interrapidisimo', 'Pasarex', 'Aeropost', name='carriertype'), nullable=False),
        sa.Column('product_value', sa.Float(), nullable=False),
        sa.Column('shipping_cost', sa.Float(), nullable=False),
        sa.Column('customs_duty', sa.Float(), nullable=False),
        sa.Column('vat', sa.Float(), nullable=False),
        sa.Column('handling_fee', sa.Float(), nullable=False),
        sa.Column('insurance', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('exchange_rate', sa.Float(), nullable=False),
        sa.Column('duty_rate', sa.Float(), nullable=False),
        sa.Column('vat_rate', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_cost_calculations_package_id'), 'import_cost_calculations', ['package_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_import_cost_calculations_package_id'), table_name='import_cost_calculations')
    op.drop_table('import_cost_calculations')
    
    op.drop_index(op.f('ix_customs_declarations_package_id'), table_name='customs_declarations')
    op.drop_index(op.f('ix_customs_declarations_declaration_id'), table_name='customs_declarations')
    op.drop_table('customs_declarations')
    
    op.drop_index(op.f('ix_package_consolidations_consolidation_id'), table_name='package_consolidations')
    op.drop_table('package_consolidations')
    
    op.drop_index(op.f('ix_package_prealerts_tracking_number'), table_name='package_prealerts')
    op.drop_index(op.f('ix_package_prealerts_mailbox_id'), table_name='package_prealerts')
    op.drop_table('package_prealerts')
    
    op.drop_index(op.f('ix_international_mailboxes_mailbox_id'), table_name='international_mailboxes')
    op.drop_index(op.f('ix_international_mailboxes_customer_id'), table_name='international_mailboxes')
    op.drop_table('international_mailboxes')