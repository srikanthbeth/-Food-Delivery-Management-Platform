"""add restaurant assignment to users

Revision ID: f1a557b96036
Revises: 6c25910c91a7
Create Date: 2026-09-08 11:08:10.508304

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f1a557b96036"
down_revision: Union[str, Sequence[str], None] = "6c25910c91a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        """
        ALTER TABLE users
        RENAME CONSTRAINT users_restaurant_id_fkey
        TO fk_users_restaurant_id
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute(
        """
        ALTER TABLE users
        RENAME CONSTRAINT fk_users_restaurant_id
        TO users_restaurant_id_fkey
        """
    )