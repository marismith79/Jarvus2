"""add_interaction_history_table

Revision ID: c8db2dbc4cf7
Revises: 497079b80600
Create Date: 2025-06-28 13:23:34.105302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8db2dbc4cf7'
down_revision: Union[str, None] = '497079b80600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
