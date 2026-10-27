"""add current_day_attempts to practice_sessions

Revision ID: b7f3a1d9c224
Revises: ca46c0634eb6
Create Date: 2026-10-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'b7f3a1d9c224'
down_revision = 'ca46c0634eb6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'practice_sessions',
        sa.Column('current_day_attempts', sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column('practice_sessions', 'current_day_attempts')
