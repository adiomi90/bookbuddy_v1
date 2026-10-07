"""add reservation model

Revision ID: f02299034388
Revises: 61de96ef9beb
Create Date: 2026-09-17 10:15:20.821089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f02299034388'
down_revision: Union[str, Sequence[str], None] = '61de96ef9beb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
