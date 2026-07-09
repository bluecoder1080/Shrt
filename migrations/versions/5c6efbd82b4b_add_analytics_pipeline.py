"""Add analytics pipeline summary tables

Revision ID: 5c6efbd82b4b
Revises: 9a6efbd82b4a
Create Date: 2026-07-09 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c6efbd82b4b'
down_revision: Union[str, None] = '9a6efbd82b4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alter click_events table to add parsed attributes and aggregation flag
    op.add_column('click_events', sa.Column('country_code', sa.String(length=10), nullable=True))
    op.add_column('click_events', sa.Column('device_family', sa.String(length=50), nullable=True))
    op.add_column('click_events', sa.Column('browser_family', sa.String(length=50), nullable=True))
    op.add_column('click_events', sa.Column('os_family', sa.String(length=50), nullable=True))
    op.add_column('click_events', sa.Column('aggregated', sa.Boolean(), server_default='false', nullable=False))
    op.create_index(op.f('ix_click_events_aggregated'), 'click_events', ['aggregated'], unique=False)

    # 2. Create daily clicks summary table
    op.create_table(
        'clicks_daily_summary',
        sa.Column('url_id', sa.BigInteger(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('click_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['url_id'], ['urls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('url_id', 'date')
    )

    # 3. Create country clicks summary table
    op.create_table(
        'clicks_country_summary',
        sa.Column('url_id', sa.BigInteger(), nullable=False),
        sa.Column('country_code', sa.String(length=10), nullable=False),
        sa.Column('click_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['url_id'], ['urls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('url_id', 'country_code')
    )

    # 4. Create referrer clicks summary table
    op.create_table(
        'clicks_referrer_summary',
        sa.Column('url_id', sa.BigInteger(), nullable=False),
        sa.Column('referrer', sa.Text(), nullable=False),
        sa.Column('click_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['url_id'], ['urls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('url_id', 'referrer')
    )

    # 5. Create device clicks summary table
    op.create_table(
        'clicks_device_summary',
        sa.Column('url_id', sa.BigInteger(), nullable=False),
        sa.Column('device_family', sa.String(length=50), nullable=False),
        sa.Column('browser_family', sa.String(length=50), nullable=False),
        sa.Column('os_family', sa.String(length=50), nullable=False),
        sa.Column('click_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['url_id'], ['urls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('url_id', 'device_family', 'browser_family', 'os_family')
    )


def downgrade() -> None:
    op.drop_table('clicks_device_summary')
    op.drop_table('clicks_referrer_summary')
    op.drop_table('clicks_country_summary')
    op.drop_table('clicks_daily_summary')
    
    op.drop_index(op.f('ix_click_events_aggregated'), table_name='click_events')
    op.drop_column('click_events', 'aggregated')
    op.drop_column('click_events', 'os_family')
    op.drop_column('click_events', 'browser_family')
    op.drop_column('click_events', 'device_family')
    op.drop_column('click_events', 'country_code')
