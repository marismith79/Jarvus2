"""Add workflow tools and triggers

Revision ID: add_workflow_tools_and_triggers
Revises: add_workflow_table
Create Date: 2024-01-01 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_workflow_tools_and_triggers'
down_revision: Union[str, None] = 'add_workflow_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tools and triggers columns to workflows table"""
    op.add_column('workflows', sa.Column('required_tools', sa.JSON(), nullable=True))
    op.add_column('workflows', sa.Column('trigger_type', sa.String(length=50), nullable=True))
    op.add_column('workflows', sa.Column('trigger_config', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove tools and triggers columns from workflows table"""
    op.drop_column('workflows', 'trigger_config')
    op.drop_column('workflows', 'trigger_type')
    op.drop_column('workflows', 'required_tools') 