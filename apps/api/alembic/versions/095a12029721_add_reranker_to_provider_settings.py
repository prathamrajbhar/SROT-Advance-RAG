"""add_reranker_to_provider_settings

Revision ID: 095a12029721
Revises: 094f26029720
Create Date: 2026-09-27 23:33:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '095a12029721'
down_revision: Union[str, None] = '094f26029720'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'provider_settings',
        sa.Column(
            'default_reranker_model',
            sa.String(length=100),
            server_default='ms-marco-MiniLM-L-12-v2',
            nullable=False,
        )
    )


def downgrade() -> None:
    op.drop_column('provider_settings', 'default_reranker_model')
