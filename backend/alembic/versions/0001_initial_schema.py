"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-10-02 17:07:06.331852
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=20), server_default='ADMIN', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.CheckConstraint("role IN ('ADMIN')", name=op.f('ck_users_role')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index('uq_users_email_lower', 'users', [sa.literal_column('lower(email)')], unique=True)
    op.create_table('audit_logs',
    sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=True),
    sa.Column('action', sa.String(length=40), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=False),
    sa.Column('entity_id', sa.String(length=40), nullable=True),
    sa.Column('before_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('after_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('request_id', sa.String(length=64), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_audit_logs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index('ix_audit_logs_occurred_at', 'audit_logs', ['occurred_at'], unique=False)
    op.create_index('ix_audit_logs_user_occurred', 'audit_logs', ['user_id', 'occurred_at'], unique=False)
    op.create_table('companies',
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('trade_name', sa.String(length=150), nullable=True),
    sa.Column('cnpj', sa.String(length=14), nullable=True),
    sa.Column('contact_name', sa.String(length=120), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=254), nullable=True),
    sa.Column('billing_cycle', sa.String(length=20), server_default='MENSAL', nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('payment_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.CheckConstraint("billing_cycle IN ('QUINZENAL','MENSAL')", name=op.f('ck_companies_billing_cycle')),
    sa.CheckConstraint("cnpj ~ '^[0-9]{14}$'", name=op.f('ck_companies_cnpj_digits')),
    sa.CheckConstraint('length(trim(name)) >= 2', name=op.f('ck_companies_name_min_length')),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_companies_created_by_users')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name=op.f('fk_companies_updated_by_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_companies'))
    )
    op.create_index('ix_companies_is_active', 'companies', ['is_active'], unique=False)
    op.create_index('uq_companies_cnpj', 'companies', ['cnpj'], unique=True, postgresql_where=sa.text('cnpj IS NOT NULL'))
    op.create_index('uq_companies_name_lower', 'companies', [sa.literal_column('lower(name)')], unique=True)
    op.create_table('cost_categories',
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('cost_type', sa.String(length=20), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.CheckConstraint("cost_type IN ('CUSTO_DIARIO','CUSTO_FIXO')", name=op.f('ck_cost_categories_cost_type')),
    sa.CheckConstraint('length(trim(name)) >= 2', name=op.f('ck_cost_categories_name_min_length')),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_cost_categories_created_by_users')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name=op.f('fk_cost_categories_updated_by_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cost_categories')),
    sa.UniqueConstraint('id', 'cost_type', name='uq_cost_categories_id_cost_type')
    )
    op.create_index('uq_cost_categories_name_lower', 'cost_categories', [sa.literal_column('lower(name)')], unique=True)
    op.create_table('customers',
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('document', sa.String(length=14), nullable=True),
    sa.Column('location', sa.String(length=150), nullable=True),
    sa.Column('billing_cycle', sa.String(length=20), server_default='MENSAL', nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('payment_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.CheckConstraint("billing_cycle IN ('A_VISTA','SEMANAL','QUINZENAL','MENSAL')", name=op.f('ck_customers_billing_cycle')),
    sa.CheckConstraint("document ~ '^([0-9]{11}|[0-9]{14})$'", name=op.f('ck_customers_document_digits')),
    sa.CheckConstraint('length(trim(name)) >= 2', name=op.f('ck_customers_name_min_length')),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_customers_created_by_users')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name=op.f('fk_customers_updated_by_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_customers'))
    )
    op.create_index('ix_customers_is_active', 'customers', ['is_active'], unique=False)
    op.create_index('ix_customers_name_lower', 'customers', [sa.literal_column('lower(name)')], unique=False)
    op.create_index('uq_customers_document', 'customers', ['document'], unique=True, postgresql_where=sa.text('document IS NOT NULL'))
    op.create_table('user_sessions',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_sessions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_sessions'))
    )
    op.create_index('ix_user_sessions_active_user', 'user_sessions', ['user_id'], unique=False, postgresql_where=sa.text('revoked_at IS NULL'))
    op.create_table('costs',
    sa.Column('category_id', sa.BigInteger(), nullable=False),
    sa.Column('cost_type', sa.String(length=20), nullable=False),
    sa.Column('cost_date', sa.Date(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.BigInteger(), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.CheckConstraint("cost_type IN ('CUSTO_DIARIO','CUSTO_FIXO')", name=op.f('ck_costs_cost_type')),
    sa.CheckConstraint('amount > 0', name=op.f('ck_costs_amount_positive')),
    sa.ForeignKeyConstraint(['category_id', 'cost_type'], ['cost_categories.id', 'cost_categories.cost_type'], name='fk_costs_category_type', onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_costs_created_by_users')),
    sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], name=op.f('fk_costs_deleted_by_users')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name=op.f('fk_costs_updated_by_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_costs'))
    )
    op.create_index('ix_costs_category_date', 'costs', ['category_id', 'cost_date'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('ix_costs_cost_date', 'costs', ['cost_date'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('ix_costs_type_date', 'costs', ['cost_type', 'cost_date'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_table('sales',
    sa.Column('buyer_type', sa.String(length=10), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=True),
    sa.Column('customer_id', sa.BigInteger(), nullable=True),
    sa.Column('sale_date', sa.Date(), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('notes', sa.String(length=500), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.BigInteger(), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.CheckConstraint("(buyer_type = 'COMPANY' AND company_id IS NOT NULL AND customer_id IS NULL) OR (buyer_type = 'CUSTOMER' AND customer_id IS NOT NULL AND company_id IS NULL)", name=op.f('ck_sales_single_buyer')),
    sa.CheckConstraint("buyer_type IN ('COMPANY','CUSTOMER')", name=op.f('ck_sales_buyer_type')),
    sa.CheckConstraint('quantity > 0', name=op.f('ck_sales_quantity_positive')),
    sa.CheckConstraint('subtotal = unit_price * quantity', name=op.f('ck_sales_subtotal_formula')),
    sa.CheckConstraint('unit_price > 0', name=op.f('ck_sales_unit_price_positive')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_sales_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_sales_created_by_users')),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name=op.f('fk_sales_customer_id_customers'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], name=op.f('fk_sales_deleted_by_users')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name=op.f('fk_sales_updated_by_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sales'))
    )
    op.create_index('ix_sales_buyer_type_date', 'sales', ['buyer_type', 'sale_date'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('ix_sales_company_date', 'sales', ['company_id', 'sale_date'], unique=False, postgresql_where=sa.text('deleted_at IS NULL AND company_id IS NOT NULL'))
    op.create_index('ix_sales_customer_date', 'sales', ['customer_id', 'sale_date'], unique=False, postgresql_where=sa.text('deleted_at IS NULL AND customer_id IS NOT NULL'))
    op.create_index('ix_sales_sale_date', 'sales', ['sale_date'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))


def downgrade() -> None:
    op.drop_index('ix_sales_sale_date', table_name='sales', postgresql_where=sa.text('deleted_at IS NULL'))
    op.drop_index('ix_sales_customer_date', table_name='sales', postgresql_where=sa.text('deleted_at IS NULL AND customer_id IS NOT NULL'))
    op.drop_index('ix_sales_company_date', table_name='sales', postgresql_where=sa.text('deleted_at IS NULL AND company_id IS NOT NULL'))
    op.drop_index('ix_sales_buyer_type_date', table_name='sales', postgresql_where=sa.text('deleted_at IS NULL'))
    op.drop_table('sales')
    op.drop_index('ix_costs_type_date', table_name='costs', postgresql_where=sa.text('deleted_at IS NULL'))
    op.drop_index('ix_costs_cost_date', table_name='costs', postgresql_where=sa.text('deleted_at IS NULL'))
    op.drop_index('ix_costs_category_date', table_name='costs', postgresql_where=sa.text('deleted_at IS NULL'))
    op.drop_table('costs')
    op.drop_index('ix_user_sessions_active_user', table_name='user_sessions', postgresql_where=sa.text('revoked_at IS NULL'))
    op.drop_table('user_sessions')
    op.drop_index('uq_customers_document', table_name='customers', postgresql_where=sa.text('document IS NOT NULL'))
    op.drop_index('ix_customers_name_lower', table_name='customers')
    op.drop_index('ix_customers_is_active', table_name='customers')
    op.drop_table('customers')
    op.drop_index('uq_cost_categories_name_lower', table_name='cost_categories')
    op.drop_table('cost_categories')
    op.drop_index('uq_companies_name_lower', table_name='companies')
    op.drop_index('uq_companies_cnpj', table_name='companies', postgresql_where=sa.text('cnpj IS NOT NULL'))
    op.drop_index('ix_companies_is_active', table_name='companies')
    op.drop_table('companies')
    op.drop_index('ix_audit_logs_user_occurred', table_name='audit_logs')
    op.drop_index('ix_audit_logs_occurred_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('uq_users_email_lower', table_name='users')
    op.drop_table('users')
