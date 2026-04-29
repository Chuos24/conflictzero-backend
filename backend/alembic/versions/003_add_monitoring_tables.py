"""Migration: Add monitoring tables for Fase 2

Revision ID: 003_add_monitoring_tables
Revises: 002_add_network_tables
Create Date: 2026-04-29 14:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_monitoring_tables'
down_revision: Union[str, None] = '002_add_network_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create supplier_snapshots table
    op.create_table(
        'supplier_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('company_id', sa.String(11), sa.ForeignKey('companies.ruc', ondelete='CASCADE'), nullable=False),
        sa.Column('ruc', sa.String(11), nullable=False, index=True),
        sa.Column('raw_data', sa.JSON(), default=dict, nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('compliance_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    
    op.create_index('idx_snapshot_company_date', 'supplier_snapshots', ['company_id', 'snapshot_date'])
    
    # Create supplier_changes table
    op.create_table(
        'supplier_changes',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('snapshot_id', sa.Integer(), sa.ForeignKey('supplier_snapshots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', sa.String(11), sa.ForeignKey('companies.ruc', ondelete='CASCADE'), nullable=False),
        sa.Column('change_type', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('previous_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), default='info'),
        sa.Column('alert_sent', sa.Boolean(), default=False),
        sa.Column('alert_sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    
    op.create_index('idx_change_company_type', 'supplier_changes', ['company_id', 'change_type'])
    op.create_index('idx_change_severity', 'supplier_changes', ['severity', 'alert_sent'])
    
    # Create monitoring_alerts table
    op.create_table(
        'monitoring_alerts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('change_id', sa.Integer(), sa.ForeignKey('supplier_changes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', sa.String(11), sa.ForeignKey('companies.ruc', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(20), default='email'),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    
    op.create_index('idx_alert_user_status', 'monitoring_alerts', ['user_id', 'status'])
    op.create_index('idx_alert_company', 'monitoring_alerts', ['company_id'])
    
    # Create monitoring_rules table
    op.create_table(
        'monitoring_rules',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', sa.String(11), sa.ForeignKey('companies.ruc', ondelete='CASCADE'), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('conditions', sa.JSON(), default=dict, nullable=False),
        sa.Column('notify_email', sa.Boolean(), default=True),
        sa.Column('notify_dashboard', sa.Boolean(), default=True),
        sa.Column('notify_webhook', sa.Boolean(), default=False),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('frequency', sa.String(20), default='daily'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create monitoring_schedules table
    op.create_table(
        'monitoring_schedules',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('status', sa.String(20), default='scheduled'),
        sa.Column('schedule_type', sa.String(20), default='daily'),
        sa.Column('total_suppliers', sa.Integer(), default=0),
        sa.Column('checked_suppliers', sa.Integer(), default=0),
        sa.Column('changes_detected', sa.Integer(), default=0),
        sa.Column('alerts_generated', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    
    op.create_index('idx_schedule_status', 'monitoring_schedules', ['status', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_schedule_status', table_name='monitoring_schedules')
    op.drop_table('monitoring_schedules')
    op.drop_table('monitoring_rules')
    op.drop_index('idx_alert_company', table_name='monitoring_alerts')
    op.drop_index('idx_alert_user_status', table_name='monitoring_alerts')
    op.drop_table('monitoring_alerts')
    op.drop_index('idx_change_severity', table_name='supplier_changes')
    op.drop_index('idx_change_company_type', table_name='supplier_changes')
    op.drop_table('supplier_changes')
    op.drop_index('idx_snapshot_company_date', table_name='supplier_snapshots')
    op.drop_table('supplier_snapshots')
