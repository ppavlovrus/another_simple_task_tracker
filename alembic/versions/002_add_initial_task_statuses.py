"""Add initial task statuses

Revision ID: 002_add_initial_task_statuses
Revises: 001_initial
Create Date: 2025-11-25 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '002_add_initial_task_statuses'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add initial task statuses to task_status table."""
    # Insert initial task statuses
    op.execute("""
        INSERT INTO task_status (name) VALUES 
        ('To Do'),
        ('In Progress'),
        ('Done'),
        ('Cancelled')
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    """Remove initial task statuses from task_status table."""
    op.execute("""
        DELETE FROM task_status 
        WHERE name IN ('To Do', 'In Progress', 'Done', 'Cancelled')
    """)


