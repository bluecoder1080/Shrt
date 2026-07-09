"""Initial migration

Revision ID: 9a6efbd82b4a
Revises: 
Create Date: 2026-07-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a6efbd82b4a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Create sequence for urls.id explicitly to ensure its name is urls_id_seq
    op.execute(sa.schema.CreateSequence(sa.Sequence('urls_id_seq')))

    # 3. Create urls table
    op.create_table(
        'urls',
        sa.Column('id', sa.BigInteger(), server_default=sa.text("nextval('urls_id_seq'::regclass)"), nullable=False),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('short_code', sa.String(length=50), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_urls_short_code'), 'urls', ['short_code'], unique=True)

    # 4. Create click_events table
    op.create_table(
        'click_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('url_id', sa.BigInteger(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['url_id'], ['urls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('click_events')
    op.drop_index(op.f('ix_urls_short_code'), table_name='urls')
    op.drop_table('urls')
    op.execute(sa.schema.DropSequence(sa.Sequence('urls_id_seq')))
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
