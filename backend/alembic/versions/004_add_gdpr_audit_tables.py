"""Migration: Add GDPR and Audit tables for Fase 3

Revision ID: 004_add_gdpr_audit_tables
Revises: 003_add_monitoring_tables
Create Date: 2026-06-23 05:09:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_add_gdpr_audit_tables'
down_revision: Union[str, None] = '003_add_monitoring_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Use UUID type compatible with both PostgreSQL and SQLite
UUID_TYPE = sa.String(36)  # UUID as string for cross-DB compatibility


def upgrade() -> None:
    # ============================================================
    # GDPR REQUESTS TABLE
    # ============================================================
    op.create_table(
        'gdpr_requests',
        sa.Column('id', UUID_TYPE, primary_key=True),
        sa.Column('company_id', UUID_TYPE, sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('request_number', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('request_type', sa.String(30), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('response_summary', sa.Text(), nullable=True),
        sa.Column('response_data_url', sa.String(500), nullable=True),
        sa.Column('requested_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('due_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('processed_by', sa.String(255), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('idx_gdpr_company_status', 'gdpr_requests', ['company_id', 'status'])
    op.create_index('idx_gdpr_status_due', 'gdpr_requests', ['status', 'due_at'])
    
    # ============================================================
    # AUDIT REPORTS TABLE
    # ============================================================
    op.create_table(
        'audit_reports',
        sa.Column('id', UUID_TYPE, primary_key=True),
        sa.Column('company_id', UUID_TYPE, sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('report_number', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('report_data', sa.JSON(), nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('json_url', sa.String(500), nullable=True),
        sa.Column('integrity_hash', sa.String(64), nullable=True),
        sa.Column('is_scheduled', sa.Boolean(), default=False),
        sa.Column('schedule_frequency', sa.String(20), nullable=True),
        sa.Column('next_scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('generated_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('idx_audit_company_type', 'audit_reports', ['company_id', 'report_type'])
    op.create_index('idx_audit_status', 'audit_reports', ['status', 'created_at'])
    
    # ============================================================
    # AUDIT REPORT SIGNATURES TABLE
    # ============================================================
    op.create_table(
        'audit_report_signatures',
        sa.Column('id', UUID_TYPE, primary_key=True),
        sa.Column('report_id', UUID_TYPE, sa.ForeignKey('audit_reports.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('signed_by', sa.String(255), nullable=False),
        sa.Column('signed_by_type', sa.String(20), default='system'),
        sa.Column('signature_hash', sa.String(64), nullable=False),
        sa.Column('document_hash', sa.String(64), nullable=False),
        sa.Column('algorithm', sa.String(50), default='SHA256'),
        sa.Column('key_id', sa.String(255), nullable=True),
        sa.Column('is_valid', sa.Boolean(), default=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # ============================================================
    # DATA RETENTION POLICIES TABLE
    # ============================================================
    op.create_table(
        'data_retention_policies',
        sa.Column('id', UUID_TYPE, primary_key=True),
        sa.Column('data_type', sa.String(50), unique=True, nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('legal_basis', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('allow_anonymization', sa.Boolean(), default=True),
        sa.Column('requires_manual_approval', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('updated_by', sa.String(255), nullable=True),
    )
    
    # Insert default retention policies
    op.bulk_insert('data_retention_policies', [
        {
            'id': '11111111-1111-1111-1111-111111111111',
            'data_type': 'verification_requests',
            'retention_days': 365 * 2,
            'legal_basis': 'contract',
            'description': 'Verificaciones de proveedores',
            'allow_anonymization': True,
            'requires_manual_approval': False,
            'is_active': True,
        },
        {
            'id': '22222222-2222-2222-2222-222222222222',
            'data_type': 'audit_logs',
            'retention_days': 365 * 3,
            'legal_basis': 'legal_obligation',
            'description': 'Logs de auditoría para compliance',
            'allow_anonymization': False,
            'requires_manual_approval': True,
            'is_active': True,
        },
        {
            'id': '33333333-3333-3333-3333-333333333333',
            'data_type': 'payment_records',
            'retention_days': 365 * 5,
            'legal_basis': 'legal_obligation',
            'description': 'Registros de pagos (requisito legal)',
            'allow_anonymization': False,
            'requires_manual_approval': True,
            'is_active': True,
        },
        {
            'id': '44444444-4444-4444-4444-444444444444',
            'data_type': 'session_logs',
            'retention_days': 90,
            'legal_basis': 'legitimate_interest',
            'description': 'Logs de sesiones de usuario',
            'allow_anonymization': True,
            'requires_manual_approval': False,
            'is_active': True,
        },
        {
            'id': '55555555-5555-5555-5555-555555555555',
            'data_type': 'gdpr_requests',
            'retention_days': 365 * 3,
            'legal_basis': 'legal_obligation',
            'description': 'Solicitudes GDPR/RGPD',
            'allow_anonymization': False,
            'requires_manual_approval': True,
            'is_active': True,
        },
    ])


def downgrade() -> None:
    op.drop_table('data_retention_policies')
    op.drop_table('audit_report_signatures')
    op.drop_index('idx_audit_status', table_name='audit_reports')
    op.drop_index('idx_audit_company_type', table_name='audit_reports')
    op.drop_table('audit_reports')
    op.drop_index('idx_gdpr_status_due', table_name='gdpr_requests')
    op.drop_index('idx_gdpr_company_status', table_name='gdpr_requests')
    op.drop_table('gdpr_requests')
